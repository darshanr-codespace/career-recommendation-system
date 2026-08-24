"""
modules/report.py
Generates a PDF career recommendation report using ReportLab.
Returns raw bytes suitable for Flask send_file().
"""
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from database.models import get_db
from modules.recommender import run_recommendation
from modules.skill_gap import compute_skill_gaps


# ── colour palette ────────────────────────────────────────────────────────────
PRIMARY   = colors.HexColor("#2563EB")   # blue
SECONDARY = colors.HexColor("#1E40AF")   # dark blue
ACCENT    = colors.HexColor("#10B981")   # green
WARN      = colors.HexColor("#F59E0B")   # amber
DANGER    = colors.HexColor("#EF4444")   # red
LIGHT_BG  = colors.HexColor("#EFF6FF")   # very light blue
DARK_TEXT = colors.HexColor("#1F2937")   # near-black
MID_TEXT  = colors.HexColor("#6B7280")   # grey


def _styles():
    base = getSampleStyleSheet()
    custom = {
        "Title": ParagraphStyle("Title", parent=base["Normal"],
            fontSize=22, textColor=PRIMARY, leading=28,
            alignment=TA_CENTER, spaceAfter=6, fontName="Helvetica-Bold"),
        "Subtitle": ParagraphStyle("Subtitle", parent=base["Normal"],
            fontSize=12, textColor=MID_TEXT, leading=16,
            alignment=TA_CENTER, spaceAfter=4),
        "SectionHead": ParagraphStyle("SectionHead", parent=base["Normal"],
            fontSize=13, textColor=SECONDARY, leading=18,
            spaceBefore=14, spaceAfter=4, fontName="Helvetica-Bold"),
        "CareerTitle": ParagraphStyle("CareerTitle", parent=base["Normal"],
            fontSize=11, textColor=PRIMARY, leading=15,
            spaceBefore=8, fontName="Helvetica-Bold"),
        "Body": ParagraphStyle("Body", parent=base["Normal"],
            fontSize=9.5, textColor=DARK_TEXT, leading=14, spaceAfter=3),
        "Small": ParagraphStyle("Small", parent=base["Normal"],
            fontSize=8, textColor=MID_TEXT, leading=11),
        "Footer": ParagraphStyle("Footer", parent=base["Normal"],
            fontSize=7.5, textColor=MID_TEXT, alignment=TA_CENTER),
    }
    return custom


def generate_report(uid: int) -> bytes:
    buf  = io.BytesIO()
    doc  = SimpleDocTemplate(buf, pagesize=A4,
                              leftMargin=2*cm, rightMargin=2*cm,
                              topMargin=2*cm, bottomMargin=2*cm)
    st   = _styles()
    conn = get_db()

    # ── user info ─────────────────────────────────────────────────────────────
    user = dict(conn.execute(
        "SELECT * FROM user WHERE user_id=?", (uid,)
    ).fetchone() or {})
    name = user.get("name", "Student")
    edu  = user.get("education_level", "—")

    # ── run recommendation engine ─────────────────────────────────────────────
    recs = run_recommendation(uid)[:5]   # top 5 for the report

    # ── fetch user skills for gap analysis ────────────────────────────────────
    skill_rows = conn.execute(
        "SELECT skill_name, proficiency FROM user_skill WHERE user_id=?", (uid,)
    ).fetchall()
    user_skills = {r["skill_name"]: r["proficiency"] for r in skill_rows}

    story = []

    # ═══════════════════════════════════════════════════════════════════════════
    # COVER
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("AI-Based Career Recommendation", st["Title"]))
    story.append(Paragraph("Personalised Career Assessment Report", st["Subtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=8))

    meta_data = [
        ["Student Name",    name],
        ["Education Level", edu],
        ["Assessment Date", datetime.now().strftime("%d %B %Y")],
        ["Assessment ID",   f"CAR-{uid:05d}-{datetime.now().strftime('%Y%m%d')}"],
    ]
    meta_tbl = Table(meta_data, colWidths=[5*cm, 11*cm])
    meta_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (0,-1), LIGHT_BG),
        ("FONTNAME",    (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9.5),
        ("TEXTCOLOR",   (0,0), (0,-1), SECONDARY),
        ("TEXTCOLOR",   (1,0), (1,-1), DARK_TEXT),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, LIGHT_BG]),
        ("BOX",         (0,0), (-1,-1), 0.5, colors.HexColor("#BFDBFE")),
        ("INNERGRID",   (0,0), (-1,-1), 0.25, colors.HexColor("#BFDBFE")),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING",  (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
    ]))
    story.append(meta_tbl)
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — TOP CAREER RECOMMENDATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("1. Top Career Recommendations", st["SectionHead"]))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=6))

    for rec in recs:
        score_pct = rec["compatibility_score"]
        bar_width  = max(1, int(score_pct * 1.5))   # scale for text bar

        story.append(Paragraph(
            f"#{rec['rank']}  {rec['career_name']}  —  {rec['domain']}",
            st["CareerTitle"]
        ))

        score_color = ACCENT if score_pct >= 70 else (WARN if score_pct >= 50 else DANGER)
        score_tbl = Table([[
            Paragraph(rec.get("description",""), st["Body"]),
            Paragraph(
                f'<font color="{score_color.hexval()}"><b>{score_pct:.1f}%</b></font><br/>'
                f'<font size="7">Compatibility</font>',
                ParagraphStyle("sc", alignment=TA_CENTER, fontSize=9)
            )
        ]], colWidths=[12*cm, 3*cm])
        score_tbl.setStyle(TableStyle([
            ("VALIGN",    (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING",(0,0),(-1,-1), 0),
            ("RIGHTPADDING",(0,0),(-1,-1), 0),
        ]))
        story.append(score_tbl)

        detail = [
            ["Avg Salary", f"₹{rec['avg_salary_lpa']} LPA",
             "Growth",     rec["growth_rate"],
             "Work Env.",  rec["work_environment"]],
        ]
        dtbl = Table(detail, colWidths=[2.5*cm,2.5*cm,1.5*cm,2.5*cm,2.5*cm,3.5*cm])
        dtbl.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(0,-1), LIGHT_BG),
            ("BACKGROUND",(2,0),(2,-1), LIGHT_BG),
            ("BACKGROUND",(4,0),(4,-1), LIGHT_BG),
            ("FONTNAME",  (0,0),(0,-1), "Helvetica-Bold"),
            ("FONTNAME",  (2,0),(2,-1), "Helvetica-Bold"),
            ("FONTNAME",  (4,0),(4,-1), "Helvetica-Bold"),
            ("FONTSIZE",  (0,0),(-1,-1), 8),
            ("TEXTCOLOR", (0,0),(0,-1),  SECONDARY),
            ("TEXTCOLOR", (2,0),(2,-1),  SECONDARY),
            ("TEXTCOLOR", (4,0),(4,-1),  SECONDARY),
            ("BOX",       (0,0),(-1,-1), 0.5, colors.HexColor("#BFDBFE")),
            ("INNERGRID", (0,0),(-1,-1), 0.25, colors.HexColor("#BFDBFE")),
            ("TOPPADDING",(0,0),(-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
            ("LEFTPADDING",(0,0),(-1,-1), 6),
        ]))
        story.append(dtbl)
        story.append(Spacer(1, 0.3*cm))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — SKILL GAP SUMMARIES
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("2. Skill Gap Analysis", st["SectionHead"]))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=6))

    for rec in recs:
        cid = rec["career_id"]
        req_rows = conn.execute(
            "SELECT skill_name, importance, is_mandatory FROM career_skill WHERE career_id=?",
            (cid,)
        ).fetchall()
        career_reqs = {
            r["skill_name"]: {"importance": r["importance"], "is_mandatory": r["is_mandatory"]}
            for r in req_rows
        }
        gaps = compute_skill_gaps(user_skills, career_reqs)

        story.append(Paragraph(f"Career: {rec['career_name']}", st["CareerTitle"]))

        tbl_data = [["Skill", "Required", "Your Level", "Gap", "Status"]]
        for skill, g in gaps.items():
            status_color = (
                "#10B981" if g["status"] == "strength" else
                "#F59E0B" if g["status"] == "minor_gap" else
                "#EF4444"
            )
            status_label = g["status"].replace("_", " ").title()
            tbl_data.append([
                skill,
                str(g["required"]) + "/5",
                str(g["current"])  + "/5",
                str(g["gap"]),
                Paragraph(f'<font color="{status_color}">● {status_label}</font>',
                          ParagraphStyle("ss", fontSize=8)),
            ])

        skill_tbl = Table(tbl_data, colWidths=[5*cm, 2.2*cm, 2.5*cm, 1.8*cm, 3.5*cm])
        skill_tbl.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0),  PRIMARY),
            ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
            ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, LIGHT_BG]),
            ("BOX",         (0,0), (-1,-1), 0.5, colors.HexColor("#BFDBFE")),
            ("INNERGRID",   (0,0), (-1,-1), 0.25, colors.HexColor("#BFDBFE")),
            ("TOPPADDING",  (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("ALIGN",       (1,0), (-1,-1), "CENTER"),
        ]))
        story.append(skill_tbl)
        story.append(Spacer(1, 0.4*cm))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — LEARNING ROADMAP
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("3. Prioritised Learning Roadmap", st["SectionHead"]))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=6))
    story.append(Paragraph(
        "The resources below are mapped to skill gaps in your top recommended career.",
        st["Body"]
    ))
    story.append(Spacer(1, 0.2*cm))

    if recs:
        top_cid = recs[0]["career_id"]
        resources = conn.execute(
            "SELECT * FROM learning_resource WHERE career_id=?", (top_cid,)
        ).fetchall()

        if resources:
            res_data = [["Skill", "Resource", "Provider", "Type"]]
            for r in resources:
                res_data.append([r["skill_name"], r["title"], r["provider"], r["resource_type"]])
            res_tbl = Table(res_data, colWidths=[3.5*cm, 7*cm, 3*cm, 1.5*cm])
            res_tbl.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,0),  SECONDARY),
                ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
                ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
                ("FONTSIZE",    (0,0), (-1,-1), 8),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, LIGHT_BG]),
                ("BOX",         (0,0), (-1,-1), 0.5, colors.HexColor("#BFDBFE")),
                ("INNERGRID",   (0,0), (-1,-1), 0.25, colors.HexColor("#BFDBFE")),
                ("TOPPADDING",  (0,0), (-1,-1), 4),
                ("BOTTOMPADDING",(0,0),(-1,-1), 4),
                ("LEFTPADDING", (0,0), (-1,-1), 6),
                ("WORDWRAP",    (1,1), (1,-1), True),
            ]))
            story.append(res_tbl)
        else:
            story.append(Paragraph("No resources found for this career.", st["Body"]))

    # ── footer note ───────────────────────────────────────────────────────────
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MID_TEXT))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Generated by AI-Based Career Recommendation System  •  "
        f"Report Date: {datetime.now().strftime('%d %b %Y %H:%M')}  •  "
        "For guidance purposes only.",
        st["Footer"]
    ))

    conn.close()
    doc.build(story)
    return buf.getvalue()
