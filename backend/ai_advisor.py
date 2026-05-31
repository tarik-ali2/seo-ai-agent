"""
Claude AI-powered SEO advisor.
Uses Anthropic claude-haiku-4-5 for fast, smart SEO recommendations.
Requires ANTHROPIC_API_KEY in .env
"""
import os, json
import anthropic

_client = None

def _get_client():
    global _client
    if _client is None:
        key = os.getenv("ANTHROPIC_API_KEY", "")
        if not key:
            return None
        _client = anthropic.Anthropic(api_key=key)
    return _client


def generate_seo_recommendations(
    url: str,
    technical_data: dict,
    pages_data: list,
    pagespeed_data: dict | None = None,
) -> dict:
    """
    Send audit summary to Claude and get smart SEO recommendations.
    Returns structured JSON or error dict.
    """
    client = _get_client()
    if client is None:
        return {"error": "ANTHROPIC_API_KEY not set. Add it to .env file."}

    # Build concise summary for Claude (keep tokens low)
    pages_summary = []
    for p in pages_data[:8]:
        cur = p.get("current", {})
        pages_summary.append({
            "url": p.get("url", ""),
            "type": p.get("page_type", ""),
            "score": p.get("score", 0),
            "title": cur.get("title", ""),
            "title_len": cur.get("title_length", 0),
            "meta_len": cur.get("meta_length", 0),
            "word_count": cur.get("word_count", 0),
            "h1_count": len(cur.get("h1", [])),
            "has_schema": cur.get("schema_count", 0) > 0,
            "has_canonical": bool(cur.get("canonical")),
            "has_og": bool(cur.get("og_title")),
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

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = message.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {e}", "raw": raw[:500]}
    except anthropic.AuthenticationError:
        return {"error": "Invalid ANTHROPIC_API_KEY. Check your .env file."}
    except Exception as e:
        return {"error": str(e)}


def generate_competitor_ai_insights(comparison_data: dict) -> dict:
    """AI insights for competitor comparison."""
    client = _get_client()
    if client is None:
        return {"error": "ANTHROPIC_API_KEY not set."}

    summary = {
        "our_domain": comparison_data.get("our_domain"),
        "competitor_domain": comparison_data.get("competitor_domain"),
        "our_score": comparison_data.get("our_stats", {}).get("onpage_avg_score", 0),
        "competitor_score": comparison_data.get("competitor_stats", {}).get("onpage_avg_score", 0),
        "keyword_gap_count": len(comparison_data.get("keyword_gap", [])),
        "top_missing_keywords": comparison_data.get("keyword_gap", [])[:10],
        "opportunities_count": len(comparison_data.get("opportunities", [])),
        "verdict": comparison_data.get("verdict", {}).get("status", ""),
    }

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"""You are an SEO strategist. Analyze this competitor comparison and give strategic advice.

DATA: {json.dumps(summary, indent=2)}

Return JSON only:
{{
  "strategic_summary": "2 sentences on competitive position",
  "biggest_opportunity": "single most impactful thing to do to beat competitor",
  "content_strategy": ["3 content pieces to create based on keyword gap"],
  "realistic_timeline": "honest estimate to reach competitive parity"
}}"""
            }]
        )
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as e:
        return {"error": str(e)}
