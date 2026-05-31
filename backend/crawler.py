import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


# ── JS detection ──────────────────────────────────────────────────────────────

def _is_js_heavy(html: str, word_count: int) -> bool:
    """Returns True if page needs JS rendering."""
    if word_count < 50:
        return True
    indicators = [
        "__NEXT_DATA__", "__nuxt", "ng-version", "data-reactroot",
        "_app.js", "_next/static", "window.__REDUX", "Vue.config",
    ]
    return any(i in html for i in indicators)


# ── Playwright JS renderer ────────────────────────────────────────────────────

def _crawl_with_playwright(url: str) -> str:
    """Use headless Chromium to render JS-heavy pages. Returns rendered HTML."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=HEADERS["User-Agent"],
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=25000)
            # Wait for main content to render
            page.wait_for_timeout(2000)
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        return f"PLAYWRIGHT_ERROR:{e}"


# ── Core page data extraction ─────────────────────────────────────────────────

def _extract_from_html(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    parsed_url = urlparse(url)

    # Remove script/style noise
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_desc_tag.get("content", "").strip() if meta_desc_tag else ""

    canonical_tag = soup.find("link", attrs={"rel": "canonical"})
    canonical = canonical_tag.get("href", "").strip() if canonical_tag else ""

    h1 = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)]
    h2 = [h.get_text(strip=True) for h in soup.find_all("h2") if h.get_text(strip=True)]
    h3 = [h.get_text(strip=True) for h in soup.find_all("h3") if h.get_text(strip=True)]

    images_without_alt = []
    for img in soup.find_all("img"):
        alt = (img.get("alt") or "").strip()
        if not alt:
            src = img.get("src") or img.get("data-src") or img.get("data-lazy-src", "")
            if src and not src.startswith("data:"):
                images_without_alt.append(urljoin(url, src))

    internal_links = []
    seen_links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        full_url = urljoin(url, href)
        if urlparse(full_url).netloc == parsed_url.netloc and full_url not in seen_links:
            seen_links.add(full_url)
            anchor = a.get_text(strip=True)[:80]
            if anchor:
                internal_links.append({"url": full_url, "text": anchor})

    schema_markup = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            if script.string:
                data = json.loads(script.string)
                schema_markup.append(data)
        except Exception:
            pass

    robots_meta_tag = soup.find("meta", attrs={"name": "robots"})
    robots_meta = robots_meta_tag.get("content", "").strip() if robots_meta_tag else ""

    og_tags = {}
    for prop in ["og:title", "og:description", "og:image", "og:url"]:
        tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
        og_tags[prop.replace("og:", "")] = tag.get("content", "") if tag else ""

    # Get page text (for word count + keyword extraction)
    body = soup.find("body") or soup
    body_text = body.get_text(separator=" ", strip=True)
    word_count = len(body_text.split())

    # Content sections
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 30]

    return {
        "title": title,
        "meta_description": meta_description,
        "canonical": canonical,
        "h1": h1,
        "h2": h2,
        "h3": h3,
        "images_without_alt": images_without_alt[:30],
        "internal_links": internal_links[:60],
        "schema_markup": schema_markup,
        "robots_meta": robots_meta,
        "og_tags": og_tags,
        "word_count": word_count,
        "body_text_sample": body_text[:500],
        "paragraphs": paragraphs[:5],
        "slug": parsed_url.path or "/",
    }


# ── Single page crawl ─────────────────────────────────────────────────────────

def crawl_page(url: str) -> dict:
    base = {"url": url, "error": None, "render_method": "requests"}

    try:
        # Step 1: Try with requests first (fast)
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        html = response.text
        base["status_code"] = response.status_code

        extracted = _extract_from_html(html, url)
        base.update(extracted)

        # Step 2: If JS-heavy site detected, re-render with Playwright
        if _is_js_heavy(html, extracted["word_count"]):
            base["render_method"] = "playwright"
            rendered_html = _crawl_with_playwright(url)
            if rendered_html.startswith("PLAYWRIGHT_ERROR:"):
                base["playwright_error"] = rendered_html
            else:
                js_data = _extract_from_html(rendered_html, url)
                # Merge — prefer Playwright data where it has more content
                for key in ["title", "meta_description", "h1", "h2", "h3",
                            "images_without_alt", "internal_links", "schema_markup",
                            "robots_meta", "og_tags", "word_count", "body_text_sample",
                            "paragraphs", "canonical"]:
                    requests_val = extracted.get(key)
                    pw_val = js_data.get(key)
                    # Use Playwright value if it has more content
                    if isinstance(pw_val, str) and len(pw_val) > len(requests_val or ""):
                        base[key] = pw_val
                    elif isinstance(pw_val, list) and len(pw_val) > len(requests_val or []):
                        base[key] = pw_val
                    elif isinstance(pw_val, int) and pw_val > (requests_val or 0):
                        base[key] = pw_val

        return base

    except requests.exceptions.Timeout:
        return {**base, "error": "Request timed out after 15s"}
    except requests.exceptions.ConnectionError:
        return {**base, "error": "Cannot connect to server — check if URL is correct"}
    except requests.exceptions.HTTPError as e:
        return {**base, "error": f"HTTP {e.response.status_code} error"}
    except Exception as e:
        return {**base, "error": str(e)}


# ── robots.txt ────────────────────────────────────────────────────────────────

def fetch_robots_txt(base_url: str) -> str:
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        r = requests.get(robots_url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.text
        return f"robots.txt not found (HTTP {r.status_code})"
    except Exception as e:
        return f"Failed to fetch robots.txt: {e}"


# ── sitemap.xml ───────────────────────────────────────────────────────────────

def fetch_sitemap(base_url: str) -> dict:
    parsed = urlparse(base_url)
    for path in ["/sitemap.xml", "/sitemap_index.xml", "/sitemap/", "/sitemap"]:
        sitemap_url = f"{parsed.scheme}://{parsed.netloc}{path}"
        try:
            r = requests.get(sitemap_url, headers=HEADERS, timeout=10)
            if r.status_code == 200 and ("xml" in r.headers.get("content-type", "") or "<url" in r.text):
                soup = BeautifulSoup(r.content, "xml")
                urls = [loc.text.strip() for loc in soup.find_all("loc")]
                return {
                    "found": True,
                    "url": sitemap_url,
                    "url_count": len(urls),
                    "sample_urls": urls[:20],
                }
        except Exception:
            continue
    return {"found": False, "url": f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"}


# ── Multi-page crawl ──────────────────────────────────────────────────────────

def crawl_website(base_url: str, max_pages: int = 8, progress_callback=None) -> list:
    pages = []
    visited = set()
    to_visit = [base_url]

    while to_visit and len(pages) < max_pages:
        url = to_visit.pop(0)

        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/") or base_url
        if normalized in visited:
            continue
        visited.add(normalized)

        if progress_callback:
            progress_callback(f"Crawling ({len(pages)+1}/{max_pages}): {url[:60]}")

        page_data = crawl_page(url)
        pages.append(page_data)

        if not page_data.get("error") and len(pages) < max_pages:
            for link in page_data.get("internal_links", [])[:6]:
                link_url = link["url"]
                lp = urlparse(link_url)
                link_norm = f"{lp.scheme}://{lp.netloc}{lp.path}".rstrip("/")
                if link_norm not in visited and link_url not in to_visit:
                    to_visit.append(link_url)

        time.sleep(0.8)

    return pages
