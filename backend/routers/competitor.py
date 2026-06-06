import os
import time
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db, DATABASE_URL
from security import validate_crawl_url
from logger import get_logger
import models
import auth as auth_utils
import crawler
import seo_analyzer
import competitor_analyzer
import competitor_word
import ai_advisor

log = get_logger("seo_agent.competitor")

router = APIRouter(prefix="/api/competitor", tags=["competitor"])
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports", "competitor")

MAX_COMPARISON_SECONDS = 300
MAX_COMPARISONS_PER_HOUR = 5


class CompetitorRequest(BaseModel):
    our_url: str
    competitor_url: str


def _run_comparison(job_id: int, our_url: str, comp_url: str, db_url: str):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    start_time = time.monotonic()

    def check_timeout(step: str):
        elapsed = time.monotonic() - start_time
        if elapsed > MAX_COMPARISON_SECONDS:
            raise TimeoutError(
                f"Comparison exceeded {MAX_COMPARISON_SECONDS}s limit (stopped at: {step})"
            )

    job = db.query(models.Audit).filter(models.Audit.id == job_id).first()
    if not job:
        return

    def prog(msg: str, pct: int):
        job.progress = pct
        job.progress_message = msg
        db.commit()

    try:
        log.info("Competitor comparison %d started — %s vs %s", job_id, our_url, comp_url)

        check_timeout("crawl our site")
        prog(f"Crawling our site: {our_url}", 10)
        our_pages = crawler.crawl_website(our_url, max_pages=6)

        check_timeout("crawl competitor")
        prog(f"Crawling competitor: {comp_url}", 30)
        comp_pages = crawler.crawl_website(comp_url, max_pages=6)

        check_timeout("robots/sitemaps")
        prog("Fetching robots.txt & sitemaps...", 50)
        our_robots = crawler.fetch_robots_txt(our_url)
        comp_robots = crawler.fetch_robots_txt(comp_url)
        our_sitemap = crawler.fetch_sitemap(our_url)
        comp_sitemap = crawler.fetch_sitemap(comp_url)

        check_timeout("technical analysis")
        prog("Analyzing technical SEO...", 60)
        our_tech = seo_analyzer.analyze_technical_seo(our_url, our_robots, our_sitemap, our_pages)
        comp_tech = seo_analyzer.analyze_technical_seo(comp_url, comp_robots, comp_sitemap, comp_pages)

        check_timeout("comparison")
        prog("Running competitor analysis...", 75)
        result = competitor_analyzer.run_competitor_analysis(
            our_url, our_pages, our_tech,
            comp_url, comp_pages, comp_tech,
        )

        check_timeout("AI insights")
        prog("Generating AI-powered competitor insights...", 82)
        ai_insights = ai_advisor.generate_competitor_ai_insights(result)
        result["ai_insights"] = ai_insights

        check_timeout("word document")
        prog("Generating comparison Word document...", 90)
        out_dir = os.path.join(REPORTS_DIR, str(job_id))
        os.makedirs(out_dir, exist_ok=True)
        doc_path = os.path.join(out_dir, "Competitor_SEO_Comparison.docx")
        competitor_word.create_competitor_comparison_doc(result, doc_path)

        audit_result = models.AuditResult(
            audit_id=job_id,
            technical_seo=our_tech,
            pages_data=result.get("page_comparison", []),
            suggestions=result,
            gtm_guide={},
        )
        db.add(audit_result)

        job.status = "completed"
        job.progress = 100
        job.progress_message = "Comparison complete!"
        job.completed_at = datetime.utcnow()
        db.commit()

        elapsed = time.monotonic() - start_time
        log.info("Competitor comparison %d completed in %.1fs", job_id, elapsed)

    except TimeoutError as e:
        log.warning("Competitor comparison %d timed out: %s", job_id, e)
        job.status = "failed"
        job.progress_message = f"Comparison timed out after {MAX_COMPARISON_SECONDS}s."
        db.commit()
    except Exception as e:
        log.exception(
            "Competitor comparison %d failed — %s: %s", job_id, type(e).__name__, e
        )
        job.status = "failed"
        job.progress_message = f"Error: {type(e).__name__} — {str(e)[:200]}"
        db.commit()
    finally:
        db.close()


@router.post("/start")
def start_comparison(
    data: CompetitorRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    # Validate both URLs and guard against SSRF
    our_url = validate_crawl_url(data.our_url)
    comp_url = validate_crawl_url(data.competitor_url)

    if our_url == comp_url:
        raise HTTPException(
            status_code=400,
            detail="Our URL and competitor URL must be different.",
        )

    # Per-user hourly rate limit
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_count = (
        db.query(models.Audit)
        .filter(
            models.Audit.user_id == current_user.id,
            models.Audit.audit_type == "competitor",
            models.Audit.created_at >= one_hour_ago,
        )
        .count()
    )
    if recent_count >= MAX_COMPARISONS_PER_HOUR:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit: max {MAX_COMPARISONS_PER_HOUR} competitor comparisons per hour.",
        )

    job = models.Audit(
        user_id=current_user.id,
        url=our_url,
        audit_type="competitor",
        status="running",
        progress=5,
        progress_message=f"Starting comparison: {our_url} vs {comp_url}",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(_run_comparison, job.id, our_url, comp_url, DATABASE_URL)

    log.info(
        "Competitor comparison %d queued by user %s — %s vs %s",
        job.id, current_user.username, our_url, comp_url,
    )

    return {
        "audit_id": job.id,
        "status": "running",
        "message": f"Comparison started: {our_url} vs {comp_url}",
    }


@router.get("/{audit_id}/download")
def download_comparison(
    audit_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    audit = db.query(models.Audit).filter(
        models.Audit.id == audit_id,
        models.Audit.user_id == current_user.id,
    ).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found.")

    doc_path = os.path.join(REPORTS_DIR, str(audit_id), "Competitor_SEO_Comparison.docx")
    if not os.path.exists(doc_path):
        raise HTTPException(status_code=404, detail="Report not yet generated.")

    return FileResponse(
        path=doc_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"Competitor_SEO_Comparison_{audit_id}.docx",
    )
