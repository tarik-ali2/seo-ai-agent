import os
import time
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from security import validate_crawl_url
from logger import get_logger
import models
import auth as auth_utils
import crawler
import seo_analyzer
import word_generator
import pagespeed
import ai_advisor

log = get_logger("seo_agent.audit")

router = APIRouter(prefix="/api/audit", tags=["audit"])

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")

# Background task must complete within this many seconds or it is aborted
MAX_AUDIT_SECONDS = 300

# Max audits a single user may start per hour
MAX_AUDITS_PER_HOUR = 10


class AuditRequest(BaseModel):
    url: str
    audit_type: str  # full | technical | onpage | product | category | blog | tracking


AUDIT_TYPES = {
    "full": "Full SEO Audit",
    "technical": "Technical SEO Audit",
    "onpage": "On-Page SEO",
    "product": "Product Page SEO",
    "category": "Category Page SEO",
    "blog": "Blog SEO Plan",
    "tracking": "GTM/GA4/Meta Pixel Guide",
}


def run_audit_task(audit_id: int, url: str, audit_type: str, db_url: str):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    start_time = time.monotonic()

    def check_timeout(step: str):
        elapsed = time.monotonic() - start_time
        if elapsed > MAX_AUDIT_SECONDS:
            raise TimeoutError(
                f"Audit exceeded {MAX_AUDIT_SECONDS}s limit (stopped at: {step})"
            )

    try:
        audit = db.query(models.Audit).filter(models.Audit.id == audit_id).first()
        if not audit:
            return

        def update_progress(msg: str, pct: int):
            audit.progress = pct
            audit.progress_message = msg
            db.commit()

        log.info("Audit %d started — %s (%s)", audit_id, url, audit_type)
        update_progress("Starting audit...", 5)

        max_pages = 15 if audit_type == "full" else 10 if audit_type == "technical" else 5

        check_timeout("crawl")
        update_progress("Crawling website pages...", 15)
        pages = crawler.crawl_website(url, max_pages=max_pages)

        check_timeout("robots.txt")
        update_progress("Fetching robots.txt...", 35)
        robots_txt = crawler.fetch_robots_txt(url)

        check_timeout("sitemap")
        update_progress("Fetching sitemap...", 45)
        sitemap = crawler.fetch_sitemap(url)

        check_timeout("technical analysis")
        update_progress("Analyzing technical SEO...", 55)
        technical_data = seo_analyzer.analyze_technical_seo(url, robots_txt, sitemap, pages)

        check_timeout("page analysis")
        update_progress("Analyzing pages...", 65)
        pages_analysis = []
        for page in pages:
            if not page.get("error"):
                pages_analysis.append(seo_analyzer.analyze_page(page))

        check_timeout("tracking guide")
        update_progress("Generating tracking guide...", 72)
        tracking_guide = seo_analyzer.generate_tracking_guide(url)

        check_timeout("pagespeed")
        update_progress("Fetching Google PageSpeed Insights...", 78)
        pagespeed_data = pagespeed.run_full_pagespeed(url)

        check_timeout("AI recommendations")
        update_progress("Generating AI-powered recommendations...", 84)
        ai_recommendations = ai_advisor.generate_seo_recommendations(
            url, technical_data, pages_analysis, pagespeed_data
        )

        audit_result = models.AuditResult(
            audit_id=audit_id,
            technical_seo=technical_data,
            pages_data=pages_analysis,
            suggestions={
                "pages_count": len(pages_analysis),
                "pagespeed": pagespeed_data,
                "ai_recommendations": ai_recommendations,
            },
            gtm_guide=tracking_guide,
        )
        db.add(audit_result)

        check_timeout("word generation")
        update_progress("Generating Word documents...", 92)
        output_dir = os.path.join(REPORTS_DIR, str(audit_id))
        audit_data = {
            "technical_seo": technical_data,
            "pages_analysis": pages_analysis,
            "tracking_guide": tracking_guide,
            "pagespeed": pagespeed_data,
            "ai_recommendations": ai_recommendations,
        }
        word_generator.generate_all_documents(audit_data, output_dir)

        audit.status = "completed"
        audit.progress = 100
        audit.progress_message = "Audit complete!"
        audit.completed_at = datetime.utcnow()
        db.commit()

        elapsed = time.monotonic() - start_time
        log.info("Audit %d completed in %.1fs — %s", audit_id, elapsed, url)

    except TimeoutError as e:
        log.warning("Audit %d timed out: %s", audit_id, e)
        audit = db.query(models.Audit).filter(models.Audit.id == audit_id).first()
        if audit:
            audit.status = "failed"
            audit.progress_message = f"Audit timed out after {MAX_AUDIT_SECONDS}s. Try a smaller site or use 'Technical' audit type."
            db.commit()
    except Exception as e:
        log.exception("Audit %d failed — %s: %s", audit_id, type(e).__name__, e)
        audit = db.query(models.Audit).filter(models.Audit.id == audit_id).first()
        if audit:
            audit.status = "failed"
            audit.progress_message = f"Error: {type(e).__name__} — {str(e)[:200]}"
            db.commit()
    finally:
        db.close()


@router.post("/start")
def start_audit(
    data: AuditRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    if data.audit_type not in AUDIT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audit type. Choose from: {list(AUDIT_TYPES.keys())}",
        )

    # Validate URL and guard against SSRF
    validated_url = validate_crawl_url(data.url)

    # Per-user hourly rate limit (DB-count based, works regardless of IP)
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_count = (
        db.query(models.Audit)
        .filter(
            models.Audit.user_id == current_user.id,
            models.Audit.created_at >= one_hour_ago,
        )
        .count()
    )
    if recent_count >= MAX_AUDITS_PER_HOUR:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit: max {MAX_AUDITS_PER_HOUR} audits per hour. Please wait before starting a new audit.",
        )

    audit = models.Audit(
        user_id=current_user.id,
        url=validated_url,
        audit_type=data.audit_type,
        status="running",
        progress=0,
        progress_message="Queued...",
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    from database import DATABASE_URL
    background_tasks.add_task(
        run_audit_task, audit.id, audit.url, audit.audit_type, DATABASE_URL
    )

    log.info(
        "Audit %d queued by user %s — %s (%s)",
        audit.id, current_user.username, validated_url, data.audit_type,
    )

    return {
        "audit_id": audit.id,
        "status": audit.status,
        "message": f"Audit started for {audit.url}",
    }


@router.get("/{audit_id}/status")
def get_audit_status(
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

    return {
        "audit_id": audit.id,
        "url": audit.url,
        "audit_type": audit.audit_type,
        "status": audit.status,
        "progress": audit.progress,
        "progress_message": audit.progress_message,
        "created_at": audit.created_at,
        "completed_at": audit.completed_at,
    }


@router.get("/{audit_id}/results")
def get_audit_results(
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
    if audit.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Audit not completed yet (status: {audit.status})",
        )

    result = db.query(models.AuditResult).filter(
        models.AuditResult.audit_id == audit_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Results not found.")

    return {
        "audit_id": audit.id,
        "url": audit.url,
        "audit_type": audit.audit_type,
        "technical_seo": result.technical_seo,
        "pages_data": result.pages_data,
        "suggestions": result.suggestions,
        "gtm_guide": result.gtm_guide,
    }


@router.get("/benchmarks")
def get_benchmarks(
    url: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    """Return score history for completed audits (optionally filtered by URL)."""
    query = (
        db.query(models.Audit)
        .filter(
            models.Audit.user_id == current_user.id,
            models.Audit.status == "completed",
        )
    )
    if url:
        query = query.filter(models.Audit.url == url)

    audits = query.order_by(models.Audit.created_at.desc()).limit(10).all()

    def _extract_scores(result):
        s = {}
        if not result:
            return s
        if result.suggestions:
            ps = result.suggestions.get("pagespeed", {})
            mobile = ps.get("mobile", {})
            if not mobile.get("error") and mobile.get("scores"):
                ms = mobile["scores"]
                s["performance"]    = ms.get("performance", 0)
                s["seo"]            = ms.get("seo", 0)
                s["accessibility"]  = ms.get("accessibility", 0)
                s["best_practices"] = ms.get("best_practices", 0)
        if result.pages_data:
            overalls = [
                p["scores"]["overall"]
                for p in result.pages_data
                if p.get("scores") and p["scores"].get("overall") is not None
            ]
            if overalls:
                s["onpage"] = round(sum(overalls) / len(overalls))
        return s

    rows = []
    for a in audits:
        result = db.query(models.AuditResult).filter(models.AuditResult.audit_id == a.id).first()
        rows.append({
            "audit_id":    a.id,
            "url":         a.url,
            "audit_type":  a.audit_type,
            "created_at":  a.created_at,
            "scores":      _extract_scores(result),
        })

    # Unique URLs for the dropdown
    all_urls = (
        db.query(models.Audit.url)
        .filter(
            models.Audit.user_id == current_user.id,
            models.Audit.status == "completed",
        )
        .distinct()
        .all()
    )

    return {
        "audits": rows,
        "available_urls": [u[0] for u in all_urls],
    }


@router.get("/list")
def list_audits(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    audits = (
        db.query(models.Audit)
        .filter(models.Audit.user_id == current_user.id)
        .order_by(models.Audit.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "audit_id": a.id,
            "url": a.url,
            "audit_type": a.audit_type,
            "status": a.status,
            "progress": a.progress,
            "created_at": a.created_at,
            "completed_at": a.completed_at,
        }
        for a in audits
    ]
