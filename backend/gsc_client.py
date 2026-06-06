"""
Google Search Console API client.

Handles:
  - Building authorized service from stored OAuth tokens
  - Auto-refreshing expired access tokens
  - All Search Analytics query functions
"""
import os
from datetime import date, timedelta

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from logger import get_logger

log = get_logger("seo_agent.gsc_client")

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
TOKEN_URI = "https://oauth2.googleapis.com/token"


# ── Service builder ───────────────────────────────────────────────────────────

def build_service(cred_dict: dict) -> tuple:
    """
    Build an authorized Search Console service.
    Returns (service, updated_cred_dict) — cred_dict may contain a refreshed token.
    """
    creds = Credentials(
        token=cred_dict.get("access_token"),
        refresh_token=cred_dict.get("refresh_token"),
        token_uri=TOKEN_URI,
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=SCOPES,
    )
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            log.info("GSC access token refreshed")
            cred_dict = {
                **cred_dict,
                "access_token": creds.token,
            }
        except Exception as e:
            log.error("Token refresh failed: %s", e)
            raise

    service = build("searchconsole", "v1", credentials=creds)
    return service, cred_dict


# ── Helper ────────────────────────────────────────────────────────────────────

def _ds(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def _date_range(days: int) -> tuple[str, str]:
    end = date.today() - timedelta(days=3)   # GSC data lags ~3 days
    start = end - timedelta(days=days - 1)
    return _ds(start), _ds(end)


def _query(service, site_url: str, body: dict) -> list:
    result = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
    return result.get("rows", [])


# ── API calls ─────────────────────────────────────────────────────────────────

def list_properties(service) -> list[dict]:
    """Return list of all verified GSC properties."""
    result = service.sites().list().execute()
    return [
        {"url": s["siteUrl"], "permission": s.get("permissionLevel", "")}
        for s in result.get("siteEntry", [])
    ]


def get_overview(service, site_url: str, days: int = 28) -> dict:
    """Site-wide aggregate metrics for the last N days."""
    start, end = _date_range(days)
    rows = _query(service, site_url, {
        "startDate": start, "endDate": end, "dimensions": [],
    })
    r = rows[0] if rows else {}
    return {
        "clicks":      int(r.get("clicks", 0)),
        "impressions": int(r.get("impressions", 0)),
        "ctr":         round(r.get("ctr", 0) * 100, 2),
        "position":    round(r.get("position", 0), 1),
        "date_range":  f"{start} to {end}",
        "days":        days,
    }


def get_top_queries(service, site_url: str, days: int = 28, limit: int = 50) -> list[dict]:
    """Top queries ranked by clicks."""
    start, end = _date_range(days)
    rows = _query(service, site_url, {
        "startDate": start, "endDate": end,
        "dimensions": ["query"],
        "rowLimit": limit,
        "orderBy": [{"fieldName": "clicks", "sortOrder": "DESCENDING"}],
    })
    return [
        {
            "query":       r["keys"][0],
            "clicks":      int(r.get("clicks", 0)),
            "impressions": int(r.get("impressions", 0)),
            "ctr":         round(r.get("ctr", 0) * 100, 2),
            "position":    round(r.get("position", 0), 1),
        }
        for r in rows
    ]


def get_top_pages(service, site_url: str, days: int = 28, limit: int = 50) -> list[dict]:
    """Top pages ranked by clicks."""
    start, end = _date_range(days)
    rows = _query(service, site_url, {
        "startDate": start, "endDate": end,
        "dimensions": ["page"],
        "rowLimit": limit,
        "orderBy": [{"fieldName": "clicks", "sortOrder": "DESCENDING"}],
    })
    return [
        {
            "page":        r["keys"][0],
            "clicks":      int(r.get("clicks", 0)),
            "impressions": int(r.get("impressions", 0)),
            "ctr":         round(r.get("ctr", 0) * 100, 2),
            "position":    round(r.get("position", 0), 1),
        }
        for r in rows
    ]


def get_date_trend(service, site_url: str, days: int = 90) -> list[dict]:
    """Daily clicks/impressions for the last N days (for trend charts)."""
    start, end = _date_range(days)
    rows = _query(service, site_url, {
        "startDate": start, "endDate": end,
        "dimensions": ["date"],
        "rowLimit": days + 5,
        "orderBy": [{"fieldName": "date", "sortOrder": "ASCENDING"}],
    })
    return [
        {
            "date":        r["keys"][0],
            "clicks":      int(r.get("clicks", 0)),
            "impressions": int(r.get("impressions", 0)),
            "ctr":         round(r.get("ctr", 0) * 100, 2),
            "position":    round(r.get("position", 0), 1),
        }
        for r in rows
    ]


def get_device_breakdown(service, site_url: str, days: int = 28) -> list[dict]:
    """Metrics by device type (MOBILE / DESKTOP / TABLET)."""
    start, end = _date_range(days)
    rows = _query(service, site_url, {
        "startDate": start, "endDate": end,
        "dimensions": ["device"],
    })
    return [
        {
            "device":      r["keys"][0].lower(),
            "clicks":      int(r.get("clicks", 0)),
            "impressions": int(r.get("impressions", 0)),
            "ctr":         round(r.get("ctr", 0) * 100, 2),
            "position":    round(r.get("position", 0), 1),
        }
        for r in rows
    ]


def get_keyword_trends(service, site_url: str, window: int = 28, limit: int = 100) -> dict:
    """
    Compare keyword positions between current and previous window.
    Returns per-keyword metrics for both periods so the analyzer can
    classify each keyword as Rising / Falling / New / Lost / Stable.
    """
    end = date.today() - timedelta(days=3)
    cur_start  = end - timedelta(days=window - 1)
    prev_end   = cur_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=window - 1)

    def _fetch_queries(s, e):
        rows = _query(service, site_url, {
            "startDate": _ds(s), "endDate": _ds(e),
            "dimensions": ["query"],
            "rowLimit": limit,
            "orderBy": [{"fieldName": "impressions", "sortOrder": "DESCENDING"}],
        })
        return {
            r["keys"][0]: {
                "clicks":      int(r.get("clicks", 0)),
                "impressions": int(r.get("impressions", 0)),
                "ctr":         round(r.get("ctr", 0) * 100, 2),
                "position":    round(r.get("position", 0), 1),
            }
            for r in rows
        }

    current  = _fetch_queries(cur_start, end)
    previous = _fetch_queries(prev_start, prev_end)

    return {
        "current_period":  f"{_ds(cur_start)} to {_ds(end)}",
        "previous_period": f"{_ds(prev_start)} to {_ds(prev_end)}",
        "current":  current,
        "previous": previous,
    }


def get_period_comparison(service, site_url: str, window: int = 28) -> dict:
    """
    Compare current window vs previous window at page level.
    Returns {current_period, previous_period, current: {page: metrics}, previous: {page: metrics}}
    """
    end = date.today() - timedelta(days=3)
    cur_start = end - timedelta(days=window - 1)
    prev_end = cur_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=window - 1)

    def _fetch(s, e):
        rows = _query(service, site_url, {
            "startDate": _ds(s), "endDate": _ds(e),
            "dimensions": ["page"],
            "rowLimit": 100,
            "orderBy": [{"fieldName": "clicks", "sortOrder": "DESCENDING"}],
        })
        return {
            r["keys"][0]: {
                "clicks":      int(r.get("clicks", 0)),
                "impressions": int(r.get("impressions", 0)),
                "ctr":         round(r.get("ctr", 0) * 100, 2),
                "position":    round(r.get("position", 0), 1),
            }
            for r in rows
        }

    return {
        "current_period":  f"{_ds(cur_start)} to {_ds(end)}",
        "previous_period": f"{_ds(prev_start)} to {_ds(prev_end)}",
        "current":  _fetch(cur_start, end),
        "previous": _fetch(prev_start, prev_end),
    }
