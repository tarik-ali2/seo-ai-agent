"""
Google PageSpeed Insights API — free, no key required for anonymous usage.
With API key: 25,000 req/day. Without key: ~100 req/day.
Set PAGESPEED_API_KEY in .env for higher limits.
"""
import os
import requests

API_KEY = os.getenv("PAGESPEED_API_KEY", "")
ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

CATEGORIES = ["performance", "seo", "accessibility", "best-practices"]


def _score(val) -> int:
    if val is None:
        return 0
    return int(round(float(val) * 100))


def _audit_score(audits: dict, key: str) -> int:
    a = audits.get(key, {})
    s = a.get("score")
    return _score(s) if s is not None else -1


def fetch(url: str, strategy: str = "mobile") -> dict:
    params = {
        "url": url,
        "strategy": strategy,
        "category": CATEGORIES,
    }
    if API_KEY:
        params["key"] = API_KEY

    try:
        r = requests.get(ENDPOINT, params=params, timeout=45)
        if not r.ok:
            return {"error": f"PageSpeed API returned {r.status_code}"}
        data = r.json()
    except Exception as e:
        return {"error": str(e)}

    lr = data.get("lighthouseResult", {})
    cats = lr.get("categories", {})
    audits = lr.get("audits", {})

    # Core Web Vitals
    lcp = audits.get("largest-contentful-paint", {})
    cls = audits.get("cumulative-layout-shift", {})
    fcp = audits.get("first-contentful-paint", {})
    tbt = audits.get("total-blocking-time", {})
    si  = audits.get("speed-index", {})
    tti = audits.get("interactive", {})

    def cwv_status(key, good_threshold, warn_threshold):
        val = audits.get(key, {}).get("numericValue", 0)
        if val == 0:
            return "N/A"
        if val <= good_threshold:
            return "good"
        if val <= warn_threshold:
            return "needs-improvement"
        return "poor"

    # Opportunities (things that can save load time)
    opportunities = []
    for k, a in audits.items():
        if (
            a.get("score") is not None
            and a.get("score") < 0.9
            and a.get("details", {}).get("type") == "opportunity"
        ):
            savings = a.get("details", {}).get("overallSavingsMs", 0)
            opportunities.append({
                "id": k,
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "display_value": a.get("displayValue", ""),
                "savings_ms": int(savings),
            })
    opportunities.sort(key=lambda x: -x["savings_ms"])

    # Diagnostics
    diagnostics = []
    for k, a in audits.items():
        if (
            a.get("score") is not None
            and a.get("score") < 0.9
            and a.get("details", {}).get("type") == "table"
            and k not in [o["id"] for o in opportunities]
        ):
            diagnostics.append({
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "display_value": a.get("displayValue", ""),
            })

    # SEO-specific audits
    seo_audits = {}
    seo_keys = [
        "document-title", "meta-description", "http-status-code",
        "link-text", "crawlable-anchors", "is-crawlable",
        "robots-txt", "image-alt", "hreflang", "canonical",
        "structured-data", "tap-targets", "font-size", "viewport",
    ]
    for k in seo_keys:
        if k in audits:
            a = audits[k]
            seo_audits[k] = {
                "title": a.get("title", ""),
                "score": _score(a.get("score")) if a.get("score") is not None else None,
                "display_value": a.get("displayValue", ""),
                "description": a.get("description", ""),
            }

    return {
        "strategy": strategy,
        "scores": {
            "performance":     _score(cats.get("performance", {}).get("score")),
            "seo":             _score(cats.get("seo", {}).get("score")),
            "accessibility":   _score(cats.get("accessibility", {}).get("score")),
            "best_practices":  _score(cats.get("best-practices", {}).get("score")),
        },
        "core_web_vitals": {
            "lcp": {
                "label": "Largest Contentful Paint",
                "value": lcp.get("displayValue", "N/A"),
                "numeric_ms": lcp.get("numericValue", 0),
                "status": cwv_status("largest-contentful-paint", 2500, 4000),
                "description": "Time until the largest content element is painted",
            },
            "cls": {
                "label": "Cumulative Layout Shift",
                "value": cls.get("displayValue", "N/A"),
                "numeric": cls.get("numericValue", 0),
                "status": cwv_status("cumulative-layout-shift", 0.1, 0.25),
                "description": "Visual stability — how much the page shifts during load",
            },
            "fcp": {
                "label": "First Contentful Paint",
                "value": fcp.get("displayValue", "N/A"),
                "numeric_ms": fcp.get("numericValue", 0),
                "status": cwv_status("first-contentful-paint", 1800, 3000),
                "description": "Time until first text or image is painted",
            },
            "tbt": {
                "label": "Total Blocking Time",
                "value": tbt.get("displayValue", "N/A"),
                "numeric_ms": tbt.get("numericValue", 0),
                "status": cwv_status("total-blocking-time", 200, 600),
                "description": "Total time the main thread was blocked",
            },
            "speed_index": {
                "label": "Speed Index",
                "value": si.get("displayValue", "N/A"),
                "numeric_ms": si.get("numericValue", 0),
                "status": cwv_status("speed-index", 3400, 5800),
                "description": "How quickly page contents are visually populated",
            },
            "tti": {
                "label": "Time to Interactive",
                "value": tti.get("displayValue", "N/A"),
                "numeric_ms": tti.get("numericValue", 0),
                "status": cwv_status("interactive", 3800, 7300),
                "description": "Time until page is fully interactive",
            },
        },
        "opportunities": opportunities[:8],
        "diagnostics": diagnostics[:6],
        "seo_audits": seo_audits,
    }


def run_full_pagespeed(url: str) -> dict:
    """Run both mobile and desktop, return combined result."""
    mobile  = fetch(url, strategy="mobile")
    desktop = fetch(url, strategy="desktop")
    return {
        "url": url,
        "mobile":  mobile,
        "desktop": desktop,
        "error": mobile.get("error") or desktop.get("error"),
    }
