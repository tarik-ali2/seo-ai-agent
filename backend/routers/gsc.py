"""
Google Search Console router.

Endpoints:
  GET  /api/gsc/config               — check if OAuth is configured
  GET  /api/gsc/auth/url             — get OAuth URL (requires JWT auth)
  GET  /api/gsc/auth/callback        — OAuth callback from Google
  GET  /api/gsc/status               — connection status + properties list
  DELETE /api/gsc/disconnect         — remove stored credentials
  GET  /api/gsc/properties           — list GSC properties
  POST /api/gsc/audit/start          — start a GSC audit job
  GET  /api/gsc/audit/{id}/status    — poll job progress
  GET  /api/gsc/audit/{id}/results   — get completed results
  GET  /api/gsc/audit/{id}/download/{fmt} — download docx-zip or pdf
  GET  /api/gsc/audit/list           — list recent GSC audits
"""
import os, time
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db, DATABASE_URL
from logger import get_logger
import models, auth as auth_utils
from auth import SECRET_KEY

log = get_logger("seo_agent.gsc_router")

router = APIRouter(prefix="/api/gsc", tags=["gsc"])

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports", "gsc")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "http://localhost:8000/api/gsc/auth/callback",
)

MAX_GSC_AUDIT_SECONDS = 180
MAX_GSC_AUDITS_PER_HOUR = 5


# ── OAuth helpers ─────────────────────────────────────────────────────────────

def _client_config() -> dict:
    return {
        "web": {
            "client_id":     os.getenv("GOOGLE_CLIENT_ID", ""),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
            "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
            "token_uri":     "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    }


def _create_flow():
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_config(_client_config(), scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI
    return flow


def _create_state(user_id: int) -> str:
    from jose import jwt
    return jwt.encode(
        {"sub": str(user_id), "exp": datetime.utcnow() + timedelta(minutes=15)},
        SECRET_KEY, algorithm="HS256",
    )


def _decode_state(state: str) -> int:
    from jose import jwt, JWTError
    try:
        payload = jwt.decode(state, SECRET_KEY, algorithms=["HS256"])
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(400, "Invalid or expired OAuth state.")


def _get_credential(db: Session, user_id: int) -> models.GSCCredential | None:
    return db.query(models.GSCCredential).filter(
        models.GSCCredential.user_id == user_id
    ).first()


# ── Public config check ───────────────────────────────────────────────────────

@router.get("/config")
def get_config():
    """Returns whether Google OAuth is configured in the environment."""
    return {
        "configured": bool(
            os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET")
        ),
        "redirect_uri": REDIRECT_URI,
    }


# ── OAuth flow ────────────────────────────────────────────────────────────────

@router.get("/auth/url")
def get_auth_url(current_user: models.User = Depends(auth_utils.get_current_user)):
    if not os.getenv("GOOGLE_CLIENT_ID"):
        raise HTTPException(400, "Google OAuth not configured. Set GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET in backend/.env")
    flow = _create_flow()
    state = _create_state(current_user.id)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return {"auth_url": auth_url}


@router.get("/auth/callback")
def oauth_callback(code: str, state: str, db: Session = Depends(get_db)):
    """Google redirects here after user grants permission."""
    user_id = _decode_state(state)

    try:
        flow = _create_flow()
        flow.fetch_token(code=code)
        creds = flow.credentials
    except Exception as e:
        log.error("OAuth token exchange failed: %s", e)
        return RedirectResponse(f"{FRONTEND_URL}/dashboard?gsc_error=oauth_failed")

    # Upsert credentials
    existing = _get_credential(db, user_id)
    if existing:
        existing.access_token  = creds.token
        existing.refresh_token = creds.refresh_token or existing.refresh_token
        existing.token_expiry  = creds.expiry
    else:
        db.add(models.GSCCredential(
            user_id=user_id,
            access_token=creds.token,
            refresh_token=creds.refresh_token,
            token_expiry=creds.expiry,
        ))
    db.commit()

    log.info("GSC connected for user_id=%d", user_id)
    return RedirectResponse(f"{FRONTEND_URL}/dashboard?gsc_connected=true")


# ── Connection status ─────────────────────────────────────────────────────────

@router.get("/status")
def get_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    """Check if user has connected GSC and return their properties."""
    cred = _get_credential(db, current_user.id)
    if not cred:
        return {"connected": False, "properties": []}

    try:
        import gsc_client
        service, updated = gsc_client.build_service({
            "access_token":  cred.access_token,
            "refresh_token": cred.refresh_token,
        })
        if updated["access_token"] != cred.access_token:
            cred.access_token = updated["access_token"]
            db.commit()
        props = gsc_client.list_properties(service)
        return {"connected": True, "properties": props}
    except Exception as e:
        log.warning("GSC status check failed for user %d: %s", current_user.id, e)
        return {"connected": True, "properties": [], "warning": str(e)}


@router.delete("/disconnect")
def disconnect(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    cred = _get_credential(db, current_user.id)
    if cred:
        db.delete(cred)
        db.commit()
    return {"message": "Google Search Console disconnected."}


# ── Keyword Rank Tracker ─────────────────────────────────────────────────────

@router.get("/keywords/trends")
def get_keyword_trends(
    property_url: str,
    window: int = 28,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    """
    Fetch keyword position changes: current window vs previous window.
    Returns rising / falling / new / lost / stable classification per keyword.
    """
    cred = _get_credential(db, current_user.id)
    if not cred:
        raise HTTPException(400, "Google Search Console not connected.")

    try:
        import gsc_client, gsc_analyzer
        service, updated = gsc_client.build_service({
            "access_token":  cred.access_token,
            "refresh_token": cred.refresh_token,
        })
        if updated["access_token"] != cred.access_token:
            cred.access_token = updated["access_token"]
            db.commit()

        trends_raw = gsc_client.get_keyword_trends(service, property_url, window=window)
        result     = gsc_analyzer.classify_keyword_trends(trends_raw)
        log.info(
            "Keyword trends fetched for user %d — %s (%d keywords)",
            current_user.id, property_url, result["summary"]["total"],
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.error("Keyword trends failed for user %d: %s", current_user.id, e)
        raise HTTPException(500, f"Failed to fetch keyword trends: {str(e)[:200]}")


# ── Audit background task ─────────────────────────────────────────────────────

def _run_gsc_audit(report_id: int, property_url: str, cred_dict: dict, db_url: str):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    DB = sessionmaker(bind=engine)
    db = DB()

    start = time.monotonic()

    def timeout_check(step: str):
        if time.monotonic() - start > MAX_GSC_AUDIT_SECONDS:
            raise TimeoutError(f"GSC audit timed out at '{step}'")

    def prog(msg: str, pct: int):
        r = db.query(models.GSCReport).filter(models.GSCReport.id == report_id).first()
        if r:
            r.progress = pct
            r.progress_message = msg
            db.commit()

    try:
        import gsc_client, gsc_analyzer
        from ai_providers import generate_json, active_provider
        import gsc_word, gsc_pdf

        log.info("GSC audit %d started — %s", report_id, property_url)
        prog("Building Search Console connection...", 5)

        service, updated_cred = gsc_client.build_service(cred_dict)
        if updated_cred["access_token"] != cred_dict.get("access_token"):
            # Persist refreshed token
            cred_rec = db.query(models.GSCCredential).filter(
                models.GSCCredential.access_token == cred_dict["access_token"]
            ).first()
            if cred_rec:
                cred_rec.access_token = updated_cred["access_token"]
                db.commit()

        timeout_check("overview")
        prog("Fetching site performance overview...", 12)
        overview = gsc_client.get_overview(service, property_url, days=28)

        timeout_check("queries")
        prog("Fetching top search queries...", 22)
        top_queries = gsc_client.get_top_queries(service, property_url, days=28, limit=50)

        timeout_check("pages")
        prog("Fetching top pages...", 32)
        top_pages = gsc_client.get_top_pages(service, property_url, days=28, limit=50)

        timeout_check("trend")
        prog("Fetching 90-day trend data...", 42)
        date_trend = gsc_client.get_date_trend(service, property_url, days=90)

        timeout_check("devices")
        prog("Fetching device breakdown...", 50)
        devices = gsc_client.get_device_breakdown(service, property_url)

        timeout_check("comparison")
        prog("Comparing vs previous period...", 58)
        period = gsc_client.get_period_comparison(service, property_url)

        # Analysis
        timeout_check("analysis")
        prog("Detecting keyword opportunities...", 65)
        opps = gsc_analyzer.detect_keyword_opportunities(top_queries)

        prog("Detecting CTR opportunities...", 70)
        ctr_opps = gsc_analyzer.detect_ctr_opportunities(top_pages)

        prog("Detecting declining pages...", 74)
        declining = gsc_analyzer.detect_declining_pages(period)

        summary = gsc_analyzer.build_summary(overview, top_queries, top_pages, opps, declining, ctr_opps)

        # AI insights
        timeout_check("AI")
        prog("Generating AI-powered insights...", 80)
        ai_insights = _generate_ai_insights(overview, top_queries, top_pages, opps, declining, ctr_opps, summary)

        # Update DB record with all data
        report = db.query(models.GSCReport).filter(models.GSCReport.id == report_id).first()
        if not report:
            return

        report.overview         = overview
        report.top_queries      = top_queries
        report.top_pages        = top_pages
        report.date_trend       = date_trend
        report.device_breakdown = devices
        report.period_comparison = period
        report.opportunities    = opps
        report.ctr_opportunities = ctr_opps
        report.declining_pages  = declining
        report.ai_insights      = ai_insights
        db.commit()

        # Generate reports
        timeout_check("reports")
        prog("Generating Word reports (DOCX)...", 88)
        out_dir = os.path.join(REPORTS_DIR, str(report_id))
        report_data = {
            "property_url":    property_url,
            "overview":        overview,
            "top_queries":     top_queries,
            "top_pages":       top_pages,
            "device_breakdown":devices,
            "period_comparison":period,
            "opportunities":   opps,
            "ctr_opportunities":ctr_opps,
            "declining_pages": declining,
            "ai_insights":     ai_insights,
            "summary":         summary,
        }
        gsc_word.generate_all_gsc_docs(report_data, out_dir)

        prog("Generating PDF report...", 94)
        pdf_path = os.path.join(out_dir, "GSC_Audit.pdf")
        gsc_pdf.create_gsc_pdf(report_data, pdf_path)

        report.status = "completed"
        report.progress = 100
        report.progress_message = "GSC audit complete!"
        report.completed_at = datetime.utcnow()
        db.commit()

        elapsed = time.monotonic() - start
        log.info("GSC audit %d completed in %.1fs", report_id, elapsed)

    except TimeoutError as e:
        log.warning("GSC audit %d timed out: %s", report_id, e)
        r = db.query(models.GSCReport).filter(models.GSCReport.id == report_id).first()
        if r:
            r.status = "failed"
            r.progress_message = f"Timed out after {MAX_GSC_AUDIT_SECONDS}s."
            db.commit()
    except Exception as e:
        log.exception("GSC audit %d failed: %s", report_id, e)
        r = db.query(models.GSCReport).filter(models.GSCReport.id == report_id).first()
        if r:
            r.status = "failed"
            r.progress_message = f"{type(e).__name__}: {str(e)[:200]}"
            db.commit()
    finally:
        db.close()


def _generate_ai_insights(overview, top_queries, top_pages, opps, declining, ctr_opps, summary) -> dict:
    from ai_providers import generate_json, active_provider
    import json

    if active_provider() == "none":
        return {"error": "No AI provider configured."}

    prompt_data = {
        "performance": {
            "clicks":      summary["total_clicks"],
            "impressions": summary["total_impressions"],
            "avg_ctr":     summary["avg_ctr"],
            "avg_position":summary["avg_position"],
            "date_range":  summary["date_range"],
        },
        "top_queries":  [{"query": q["query"], "clicks": q["clicks"], "position": q["position"]} for q in top_queries[:10]],
        "top_pages":    [{"page": p["page"], "clicks": p["clicks"]} for p in top_pages[:5]],
        "page2_opportunities": len(opps),
        "top_opportunities": [{"query": o["query"], "position": o["current_position"], "impressions": o["impressions"]} for o in opps[:5]],
        "ctr_opportunities": len(ctr_opps),
        "declining_pages": len(declining),
        "critical_declines": summary["critical_declines"],
        "top_declines": [{"page": d["page"], "pct_change": d["pct_change"]} for d in declining[:3]],
    }

    system = (
        "You are a senior SEO analyst. Analyze Google Search Console data and give concrete, "
        "specific, actionable recommendations. Respond ONLY with valid JSON — no markdown."
    )
    user = f"""Analyze this Search Console data and return this exact JSON:

DATA: {json.dumps(prompt_data, indent=2)}

Return:
{{
  "health_assessment": "2-3 sentences on overall search performance",
  "top_priority_actions": [
    {{
      "action": "specific action",
      "impact": "high/medium/low",
      "effort": "1 day / 1 week / 1 month",
      "why": "why this will improve rankings/traffic"
    }}
  ],
  "traffic_recovery": "Strategy for pages that lost clicks",
  "ctr_improvement_tips": "Specific tips to improve click-through rates",
  "content_plan": "3 content pieces to create based on page-2 opportunities",
  "quick_wins": ["win1", "win2", "win3"],
  "estimated_monthly_clicks": "Realistic estimate if all opportunities are addressed"
}}"""

    return generate_json(system, user, max_tokens=2048)


# ── Audit API endpoints ───────────────────────────────────────────────────────

class AuditStartRequest(BaseModel):
    property_url: str


@router.post("/audit/start")
def start_gsc_audit(
    data: AuditStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    cred = _get_credential(db, current_user.id)
    if not cred:
        raise HTTPException(400, "Google Search Console not connected. Use /api/gsc/auth/url to connect.")

    # Rate limit
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent = db.query(models.GSCReport).filter(
        models.GSCReport.user_id == current_user.id,
        models.GSCReport.created_at >= one_hour_ago,
    ).count()
    if recent >= MAX_GSC_AUDITS_PER_HOUR:
        raise HTTPException(429, f"Rate limit: max {MAX_GSC_AUDITS_PER_HOUR} GSC audits per hour.")

    report = models.GSCReport(
        user_id=current_user.id,
        property_url=data.property_url.strip().rstrip("/"),
        status="running",
        progress=0,
        progress_message="Queued...",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    cred_dict = {
        "access_token":  cred.access_token,
        "refresh_token": cred.refresh_token,
    }
    background_tasks.add_task(
        _run_gsc_audit, report.id, report.property_url, cred_dict, DATABASE_URL
    )

    log.info("GSC audit %d queued by %s for %s", report.id, current_user.username, report.property_url)
    return {"report_id": report.id, "status": "running", "message": f"GSC audit started for {report.property_url}"}


@router.get("/audit/list")
def list_gsc_audits(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    reports = (
        db.query(models.GSCReport)
        .filter(models.GSCReport.user_id == current_user.id)
        .order_by(models.GSCReport.created_at.desc())
        .limit(10)
        .all()
    )
    return [
        {
            "report_id":    r.id,
            "property_url": r.property_url,
            "status":       r.status,
            "progress":     r.progress,
            "created_at":   r.created_at,
            "completed_at": r.completed_at,
        }
        for r in reports
    ]


@router.get("/audit/{report_id}/status")
def get_gsc_audit_status(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    r = db.query(models.GSCReport).filter(
        models.GSCReport.id == report_id,
        models.GSCReport.user_id == current_user.id,
    ).first()
    if not r:
        raise HTTPException(404, "Report not found.")
    return {
        "report_id":        r.id,
        "property_url":     r.property_url,
        "status":           r.status,
        "progress":         r.progress,
        "progress_message": r.progress_message,
        "created_at":       r.created_at,
        "completed_at":     r.completed_at,
    }


@router.get("/audit/{report_id}/results")
def get_gsc_audit_results(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    r = db.query(models.GSCReport).filter(
        models.GSCReport.id == report_id,
        models.GSCReport.user_id == current_user.id,
    ).first()
    if not r:
        raise HTTPException(404, "Report not found.")
    if r.status != "completed":
        raise HTTPException(400, f"Report not ready yet (status: {r.status})")
    return {
        "report_id":         r.id,
        "property_url":      r.property_url,
        "overview":          r.overview,
        "top_queries":       r.top_queries,
        "top_pages":         r.top_pages,
        "date_trend":        r.date_trend,
        "device_breakdown":  r.device_breakdown,
        "period_comparison": r.period_comparison,
        "opportunities":     r.opportunities,
        "ctr_opportunities": r.ctr_opportunities,
        "declining_pages":   r.declining_pages,
        "ai_insights":       r.ai_insights,
    }


@router.get("/audit/{report_id}/download/{fmt}")
def download_gsc_report(
    report_id: int,
    fmt: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    """Download format: 'docx' (ZIP of all docs) or 'pdf'."""
    r = db.query(models.GSCReport).filter(
        models.GSCReport.id == report_id,
        models.GSCReport.user_id == current_user.id,
    ).first()
    if not r:
        raise HTTPException(404, "Report not found.")
    if r.status != "completed":
        raise HTTPException(400, "Report not completed yet.")

    out_dir = os.path.join(REPORTS_DIR, str(report_id))

    if fmt == "pdf":
        path = os.path.join(out_dir, "GSC_Audit.pdf")
        if not os.path.exists(path):
            raise HTTPException(404, "PDF not found — re-run the audit.")
        return FileResponse(path, media_type="application/pdf",
                            filename=f"GSC_Audit_{report_id}.pdf")
    else:
        path = os.path.join(out_dir, "GSC_Reports.zip")
        if not os.path.exists(path):
            raise HTTPException(404, "Reports not found — re-run the audit.")
        return FileResponse(path, media_type="application/zip",
                            filename=f"GSC_Reports_{report_id}.zip")
