"""
Google Search Console data analyzer.

Detects:
  - Keyword opportunities (page 2 rankings with high impressions)
  - Declining pages (click drops vs previous period)
  - CTR opportunities (high impressions but below-average CTR)
  - Quick wins (position 8-15 with good impressions)
"""

# Industry-average CTR by search position (Backlinko / Advanced Web Ranking research)
_CTR_BENCHMARK = {
    1: 27.6, 2: 15.8, 3: 11.0, 4: 8.4, 5: 6.3,
    6: 4.9,  7: 3.9,  8: 3.3,  9: 2.7, 10: 2.4,
}


def _expected_ctr(position: float) -> float:
    """Expected CTR% for a given average search position."""
    p = round(position)
    if p in _CTR_BENCHMARK:
        return _CTR_BENCHMARK[p]
    elif p <= 20:
        return max(0.5, 2.4 - (p - 10) * 0.15)
    return 0.3


# ── Opportunity detectors ─────────────────────────────────────────────────────

def detect_keyword_opportunities(queries: list[dict]) -> list[dict]:
    """
    Queries sitting on page 2 (position 11–30) with enough impressions.
    These are the easiest to push to page 1.
    """
    results = []
    for q in queries:
        pos = q.get("position", 0)
        impr = q.get("impressions", 0)
        if pos < 11 or pos > 30 or impr < 30:
            continue
        exp_ctr = _expected_ctr(pos)
        potential_clicks = int(impr * _expected_ctr(max(pos - 5, 1)) / 100)
        current_clicks = q.get("clicks", 0)
        results.append({
            "query":            q["query"],
            "current_position": round(pos, 1),
            "impressions":      impr,
            "clicks":           current_clicks,
            "current_ctr":      q.get("ctr", 0),
            "expected_ctr":     round(exp_ctr, 1),
            "potential_clicks": max(0, potential_clicks - current_clicks),
            "gap_to_page1":     round(pos - 10, 1),
            "priority":         "high" if pos <= 15 and impr >= 100 else "medium",
        })
    return sorted(results, key=lambda x: (-x["impressions"], x["current_position"]))[:25]


def detect_ctr_opportunities(pages: list[dict]) -> list[dict]:
    """
    Pages with good impressions but significantly below-average CTR.
    Usually fixed by improving title tag and meta description.
    """
    results = []
    for p in pages:
        pos = p.get("position", 0)
        impr = p.get("impressions", 0)
        actual_ctr = p.get("ctr", 0)
        if impr < 50 or pos > 20:
            continue
        exp_ctr = _expected_ctr(pos)
        if actual_ctr >= exp_ctr * 0.7:   # only flag if 30%+ below expected
            continue
        extra_clicks = int(impr * (exp_ctr - actual_ctr) / 100)
        results.append({
            "page":             p["page"],
            "impressions":      impr,
            "clicks":           p.get("clicks", 0),
            "actual_ctr":       round(actual_ctr, 2),
            "expected_ctr":     round(exp_ctr, 1),
            "ctr_gap":          round(exp_ctr - actual_ctr, 1),
            "position":         round(pos, 1),
            "potential_extra_clicks": max(0, extra_clicks),
            "fix":              "Rewrite title tag and meta description to be more compelling",
        })
    return sorted(results, key=lambda x: -x["impressions"])[:20]


def detect_declining_pages(period: dict) -> list[dict]:
    """
    Pages where clicks dropped by ≥20% vs the previous same-length window.
    Sorted by absolute click loss (biggest losses first).
    """
    current = period.get("current", {})
    previous = period.get("previous", {})
    results = []

    for page, cur in current.items():
        prev = previous.get(page)
        if not prev or prev["clicks"] < 5:
            continue
        delta_clicks = cur["clicks"] - prev["clicks"]
        pct_change = round((delta_clicks / max(prev["clicks"], 1)) * 100, 1)
        if pct_change >= -20:
            continue
        delta_pos = round(cur["position"] - prev["position"], 1)
        results.append({
            "page":             page,
            "current_clicks":   cur["clicks"],
            "previous_clicks":  prev["clicks"],
            "click_change":     delta_clicks,
            "pct_change":       pct_change,
            "current_position": round(cur["position"], 1),
            "previous_position":round(prev["position"], 1),
            "position_change":  delta_pos,
            "severity": (
                "critical" if pct_change <= -50
                else "high" if pct_change <= -30
                else "medium"
            ),
            "likely_cause": (
                "Ranking drop — page moved down in SERP" if delta_pos > 2
                else "CTR drop — impressions stable but fewer clicks"
                if abs(delta_pos) <= 1
                else "Mixed: both ranking and CTR changes"
            ),
        })

    return sorted(results, key=lambda x: x["click_change"])[:20]


# ── Keyword trend classifier ──────────────────────────────────────────────────

def classify_keyword_trends(trends: dict) -> dict:
    """
    Compare current vs previous period keyword data.
    Classifies each keyword as: rising | falling | new | lost | stable
    Returns summary + per-keyword list sorted by impressions.
    """
    current  = trends.get("current", {})
    previous = trends.get("previous", {})

    keywords = []

    all_queries = set(current.keys()) | set(previous.keys())

    for query in all_queries:
        cur  = current.get(query)
        prev = previous.get(query)

        if cur and prev:
            pos_change   = round(prev["position"] - cur["position"], 1)  # positive = improved
            click_change = cur["clicks"] - prev["clicks"]
            impr_change  = cur["impressions"] - prev["impressions"]
            pct_clicks   = round((click_change / max(prev["clicks"], 1)) * 100, 1)

            if pos_change >= 3:
                trend = "rising"
            elif pos_change <= -3:
                trend = "falling"
            else:
                trend = "stable"

            keywords.append({
                "query":            query,
                "trend":            trend,
                "current_position": cur["position"],
                "previous_position":prev["position"],
                "position_change":  pos_change,
                "clicks":           cur["clicks"],
                "previous_clicks":  prev["clicks"],
                "click_change":     click_change,
                "click_change_pct": pct_clicks,
                "impressions":      cur["impressions"],
                "ctr":              cur["ctr"],
            })

        elif cur and not prev:
            keywords.append({
                "query":            query,
                "trend":            "new",
                "current_position": cur["position"],
                "previous_position":None,
                "position_change":  None,
                "clicks":           cur["clicks"],
                "previous_clicks":  0,
                "click_change":     cur["clicks"],
                "click_change_pct": 100.0,
                "impressions":      cur["impressions"],
                "ctr":              cur["ctr"],
            })

        elif prev and not cur:
            if prev["impressions"] >= 20:
                keywords.append({
                    "query":            query,
                    "trend":            "lost",
                    "current_position": None,
                    "previous_position":prev["position"],
                    "position_change":  None,
                    "clicks":           0,
                    "previous_clicks":  prev["clicks"],
                    "click_change":     -prev["clicks"],
                    "click_change_pct": -100.0,
                    "impressions":      0,
                    "ctr":              0,
                })

    keywords.sort(key=lambda x: -(x["impressions"] or 0))

    rising  = [k for k in keywords if k["trend"] == "rising"]
    falling = [k for k in keywords if k["trend"] == "falling"]
    new_kw  = [k for k in keywords if k["trend"] == "new"]
    lost    = [k for k in keywords if k["trend"] == "lost"]
    stable  = [k for k in keywords if k["trend"] == "stable"]

    return {
        "current_period":  trends.get("current_period", ""),
        "previous_period": trends.get("previous_period", ""),
        "summary": {
            "total":   len(keywords),
            "rising":  len(rising),
            "falling": len(falling),
            "new":     len(new_kw),
            "lost":    len(lost),
            "stable":  len(stable),
        },
        "keywords": keywords[:150],
    }


# ── Summary helpers ───────────────────────────────────────────────────────────

def build_summary(
    overview: dict,
    top_queries: list,
    top_pages: list,
    opportunities: list,
    declining: list,
    ctr_opps: list,
) -> dict:
    """
    Build a compact summary dict for the AI prompt and report header.
    """
    total_potential_clicks = sum(o.get("potential_clicks", 0) for o in opportunities)
    total_ctr_clicks = sum(o.get("potential_extra_clicks", 0) for o in ctr_opps)
    total_lost_clicks = sum(abs(d.get("click_change", 0)) for d in declining)

    return {
        "total_clicks":       overview.get("clicks", 0),
        "total_impressions":  overview.get("impressions", 0),
        "avg_ctr":            overview.get("ctr", 0),
        "avg_position":       overview.get("position", 0),
        "date_range":         overview.get("date_range", ""),
        "top_query":          top_queries[0]["query"] if top_queries else "",
        "top_page":           top_pages[0]["page"] if top_pages else "",
        "keyword_opportunities":      len(opportunities),
        "potential_clicks_from_p2":   total_potential_clicks,
        "ctr_opportunities":          len(ctr_opps),
        "potential_clicks_from_ctr":  total_ctr_clicks,
        "declining_pages":            len(declining),
        "total_lost_clicks":          total_lost_clicks,
        "critical_declines":          sum(1 for d in declining if d["severity"] == "critical"),
    }
