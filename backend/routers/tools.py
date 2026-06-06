"""
SEO Tools router.

Endpoints:
  POST /api/tools/content-brief    — AI content brief for a keyword
  POST /api/tools/schema           — AI JSON-LD schema generator
  GET  /api/tools/domain-authority — OpenPageRank free domain authority scores
  GET  /api/tools/rank-tracker     — List tracked keywords
  POST /api/tools/rank-tracker     — Add keyword to track
  DELETE /api/tools/rank-tracker/{id} — Remove tracked keyword
  GET  /api/tools/rank-tracker/history — GSC position history for tracked keyword
"""
import os
import requests
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from logger import get_logger
import models
import auth as auth_utils
import ai_advisor
import crawler

log = get_logger("seo_agent.tools")

router = APIRouter(prefix="/api/tools", tags=["tools"])

OPR_API_KEY = os.getenv("OPR_API_KEY", "")


# ── Pydantic models ───────────────────────────────────────────────────────────

class BriefRequest(BaseModel):
    keyword: str
    page_type: str = "blog"   # blog|product|category|homepage|landing
    url: str = ""
    crawl_url: bool = False    # if True, crawl url first and include page data

class SchemaRequest(BaseModel):
    url: str
    schema_type: str = "Article"  # Article|Product|LocalBusiness|FAQ|BreadcrumbList|Organization

class TrackRequest(BaseModel):
    keyword: str
    site_url: str   # GSC property URL, e.g. https://bechdu.in


# ── Content Brief ─────────────────────────────────────────────────────────────

@router.post("/content-brief")
def create_content_brief(
    req: BriefRequest,
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    page_data = None
    if req.crawl_url and req.url:
        try:
            pages = crawler.crawl_website(req.url, max_pages=1)
            if pages and not pages[0].get("error"):
                p = pages[0]
                page_data = {
                    "title":       p.get("title", ""),
                    "h1":          (p.get("h1") or [""])[0],
                    "meta_description": p.get("meta_description", ""),
                    "word_count":  p.get("word_count", 0),
                }
        except Exception as e:
            log.warning("Could not crawl %s for brief: %s", req.url, e)

    result = ai_advisor.generate_content_brief(
        keyword=req.keyword.strip(),
        page_type=req.page_type,
        url=req.url,
        page_data=page_data,
    )
    if "error" in result:
        raise HTTPException(500, result["error"])
    return result


# ── Schema Generator ─────────────────────────────────────────────────────────

@router.post("/schema")
def generate_schema(
    req: SchemaRequest,
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    page_data = {"url": req.url, "domain": req.url.split("/")[2] if "://" in req.url else req.url}
    try:
        pages = crawler.crawl_website(req.url, max_pages=1)
        if pages and not pages[0].get("error"):
            p = pages[0]
            page_data.update({
                "title":            p.get("title", ""),
                "meta_description": p.get("meta_description", ""),
                "h1":               (p.get("h1") or [""])[0],
                "h2s":              p.get("h2", [])[:6],
                "word_count":       p.get("word_count", 0),
            })
    except Exception as e:
        log.warning("Could not crawl %s for schema: %s", req.url, e)

    result = ai_advisor.generate_schema_markup(page_data, req.schema_type)
    if "error" in result:
        raise HTTPException(500, result["error"])
    return {"schema_type": req.schema_type, "url": req.url, "json_ld": result}


# ── Domain Authority (OpenPageRank) ──────────────────────────────────────────

@router.get("/domain-authority")
def get_domain_authority(
    domains: str,
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    """
    domains: comma-separated list, e.g. "bechdu.in,cashify.in"
    Uses OpenPageRank free API — add OPR_API_KEY to .env (free at openpagerank.com)
    """
    domain_list = [d.strip().lower().replace("https://","").replace("http://","").rstrip("/")
                   for d in domains.split(",") if d.strip()][:5]

    if not domain_list:
        raise HTTPException(400, "Provide at least one domain.")

    if not OPR_API_KEY:
        return {
            "no_key": True,
            "message": "Add OPR_API_KEY to backend/.env for domain authority scores. Free at openpagerank.com",
            "domains": [{"domain": d, "page_rank_integer": None, "rank": None} for d in domain_list],
        }

    params = {f"domains[{i}]": d for i, d in enumerate(domain_list)}
    try:
        resp = requests.get(
            "https://openpagerank.com/api/v1.0/getPageRank",
            params=params,
            headers={"API-OPR": OPR_API_KEY},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "no_key": False,
            "domains": [
                {
                    "domain":            r.get("domain"),
                    "page_rank_integer": r.get("page_rank_integer"),
                    "page_rank_decimal": r.get("page_rank_decimal"),
                    "rank":              r.get("rank"),
                }
                for r in data.get("response", [])
            ],
        }
    except Exception as e:
        raise HTTPException(500, f"OpenPageRank API error: {str(e)[:200]}")


# ── Rank Tracker ──────────────────────────────────────────────────────────────

@router.get("/rank-tracker")
def list_tracked_keywords(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    rows = db.query(models.TrackedKeyword).filter(
        models.TrackedKeyword.user_id == current_user.id
    ).order_by(models.TrackedKeyword.created_at.desc()).all()
    return [{"id": r.id, "keyword": r.keyword, "site_url": r.site_url, "created_at": r.created_at} for r in rows]


@router.post("/rank-tracker")
def add_tracked_keyword(
    req: TrackRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    existing = db.query(models.TrackedKeyword).filter(
        models.TrackedKeyword.user_id == current_user.id,
        models.TrackedKeyword.keyword == req.keyword.strip().lower(),
        models.TrackedKeyword.site_url == req.site_url.strip(),
    ).first()
    if existing:
        return {"id": existing.id, "keyword": existing.keyword, "site_url": existing.site_url, "already_exists": True}

    limit = db.query(models.TrackedKeyword).filter(
        models.TrackedKeyword.user_id == current_user.id
    ).count()
    if limit >= 50:
        raise HTTPException(400, "Maximum 50 tracked keywords per account.")

    kw = models.TrackedKeyword(
        user_id=current_user.id,
        keyword=req.keyword.strip().lower(),
        site_url=req.site_url.strip(),
    )
    db.add(kw); db.commit(); db.refresh(kw)
    log.info("User %s tracking keyword: %s / %s", current_user.username, kw.keyword, kw.site_url)
    return {"id": kw.id, "keyword": kw.keyword, "site_url": kw.site_url}


@router.delete("/rank-tracker/{kw_id}")
def remove_tracked_keyword(
    kw_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    kw = db.query(models.TrackedKeyword).filter(
        models.TrackedKeyword.id == kw_id,
        models.TrackedKeyword.user_id == current_user.id,
    ).first()
    if not kw:
        raise HTTPException(404, "Keyword not found.")
    db.delete(kw); db.commit()
    return {"deleted": True}


@router.get("/rank-tracker/history")
def get_rank_history(
    keyword: str,
    site_url: str,
    days: int = 90,
    current_user: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch daily position history for a tracked keyword from GSC."""
    from routers.gsc import _get_credential
    import gsc_client

    cred = _get_credential(db, current_user.id)
    if not cred:
        raise HTTPException(400, "Google Search Console not connected.")

    try:
        service, updated = gsc_client.build_service({
            "access_token": cred.access_token,
            "refresh_token": cred.refresh_token,
        })
        if updated["access_token"] != cred.access_token:
            cred.access_token = updated["access_token"]
            db.commit()

        end = date.today() - timedelta(days=3)
        start = end - timedelta(days=days - 1)

        result = service.searchanalytics().query(
            siteUrl=site_url,
            body={
                "startDate": end.strftime("%Y-%m-%d") if days <= 28 else start.strftime("%Y-%m-%d"),
                "endDate": end.strftime("%Y-%m-%d"),
                "dimensions": ["date"],
                "dimensionFilterGroups": [{
                    "filters": [{
                        "dimension": "query",
                        "operator": "equals",
                        "expression": keyword,
                    }]
                }],
                "rowLimit": days,
                "orderBy": [{"fieldName": "date", "sortOrder": "ASCENDING"}],
            }
        ).execute()

        rows = result.get("rows", [])
        history = [
            {
                "date":       r["keys"][0],
                "position":   round(r.get("position", 0), 1),
                "clicks":     int(r.get("clicks", 0)),
                "impressions":int(r.get("impressions", 0)),
                "ctr":        round(r.get("ctr", 0) * 100, 2),
            }
            for r in rows
        ]
        current_pos = history[-1]["position"] if history else None
        best_pos    = min((h["position"] for h in history), default=None)
        worst_pos   = max((h["position"] for h in history), default=None)

        return {
            "keyword":     keyword,
            "site_url":    site_url,
            "history":     history,
            "current_position": current_pos,
            "best_position":    best_pos,
            "worst_position":   worst_pos,
            "data_points":      len(history),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch rank history: {str(e)[:200]}")
