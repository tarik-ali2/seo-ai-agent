from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from database import get_db, DATABASE_URL
import models, auth as auth_utils
import crawler, seo_analyzer, competitor_analyzer, competitor_word
import os

router = APIRouter(prefix="/api/competitor", tags=["competitor"])
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports", "competitor")


class CompetitorRequest(BaseModel):
    our_url: str
    competitor_url: str


def _run_comparison(job_id: int, our_url: str, comp_url: str, db_url: str):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    job = db.query(models.Audit).filter(models.Audit.id == job_id).first()
    if not job:
        return

    def prog(msg, pct):
        job.progress = pct
        job.progress_message = msg
        db.commit()

    try:
        prog(f"Crawling our site: {our_url}", 10)
        our_pages = crawler.crawl_website(our_url, max_pages=6)

        prog(f"Crawling competitor: {comp_url}", 30)
        comp_pages = crawler.crawl_website(comp_url, max_pages=6)

        prog("Fetching robots.txt & sitemaps...", 50)
        our_robots  = crawler.fetch_robots_txt(our_url)
        comp_robots = crawler.fetch_robots_txt(comp_url)
        our_sitemap = crawler.fetch_sitemap(our_url)
        comp_sitemap = crawler.fetch_sitemap(comp_url)

        prog("Analyzing technical SEO...", 60)
        our_tech  = seo_analyzer.analyze_technical_seo(our_url, our_robots, our_sitemap, our_pages)
        comp_tech = seo_analyzer.analyze_technical_seo(comp_url, comp_robots, comp_sitemap, comp_pages)

        prog("Running competitor analysis...", 75)
        result = competitor_analyzer.run_competitor_analysis(
            our_url, our_pages, our_tech,
            comp_url, comp_pages, comp_tech,
        )

        prog("Generating comparison Word document...", 88)
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

    except Exception as e:
        job.status = "failed"
        job.progress_message = f"Error: {e}"
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
    our_url  = data.our_url.strip().rstrip("/")
    comp_url = data.competitor_url.strip().rstrip("/")

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
        raise HTTPException(404, "Audit not found")

    doc_path = os.path.join(REPORTS_DIR, str(audit_id), "Competitor_SEO_Comparison.docx")
    if not os.path.exists(doc_path):
        raise HTTPException(404, "Report not yet generated")

    return FileResponse(
        path=doc_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"Competitor_SEO_Comparison_{audit_id}.docx",
    )
