"""
GSC Word report generator — produces 3 .docx files + 1 ZIP.

Documents:
  1. GSC_Full_Audit.docx         — complete data + AI insights
  2. GSC_Traffic_Loss.docx       — declining pages deep-dive
  3. GSC_Keyword_Opportunities.docx — page-2 + CTR opportunities
"""
import os, io, zipfile
from datetime import datetime

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ── Colour palette ────────────────────────────────────────────────────────────
C_BLUE   = RGBColor(0x00, 0x66, 0xAA)
C_CYAN   = RGBColor(0x00, 0xC2, 0xE0)
C_GREEN  = RGBColor(0x16, 0xA3, 0x4A)
C_RED    = RGBColor(0xDC, 0x26, 0x26)
C_ORANGE = RGBColor(0xEA, 0x58, 0x0C)
C_GREY   = RGBColor(0xF8, 0xFA, 0xFC)
C_DARK   = RGBColor(0x1E, 0x29, 0x3B)
C_MID    = RGBColor(0x47, 0x55, 0x69)


# ── Low-level helpers ─────────────────────────────────────────────────────────

def _set_cell_bg(cell, hex_color: str):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _heading(doc: Document, text: str, level: int = 1):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(14 if level == 1 else 12)
    run.font.color.rgb = C_BLUE if level == 1 else C_DARK
    if level == 1:
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
    return p


def _subtext(doc: Document, text: str, color=None):
    p = doc.add_paragraph(text)
    p.runs[0].font.size = Pt(10)
    if color:
        p.runs[0].font.color.rgb = color
    p.paragraph_format.space_after = Pt(4)
    return p


def _kv_table(doc: Document, rows: list[tuple]):
    """Simple 2-column key-value table."""
    table = doc.add_table(rows=len(rows), cols=2)
    table.style = "Table Grid"
    for i, (k, v) in enumerate(rows):
        row = table.rows[i]
        row.cells[0].text = k
        row.cells[0].paragraphs[0].runs[0].bold = True
        row.cells[0].paragraphs[0].runs[0].font.size = Pt(9)
        row.cells[1].text = str(v)
        row.cells[1].paragraphs[0].runs[0].font.size = Pt(9)
        _set_cell_bg(row.cells[0], "EBF4FF")
    return table


def _data_table(doc: Document, headers: list[str], data: list[list], col_widths=None):
    """Multi-column data table with a blue header row."""
    if not data:
        doc.add_paragraph("No data available.").runs[0].font.color.rgb = C_MID
        return

    table = doc.add_table(rows=1 + len(data), cols=len(headers))
    table.style = "Table Grid"

    # Header row
    hrow = table.rows[0]
    for j, h in enumerate(headers):
        cell = hrow.cells[j]
        cell.text = h
        run = cell.paragraphs[0].runs[0]
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        run.font.size = Pt(9)
        _set_cell_bg(cell, "0066AA")

    # Data rows
    for i, row_data in enumerate(data):
        row = table.rows[i + 1]
        bg = "F8FAFC" if i % 2 == 0 else "FFFFFF"
        for j, val in enumerate(row_data):
            cell = row.cells[j]
            cell.text = str(val)
            cell.paragraphs[0].runs[0].font.size = Pt(9)
            _set_cell_bg(cell, bg)

    # Column widths
    if col_widths:
        for j, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[j].width = Cm(w)

    return table


def _divider(doc: Document):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)


def _cover_page(doc: Document, title: str, subtitle: str, property_url: str):
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("SEO AI AGENT")
    run.bold = True
    run.font.size = Pt(10)
    run.font.color.rgb = C_CYAN

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run2 = p2.add_run(title)
    run2.bold = True
    run2.font.size = Pt(22)
    run2.font.color.rgb = C_BLUE

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p3.add_run(subtitle).font.color.rgb = C_MID

    doc.add_paragraph()
    _kv_table(doc, [
        ("Property", property_url),
        ("Report Date", datetime.utcnow().strftime("%B %d, %Y")),
        ("Data Period", "Last 28 days (Google Search Console)"),
    ])
    doc.add_page_break()


# ── Document 1: Full Audit ────────────────────────────────────────────────────

def create_full_audit_doc(report_data: dict, output_path: str):
    doc = Document()
    # Narrow margins
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    prop = report_data.get("property_url", "")
    _cover_page(doc, "Search Console Full Audit", "Performance, Rankings & Opportunities", prop)

    overview = report_data.get("overview", {})
    ai = report_data.get("ai_insights", {})
    summary = report_data.get("summary", {})

    # ── Section 1: Performance Overview ──────────────────────────────────────
    _heading(doc, "1. Performance Overview")
    _kv_table(doc, [
        ("Date Range",        overview.get("date_range", "")),
        ("Total Clicks",      f"{overview.get('clicks', 0):,}"),
        ("Total Impressions", f"{overview.get('impressions', 0):,}"),
        ("Average CTR",       f"{overview.get('ctr', 0)}%"),
        ("Average Position",  str(overview.get("position", 0))),
    ])
    _divider(doc)

    # Device breakdown
    devices = report_data.get("device_breakdown", [])
    if devices:
        _heading(doc, "Device Breakdown", 2)
        _data_table(doc,
            ["Device", "Clicks", "Impressions", "CTR %", "Avg Position"],
            [[d["device"].title(), f"{d['clicks']:,}", f"{d['impressions']:,}", f"{d['ctr']}%", d["position"]] for d in devices],
        )
    _divider(doc)

    # ── Section 2: AI Insights ────────────────────────────────────────────────
    if ai and "error" not in ai:
        _heading(doc, "2. AI-Powered Analysis")
        if ai.get("health_assessment"):
            _subtext(doc, ai["health_assessment"])
        if ai.get("top_priority_actions"):
            _heading(doc, "Priority Actions", 2)
            for i, action in enumerate(ai["top_priority_actions"][:5], 1):
                p = doc.add_paragraph(style="List Number")
                p.add_run(f"[{action.get('impact','').upper()}] ").bold = True
                p.add_run(action.get("action", ""))
                if action.get("why"):
                    doc.add_paragraph(f"   → {action['why']}").runs[0].font.color.rgb = C_MID
        if ai.get("traffic_recovery"):
            _heading(doc, "Traffic Recovery Plan", 2)
            _subtext(doc, ai["traffic_recovery"])
        _divider(doc)

    # ── Section 3: Top Queries ────────────────────────────────────────────────
    _heading(doc, "3. Top Search Queries (by Clicks)")
    queries = report_data.get("top_queries", [])[:30]
    _data_table(doc,
        ["Query", "Clicks", "Impressions", "CTR %", "Avg Position"],
        [[q["query"][:60], f"{q['clicks']:,}", f"{q['impressions']:,}", f"{q['ctr']}%", q["position"]] for q in queries],
        col_widths=[7, 2, 2.5, 2, 2.5],
    )
    _divider(doc)

    # ── Section 4: Top Pages ──────────────────────────────────────────────────
    _heading(doc, "4. Top Pages (by Clicks)")
    pages = report_data.get("top_pages", [])[:30]
    _data_table(doc,
        ["Page URL", "Clicks", "Impressions", "CTR %", "Avg Position"],
        [[p["page"][:70], f"{p['clicks']:,}", f"{p['impressions']:,}", f"{p['ctr']}%", p["position"]] for p in pages],
        col_widths=[8.5, 2, 2.5, 2, 2],
    )
    _divider(doc)

    # ── Section 5: Declining Pages ────────────────────────────────────────────
    declining = report_data.get("declining_pages", [])
    _heading(doc, "5. Declining Pages")
    if declining:
        _data_table(doc,
            ["Page", "Current Clicks", "Prev Clicks", "Change", "% Change", "Severity"],
            [
                [d["page"][:65], d["current_clicks"], d["previous_clicks"],
                 d["click_change"], f"{d['pct_change']}%", d["severity"].upper()]
                for d in declining[:20]
            ],
            col_widths=[8, 2, 2, 2, 2, 2],
        )
    else:
        _subtext(doc, "No significant traffic declines detected in this period.", C_GREEN)
    _divider(doc)

    # ── Section 6: Opportunities ──────────────────────────────────────────────
    opps = report_data.get("opportunities", [])
    ctr_opps = report_data.get("ctr_opportunities", [])

    _heading(doc, "6. Keyword Opportunities (Page 2 Rankings)")
    if opps:
        _data_table(doc,
            ["Query", "Position", "Impressions", "Potential Clicks", "Priority"],
            [[o["query"][:55], o["current_position"], f"{o['impressions']:,}", f"+{o['potential_clicks']}", o["priority"].upper()] for o in opps[:20]],
            col_widths=[7, 2, 2.5, 2.5, 2],
        )
    else:
        _subtext(doc, "No page-2 opportunities detected.", C_MID)
    _divider(doc)

    _heading(doc, "7. CTR Improvement Opportunities")
    if ctr_opps:
        _data_table(doc,
            ["Page", "Impressions", "Actual CTR%", "Expected CTR%", "Extra Clicks"],
            [[o["page"][:65], f"{o['impressions']:,}", f"{o['actual_ctr']}%", f"{o['expected_ctr']}%", f"+{o['potential_extra_clicks']}"] for o in ctr_opps[:15]],
            col_widths=[8, 2, 2, 2.5, 2],
        )
    else:
        _subtext(doc, "No significant CTR gaps detected.", C_MID)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    return output_path


# ── Document 2: Traffic Loss Report ──────────────────────────────────────────

def create_traffic_loss_doc(report_data: dict, output_path: str):
    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2); section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5); section.right_margin = Cm(2.5)

    prop = report_data.get("property_url", "")
    _cover_page(doc, "Traffic Loss Report", "Pages Losing Rankings & Clicks", prop)

    period = report_data.get("period_comparison", {})
    declining = report_data.get("declining_pages", [])

    _heading(doc, "Comparison Window")
    _kv_table(doc, [
        ("Current Period",  period.get("current_period", "")),
        ("Previous Period", period.get("previous_period", "")),
        ("Pages Analysed",  str(len(period.get("current", {})))),
        ("Declining Pages", str(len(declining))),
    ])
    _divider(doc)

    if not declining:
        _subtext(doc, "No significant traffic declines detected. Your site is holding its rankings.", C_GREEN)
    else:
        _heading(doc, "Declining Pages — Detail")
        for d in declining:
            _heading(doc, d["page"][:80], 2)
            _kv_table(doc, [
                ("Current Clicks",    str(d["current_clicks"])),
                ("Previous Clicks",   str(d["previous_clicks"])),
                ("Click Change",      f"{d['click_change']} ({d['pct_change']}%)"),
                ("Current Position",  str(d["current_position"])),
                ("Previous Position", str(d["previous_position"])),
                ("Position Change",   f"{d['position_change']:+}"),
                ("Likely Cause",      d.get("likely_cause", "")),
                ("Severity",          d["severity"].upper()),
            ])
            _divider(doc)

    ai = report_data.get("ai_insights", {})
    if ai and ai.get("traffic_recovery"):
        _heading(doc, "AI Recovery Plan")
        _subtext(doc, ai["traffic_recovery"])
        if ai.get("quick_wins"):
            _heading(doc, "Quick Wins", 2)
            for w in ai["quick_wins"]:
                doc.add_paragraph(w, style="List Bullet")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    return output_path


# ── Document 3: Keyword Opportunities ────────────────────────────────────────

def create_opportunities_doc(report_data: dict, output_path: str):
    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2); section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5); section.right_margin = Cm(2.5)

    prop = report_data.get("property_url", "")
    _cover_page(doc, "Keyword Opportunity Report", "Page-2 Rankings & CTR Improvements", prop)

    opps    = report_data.get("opportunities", [])
    ctr_opps = report_data.get("ctr_opportunities", [])
    ai      = report_data.get("ai_insights", {})

    # Summary
    total_potential = sum(o.get("potential_clicks", 0) for o in opps)
    total_ctr_clicks = sum(o.get("potential_extra_clicks", 0) for o in ctr_opps)
    _heading(doc, "Opportunity Summary")
    _kv_table(doc, [
        ("Page-2 Keyword Opportunities", str(len(opps))),
        ("Potential Clicks (Page-2)",    f"+{total_potential:,} /month"),
        ("CTR Improvement Opportunities",str(len(ctr_opps))),
        ("Potential Clicks (CTR Fix)",   f"+{total_ctr_clicks:,} /month"),
    ])
    _divider(doc)

    # Page-2 opportunities
    _heading(doc, "Page 2 Keywords — Push to Page 1")
    if opps:
        _subtext(doc, "These queries rank positions 11–30. With focused content optimization, they can reach page 1.")
        _data_table(doc,
            ["Query", "Position", "Impressions/mo", "Potential Clicks", "Priority", "Gap to Page 1"],
            [[o["query"][:55], o["current_position"], f"{o['impressions']:,}", f"+{o['potential_clicks']}", o["priority"].upper(), f"{o['gap_to_page1']} pos"] for o in opps],
            col_widths=[7, 2, 2.5, 2.5, 2, 2],
        )
        _divider(doc)
        if ai and ai.get("content_plan"):
            _heading(doc, "AI Content Plan", 2)
            _subtext(doc, ai["content_plan"])
    else:
        _subtext(doc, "No page-2 opportunities detected for the current data window.", C_MID)
    _divider(doc)

    # CTR opportunities
    _heading(doc, "CTR Improvement Opportunities")
    if ctr_opps:
        _subtext(doc, "These pages get impressions but their click-through rate is below average. Fix the title/meta description.")
        _data_table(doc,
            ["Page", "Impressions/mo", "Actual CTR%", "Expected CTR%", "Extra Clicks", "Fix"],
            [[o["page"][:55], f"{o['impressions']:,}", f"{o['actual_ctr']}%", f"{o['expected_ctr']}%", f"+{o['potential_extra_clicks']}", o.get("fix","Rewrite title/meta")[:40]] for o in ctr_opps],
            col_widths=[6.5, 2.5, 2, 2.5, 2, 5],
        )
    else:
        _subtext(doc, "No significant CTR gaps found.", C_MID)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    return output_path


# ── ZIP all 3 docs ────────────────────────────────────────────────────────────

def generate_all_gsc_docs(report_data: dict, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    p1 = os.path.join(output_dir, "1_GSC_Full_Audit.docx")
    p2 = os.path.join(output_dir, "2_GSC_Traffic_Loss.docx")
    p3 = os.path.join(output_dir, "3_GSC_Keyword_Opportunities.docx")

    create_full_audit_doc(report_data, p1)
    create_traffic_loss_doc(report_data, p2)
    create_opportunities_doc(report_data, p3)

    zip_path = os.path.join(output_dir, "GSC_Reports.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in [p1, p2, p3]:
            zf.write(p, os.path.basename(p))

    return zip_path
