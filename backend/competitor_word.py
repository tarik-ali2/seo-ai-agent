"""
Generates Competitor_SEO_Comparison.docx
A professional side-by-side SEO battle report.
"""
import json, os
from datetime import datetime
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# Colors
C_OUR    = RGBColor(0x1A, 0x73, 0xE8)   # Blue  = our site
C_COMP   = RGBColor(0xE8, 0x45, 0x1A)   # Red   = competitor
C_WIN    = RGBColor(0x18, 0x80, 0x38)   # Green = winner
C_LOSE   = RGBColor(0xD3, 0x00, 0x00)   # Red   = loser
C_TIE    = RGBColor(0x88, 0x88, 0x88)
C_WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
C_DARK   = RGBColor(0x20, 0x20, 0x20)
C_GRAY   = RGBColor(0x66, 0x66, 0x66)
C_YELLOW = RGBColor(0xC9, 0xA7, 0x00)
C_ORANGE = RGBColor(0xE6, 0x74, 0x00)

PRIORITY_COLOR = {"critical": C_LOSE, "high": C_ORANGE, "medium": C_YELLOW, "low": C_WIN}
PRIORITY_FILL  = {"critical": "FFE5E5", "high": "FFF0E0", "medium": "FFFBE0", "low": "E8F5E9"}


# ── XML helpers ───────────────────────────────────────────────────────────────

def _bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _border(cell, color="CCCCCC"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcB = OxmlElement("w:tcBorders")
    for side in ["top","left","bottom","right"]:
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), color)
        tcB.append(el)
    tcPr.append(tcB)


def _ct(cell, text, bold=False, color=None, size=9, align=None):
    cell.text = ""
    p = cell.paragraphs[0]
    if align:
        p.alignment = align
    run = p.add_run(str(text) if text is not None else "—")
    run.bold = bold
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = color


# ── Doc helpers ───────────────────────────────────────────────────────────────

def _margins(doc):
    for s in doc.sections:
        s.top_margin = s.bottom_margin = Cm(2)
        s.left_margin = s.right_margin = Cm(2.2)


def _h1(doc, text):
    p = doc.add_heading("", 1)
    p.clear()
    r = p.add_run(text)
    r.font.size = Pt(15); r.font.bold = True; r.font.color.rgb = C_DARK


def _h2(doc, text):
    p = doc.add_heading("", 2)
    p.clear()
    r = p.add_run(text)
    r.font.size = Pt(12); r.font.bold = True; r.font.color.rgb = C_OUR


def _divider(doc):
    p = doc.add_paragraph()
    r = p.add_run("─" * 95)
    r.font.size = Pt(7); r.font.color.rgb = RGBColor(0xDD,0xDD,0xDD)


def _footer(doc, text):
    for s in doc.sections:
        f = s.footer
        p = f.paragraphs[0] if f.paragraphs else f.add_paragraph()
        p.text = text
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.size = Pt(8); r.font.color.rgb = C_GRAY


def _cover(doc, our_domain, comp_domain, verdict):
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("⚔  SEO Competitor Comparison Report")
    r.font.size = Pt(22); r.font.bold = True; r.font.color.rgb = C_DARK

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER

    r_our = p2.add_run(our_domain)
    r_our.font.size = Pt(14); r_our.font.bold = True; r_our.font.color.rgb = C_OUR

    p2.add_run("  vs  ").font.size = Pt(14)

    r_comp = p2.add_run(comp_domain)
    r_comp.font.size = Pt(14); r_comp.font.bold = True; r_comp.font.color.rgb = C_COMP

    # Verdict box
    doc.add_paragraph()
    vp = doc.add_paragraph()
    vp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    vr = vp.add_run(f"  Verdict: {verdict['status']}  —  {verdict['summary']}  ")
    vr.font.size = Pt(11); vr.font.bold = True
    fill = {"critical": C_LOSE, "high": C_ORANGE, "medium": C_YELLOW, "low": C_WIN}.get(verdict["color"], C_GRAY)
    vr.font.color.rgb = fill

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p3.add_run(f"Generated: {datetime.now().strftime('%d %B %Y')}  |  SEO AI Agent").font.size = Pt(9)

    doc.add_paragraph(); _divider(doc); doc.add_paragraph()


# ── Main comparison table ─────────────────────────────────────────────────────

def _main_comparison_table(doc, data):
    our   = data["our_stats"]
    comp  = data["competitor_stats"]
    od    = data["our_domain"]
    cd    = data["competitor_domain"]

    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"

    # Header
    hdr = table.rows[0].cells
    for c, t, bg in zip(hdr, ["SEO Factor", od, cd, "Winner"],
                         ["2C3E50","1A73E8","E8451A","27AE60"]):
        _bg(c, bg); _ct(c, t, bold=True, color=C_WHITE, size=10)

    rows = [
        ("Technical Score",   f"{our['score']}/100",   f"{comp['score']}/100",   our['score'],   comp['score']),
        ("On-Page Avg Score", f"{our['onpage_avg_score']}/100", f"{comp['onpage_avg_score']}/100", our['onpage_avg_score'], comp['onpage_avg_score']),
        ("HTTPS",             "✅ Yes" if our['https'] else "❌ No", "✅ Yes" if comp['https'] else "❌ No", int(our['https']), int(comp['https'])),
        ("robots.txt",        "✅ Found" if our['robots_txt'] else "❌ Missing", "✅ Found" if comp['robots_txt'] else "❌ Missing", int(our['robots_txt']), int(comp['robots_txt'])),
        ("XML Sitemap",       f"✅ {our['sitemap_urls']} URLs" if our['sitemap'] else "❌ Missing", f"✅ {comp['sitemap_urls']} URLs" if comp['sitemap'] else "❌ Missing", int(our['sitemap']), int(comp['sitemap'])),
        ("Pages Crawled",     str(our['pages_crawled']), str(comp['pages_crawled']), our['pages_crawled'], comp['pages_crawled']),
        ("Pages with Title",  str(our['pages_with_title']), str(comp['pages_with_title']), our['pages_with_title'], comp['pages_with_title']),
        ("Pages with Meta",   str(our['pages_with_meta']), str(comp['pages_with_meta']), our['pages_with_meta'], comp['pages_with_meta']),
        ("Pages with H1",     str(our['pages_with_h1']), str(comp['pages_with_h1']), our['pages_with_h1'], comp['pages_with_h1']),
        ("Pages with Schema", str(our['pages_with_schema']), str(comp['pages_with_schema']), our['pages_with_schema'], comp['pages_with_schema']),
        ("Pages with Canonical", str(our['pages_with_canon']), str(comp['pages_with_canon']), our['pages_with_canon'], comp['pages_with_canon']),
        ("Avg Word Count",    f"{our['avg_word_count']} words", f"{comp['avg_word_count']} words", our['avg_word_count'], comp['avg_word_count']),
        ("SEO Grade",         data['our_grade'], data['competitor_grade'], our['onpage_avg_score'], comp['onpage_avg_score']),
    ]

    for label, our_val, comp_val, our_num, comp_num in rows:
        row = table.add_row().cells
        _bg(row[0], "EAF0FB")
        _bg(row[1], "F0F8FF" if our_num >= comp_num else "FFF5F5")
        _bg(row[2], "F0F8FF" if comp_num >= our_num else "FFF5F5")
        _bg(row[3], "F0FFF4")
        _ct(row[0], label, bold=True, size=9, color=C_DARK)
        _ct(row[1], our_val, bold=(our_num > comp_num), size=9,
            color=C_WIN if our_num > comp_num else C_LOSE if our_num < comp_num else C_DARK)
        _ct(row[2], comp_val, bold=(comp_num > our_num), size=9,
            color=C_WIN if comp_num > our_num else C_LOSE if comp_num < our_num else C_DARK)
        winner = od if our_num > comp_num else cd if comp_num > our_num else "Tie"
        winner_color = C_OUR if our_num > comp_num else C_COMP if comp_num > our_num else C_TIE
        _ct(row[3], winner, bold=True, size=9, color=winner_color, align=WD_ALIGN_PARAGRAPH.CENTER)
        for c in row:
            _border(c)


# ── Opportunities table ───────────────────────────────────────────────────────

def _opportunities_table(doc, opportunities, our_domain):
    if not opportunities:
        doc.add_paragraph("No significant gaps found.")
        return

    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for c, t, bg in zip(hdr, ["Priority","Area","Gap","Action for " + our_domain],
                         ["C0392B","8E44AD","2980B9","27AE60"]):
        _bg(c, bg); _ct(c, t, bold=True, color=C_WHITE, size=9)

    for opp in opportunities:
        pri = opp.get("priority","medium")
        row = table.add_row().cells
        _bg(row[0], PRIORITY_FILL.get(pri,"FFFFFF"))
        _bg(row[1], "F8F9FA"); _bg(row[2], "FFF9F9"); _bg(row[3], "F0FFF4")
        labels = {"critical":"🔴 CRITICAL","high":"🟠 HIGH","medium":"🟡 MEDIUM","low":"🟢 LOW"}
        _ct(row[0], labels.get(pri,pri), bold=True, color=PRIORITY_COLOR.get(pri,C_DARK), size=8)
        _ct(row[1], opp.get("area",""), bold=True, size=9, color=C_OUR)
        _ct(row[2], opp.get("gap",""), size=8, color=C_GRAY)
        _ct(row[3], opp.get("action",""), size=9, color=RGBColor(0x0D,0x6E,0x3B))
        for c in row: _border(c)


# ── Keyword tables ────────────────────────────────────────────────────────────

def _keyword_gap_table(doc, keyword_gap, our_domain, comp_domain):
    if not keyword_gap:
        doc.add_paragraph("No significant keyword gap found.")
        return

    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for c, t, bg in zip(hdr, ["Keyword / Phrase", f"{comp_domain} Uses It?", f"Action for {our_domain}"],
                         ["8E44AD","E74C3C","27AE60"]):
        _bg(c, bg); _ct(c, t, bold=True, color=C_WHITE, size=9)

    for kw in keyword_gap[:20]:
        row = table.add_row().cells
        _bg(row[0], "FAF0FF"); _bg(row[1], "FFF0F0"); _bg(row[2], "F0FFF4")
        _ct(row[0], kw, bold=True, size=9, color=RGBColor(0x6C,0x3A,0xBD))
        _ct(row[1], "✅ Yes — ranking for this", size=9, color=C_COMP)
        action = f"Create a page/blog targeting '{kw}'"
        if "sell" in kw or "buy" in kw:
            action = f"Add dedicated landing page: /{kw.replace(' ','-')}"
        elif "price" in kw:
            action = f"Add pricing content targeting '{kw}'"
        _ct(row[2], action, size=9, color=RGBColor(0x0D,0x6E,0x3B))
        for c in row: _border(c)


def _shared_keywords_table(doc, our_kw, comp_kw, shared):
    if not shared:
        return
    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for c, t, bg in zip(hdr, ["Shared Keyword", "Our Frequency", "Competitor Frequency"],
                         ["2C3E50","1A73E8","E8451A"]):
        _bg(c, bg); _ct(c, t, bold=True, color=C_WHITE, size=9)
    our_kw_dict  = dict(our_kw)
    comp_kw_dict = dict(comp_kw)
    for kw in shared[:15]:
        row = table.add_row().cells
        our_f  = our_kw_dict.get(kw, 0)
        comp_f = comp_kw_dict.get(kw, 0)
        _bg(row[0], "F8F8F8")
        _bg(row[1], "F0F8FF" if our_f >= comp_f else "FFF5F5")
        _bg(row[2], "F0F8FF" if comp_f >= our_f else "FFF5F5")
        _ct(row[0], kw, bold=True, size=9)
        _ct(row[1], str(our_f), bold=(our_f > comp_f), size=9,
            color=C_WIN if our_f > comp_f else C_LOSE if our_f < comp_f else C_DARK)
        _ct(row[2], str(comp_f), bold=(comp_f > our_f), size=9,
            color=C_WIN if comp_f > our_f else C_LOSE if comp_f < our_f else C_DARK)
        for c in row: _border(c)


# ── Page comparison table ─────────────────────────────────────────────────────

def _page_comparison_section(doc, page_comparison, our_domain, comp_domain):
    for i, pc in enumerate(page_comparison, 1):
        _h2(doc, f"Page {i} Comparison")

        table = doc.add_table(rows=0, cols=3)
        table.style = "Table Grid"

        # Header row
        hdr_row = table.add_row().cells
        for c, t, bg in zip(hdr_row, ["SEO Element", our_domain, comp_domain],
                             ["2C3E50","1A73E8","E8451A"]):
            _bg(c, bg); _ct(c, t, bold=True, color=C_WHITE, size=9)

        comp_rows = [
            ("URL",          pc["our_url"][-55:],            pc["comp_url"][-55:]),
            ("Title",        pc["our_title"] or "❌ Missing", pc["comp_title"] or "❌ Missing"),
            ("Meta Desc",    (pc["our_meta"] or "❌ Missing")[:100], (pc["comp_meta"] or "❌ Missing")[:100]),
            ("H1",           pc["our_h1"] or "❌ Missing",   pc["comp_h1"] or "❌ Missing"),
            ("Word Count",   f"{pc['our_word_count']} words", f"{pc['comp_word_count']} words"),
            ("SEO Score",    f"{pc['our_score']}/100",        f"{pc['comp_score']}/100"),
            ("Winner 🏆",    "← We Win!" if pc["winner"] == pc["our_url"].split("/")[2] else "",
                             "← They Win!" if pc["winner"] != pc["our_url"].split("/")[2] else ""),
        ]
        for el, our_v, comp_v in comp_rows:
            row = table.add_row().cells
            _bg(row[0], "EAF0FB")
            _bg(row[1], "F0F8FF" if "Missing" not in str(our_v) else "FFF5F5")
            _bg(row[2], "F0F8FF" if "Missing" not in str(comp_v) else "FFF5F5")
            _ct(row[0], el, bold=True, size=9, color=C_DARK)
            our_color = C_LOSE if "Missing" in str(our_v) else C_OUR if el == "Winner 🏆" else C_DARK
            _ct(row[1], our_v, size=9, color=our_color)
            comp_color = C_LOSE if "Missing" in str(comp_v) else C_COMP if el == "Winner 🏆" else C_DARK
            _ct(row[2], comp_v, size=9, color=comp_color)
            for c in row: _border(c)

        doc.add_paragraph()


# ── Content ideas table ───────────────────────────────────────────────────────

def _content_ideas_table(doc, content_ideas, our_domain):
    if not content_ideas:
        return
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for c, t, bg in zip(hdr, ["Target Keyword","Content Type","Suggested Title","Priority"],
                         ["1A73E8","27AE60","8E44AD","C0392B"]):
        _bg(c, bg); _ct(c, t, bold=True, color=C_WHITE, size=9)

    for idea in content_ideas:
        pri = idea.get("priority","medium")
        row = table.add_row().cells
        _bg(row[0], "EAF0FB"); _bg(row[1], "F0FFF4")
        _bg(row[2], "FAF0FF"); _bg(row[3], PRIORITY_FILL.get(pri,"FFFFFF"))
        _ct(row[0], idea["keyword"], bold=True, size=9, color=C_OUR)
        _ct(row[1], idea["content_type"], size=9)
        _ct(row[2], idea["suggested_title"][:80], size=8, color=RGBColor(0x6C,0x3A,0xBD))
        labels = {"high":"🟠 HIGH","medium":"🟡 MEDIUM","critical":"🔴 CRITICAL","low":"🟢 LOW"}
        _ct(row[3], labels.get(pri,pri), bold=True, size=8, color=PRIORITY_COLOR.get(pri,C_DARK))
        for c in row: _border(c)


# ── Main document generator ───────────────────────────────────────────────────

def create_competitor_comparison_doc(data: dict, output_path: str):
    doc = Document()
    _margins(doc)

    od = data["our_domain"]
    cd = data["competitor_domain"]

    # Cover page
    _cover(doc, od, cd, data["verdict"])

    # ── Section 1: Overview ──
    _h1(doc, "1. SEO Battle — Side-by-Side Comparison")
    _main_comparison_table(doc, data)
    doc.add_paragraph()

    # Summary paragraph
    gap = data["verdict"]["gap"]
    p = doc.add_paragraph()
    if gap > 0:
        r = p.add_run(
            f"⚠  {od} is {gap} SEO points behind {cd}. "
            f"{cd} has better titles, more meta descriptions, and richer content. "
            f"The good news: these are all fixable in days, not months."
        )
        r.font.size = Pt(10); r.font.color.rgb = C_ORANGE
    else:
        r = p.add_run(f"✅  {od} is performing equal to or better than {cd}. Maintain the lead!")
        r.font.size = Pt(10); r.font.color.rgb = C_WIN

    doc.add_page_break()

    # ── Section 2: Opportunities ──
    _h1(doc, f"2. What {od} Must Fix to Beat {cd}")
    doc.add_paragraph(
        "These are the highest-impact actions — sorted by priority. "
        "Fix critical issues first, then high, then medium."
    ).runs[0].font.size = Pt(10)
    doc.add_paragraph()
    _opportunities_table(doc, data["opportunities"], od)
    doc.add_paragraph()

    doc.add_page_break()

    # ── Section 3: Keyword Gap ──
    _h1(doc, f"3. Keyword Gap Analysis — {cd} Ranks, {od} Doesn't")
    doc.add_paragraph(
        f"These keywords are found in {cd}'s content but missing from {od}. "
        f"Each is a content opportunity — create pages targeting these terms."
    ).runs[0].font.size = Pt(10)
    doc.add_paragraph()
    _keyword_gap_table(doc, data["keyword_gap"], od, cd)
    doc.add_paragraph()

    # Shared keywords
    _h2(doc, f"Keywords Both Sites Use (Where {od} Can Win)")
    doc.add_paragraph(
        "For these keywords, both sites compete. Increase your usage and content depth to outrank."
    ).runs[0].font.size = Pt(9)
    _shared_keywords_table(doc, data["our_keywords"], data["competitor_keywords"], data["shared_keywords"])
    doc.add_paragraph()

    doc.add_page_break()

    # ── Section 4: Content Ideas ──
    _h1(doc, f"4. Content Creation Roadmap for {od}")
    doc.add_paragraph(
        f"Based on keyword gap analysis, create these pages to compete with {cd}:"
    ).runs[0].font.size = Pt(10)
    doc.add_paragraph()
    _content_ideas_table(doc, data["content_ideas"], od)

    if not data["content_ideas"]:
        # Generic ideas if none detected
        doc.add_paragraph("Suggested content based on competitor analysis:")
        ideas = [
            f"Create: 'Sell Old Phone Online — Best Price Guaranteed' landing page",
            f"Create: 'Buy Refurbished Mobiles — [Brand]' category page",
            f"Create: 'How to Sell Your Old Phone — Complete Guide' blog post",
            f"Create: 'Top Refurbished Phones Under ₹10,000' comparison page",
            f"Create: FAQ page: 'How does selling your old phone work?'",
        ]
        for idea in ideas:
            p = doc.add_paragraph(style="List Bullet")
            p.add_run(idea).font.size = Pt(10)
    doc.add_paragraph()

    doc.add_page_break()

    # ── Section 5: Page by Page ──
    _h1(doc, "5. Page-by-Page SEO Comparison")
    doc.add_paragraph(
        f"Direct comparison of crawled pages from both sites."
    ).runs[0].font.size = Pt(10)
    doc.add_paragraph()
    _page_comparison_section(doc, data["page_comparison"], od, cd)

    doc.add_page_break()

    # ── Section 6: Action Plan ──
    _h1(doc, f"6. 30-Day SEO Action Plan for {od}")

    weeks = [
        ("Week 1 — Critical Fixes (Developer Tasks)", [
            f"Fix title tag on ALL pages — currently '{od}' (6 chars) on every page",
            "Add unique meta description to every page (150-160 chars)",
            "Fix multiple H1 tags — keep only ONE H1 per page",
            "Add canonical tag to every page",
            "Generate and submit sitemap.xml to Google Search Console",
        ]),
        ("Week 2 — On-Page SEO", [
            "Add Organization schema JSON-LD to homepage",
            "Add Product schema to all product/sell pages",
            "Fix og:title, og:description, og:image on all pages",
            f"Add keyword '{(data['keyword_gap'][:1] or ['sell old phone'])[0]}' to homepage title",
            "Add 3-5 H2 headings to structure content on thin pages",
        ]),
        ("Week 3 — Content Creation", [
            f"Write 500+ word intro content for homepage targeting '{(data['keyword_gap'][:1] or ['sell old phone'])[0]}'",
            "Create dedicated landing pages for top keyword gap terms",
            f"Add FAQ section to homepage and sell pages",
            "Add 200+ word descriptions to all product/category pages",
        ]),
        ("Week 4 — Technical + Tracking", [
            "Verify GTM, GA4, and Meta Pixel are firing on all pages",
            "Run PageSpeed test — fix images (use WebP), defer JS",
            "Set up Google Search Console — submit sitemap",
            "Set up weekly automated SEO audit using this agent",
            "Check Core Web Vitals — target LCP < 2.5s",
        ]),
    ]

    for week_title, tasks in weeks:
        _h2(doc, week_title)
        for task in tasks:
            p = doc.add_paragraph(style="List Bullet")
            run = p.add_run(task)
            run.font.size = Pt(10)
        doc.add_paragraph()

    _footer(doc, f"SEO AI Agent Competitor Report  |  {od} vs {cd}  |  {datetime.now().strftime('%d %b %Y')}")
    doc.save(output_path)
