"""
GSC PDF report generator — single professional PDF using reportlab.
"""
import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle,
    Spacer, HRFlowable, PageBreak, KeepTogether,
)

# ── Colour palette ────────────────────────────────────────────────────────────
BLUE      = HexColor("#0066AA")
CYAN      = HexColor("#00C2E0")
GREEN     = HexColor("#16A34A")
RED       = HexColor("#DC2626")
ORANGE    = HexColor("#EA580C")
DARK      = HexColor("#1E293B")
MID       = HexColor("#475569")
LIGHT     = HexColor("#F1F5F9")
WHITE     = colors.white
HEADER_BG = BLUE


# ── Style helpers ─────────────────────────────────────────────────────────────

def _styles():
    base = getSampleStyleSheet()
    custom = {
        "cover_title": ParagraphStyle("cover_title", fontSize=26, textColor=BLUE,
                                       spaceAfter=8, alignment=TA_CENTER, fontName="Helvetica-Bold"),
        "cover_sub":   ParagraphStyle("cover_sub", fontSize=13, textColor=MID,
                                       spaceAfter=4, alignment=TA_CENTER),
        "h1":          ParagraphStyle("h1", fontSize=14, textColor=BLUE, fontName="Helvetica-Bold",
                                       spaceBefore=14, spaceAfter=6),
        "h2":          ParagraphStyle("h2", fontSize=11, textColor=DARK, fontName="Helvetica-Bold",
                                       spaceBefore=8, spaceAfter=4),
        "body":        ParagraphStyle("body", fontSize=9, textColor=DARK, spaceAfter=4, leading=13),
        "small":       ParagraphStyle("small", fontSize=8, textColor=MID, spaceAfter=2),
        "label":       ParagraphStyle("label", fontSize=9, textColor=MID, fontName="Helvetica-Bold"),
        "bullet":      ParagraphStyle("bullet", fontSize=9, textColor=DARK, spaceAfter=3,
                                       leftIndent=12, bulletIndent=0),
        "metric_val":  ParagraphStyle("metric_val", fontSize=20, textColor=BLUE, fontName="Helvetica-Bold",
                                       alignment=TA_CENTER),
        "metric_lbl":  ParagraphStyle("metric_lbl", fontSize=8, textColor=MID, alignment=TA_CENTER),
    }
    return custom


def _hr():
    return HRFlowable(width="100%", thickness=0.5, color=HexColor("#CBD5E1"),
                       spaceAfter=6, spaceBefore=6)


def _tbl_style(header_rows=1):
    return TableStyle([
        # Header
        ("BACKGROUND",  (0, 0), (-1, header_rows - 1), HEADER_BG),
        ("TEXTCOLOR",   (0, 0), (-1, header_rows - 1), WHITE),
        ("FONTNAME",    (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, header_rows - 1), 8),
        ("ALIGN",       (0, 0), (-1, header_rows - 1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        # Alternating rows
        ("ROWBACKGROUNDS", (0, header_rows), (-1, -1), [WHITE, LIGHT]),
        ("FONTSIZE",    (0, header_rows), (-1, -1), 8),
        ("TEXTCOLOR",   (0, header_rows), (-1, -1), DARK),
        # Grid
        ("GRID",        (0, 0), (-1, -1), 0.3, HexColor("#CBD5E1")),
        ("TOPPADDING",  (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0),(-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",(0, 0), (-1, -1), 4),
    ])


def _kv_tbl(rows: list[tuple], st: dict):
    data = [[Paragraph(str(k), st["label"]), Paragraph(str(v), st["body"])] for k, v in rows]
    tbl = Table(data, colWidths=[4.5 * cm, 12 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (0, -1), LIGHT),
        ("GRID",        (0, 0), (-1, -1), 0.3, HexColor("#CBD5E1")),
        ("TOPPADDING",  (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0),(-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return tbl


def _metric_box(label: str, value: str, st: dict):
    data = [
        [Paragraph(value, st["metric_val"])],
        [Paragraph(label, st["metric_lbl"])],
    ]
    tbl = Table(data, colWidths=[4 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (0, -1), LIGHT),
        ("BOX",         (0, 0), (-1, -1), 0.5, HexColor("#CBD5E1")),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0),(-1, -1), 6),
    ]))
    return tbl


# ── Page header/footer callbacks ──────────────────────────────────────────────

class _PageTemplate:
    def __init__(self, property_url: str):
        self.prop = property_url

    def on_page(self, canvas, doc):
        canvas.saveState()
        # Top stripe
        canvas.setFillColor(BLUE)
        canvas.rect(0, A4[1] - 14 * mm, A4[0], 14 * mm, fill=1, stroke=0)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(18 * mm, A4[1] - 9 * mm, "SEO AI AGENT  |  Search Console Audit")
        canvas.setFont("Helvetica", 7)
        canvas.drawRightString(A4[0] - 18 * mm, A4[1] - 9 * mm, self.prop[:60])
        # Footer
        canvas.setFillColor(MID)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(18 * mm, 8 * mm, f"Generated {datetime.utcnow().strftime('%Y-%m-%d')}")
        canvas.drawRightString(A4[0] - 18 * mm, 8 * mm, f"Page {doc.page}")
        canvas.restoreState()


# ── Main PDF generator ────────────────────────────────────────────────────────

def create_gsc_pdf(report_data: dict, output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    prop    = report_data.get("property_url", "")
    ov      = report_data.get("overview", {})
    ai      = report_data.get("ai_insights", {})
    queries = report_data.get("top_queries", [])
    pages   = report_data.get("top_pages", [])
    opps    = report_data.get("opportunities", [])
    ctr_opps= report_data.get("ctr_opportunities", [])
    declining = report_data.get("declining_pages", [])
    devices = report_data.get("device_breakdown", [])

    tpl = _PageTemplate(prop)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=22 * mm, bottomMargin=18 * mm,
    )

    st = _styles()
    story = []

    # ── Cover ─────────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 2 * cm),
        Paragraph("SEARCH CONSOLE AUDIT REPORT", st["cover_title"]),
        Paragraph("Performance Intelligence  •  Traffic Analysis  •  Growth Opportunities", st["cover_sub"]),
        Spacer(1, 1 * cm),
        _kv_tbl([
            ("Property",     prop),
            ("Report Date",  datetime.utcnow().strftime("%B %d, %Y")),
            ("Data Period",  ov.get("date_range", "Last 28 days")),
            ("Generated by", "SEO AI Agent + Google Search Console API"),
        ], st),
        PageBreak(),
    ]

    # ── Performance metrics boxes ─────────────────────────────────────────────
    story.append(Paragraph("1. Performance Overview", st["h1"]))
    story.append(_hr())

    metrics_row = Table(
        [[
            _metric_box("Total Clicks",      f"{ov.get('clicks',0):,}",      st),
            _metric_box("Total Impressions",  f"{ov.get('impressions',0):,}", st),
            _metric_box("Avg CTR",            f"{ov.get('ctr',0)}%",          st),
            _metric_box("Avg Position",       str(ov.get("position", 0)),     st),
        ]],
        colWidths=[4 * cm] * 4,
        hAlign="LEFT",
    )
    metrics_row.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    story += [metrics_row, Spacer(1, 0.4 * cm)]

    # Device breakdown
    if devices:
        story.append(Paragraph("Device Breakdown", st["h2"]))
        dev_data = [["Device", "Clicks", "Impressions", "CTR %", "Avg Position"]]
        for d in devices:
            dev_data.append([d["device"].title(), f"{d['clicks']:,}", f"{d['impressions']:,}", f"{d['ctr']}%", d["position"]])
        dev_tbl = Table(dev_data, colWidths=[4*cm, 3*cm, 4*cm, 3*cm, 3*cm])
        dev_tbl.setStyle(_tbl_style())
        story += [dev_tbl, Spacer(1, 0.3 * cm)]

    # ── AI Analysis ───────────────────────────────────────────────────────────
    if ai and "error" not in ai:
        story += [_hr(), Paragraph("2. AI-Powered Analysis", st["h1"]), _hr()]
        if ai.get("health_assessment"):
            story.append(Paragraph(ai["health_assessment"], st["body"]))
        if ai.get("top_priority_actions"):
            story.append(Paragraph("Priority Actions", st["h2"]))
            for item in ai["top_priority_actions"][:5]:
                impact = item.get("impact", "").upper()
                color = "red" if impact == "HIGH" else "orange" if impact == "MEDIUM" else "green"
                story.append(Paragraph(
                    f'<font color="{color}"><b>[{impact}]</b></font> {item.get("action","")}',
                    st["bullet"]
                ))
                if item.get("why"):
                    story.append(Paragraph(f"   {item['why']}", st["small"]))
        if ai.get("quick_wins"):
            story.append(Paragraph("Quick Wins", st["h2"]))
            for w in ai["quick_wins"]:
                story.append(Paragraph(f"✓  {w}", st["bullet"]))

    # ── Top Queries ───────────────────────────────────────────────────────────
    story += [_hr(), Paragraph("3. Top Search Queries", st["h1"]), _hr()]
    q_data = [["Query", "Clicks", "Impressions", "CTR %", "Avg Pos"]]
    for q in queries[:30]:
        q_data.append([q["query"][:55], f"{q['clicks']:,}", f"{q['impressions']:,}", f"{q['ctr']}%", q["position"]])
    q_tbl = Table(q_data, colWidths=[9*cm, 2.5*cm, 3*cm, 2*cm, 2*cm])
    q_tbl.setStyle(_tbl_style())
    story += [q_tbl, Spacer(1, 0.3 * cm)]

    # ── Top Pages ─────────────────────────────────────────────────────────────
    story += [_hr(), Paragraph("4. Top Pages", st["h1"]), _hr()]
    pg_data = [["Page URL", "Clicks", "Impressions", "CTR %", "Avg Pos"]]
    for p in pages[:25]:
        pg_data.append([p["page"][:65], f"{p['clicks']:,}", f"{p['impressions']:,}", f"{p['ctr']}%", p["position"]])
    pg_tbl = Table(pg_data, colWidths=[10*cm, 2*cm, 2.5*cm, 2*cm, 2*cm])
    pg_tbl.setStyle(_tbl_style())
    story += [pg_tbl, Spacer(1, 0.3 * cm)]

    # ── Declining Pages ───────────────────────────────────────────────────────
    story += [_hr(), Paragraph("5. Declining Pages", st["h1"]), _hr()]
    if declining:
        dec_data = [["Page", "Curr Clicks", "Prev Clicks", "Change", "% Chg", "Severity"]]
        for d in declining[:20]:
            dec_data.append([
                d["page"][:60], d["current_clicks"], d["previous_clicks"],
                d["click_change"], f"{d['pct_change']}%", d["severity"].upper()
            ])
        dec_tbl = Table(dec_data, colWidths=[9*cm, 2*cm, 2*cm, 2*cm, 1.5*cm, 2*cm])
        dec_tbl.setStyle(TableStyle([
            *_tbl_style().getCommands(),
            ("TEXTCOLOR", (5, 1), (5, -1), RED),
        ]))
        story.append(dec_tbl)
    else:
        story.append(Paragraph("No significant traffic declines detected.", ParagraphStyle("ok", textColor=GREEN, fontSize=9)))

    # ── Opportunities ─────────────────────────────────────────────────────────
    story += [_hr(), Paragraph("6. Keyword Opportunities (Page 2)", st["h1"]), _hr()]
    if opps:
        opp_data = [["Query", "Position", "Impressions", "+Potential Clicks", "Priority"]]
        for o in opps[:20]:
            opp_data.append([o["query"][:55], o["current_position"], f"{o['impressions']:,}", f"+{o['potential_clicks']}", o["priority"].upper()])
        opp_tbl = Table(opp_data, colWidths=[8.5*cm, 2*cm, 2.5*cm, 3*cm, 2.5*cm])
        opp_tbl.setStyle(_tbl_style())
        story.append(opp_tbl)
    else:
        story.append(Paragraph("No page-2 opportunities detected.", st["small"]))

    story += [Spacer(1, 0.3*cm), _hr(), Paragraph("7. CTR Improvement Opportunities", st["h1"]), _hr()]
    if ctr_opps:
        ctr_data = [["Page", "Impressions", "Actual CTR%", "Expected CTR%", "+Clicks"]]
        for o in ctr_opps[:15]:
            ctr_data.append([o["page"][:60], f"{o['impressions']:,}", f"{o['actual_ctr']}%", f"{o['expected_ctr']}%", f"+{o['potential_extra_clicks']}"])
        ctr_tbl = Table(ctr_data, colWidths=[9*cm, 2.5*cm, 2.5*cm, 3*cm, 1.5*cm])
        ctr_tbl.setStyle(_tbl_style())
        story.append(ctr_tbl)
    else:
        story.append(Paragraph("No significant CTR gaps detected.", st["small"]))

    # Build
    doc.build(story, onFirstPage=tpl.on_page, onLaterPages=tpl.on_page)
    return output_path
