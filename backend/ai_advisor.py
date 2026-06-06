"""
AI-powered SEO advisor.

Uses Google Gemini (primary) with Anthropic Claude fallback.
Provider selection is automatic — configure keys in backend/.env.
"""
import json
from ai_providers import generate_json, active_provider
from logger import get_logger

log = get_logger("seo_agent.ai_advisor")


def generate_seo_recommendations(
    url: str,
    technical_data: dict,
    pages_data: list,
    pagespeed_data: dict | None = None,
) -> dict:
    """
    Generate structured SEO recommendations for a completed audit.
    Returns a dict with grade, executive summary, top actions, roadmap, etc.
    """
    if active_provider() == "none":
        return {
            "error": (
                "No AI provider configured. "
                "Add GEMINI_API_KEY or ANTHROPIC_API_KEY to backend/.env"
            )
        }

    # Build compact audit summary (keep token usage low)
    pages_summary = []
    for p in pages_data[:8]:
        cur = p.get("current", {})
        pages_summary.append({
            "url": p.get("url", ""),
            "type": p.get("page_type", ""),
            "score": p.get("score", 0),
            "title_len": cur.get("title_length", 0),
            "meta_len": cur.get("meta_length", 0),
            "word_count": cur.get("word_count", 0),
            "h1_count": len(cur.get("h1", [])),
            "has_schema": cur.get("schema_count", 0) > 0,
            "has_canonical": bool(cur.get("canonical")),
            "critical_issues": [
                i["element"] for i in p.get("issues", [])
                if i.get("priority") == "critical"
            ][:4],
        })

    tech = technical_data or {}
    psp_mobile = (pagespeed_data or {}).get("mobile", {})
    perf_score = psp_mobile.get("scores", {}).get("performance", "N/A")
    seo_score  = psp_mobile.get("scores", {}).get("seo", "N/A")
    lcp = psp_mobile.get("core_web_vitals", {}).get("lcp", {}).get("value", "N/A")
    cls = psp_mobile.get("core_web_vitals", {}).get("cls", {}).get("value", "N/A")

    prompt_data = {
        "website": url,
        "technical_score": tech.get("score", 0),
        "https": tech.get("https_enabled", False),
        "sitemap_found": tech.get("sitemap", {}).get("found", False),
        "robots_ok": tech.get("robots_txt_found", False),
        "critical_issues": tech.get("summary", {}).get("critical", 0),
        "high_issues": tech.get("summary", {}).get("high", 0),
        "pagespeed_performance": perf_score,
        "pagespeed_seo": seo_score,
        "lcp": lcp,
        "cls": cls,
        "pages": pages_summary,
    }

    system_prompt = (
        "You are an expert SEO consultant with 15+ years of experience. "
        "Analyze website audit data and give actionable, specific recommendations. "
        "Always be concise, practical, and prioritize by business impact. "
        "Respond ONLY with valid JSON — no markdown, no extra text."
    )

    user_prompt = f"""Analyze this SEO audit and respond with a JSON object:

AUDIT DATA:
{json.dumps(prompt_data, indent=2)}

Return this exact JSON structure:
{{
  "seo_grade": "A/B/C/D/F",
  "executive_summary": "2-3 sentence summary of SEO health and most urgent problem",
  "top_5_actions": [
    {{
      "rank": 1,
      "action": "specific action to take",
      "element": "what to fix (Title Tag / Meta / H1 / Schema etc)",
      "pages_affected": "number or 'all pages'",
      "impact": "high/medium/low",
      "effort": "1 hour / 1 day / 1 week",
      "why": "why this matters for rankings"
    }}
  ],
  "quick_wins": [
    "specific fix that takes under 30 minutes"
  ],
  "30_day_roadmap": {{
    "week_1_critical": ["action1", "action2"],
    "week_2_onpage": ["action1", "action2"],
    "week_3_content": ["action1", "action2"],
    "week_4_technical": ["action1", "action2"]
  }},
  "performance_insights": "2 sentences about Core Web Vitals and what to fix",
  "estimated_impact": "Realistic estimate: fixing these issues could improve rankings by X positions or traffic by Y% in Z months"
}}"""

    result = generate_json(system_prompt, user_prompt, max_tokens=4096)

    if "error" in result:
        log.warning("SEO recommendations failed for %s: %s", url, result["error"])
    else:
        log.info("SEO recommendations generated for %s (grade: %s)", url, result.get("seo_grade", "?"))

    return result


def generate_competitor_ai_insights(comparison_data: dict) -> dict:
    """
    Generate AI-powered strategic insights for a competitor comparison.
    Returns a dict with strategic summary, biggest opportunity, content strategy, timeline.
    """
    if active_provider() == "none":
        return {"error": "No AI provider configured."}

    summary = {
        "our_domain":           comparison_data.get("our_domain"),
        "competitor_domain":    comparison_data.get("competitor_domain"),
        "our_score":            comparison_data.get("our_stats", {}).get("onpage_avg_score", 0),
        "competitor_score":     comparison_data.get("competitor_stats", {}).get("onpage_avg_score", 0),
        "verdict":              comparison_data.get("verdict", {}).get("status", ""),
        "verdict_summary":      comparison_data.get("verdict", {}).get("summary", ""),
        "keyword_gap_count":    len(comparison_data.get("keyword_gap", [])),
        "top_missing_keywords": comparison_data.get("keyword_gap", [])[:12],
        "opportunities_count":  len(comparison_data.get("opportunities", [])),
        "top_opportunities":    [
            o.get("area") for o in comparison_data.get("opportunities", [])[:5]
        ],
    }

    system_prompt = (
        "You are a senior SEO strategist. "
        "Respond ONLY with valid JSON — no markdown, no extra text."
    )

    user_prompt = f"""Analyze this competitor SEO comparison and give strategic advice.

COMPARISON DATA:
{json.dumps(summary, indent=2)}

Return this exact JSON structure:
{{
  "strategic_summary": "2-3 sentences on the competitive position and overall situation",
  "biggest_opportunity": "The single most impactful thing to do to beat the competitor — be specific",
  "content_strategy": [
    "Content piece 1 title and why it will rank",
    "Content piece 2 title and why it will rank",
    "Content piece 3 title and why it will rank"
  ],
  "quick_wins": [
    "Quick win 1 achievable in under a week",
    "Quick win 2 achievable in under a week"
  ],
  "realistic_timeline": "Honest estimate with milestones to reach competitive parity",
  "risk_if_ignored": "What happens to rankings if these gaps are not addressed in 3 months"
}}"""

    result = generate_json(system_prompt, user_prompt, max_tokens=2048)

    if "error" in result:
        log.warning("Competitor AI insights failed: %s", result["error"])
    else:
        log.info(
            "Competitor AI insights generated: %s vs %s",
            comparison_data.get("our_domain", "?"),
            comparison_data.get("competitor_domain", "?"),
        )

    return result


def generate_content_brief(keyword: str, page_type: str = "blog", url: str = "", page_data: dict = None) -> dict:
    """Generate a full SEO content brief for a target keyword."""
    if active_provider() == "none":
        return {"error": "No AI provider configured."}

    context = ""
    if page_data:
        context = f"\nExisting page data: title='{page_data.get('title','')}', h1='{page_data.get('h1','')}', word_count={page_data.get('word_count',0)}"

    user_prompt = f"""Create a complete SEO content brief for a writer.

Target keyword: {keyword}
Page type: {page_type}
Website URL: {url or "not specified"}{context}

Return this exact JSON structure:
{{
  "search_intent": "informational|transactional|navigational|commercial",
  "meta_title": "SEO title 50-60 chars with keyword",
  "meta_description": "compelling 150-160 char meta description",
  "h1": "Main H1 heading with keyword",
  "target_word_count": 1500,
  "content_angle": "Unique hook or angle that differentiates this content",
  "outline": [
    {{
      "h2": "Section heading",
      "h3s": ["subsection 1", "subsection 2"],
      "word_target": 300,
      "key_points": ["what to cover in this section"]
    }}
  ],
  "semantic_keywords": ["related keyword 1", "related keyword 2", "related keyword 3", "related keyword 4", "related keyword 5"],
  "questions_to_answer": ["Question 1?", "Question 2?", "Question 3?"],
  "faq": [
    {{"q": "Frequently asked question?", "a": "Clear concise answer in 1-2 sentences"}},
    {{"q": "Second FAQ question?", "a": "Answer"}},
    {{"q": "Third FAQ question?", "a": "Answer"}}
  ],
  "cta": "Recommended call-to-action for this page type",
  "internal_link_suggestions": ["Type of page to link from", "Type of page to link to"],
  "estimated_ranking_time": "Realistic estimate to rank on page 1"
}}"""

    system_prompt = (
        "You are a senior SEO content strategist with 15 years of experience. "
        "Generate detailed, actionable content briefs that help writers create content that ranks. "
        "Respond ONLY with valid JSON — no markdown, no extra text."
    )

    result = generate_json(system_prompt, user_prompt, max_tokens=3000)
    if "error" in result:
        log.warning("Content brief failed for '%s': %s", keyword, result["error"])
    else:
        log.info("Content brief generated for keyword: %s", keyword)
    return result


def generate_schema_markup(page_data: dict, schema_type: str) -> dict:
    """Generate JSON-LD schema markup for a given page and schema type."""
    if active_provider() == "none":
        return {"error": "No AI provider configured."}

    user_prompt = f"""Generate valid Schema.org JSON-LD markup for this webpage.

Schema type requested: {schema_type}
Page URL: {page_data.get('url', '')}
Page title: {page_data.get('title', '')}
Meta description: {page_data.get('meta_description', '')}
H1: {page_data.get('h1', '')}
H2 headings: {json.dumps(page_data.get('h2s', [])[:5])}
Word count: {page_data.get('word_count', 0)}
Domain: {page_data.get('domain', '')}

Generate a complete, valid JSON-LD schema object. Use realistic placeholder values where real data is unknown (e.g. "[Your Brand Name]", "[Phone Number]").
Return ONLY the JSON-LD object — a single JSON object starting with {{"@context": "https://schema.org", "@type": "..."}}. No markdown, no extra text."""

    system_prompt = (
        "You are an expert in Schema.org structured data. "
        "Generate complete, valid JSON-LD that will pass Google's Rich Results Test. "
        "Respond ONLY with the JSON-LD object — no markdown fences, no explanation."
    )

    result = generate_json(system_prompt, user_prompt, max_tokens=1500)
    if "error" in result:
        log.warning("Schema generation failed for %s: %s", schema_type, result["error"])
    else:
        log.info("Schema generated: %s for %s", schema_type, page_data.get('url', ''))
    return result
