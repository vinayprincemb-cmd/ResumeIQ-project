from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


LIST_SECTIONS = [
    ("education", "Education"),
    ("experience", "Experience"),
    ("projects", "Projects"),
    ("internships", "Internships"),
    ("skills", "Skills"),
    ("technical_skills", "Technical Skills"),
    ("soft_skills", "Soft Skills"),
    ("achievements", "Achievements"),
    ("certifications", "Certifications"),
    ("languages", "Languages"),
    ("interests", "Interests"),
    ("references", "References"),
    ("social_links", "Social Links"),
]

SECTION_TITLES = dict(LIST_SECTIONS)
SECTION_TITLES["career_objective"] = "Career Objective"


def _safe_hex(value, fallback="#0F766E"):
    text = str(value or fallback).strip()
    if len(text) == 7 and text.startswith("#"):
        return text
    return fallback


def _styles(accent="#0F766E", font="Helvetica"):
    styles = getSampleStyleSheet()
    body_font = "Times-Roman" if "times" in str(font).lower() or "georgia" in str(font).lower() else "Helvetica"
    heading_font = "Times-Bold" if body_font == "Times-Roman" else "Helvetica-Bold"
    styles.add(
        ParagraphStyle(
            "ResumeName",
            parent=styles["Title"],
            fontName=heading_font,
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#111827"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            "ResumeContact",
            parent=styles["BodyText"],
            fontName=body_font,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#4B5563"),
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            "ResumeSection",
            parent=styles["Heading2"],
            fontName=heading_font,
            fontSize=11,
            leading=14,
            textColor=colors.HexColor(accent),
            spaceBefore=10,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            "ResumeBody",
            parent=styles["BodyText"],
            fontName=body_font,
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#1F2937"),
            spaceAfter=4,
        )
    )
    return styles


def _as_items(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [line.strip() for line in value.splitlines() if line.strip()]
    return []


def _add_rule(story, accent="#D1D5DB"):
    rule = Table([[""]], colWidths=[500], rowHeights=[1])
    rule.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(accent))]))
    story.append(rule)
    story.append(Spacer(1, 5))


def create_resume_pdf(resume):
    accent = _safe_hex(resume.get("accent_color") or resume.get("color_theme"))
    styles = _styles(accent, resume.get("font"))
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=42,
        bottomMargin=42,
        title="ResumeIQ+ Resume",
    )
    story = []
    personal = resume.get("personal_details") or {}
    name = personal.get("full_name") or "Your Name"
    contact_bits = [
        personal.get("email"),
        personal.get("phone"),
        personal.get("location"),
        personal.get("portfolio"),
        personal.get("linkedin"),
    ]
    contact = " | ".join(str(bit).strip() for bit in contact_bits if str(bit or "").strip())

    template = str(resume.get("template") or "Professional")
    if resume.get("show_photo"):
        initials = escape(name[:1].upper() or "R")
        photo = Table([[Paragraph(initials, styles["ResumeName"])]], colWidths=[44], rowHeights=[44])
        photo.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(accent)), ("TEXTCOLOR", (0, 0), (-1, -1), colors.white), ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story.append(photo)
        story.append(Spacer(1, 6))

    story.append(Paragraph(escape(name), styles["ResumeName"]))
    story.append(Paragraph(escape(template), styles["ResumeContact"]))
    if contact:
        story.append(Paragraph(escape(contact), styles["ResumeContact"]))

    order = resume.get("section_order") if isinstance(resume.get("section_order"), list) else ["career_objective"] + [key for key, _title in LIST_SECTIONS]
    for key in order:
        title = SECTION_TITLES.get(key)
        if not title:
            continue
        if key == "career_objective":
            value = str(resume.get("career_objective") or "").strip()
            if not value:
                continue
            story.append(Paragraph(escape(title), styles["ResumeSection"]))
            _add_rule(story, accent)
            story.append(Paragraph(escape(value), styles["ResumeBody"]))
            continue
        items = _as_items(resume.get(key))
        if not items:
            continue
        story.append(Paragraph(escape(title), styles["ResumeSection"]))
        _add_rule(story, accent)
        for item in items:
            story.append(Paragraph(f"&bull; {escape(item)}", styles["ResumeBody"]))

    doc.build(story)
    buffer.seek(0)
    return buffer
