import re
import json
from collections import Counter
from urllib.parse import urlparse


# ── Stop words ────────────────────────────────────────────────────────────────
STOP_WORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with","by",
    "is","it","its","this","that","be","are","was","were","been","have","has",
    "had","do","does","did","will","would","should","could","may","might","can",
    "from","as","not","no","so","if","we","you","your","our","their","they",
    "them","us","i","my","me","he","she","her","his","more","also","all","than",
    "then","some","just","about","up","out","get","into","what","how","when",
    "which","who","there","here","been","after","before","each","over","under",
    "only","both","between","through","during","without","within","along","page",
    "website","site","www","http","https","com","org","net","php","html","css",
}

PRIORITY = {"critical": 1, "high": 2, "medium": 3, "low": 4}

def _local_seo_suggestions(url: str, title: str, meta: str, h1_list: list, page_type: str, keywords: list) -> dict:
    """Generate local SEO recommendations based on actual page content."""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.replace("www.", "")
    kw = keywords[0][0] if keywords else "your service"
    kw2 = keywords[1][0] if len(keywords) > 1 else kw

    # Detect city mentions in title, meta, and H1s
    combined = title + " " + meta + " " + " ".join(h1_list)
    city_pattern = re.findall(r'\b([A-Z][a-z]{3,}(?:\s[A-Z][a-z]+)?)\b', combined)
    _ = page_type  # available for future page-type-specific local rules
    cities_present = list(set(city_pattern))[:5]

    suggestions = []
    if not cities_present:
        suggestions.append({
            "issue": "No local city/region targeting found in title or meta",
            "fix": "Add your target city/region to title and meta description for local SEO",
            "example": f"Title: '{kw.title()} in [Your City] — [Benefit] | {domain}'",
        })

    gmb_checklist = [
        "Create/claim Google Business Profile (GMB) for your location",
        "Add your complete service area (cities/regions you serve)",
        "Upload 10+ high-quality photos of your business/product",
        "Collect 20+ genuine Google reviews from customers",
        "Post weekly updates: offers, news, new services",
        "Add correct business hours, phone, and address",
    ]

    city_pages = [
        {
            "page": f"/{kw.replace(' ', '-')}-[city-slug]",
            "title": f"{kw.title()} in [City] — [Key Benefit] | [Brand]",
            "meta": f"Looking for {kw} in [City]? Get [benefit]. [CTA]. Serving [City] and nearby areas.",
            "h1": f"{kw.title()} in [City] — [Unique Value Proposition]",
            "schema_local": {
                "@context": "https://schema.org",
                "@type": "LocalBusiness",
                "name": "[Brand Name]",
                "description": f"Best {kw} service in [City]",
                "areaServed": "[City Name]",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "[City]",
                    "addressRegion": "[State]",
                    "addressCountry": "[Country Code]"
                },
                "telephone": "[Phone Number]",
                "url": f"{url}/{kw.replace(' ', '-')}-[city-slug]"
            }
        }
    ]

    return {
        "cities_found_in_content": cities_present,
        "suggestions": suggestions,
        "city_landing_pages": city_pages,
        "gmb_checklist": gmb_checklist,
        "priority_keywords": [
            f"{kw} [your city]",
            f"best {kw} near me",
            f"{kw2} [your city]",
            f"top {kw} service [your city]",
        ],
    }


# ── Keyword extraction ────────────────────────────────────────────────────────

def extract_keywords(text: str, top_n: int = 15) -> list:
    words = re.findall(r"\b[a-z]{3,}\b", text.lower())
    filtered = [w for w in words if w not in STOP_WORDS]
    bigrams = [f"{filtered[i]} {filtered[i+1]}" for i in range(len(filtered)-1)]
    all_terms = filtered + bigrams
    counter = Counter(all_terms)
    return [(term, count) for term, count in counter.most_common(top_n)]


def keyword_in_text(keyword: str, text: str) -> bool:
    return keyword.lower() in text.lower() if keyword and text else False


# ── Readability ───────────────────────────────────────────────────────────────

def readability_score(text: str) -> dict:
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    words = text.split()
    if not sentences or not words:
        return {"score": 0, "grade": "No content", "avg_sentence_length": 0}

    avg_sentence_len = len(words) / max(len(sentences), 1)
    long_sentences = sum(1 for s in sentences if len(s.split()) > 20)
    long_ratio = long_sentences / max(len(sentences), 1)

    if avg_sentence_len < 15 and long_ratio < 0.2:
        grade = "Easy to read"
        score = 90
    elif avg_sentence_len < 20 and long_ratio < 0.4:
        grade = "Moderate"
        score = 70
    elif avg_sentence_len < 25:
        grade = "Difficult"
        score = 50
    else:
        grade = "Very difficult"
        score = 30

    return {
        "score": score,
        "grade": grade,
        "avg_sentence_length": round(avg_sentence_len, 1),
        "sentence_count": len(sentences),
        "word_count": len(words),
        "long_sentences": long_sentences,
    }


# ── Issue builder with priority ───────────────────────────────────────────────

def _issue(priority: str, element: str, problem: str, fix: str) -> dict:
    return {"priority": priority, "element": element, "problem": problem, "fix": fix}


# ── Page type detection ───────────────────────────────────────────────────────

def detect_page_type(url: str, title: str, h1_list: list) -> str:
    url_lower = url.lower()
    title_text = (title + " " + " ".join(h1_list)).lower()
    if any(k in url_lower for k in ["/product", "/item", "/p/", "/buy", "/sell", "/mobile", "/phone"]) \
            or any(k in title_text for k in ["buy now", "add to cart", "product details"]):
        return "product"
    if any(k in url_lower for k in ["/category", "/collection", "/cat/", "/shop", "/brand"]):
        return "category"
    if any(k in url_lower for k in ["/blog", "/article", "/post", "/news", "/guide"]):
        return "blog"
    if urlparse(url).path in ("", "/", "/index.html", "/index.php"):
        return "homepage"
    if any(k in url_lower for k in ["/about", "/contact", "/faq", "/help"]):
        return "static"
    return "page"


# ── SEO score breakdown ───────────────────────────────────────────────────────

def _compute_scores(title, meta, h1_list, canonical, schema, word_count, images_no_alt, internal_links_count):
    scores = {}

    # Title score
    tl = len(title) if title else 0
    if not title:           scores["title"] = 0
    elif tl < 30:           scores["title"] = 40
    elif 50 <= tl <= 60:    scores["title"] = 100
    elif 40 <= tl < 50:     scores["title"] = 80
    elif tl > 70:           scores["title"] = 50
    else:                   scores["title"] = 70

    # Meta score
    ml = len(meta) if meta else 0
    if not meta:            scores["meta"] = 0
    elif ml < 100:          scores["meta"] = 40
    elif 150 <= ml <= 160:  scores["meta"] = 100
    elif 130 <= ml < 150:   scores["meta"] = 85
    elif ml > 170:          scores["meta"] = 60
    else:                   scores["meta"] = 75

    # H1 score
    if not h1_list:         scores["h1"] = 0
    elif len(h1_list) > 1:  scores["h1"] = 60
    else:                   scores["h1"] = 100

    # Content score
    if word_count < 50:     scores["content"] = 10
    elif word_count < 200:  scores["content"] = 40
    elif word_count < 300:  scores["content"] = 60
    elif word_count < 600:  scores["content"] = 80
    else:                   scores["content"] = 100

    # Technical score
    tech = 100
    if not canonical:       tech -= 25
    if not schema:          tech -= 25
    if images_no_alt > 0:   tech -= min(25, images_no_alt * 5)
    if internal_links_count < 3: tech -= 15
    scores["technical"] = max(0, tech)

    overall = int(
        scores["title"] * 0.20 +
        scores["meta"] * 0.20 +
        scores["h1"] * 0.15 +
        scores["content"] * 0.20 +
        scores["technical"] * 0.25
    )
    scores["overall"] = overall
    return scores


# ── Smart title & meta suggestions ───────────────────────────────────────────

def _smart_title(current: str, page_type: str, keywords: list) -> str:
    kw = keywords[0][0].title() if keywords else "[Primary Keyword]"
    templates = {
        "homepage":  f"{kw} | Sell & Buy Online | [Brand Name]",
        "product":   f"Buy {kw} — Best Price, Fast Delivery | [Brand]",
        "category":  f"{kw} — Shop Best Deals Online | [Brand]",
        "blog":      f"{kw} — Complete Guide [Year] | [Brand]",
        "static":    f"{kw} | [Brand Name]",
        "page":      f"{kw} | [Brand Name]",
    }
    if not current:
        return templates.get(page_type, f"[{kw}] | [Brand Name]")
    if len(current) < 30:
        return templates.get(page_type, current + " | [Add keyword + Brand]")
    if len(current) > 65:
        return current[:62].rstrip() + "... | [Brand]"
    return current


def _smart_meta(current: str, page_type: str, keywords: list) -> str:
    kw1 = keywords[0][0] if keywords else "[primary keyword]"
    kw2 = keywords[1][0] if len(keywords) > 1 else "[secondary keyword]"
    templates = {
        "homepage":  f"[Brand]: your trusted source for {kw1}. Discover {kw2} and more. [Key benefit]. [CTA — e.g. 'Get started today!']",
        "product":   f"Buy {kw1} at the best price. Compare deals, read reviews, and get fast delivery. Check {kw2} availability and order today!",
        "category":  f"Browse our {kw1} collection. Find the best deals on {kw2}. Shop now for exclusive offers and fast delivery!",
        "blog":      f"Learn everything about {kw1} in this complete guide. Discover tips on {kw2}, expert advice, and step-by-step instructions.",
        "static":    f"Learn about {kw1} at [Brand]. Get detailed information, tips, and expert guidance.",
        "page":      f"Discover {kw1} and {kw2} at [Brand]. Get detailed information, expert tips, and guidance. Visit us today!",
    }
    if not current:
        return templates.get(page_type, templates["page"])
    if len(current) < 100:
        return current.rstrip(".") + f". Learn more about {kw1} — click to explore!"
    if len(current) > 165:
        return current[:162].rstrip() + "..."
    return current


def _smart_h1(current_list: list, page_type: str, keywords: list) -> str:
    kw = keywords[0][0].title() if keywords else "[Primary Keyword]"
    if not current_list:
        templates = {
            "homepage":  f"{kw} — [Your Unique Value Proposition]",
            "product":   f"{kw} — Best Price & Fast Delivery",
            "category":  f"Shop {kw} — Find the Best Deals",
            "blog":      f"{kw}: Complete Guide [Year]",
            "static":    f"{kw} | [Brand Name]",
            "page":      f"{kw} — [Describe What You Offer]",
        }
        return templates.get(page_type, f"{kw} — [Add Your Value Proposition]")
    if len(current_list) > 1:
        return current_list[0]
    return current_list[0]


# ── Schema templates ──────────────────────────────────────────────────────────

def _schema_template(page_type: str, url: str, title: str, description: str, keywords: list) -> dict:
    kw = keywords[0][0].title() if keywords else "Product"
    base = {
        "@context": "https://schema.org",
        "url": url,
        "name": title or kw,
        "description": description or f"Best {kw} deals online",
    }
    if page_type == "product":
        base.update({
            "@type": "Product",
            "image": "[Product Image URL — 1200x630px recommended]",
            "brand": {"@type": "Brand", "name": "[Brand Name]"},
            "sku": "[Product SKU]",
            "offers": {
                "@type": "Offer",
                "priceCurrency": "INR",
                "price": "[Price]",
                "availability": "https://schema.org/InStock",
                "url": url,
                "seller": {"@type": "Organization", "name": "[Store Name]"},
            },
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": "4.5",
                "reviewCount": "100",
                "bestRating": "5",
            },
        })
    elif page_type == "category":
        base.update({
            "@type": "CollectionPage",
            "breadcrumb": {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": url.split("/")[0]+"//"+url.split("/")[2]},
                    {"@type": "ListItem", "position": 2, "name": title or kw, "item": url},
                ],
            },
        })
    elif page_type == "blog":
        base.update({
            "@type": "Article",
            "headline": title or kw,
            "author": {"@type": "Person", "name": "[Author Name]"},
            "publisher": {
                "@type": "Organization",
                "name": "[Brand Name]",
                "logo": {"@type": "ImageObject", "url": "[Logo URL]"},
            },
            "datePublished": "[YYYY-MM-DD]",
            "dateModified": "[YYYY-MM-DD]",
            "image": "[Featured Image URL]",
            "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        })
    elif page_type == "homepage":
        base.update({
            "@type": "Organization",
            "logo": "[Logo URL — 600x60px]",
            "sameAs": [
                "[Facebook Page URL]",
                "[Instagram URL]",
                "[LinkedIn URL]",
            ],
            "contactPoint": {
                "@type": "ContactPoint",
                "telephone": "[+91-XXXXXXXXXX]",
                "contactType": "customer service",
                "availableLanguage": ["English", "Hindi"],
            },
        })
    else:
        base.update({"@type": "WebPage"})
    return base


# ── Internal link suggestions ─────────────────────────────────────────────────

def _internal_link_suggestions(page_type: str) -> list:
    m = {
        "product": [
            {"anchor": "View similar products", "target": "/category/[category-slug]", "reason": "Passes link equity to category page"},
            {"anchor": "Read our buying guide", "target": "/blog/[guide-slug]", "reason": "Improves dwell time and topical authority"},
            {"anchor": "Browse by brand", "target": "/brand/[brand-slug]", "reason": "Internal link diversity"},
            {"anchor": "See customer reviews", "target": "#reviews", "reason": "Reduces bounce rate"},
            {"anchor": "Compare options", "target": "/compare/[product-slug]", "reason": "Topical depth signal"},
        ],
        "category": [
            {"anchor": "Top products in this category", "target": "/category/[sub-category]", "reason": "Deeper crawl path for Google"},
            {"anchor": "Read our complete guide", "target": "/blog/[guide-slug]", "reason": "Content depth signal"},
            {"anchor": "Browse by brand", "target": "/brand/[brand-slug]", "reason": "Brand authority pages"},
            {"anchor": "View all deals", "target": "/deals", "reason": "Conversion page boost"},
        ],
        "blog": [
            {"anchor": "[Related article title]", "target": "/blog/[related-slug]", "reason": "Topical content cluster"},
            {"anchor": "Explore our [product/service]", "target": "/[main-service-page]", "reason": "Revenue page link"},
            {"anchor": "See all [category]", "target": "/category/[category-slug]", "reason": "Navigation depth"},
            {"anchor": "About us", "target": "/about", "reason": "Trust signal"},
        ],
        "homepage": [
            {"anchor": "[Main service/product]", "target": "/[main-service-slug]", "reason": "Primary conversion page"},
            {"anchor": "How it works", "target": "/how-it-works", "reason": "Trust builder — reduces bounce"},
            {"anchor": "Browse [category]", "target": "/[category-slug]", "reason": "Category page authority"},
            {"anchor": "Our blog & guides", "target": "/blog", "reason": "Content authority signal"},
            {"anchor": "Contact us", "target": "/contact", "reason": "Local SEO + trust signal"},
        ],
        "static": [
            {"anchor": "Back to home", "target": "/", "reason": "Homepage authority"},
            {"anchor": "Our services", "target": "/[service-slug]", "reason": "Conversion funnel"},
            {"anchor": "Read our blog", "target": "/blog", "reason": "Content depth"},
        ],
    }
    return m.get(page_type, [
        {"anchor": "[Relevant anchor text]", "target": "/relevant-page", "reason": "Context relevance"},
    ])


# ── Developer code hints ──────────────────────────────────────────────────────

def _dev_hints(page_type: str, sugg: dict, url: str) -> list:
    hints = []
    hints.append({
        "priority": "critical", "section": "HTML <head>", "type": "Title Tag",
        "description": "Add/update the page title — most important SEO element",
        "code": f"<title>{sugg.get('title', '[Title Here]')}</title>",
    })
    hints.append({
        "priority": "critical", "section": "HTML <head>", "type": "Meta Description",
        "description": "Add meta description — shown in Google search results",
        "code": f'<meta name="description" content="{sugg.get("meta_description", "[Description]")}">',
    })
    hints.append({
        "priority": "critical", "section": "HTML <body> — first element", "type": "H1 Tag",
        "description": "One H1 per page — the main topic signal for Google",
        "code": f"<h1>{sugg.get('h1', '[H1 Here]')}</h1>",
    })
    hints.append({
        "priority": "high", "section": "HTML <head>", "type": "Canonical Tag",
        "description": "Prevents duplicate content penalties",
        "code": f'<link rel="canonical" href="{sugg.get("canonical", url)}">',
    })
    hints.append({
        "priority": "high", "section": "HTML <head>", "type": "Open Graph Tags",
        "description": "Controls how page looks when shared on WhatsApp/Facebook",
        "code": f'''<meta property="og:title" content="{sugg.get('title', '[Title]')}">
<meta property="og:description" content="{sugg.get('meta_description', '[Description]')[:100]}">
<meta property="og:image" content="[Featured Image URL — 1200x630px]">
<meta property="og:url" content="{url}">
<meta property="og:type" content="website">''',
    })
    schema = sugg.get("schema_json_ld")
    if schema:
        hints.append({
            "priority": "high", "section": "HTML <head> or before </body>", "type": "Schema JSON-LD",
            "description": f"Structured data for rich results in Google — use {schema.get('@type','WebPage')} type",
            "code": f'<script type="application/ld+json">\n{json.dumps(schema, indent=2, ensure_ascii=False)}\n</script>',
        })
    for alt_item in sugg.get("image_alts", [])[:3]:
        hints.append({
            "priority": "medium", "section": "<img> tag", "type": "Image Alt Text",
            "description": "Alt text helps Google understand image content",
            "code": f'<img src="{alt_item["src"]}" alt="{alt_item["suggested_alt"]}" loading="lazy" width="800" height="600">',
        })
    if page_type in ("product", "category", "homepage"):
        hints.append({
            "priority": "medium", "section": "Next.js / React", "type": "next/head (React/Next.js)",
            "description": "If using Next.js, use next/head or next-seo package",
            "code": f'''// Option 1: next/head
import Head from 'next/head';
export default function Page() {{
  return (
    <>
      <Head>
        <title>{sugg.get("title", "[Title]")}</title>
        <meta name="description" content="{sugg.get("meta_description", "[Description]")[:100]}" />
        <link rel="canonical" href="{url}" />
      </Head>
      <main>...</main>
    </>
  );
}}

// Option 2: next-seo (recommended)
// npm install next-seo
import {{ NextSeo }} from 'next-seo';
<NextSeo
  title="{sugg.get("title", "[Title]")}"
  description="{sugg.get("meta_description", "[Description]")[:100]}"
  canonical="{url}"
  openGraph={{{{
    url: '{url}',
    title: '{sugg.get("title", "[Title]")}',
    description: '{sugg.get("meta_description", "[Desc]")[:80]}',
    images: [{{ url: '[Image URL]', width: 1200, height: 630 }}],
  }}}}
/>''',
        })
    return hints


# ── Content improvement suggestions ──────────────────────────────────────────

def _content_suggestions(page_type: str, word_count: int, keywords: list, h2: list, h3: list = None) -> list:  # noqa: ARG001 (h3 reserved)
    suggs = []
    kw = keywords[0][0] if keywords else "your main topic"

    if word_count < 300:
        suggs.append({
            "issue": f"Thin content ({word_count} words)",
            "fix": f"Add at least 300-500 words of unique, helpful content about {kw}",
            "example": f"Explain what {kw} means, how it works, why customers should choose you",
        })

    if not h2:
        suggs.append({
            "issue": "No H2 subheadings",
            "fix": "Add 3-5 H2 headings to structure your content",
            "example": f"H2 ideas: 'Why Choose Us for {kw.title()}', 'How {kw.title()} Works', 'FAQs about {kw.title()}'",
        })

    if page_type == "product" and word_count < 200:
        suggs.append({
            "issue": "Product description too short",
            "fix": "Add 200+ word product description with features, benefits, specs",
            "example": "Include: specifications table, key features list, warranty info, use cases",
        })

    if page_type == "category" and word_count < 150:
        suggs.append({
            "issue": "Category page has no introductory text",
            "fix": "Add 100-150 word intro paragraph above product grid",
            "example": f"Introduce the category, mention top brands, add a buying guide link",
        })

    if page_type == "blog" and word_count < 800:
        suggs.append({
            "issue": f"Blog post too short ({word_count} words)",
            "fix": "Aim for 1000-1500 words for blog posts to rank well",
            "example": "Add sections: Introduction, Step-by-step guide, Examples, FAQs, Conclusion",
        })

    if keywords and len(h2) > 0:
        kw_in_h2 = any(kw.lower() in h.lower() for h in h2)
        if not kw_in_h2:
            suggs.append({
                "issue": f"Main keyword '{kw}' not found in any H2",
                "fix": "Include the main keyword in at least one H2 subheading",
                "example": f"H2: 'Best {kw.title()} Deals' or 'How to {kw.title()}'",
            })

    return suggs


# ── Main per-page analyzer ────────────────────────────────────────────────────

def analyze_page(page_data: dict) -> dict:
    url = page_data.get("url", "")
    title = page_data.get("title", "")
    meta_desc = page_data.get("meta_description", "")
    h1 = page_data.get("h1", [])
    h2 = page_data.get("h2", [])
    h3 = page_data.get("h3", [])
    canonical = page_data.get("canonical", "")
    images_no_alt = page_data.get("images_without_alt", [])
    internal_links = page_data.get("internal_links", [])
    schema = page_data.get("schema_markup", [])
    word_count = page_data.get("word_count", 0)
    robots_meta = page_data.get("robots_meta", "")
    og_tags = page_data.get("og_tags", {})

    page_type = detect_page_type(url, title, h1)

    # Build page text for keyword extraction
    all_text = " ".join(filter(None, [title, meta_desc, " ".join(h1), " ".join(h2), " ".join(h3)]))
    keywords = extract_keywords(all_text, top_n=15)

    # Readability
    read = readability_score(meta_desc + " " + " ".join(h2))

    # Score breakdown
    scores = _compute_scores(title, meta_desc, h1, canonical, schema, word_count, len(images_no_alt), len(internal_links))

    # Build prioritized issues
    issues_list = []

    # Critical
    if not title:
        issues_list.append(_issue("critical", "Title Tag", "Missing completely", "Add a 50-60 char title with your main keyword"))
    elif len(title) < 30:
        issues_list.append(_issue("critical", "Title Tag", f"Too short ({len(title)} chars)", "Expand to 50-60 chars with keyword + brand"))
    elif len(title) > 65:
        issues_list.append(_issue("high", "Title Tag", f"Too long ({len(title)} chars)", "Trim to under 60 chars"))

    if not meta_desc:
        issues_list.append(_issue("critical", "Meta Description", "Missing completely", "Add 150-160 char description with keyword + CTA"))
    elif len(meta_desc) < 100:
        issues_list.append(_issue("high", "Meta Description", f"Too short ({len(meta_desc)} chars)", "Expand to 150-160 chars"))
    elif len(meta_desc) > 165:
        issues_list.append(_issue("medium", "Meta Description", f"Too long ({len(meta_desc)} chars)", "Trim to 160 chars max"))

    if not h1:
        issues_list.append(_issue("critical", "H1 Tag", "Missing — Google cannot identify page topic", "Add one H1 with primary keyword"))
    elif len(h1) > 1:
        issues_list.append(_issue("high", "H1 Tag", f"Multiple H1s ({len(h1)}) found", "Keep only one H1 per page"))

    if word_count < 100:
        issues_list.append(_issue("critical", "Content", f"Only {word_count} words — page is almost empty",
            "This page appears JS-rendered. Enable SSR/SSG or add static content"))
    elif word_count < 300:
        issues_list.append(_issue("high", "Content", f"Thin content ({word_count} words)", "Add 300+ words of relevant content"))

    # High
    if not canonical:
        issues_list.append(_issue("high", "Canonical Tag", "Missing — risk of duplicate content", f'Add <link rel="canonical" href="{url}">'))
    if not schema:
        schema_type = {"product": "Product", "blog": "Article", "homepage": "Organization", "category": "CollectionPage"}.get(page_type, "WebPage")
        issues_list.append(_issue("high", "Schema Markup", f"Missing {schema_type} structured data", "Add JSON-LD schema for rich snippets in Google"))
    if not og_tags.get("title"):
        issues_list.append(_issue("high", "Open Graph", "Missing OG tags — bad WhatsApp/Facebook sharing", "Add og:title, og:description, og:image"))

    # Medium
    if images_no_alt:
        issues_list.append(_issue("medium", "Images Alt Text", f"{len(images_no_alt)} image(s) missing alt text", "Add descriptive alt text with keyword where relevant"))
    if not h2:
        issues_list.append(_issue("medium", "H2 Subheadings", "No H2 tags — content is unstructured", "Add 3-5 H2s to structure the page content"))
    if len(internal_links) < 3:
        issues_list.append(_issue("medium", "Internal Links", f"Only {len(internal_links)} internal link(s)", "Add 3-5 contextual internal links"))

    # Low
    if keywords and title:
        main_kw = keywords[0][0].lower()
        if main_kw not in title.lower():
            issues_list.append(_issue("low", "Keyword in Title", f"Main keyword '{main_kw}' not in title", f"Include '{main_kw}' in title tag"))
    if "noindex" in robots_meta.lower():
        issues_list.append(_issue("high", "Robots Meta", "noindex found — page excluded from Google", "Remove noindex if this page should be indexed"))

    # Sort by priority
    issues_list.sort(key=lambda x: PRIORITY.get(x["priority"], 99))

    # Build suggestions
    sugg = {}
    sugg["title"] = _smart_title(title, page_type, keywords)
    sugg["meta_description"] = _smart_meta(meta_desc, page_type, keywords)
    sugg["h1"] = _smart_h1(h1, page_type, keywords)
    sugg["slug"] = _suggest_slug(url)
    sugg["canonical"] = canonical or url
    sugg["schema_json_ld"] = _schema_template(page_type, url, title, meta_desc, keywords)
    sugg["image_alts"] = [
        {"src": src, "suggested_alt": _suggest_alt(src, page_type, keywords)}
        for src in images_no_alt[:10]
    ]
    sugg["internal_link_suggestions"] = _internal_link_suggestions(page_type)
    sugg["developer_hints"] = _dev_hints(page_type, sugg, url)
    sugg["content_improvements"] = _content_suggestions(page_type, word_count, keywords, h2, h3)
    sugg["local_seo"] = _local_seo_suggestions(url, title, meta_desc, h1, page_type, keywords)

    return {
        "url": url,
        "page_type": page_type,
        "scores": scores,
        "score": scores["overall"],
        "issues": issues_list,
        "keywords": keywords[:10],
        "readability": read,
        "current": {
            "title": title,
            "title_length": len(title),
            "meta_description": meta_desc,
            "meta_length": len(meta_desc),
            "h1": h1,
            "h2": h2[:8],
            "h3": h3[:8],
            "canonical": canonical,
            "word_count": word_count,
            "schema_count": len(schema),
            "schema_types": [s.get("@type","") for s in schema],
            "images_without_alt": len(images_no_alt),
            "internal_links_count": len(internal_links),
            "og_title": og_tags.get("title",""),
            "og_description": og_tags.get("description",""),
            "og_image": og_tags.get("image",""),
        },
        "suggestions": sugg,
    }


def _suggest_slug(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if not path:
        return "/"
    clean = re.sub(r"[^a-z0-9\-/]", "-", path.lower())
    clean = re.sub(r"-{2,}", "-", clean).strip("-")
    return "/" + clean


def _suggest_alt(src: str, page_type: str, keywords: list) -> str:
    kw = keywords[0][0] if keywords else "product"
    fname = src.split("/")[-1].split("?")[0].replace("-", " ").replace("_", " ").split(".")[0]
    if fname and len(fname) > 3:
        return f"{fname.title()} — {kw.title()}"
    return f"{page_type.title()} image — {kw}"


# ── Technical SEO analysis ────────────────────────────────────────────────────

def analyze_technical_seo(base_url: str, robots_txt: str, sitemap: dict, pages: list) -> dict:
    issues = []
    recommendations = []
    parsed = urlparse(base_url)

    if parsed.scheme != "https":
        issues.append(_issue("critical", "HTTPS", "Site not using HTTPS", "Migrate to HTTPS — get free SSL from Let's Encrypt"))
    else:
        recommendations.append("HTTPS is enabled — good security foundation")

    if "not found" in robots_txt.lower() or "failed" in robots_txt.lower():
        issues.append(_issue("high", "robots.txt", "File not found", "Create /robots.txt to control crawler access"))
    else:
        if "disallow: /" in robots_txt.lower() and "allow: /" not in robots_txt.lower()[:50]:
            issues.append(_issue("critical", "robots.txt", "Blocking ALL crawlers with Disallow: /", "Fix robots.txt — your site is invisible to Google!"))
        else:
            recommendations.append("robots.txt exists — review rules")

    if not sitemap.get("found"):
        issues.append(_issue("high", "Sitemap", "XML sitemap not found", "Generate sitemap.xml and submit to Google Search Console"))
    else:
        url_count = sitemap.get("url_count", 0)
        recommendations.append(f"Sitemap found with {url_count} URLs")
        if url_count > 50000:
            issues.append(_issue("medium", "Sitemap", "50,000+ URLs in one sitemap", "Split into multiple sitemaps"))

    pages_no_canonical = sum(1 for p in pages if not p.get("error") and not p.get("canonical"))
    pages_no_schema = sum(1 for p in pages if not p.get("error") and not p.get("schema_markup"))
    pages_no_title = sum(1 for p in pages if not p.get("error") and not p.get("title"))

    if pages_no_canonical:
        issues.append(_issue("high", "Canonical Tags", f"{pages_no_canonical} page(s) missing canonical", "Add canonical to every page"))
    if pages_no_schema:
        issues.append(_issue("high", "Schema Markup", f"{pages_no_schema} page(s) missing structured data", "Add Schema.org JSON-LD"))
    if pages_no_title:
        issues.append(_issue("critical", "Title Tags", f"{pages_no_title} page(s) missing title", "Add title to every page"))

    all_images_no_alt = sum(len(p.get("images_without_alt", [])) for p in pages if not p.get("error"))
    if all_images_no_alt:
        issues.append(_issue("medium", "Image Alt Text", f"{all_images_no_alt} images missing alt", "Add descriptive alt text to all images"))

    noindex_pages = [p["url"] for p in pages if not p.get("error") and "noindex" in p.get("robots_meta", "").lower()]
    if noindex_pages:
        issues.append(_issue("high", "Noindex Pages", f"{len(noindex_pages)} page(s) set to noindex", "Verify noindex is intentional"))

    issues.sort(key=lambda x: PRIORITY.get(x["priority"], 99))
    critical = sum(1 for i in issues if i["priority"] == "critical")
    high = sum(1 for i in issues if i["priority"] == "high")
    base_score = 100 - (critical * 20) - (high * 10)
    score = max(0, min(100, base_score))

    return {
        "base_url": base_url,
        "https_enabled": parsed.scheme == "https",
        "robots_txt_found": "not found" not in robots_txt.lower() and "failed" not in robots_txt.lower(),
        "robots_txt_content": robots_txt[:2000],
        "sitemap": sitemap,
        "total_pages_crawled": len(pages),
        "issues": issues,
        "recommendations": recommendations,
        "score": score,
        "summary": {
            "critical": critical,
            "high": high,
            "medium": sum(1 for i in issues if i["priority"] == "medium"),
            "low": sum(1 for i in issues if i["priority"] == "low"),
        },
    }


# ── GTM / GA4 / Meta Pixel guide ─────────────────────────────────────────────

def generate_tracking_guide(base_url: str = "") -> dict:  # noqa: ARG001
    return {
        "gtm": {
            "title": "Google Tag Manager (GTM) Setup",
            "steps": [
                "Go to tagmanager.google.com — create account + container",
                "Copy GTM container ID (format: GTM-XXXXXXX)",
                "Paste <head> snippet in your base HTML template <head>",
                "Paste <body> snippet right after <body> tag",
                "Publish the container in GTM dashboard",
            ],
            "head_snippet": """<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-XXXXXXX');</script>
<!-- End Google Tag Manager -->""",
            "body_snippet": """<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-XXXXXXX"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->""",
            "note": "Replace GTM-XXXXXXX with your actual container ID",
        },
        "ga4": {
            "title": "Google Analytics 4 (GA4) Setup",
            "steps": [
                "Go to analytics.google.com — create GA4 property",
                "Get Measurement ID (format: G-XXXXXXXXXX)",
                "In GTM: New Tag > Google Analytics: GA4 Configuration",
                "Enter Measurement ID, trigger: All Pages — Save & Publish",
            ],
            "direct_snippet": """<!-- GA4 Direct Implementation -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX', {
    page_title: document.title,
    page_location: window.location.href
  });
</script>""",
            "ecommerce_events": [
                {"event": "view_item", "trigger": "Product page load", "code": """gtag('event', 'view_item', {
  currency: '[CURRENCY_CODE]',       // e.g. 'INR', 'USD'
  value: [PRODUCT_PRICE],
  items: [{
    item_id: '[YOUR_SKU]',
    item_name: '[Product Name]',
    item_category: '[Category]',
    price: [PRODUCT_PRICE],
    quantity: 1
  }]
});"""},
                {"event": "add_to_cart", "trigger": "Add to Cart click", "code": """gtag('event', 'add_to_cart', {
  currency: '[CURRENCY_CODE]',
  value: [PRODUCT_PRICE],
  items: [{
    item_id: '[YOUR_SKU]',
    item_name: '[Product Name]',
    price: [PRODUCT_PRICE],
    quantity: 1
  }]
});"""},
                {"event": "purchase", "trigger": "Order confirmation page", "code": """gtag('event', 'purchase', {
  transaction_id: '[ORDER_ID]',
  value: [ORDER_TOTAL],
  currency: '[CURRENCY_CODE]',
  items: [{
    item_id: '[YOUR_SKU]',
    item_name: '[Product Name]',
    price: [PRODUCT_PRICE],
    quantity: [QTY]
  }]
});"""},
            ],
        },
        "meta_pixel": {
            "title": "Meta (Facebook) Pixel Setup",
            "steps": [
                "Go to business.facebook.com > Events Manager > Connect Data Source",
                "Choose Web > Meta Pixel > Get Code",
                "Copy your Pixel ID",
                "Add base code in <head> of every page",
            ],
            "base_code": """<!-- Meta Pixel Code -->
<script>
!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}
(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init', 'YOUR_PIXEL_ID');
fbq('track', 'PageView');
</script>
<noscript><img height="1" width="1" style="display:none"
src="https://www.facebook.com/tr?id=YOUR_PIXEL_ID&ev=PageView&noscript=1"/></noscript>
<!-- End Meta Pixel Code -->""",
            "ecommerce_events": [
                {"event": "ViewContent", "trigger": "Product page", "code": """fbq('track', 'ViewContent', {
  content_ids: ['[YOUR_SKU]'],
  content_type: 'product',
  value: [PRODUCT_PRICE],
  currency: '[CURRENCY_CODE]'   // e.g. 'INR', 'USD'
});"""},
                {"event": "AddToCart", "trigger": "Add to Cart button", "code": """fbq('track', 'AddToCart', {
  content_ids: ['[YOUR_SKU]'],
  content_type: 'product',
  value: [PRODUCT_PRICE],
  currency: '[CURRENCY_CODE]'
});"""},
                {"event": "Purchase", "trigger": "Order confirmation", "code": """fbq('track', 'Purchase', {
  value: [ORDER_TOTAL],
  currency: '[CURRENCY_CODE]',
  contents: [{ id: '[YOUR_SKU]', quantity: [QTY] }],
  content_type: 'product'
});"""},
            ],
        },
    }
