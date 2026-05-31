from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from database import get_db
import models
import auth as auth_utils
import crawler
import seo_analyzer
import word_generator
import pagespeed
import ai_advisor
import os

router = APIRouter(prefix="/api/audit", tags=["audit"])

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")


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

    try:
        audit = db.query(models.Audit).filter(models.Audit.id == audit_id).first()
        if not audit:
            return

        def update_progress(msg: str, pct: int):
            audit.progress = pct
            audit.progress_message = msg
            db.commit()

        update_progress("Starting audit...", 5)

        # Determine how many pages to crawl
        max_pages = 15 if audit_type == "full" else 10 if audit_type == "technical" else 5

        # Crawl pages
        update_progress("Crawling website pages...", 15)
        pages = crawler.crawl_website(url, max_pages=max_pages)

        update_progress("Fetching robots.txt...", 35)
        robots_txt = crawler.fetch_robots_txt(url)

        update_progress("Fetching sitemap...", 45)
        sitemap = crawler.fetch_sitemap(url)

        # Analyze
        update_progress("Analyzing technical SEO...", 55)
        technical_data = seo_analyzer.analyze_technical_seo(url, robots_txt, sitemap, pages)

        update_progress("Analyzing pages...", 65)
        pages_analysis = []
        for page in pages:
            if not page.get("error"):
                analysis = seo_analyzer.analyze_page(page)
                pages_analysis.append(analysis)

        update_progress("Generating tracking guide...", 72)
        tracking_guide = seo_analyzer.generate_tracking_guide(url)

        # PageSpeed Insights — real Core Web Vitals from Google
        update_progress("Fetching Google PageSpeed Insights...", 78)
        pagespeed_data = pagespeed.run_full_pagespeed(url)

        # Claude AI recommendations
        update_progress("Generating AI-powered recommendations...", 84)
        ai_recommendations = ai_advisor.generate_seo_recommendations(
            url, technical_data, pages_analysis, pagespeed_data
        )

        # Store results
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

        # Generate Word docs
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

    except Exception as e:
        audit = db.query(models.Audit).filter(models.Audit.id == audit_id).first()
        if audit:
            audit.status = "failed"
            audit.progress_message = f"Error: {str(e)}"
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
        raise HTTPException(status_code=400, detail=f"Invalid audit type. Choose from: {list(AUDIT_TYPES.keys())}")

    audit = models.Audit(
        user_id=current_user.id,
        url=data.url.strip().rstrip("/"),
        audit_type=data.audit_type,
        status="running",
        progress=0,
        progress_message="Queued...",
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    from database import DATABASE_URL
    background_tasks.add_task(run_audit_task, audit.id, audit.url, audit.audit_type, DATABASE_URL)

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
        raise HTTPException(status_code=404, detail="Audit not found")

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
        raise HTTPException(status_code=404, detail="Audit not found")
    if audit.status != "completed":
        raise HTTPException(status_code=400, detail=f"Audit not completed yet (status: {audit.status})")

    result = db.query(models.AuditResult).filter(models.AuditResult.audit_id == audit_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Results not found")

    return {
        "audit_id": audit.id,
        "url": audit.url,
        "audit_type": audit.audit_type,
        "technical_seo": result.technical_seo,
        "pages_data": result.pages_data,
        "suggestions": result.suggestions,
        "gtm_guide": result.gtm_guide,
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
