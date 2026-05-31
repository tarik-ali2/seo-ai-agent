"""
Competitor SEO Analyzer
Compares two websites side-by-side:
- Technical SEO scores
- Page-level on-page comparison
- Keyword gap analysis
- Content gap
- What to fix first to beat competitor
"""
import re
from collections import Counter
from urllib.parse import urlparse


STOP_WORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with","by",
    "is","it","its","this","that","be","are","was","were","been","have","has",
    "had","do","does","did","will","would","should","could","may","might","can",
    "from","as","not","no","so","if","we","you","your","our","their","they",
    "them","us","i","my","me","he","she","more","also","all","than","then",
    "some","just","about","up","out","into","what","how","when","which","who",
    "page","website","site","www","http","https","com","org","net",
}


def _extract_keywords_set(pages: list, top_n: int = 30) -> dict:
    """Returns {keyword: frequency} from all pages of a site."""
    all_text = " ".join(
        " ".join(filter(None, [
            p.get("title",""),
            p.get("meta_description",""),
            " ".join(p.get("h1",[])),
            " ".join(p.get("h2",[])),
            " ".join(p.get("h3",[])),
            p.get("body_text_sample",""),
        ]))
        for p in pages if not p.get("error")
    )
    words = re.findall(r"\b[a-z]{3,}\b", all_text.lower())
    filtered = [w for w in words if w not in STOP_WORDS]
    bigrams = [f"{filtered[i]} {filtered[i+1]}" for i in range(len(filtered)-1)]
    counter = Counter(filtered + bigrams)
    return dict(counter.most_common(top_n))


def _page_score(page_data: dict) -> int:
    """Quick score for a raw crawled page."""
    score = 100
    title = page_data.get("title","")
    meta  = page_data.get("meta_description","")
    h1    = page_data.get("h1",[])
    wc    = page_data.get("word_count", 0)

    if not title:             score -= 25
    elif len(title) < 30:     score -= 15
    elif len(title) > 65:     score -= 5

    if not meta:              score -= 25
    elif len(meta) < 100:     score -= 10

    if not h1:                score -= 20
    elif len(h1) > 1:         score -= 10

    if not page_data.get("canonical"): score -= 10
    if not page_data.get("schema_markup"): score -= 10
    if wc < 200:              score -= 10

    return max(0, score)


def _seo_grade(score: int) -> str:
    if score >= 85: return "Excellent ✅"
    if score >= 70: return "Good 🟢"
    if score >= 50: return "Needs Work 🟡"
    if score >= 30: return "Poor 🔴"
    return "Critical ❌"


def run_competitor_analysis(
    our_url: str, our_pages: list, our_technical: dict,
    competitor_url: str, competitor_pages: list, competitor_technical: dict,
) -> dict:
    """
    Returns complete competitor comparison data ready for Word generation.
    """
    our_domain      = urlparse(our_url).netloc
    comp_domain     = urlparse(competitor_url).netloc

    # ── Keyword analysis ─────────────────────────────────────────────────────
    our_kw   = _extract_keywords_set(our_pages)
    comp_kw  = _extract_keywords_set(competitor_pages)

    our_kw_set  = set(our_kw.keys())
    comp_kw_set = set(comp_kw.keys())

    keyword_gap      = sorted(comp_kw_set - our_kw_set)[:25]   # competitor has, we don't
    our_unique_kw    = sorted(our_kw_set - comp_kw_set)[:15]   # we have, competitor doesn't
    shared_kw        = sorted(our_kw_set & comp_kw_set)[:15]

    # ── Page-level comparison ─────────────────────────────────────────────────
    our_pages_ok   = [p for p in our_pages if not p.get("error")]
    comp_pages_ok  = [p for p in competitor_pages if not p.get("error")]

    our_avg_score  = int(sum(_page_score(p) for p in our_pages_ok) / max(len(our_pages_ok),1))
    comp_avg_score = int(sum(_page_score(p) for p in comp_pages_ok) / max(len(comp_pages_ok),1))

    # ── Technical comparison ──────────────────────────────────────────────────
    def _tech_stat(tech, pages_ok):
        pages_with_title    = sum(1 for p in pages_ok if p.get("title"))
        pages_with_meta     = sum(1 for p in pages_ok if p.get("meta_description"))
        pages_with_h1       = sum(1 for p in pages_ok if p.get("h1"))
        pages_with_schema   = sum(1 for p in pages_ok if p.get("schema_markup"))
        pages_with_canon    = sum(1 for p in pages_ok if p.get("canonical"))
        total = max(len(pages_ok),1)
        avg_wc = int(sum(p.get("word_count",0) for p in pages_ok) / total)
        return {
            "score":            tech.get("score", 0),
            "https":            tech.get("https_enabled", False),
            "robots_txt":       tech.get("robots_txt_found", False),
            "sitemap":          tech.get("sitemap",{}).get("found", False),
            "sitemap_urls":     tech.get("sitemap",{}).get("url_count", 0),
            "pages_crawled":    len(pages_ok),
            "pages_with_title": pages_with_title,
            "pages_with_meta":  pages_with_meta,
            "pages_with_h1":    pages_with_h1,
            "pages_with_schema":pages_with_schema,
            "pages_with_canon": pages_with_canon,
            "avg_word_count":   avg_wc,
            "total_issues":     len(tech.get("issues",[])),
            "onpage_avg_score": int(sum(_page_score(p) for p in pages_ok) / total),
        }

    our_stats  = _tech_stat(our_technical, our_pages_ok)
    comp_stats = _tech_stat(competitor_technical, comp_pages_ok)

    # ── Opportunities (what we need to fix to beat them) ─────────────────────
    opportunities = []

    if our_stats["onpage_avg_score"] < comp_stats["onpage_avg_score"]:
        diff = comp_stats["onpage_avg_score"] - our_stats["onpage_avg_score"]
        opportunities.append({
            "priority": "critical",
            "area": "On-Page Score Gap",
            "gap": f"{our_domain}: {our_stats['onpage_avg_score']}/100 vs {comp_domain}: {comp_stats['onpage_avg_score']}/100",
            "action": f"Fix title tags, meta descriptions, and H1s on all pages to close {diff}-point gap",
        })

    if our_stats["pages_with_meta"] < our_stats["pages_crawled"]:
        missing = our_stats["pages_crawled"] - our_stats["pages_with_meta"]
        opportunities.append({
            "priority": "critical",
            "area": "Missing Meta Descriptions",
            "gap": f"{our_domain} has {missing} pages without meta — {comp_domain} has meta on all pages",
            "action": "Write unique 150-160 char meta descriptions for every page",
        })

    if our_stats["pages_with_schema"] < comp_stats["pages_with_schema"]:
        opportunities.append({
            "priority": "high",
            "area": "Schema Markup",
            "gap": f"{our_domain}: {our_stats['pages_with_schema']} schema pages vs {comp_domain}: {comp_stats['pages_with_schema']}",
            "action": "Add Product / Organization / Article JSON-LD schema to all key pages",
        })

    if our_stats["avg_word_count"] < comp_stats["avg_word_count"]:
        diff = comp_stats["avg_word_count"] - our_stats["avg_word_count"]
        opportunities.append({
            "priority": "high",
            "area": "Content Depth",
            "gap": f"Avg words — {our_domain}: {our_stats['avg_word_count']} vs {comp_domain}: {comp_stats['avg_word_count']}",
            "action": f"Add {diff}+ more words per page. Include FAQs, buying guides, product descriptions.",
        })

    if keyword_gap:
        top_missing = keyword_gap[:5]
        opportunities.append({
            "priority": "high",
            "area": "Keyword Gap",
            "gap": f"{comp_domain} ranks for keywords {our_domain} is missing",
            "action": f"Create content targeting: {', '.join(top_missing)}",
        })

    if not our_stats["sitemap"]:
        opportunities.append({
            "priority": "high",
            "area": "XML Sitemap",
            "gap": f"{our_domain} has no sitemap — {comp_domain} has {comp_stats['sitemap_urls']} URLs indexed",
            "action": "Generate sitemap.xml and submit to Google Search Console immediately",
        })

    if our_stats["pages_with_h1"] < our_stats["pages_crawled"]:
        opportunities.append({
            "priority": "high",
            "area": "Missing H1 Tags",
            "gap": f"{our_domain} pages missing H1 — competitor has H1 on all pages",
            "action": "Add one keyword-rich H1 tag to every page",
        })

    # ── Page-by-page comparison ───────────────────────────────────────────────
    page_comparison = []
    for i, our_page in enumerate(our_pages_ok[:6]):
        our_s = _page_score(our_page)
        # Find best matching competitor page
        comp_page = comp_pages_ok[i] if i < len(comp_pages_ok) else {}
        comp_s = _page_score(comp_page) if comp_page else 0

        page_comparison.append({
            "our_url":        our_page.get("url",""),
            "our_title":      our_page.get("title",""),
            "our_meta":       our_page.get("meta_description",""),
            "our_h1":         our_page.get("h1",[""])[0] if our_page.get("h1") else "",
            "our_word_count": our_page.get("word_count",0),
            "our_score":      our_s,
            "comp_url":       comp_page.get("url","") if comp_page else "",
            "comp_title":     comp_page.get("title","") if comp_page else "",
            "comp_meta":      comp_page.get("meta_description","") if comp_page else "",
            "comp_h1":        comp_page.get("h1",[""])[0] if comp_page and comp_page.get("h1") else "",
            "comp_word_count":comp_page.get("word_count",0) if comp_page else 0,
            "comp_score":     comp_s,
            "winner":         our_domain if our_s > comp_s else comp_domain if comp_s > our_s else "Tie",
        })

    # ── Suggested content topics (from keyword gap) ──────────────────────────
    content_ideas = []
    for kw in keyword_gap[:10]:
        if any(x in kw for x in ["sell","buy","price","phone","mobile","refurbish","exchange"]):
            content_ideas.append({
                "keyword": kw,
                "content_type": "Landing page" if len(kw.split()) <= 2 else "Blog post",
                "suggested_title": f"{kw.title()} — Best Price & Fast Service | [Brand]",
                "suggested_h1": f"{kw.title()} — Complete Guide",
                "priority": "high" if comp_kw.get(kw,0) > 5 else "medium",
            })

    return {
        "our_domain":       our_domain,
        "our_url":          our_url,
        "competitor_domain":comp_domain,
        "competitor_url":   competitor_url,
        "our_stats":        our_stats,
        "competitor_stats": comp_stats,
        "our_grade":        _seo_grade(our_stats["onpage_avg_score"]),
        "competitor_grade": _seo_grade(comp_stats["onpage_avg_score"]),
        "our_keywords":     list(our_kw.items())[:20],
        "competitor_keywords": list(comp_kw.items())[:20],
        "keyword_gap":      keyword_gap,
        "our_unique_keywords": our_unique_kw,
        "shared_keywords":  shared_kw,
        "content_ideas":    content_ideas,
        "opportunities":    opportunities,
        "page_comparison":  page_comparison,
        "verdict":          _verdict(our_stats, comp_stats, our_domain, comp_domain),
    }


def _verdict(our: dict, comp: dict, our_d: str, comp_d: str) -> dict:
    our_score  = our["onpage_avg_score"]
    comp_score = comp["onpage_avg_score"]
    gap = comp_score - our_score

    if gap > 30:
        status = "Significantly Behind"
        color  = "critical"
        summary = f"{our_d} is {gap} points behind {comp_d}. Urgent action needed."
    elif gap > 15:
        status = "Behind"
        color  = "high"
        summary = f"{our_d} is {gap} points behind. With focused effort, can catch up in 2-3 months."
    elif gap > 0:
        status = "Slightly Behind"
        color  = "medium"
        summary = f"Close race! {our_d} is only {gap} points behind {comp_d}. Quick wins possible."
    elif gap == 0:
        status = "Tied"
        color  = "low"
        summary = f"Neck and neck! Both sites have similar SEO quality."
    else:
        status = "Ahead"
        color  = "low"
        summary = f"{our_d} is {abs(gap)} points ahead of {comp_d}. Maintain the lead!"

    return {"status": status, "color": color, "summary": summary, "gap": gap}
