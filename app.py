import json
from datetime import datetime
from html import escape
from io import BytesIO
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {"pdf"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

UPLOAD_FOLDER.mkdir(exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def build_export_payload(job_role, result, comparison=None):
    reports = [report for report in [result, comparison] if report]
    return {"job_role": job_role, "reports": reports}


def as_list(value):
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]

    if isinstance(value, str) and value.strip():
        return [value]

    return []


def get_sub_score(report, key):
    for item in report.get("sub_scores", []):
        if item.get("key") == key:
            return item.get("score")

    return None


def format_score(score):
    return f"{score}%" if score is not None else "N/A"


def build_pdf_styles():
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("ReportTitle", parent=styles["Title"], alignment=TA_CENTER, fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=colors.HexColor("#111827"), spaceAfter=6))
    styles.add(ParagraphStyle("ReportSubtitle", parent=styles["BodyText"], alignment=TA_CENTER, fontSize=10, leading=14, textColor=colors.HexColor("#4B5563"), spaceAfter=12))
    styles.add(ParagraphStyle("MetaText", parent=styles["BodyText"], alignment=TA_CENTER, fontSize=9, leading=12, textColor=colors.HexColor("#374151"), spaceAfter=4))
    styles.add(ParagraphStyle("SectionHeading", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=colors.HexColor("#0F766E"), spaceBefore=12, spaceAfter=8))
    styles.add(ParagraphStyle("ResumeHeading", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=colors.HexColor("#111827"), spaceBefore=14, spaceAfter=8))
    styles.add(ParagraphStyle("BodyClean", parent=styles["BodyText"], alignment=TA_LEFT, fontSize=9.5, leading=14, textColor=colors.HexColor("#1F2937"), spaceAfter=5))
    styles.add(ParagraphStyle("Muted", parent=styles["BodyText"], fontSize=9, leading=13, textColor=colors.HexColor("#6B7280"), spaceAfter=5))
    styles.add(ParagraphStyle("ScoreLarge", parent=styles["BodyText"], alignment=TA_CENTER, fontName="Helvetica-Bold", fontSize=26, leading=30, textColor=colors.HexColor("#0F766E")))

    return styles


class NumberedCanvas:
    def __init__(self, canvas, footer_text):
        self.canvas = canvas
        self.footer_text = footer_text
        self.saved_pages = []

    def __getattr__(self, name):
        return getattr(self.canvas, name)

    def showPage(self):
        self.saved_pages.append(dict(self.canvas.__dict__))
        self.canvas._startPage()

    def save(self):
        page_count = len(self.saved_pages)

        for page_number, page_state in enumerate(self.saved_pages, start=1):
            self.canvas.__dict__.update(page_state)
            self.draw_footer(page_number, page_count)
            self.canvas.showPage()

        self.canvas.save()

    def draw_footer(self, page_number, page_count):
        from reportlab.lib import colors

        self.canvas.saveState()
        self.canvas.setStrokeColor(colors.HexColor("#D1D5DB"))
        self.canvas.setLineWidth(0.5)
        self.canvas.line(54, 34, 558, 34)
        self.canvas.setFont("Helvetica", 8)
        self.canvas.setFillColor(colors.HexColor("#6B7280"))
        self.canvas.drawString(54, 22, self.footer_text)
        self.canvas.drawRightString(558, 22, f"Page {page_number} / {page_count}")
        self.canvas.restoreState()


def divider(width=510):
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    line = Table([[""]], colWidths=[width], rowHeights=[1])
    line.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#D1D5DB"))]))
    return line


def draw_header(story, styles, job_role):
    from reportlab.platypus import Paragraph, Spacer

    generated_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    story.append(Paragraph("ResumeIQ", styles["ReportTitle"]))
    story.append(Paragraph("AI-Powered Resume Analysis Report", styles["ReportSubtitle"]))
    story.append(Paragraph(f"<b>Target Job Role:</b> {escape(str(job_role or 'Not provided'))}", styles["MetaText"]))
    story.append(Paragraph(f"<b>Generated:</b> {generated_at}", styles["MetaText"]))
    story.append(Spacer(1, 8))
    story.append(divider())
    story.append(Spacer(1, 14))


def draw_section_heading(story, styles, title):
    from reportlab.platypus import Paragraph, Spacer

    story.append(Paragraph(escape(title), styles["SectionHeading"]))
    story.append(divider())
    story.append(Spacer(1, 9))


def draw_summary_box(story, styles, text):
    from reportlab.lib import colors
    from reportlab.platypus import KeepTogether, Paragraph, Spacer, Table, TableStyle

    summary = escape(str(text or "No resume summary available."))
    box = Table([[Paragraph(summary, styles["BodyClean"])]], colWidths=[480])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#D1D5DB")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(KeepTogether([Paragraph("Executive Summary", styles["SectionHeading"]), divider(), Spacer(1, 9), box]))
    story.append(Spacer(1, 10))


def draw_bullet_section(story, styles, title, items, fallback):
    from reportlab.platypus import KeepTogether, Paragraph, Spacer

    content = [Paragraph(escape(title), styles["SectionHeading"]), divider(), Spacer(1, 9)]
    items = as_list(items)

    if not items:
        content.append(Paragraph(escape(fallback), styles["Muted"]))
    else:
        for item in items:
            content.append(Paragraph(f"&bull; {escape(str(item))}", styles["BodyClean"]))

    story.append(KeepTogether(content))
    story.append(Spacer(1, 8))


def draw_ats_card(story, styles, report):
    from reportlab.lib import colors
    from reportlab.platypus import KeepTogether, Paragraph, Spacer, Table, TableStyle

    score = format_score(report.get("ats_score"))
    data = [
        [Paragraph("Overall ATS Score", styles["BodyClean"]), Paragraph(score, styles["ScoreLarge"])],
        ["Skills Match", format_score(get_sub_score(report, "skills_match"))],
        ["Experience Match", format_score(get_sub_score(report, "experience_match"))],
        ["Resume Formatting", format_score(get_sub_score(report, "resume_formatting"))],
        ["Keyword Optimization", format_score(get_sub_score(report, "keyword_optimization"))],
    ]

    content = [Paragraph("ATS Metrics", styles["SectionHeading"]), divider(), Spacer(1, 9)]
    table = Table(data, colWidths=[310, 170])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#CCFBF1")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F766E")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 15),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#99F6E4")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    content.append(table)
    story.append(KeepTogether(content))
    story.append(Spacer(1, 12))


def draw_keywords(story, styles, report):
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    keywords = as_list(report.get("important_keywords"))
    if not keywords:
        return

    draw_section_heading(story, styles, "Skills Match")
    rows = []
    row = []

    for keyword in keywords:
        row.append(Paragraph(escape(keyword), styles["BodyClean"]))
        if len(row) == 3:
            rows.append(row)
            row = []

    if row:
        while len(row) < 3:
            row.append("")
        rows.append(row)

    table = Table(rows, colWidths=[160, 160, 160])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ECFDF5")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#A7F3D0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1FAE5")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 8))


def categorize_keywords(keywords):
    categories = {
        "Frontend": [],
        "Backend": [],
        "Tools": [],
        "Soft Skills": [],
    }
    frontend_terms = {"html", "css", "javascript", "react", "vue", "angular", "ui", "ux", "frontend", "tailwind"}
    backend_terms = {"python", "java", "node", "flask", "django", "api", "sql", "database", "backend", "server"}
    tool_terms = {"git", "docker", "aws", "azure", "gcp", "tableau", "power bi", "excel", "kubernetes", "ci/cd"}

    for keyword in keywords:
        lowered = keyword.lower()
        if any(term in lowered for term in frontend_terms):
            categories["Frontend"].append(keyword)
        elif any(term in lowered for term in backend_terms):
            categories["Backend"].append(keyword)
        elif any(term in lowered for term in tool_terms):
            categories["Tools"].append(keyword)
        else:
            categories["Soft Skills"].append(keyword)

    return categories


def draw_compact_skills(story, styles, report):
    from reportlab.lib import colors
    from reportlab.platypus import KeepTogether, Paragraph, Spacer, Table, TableStyle

    keywords = as_list(report.get("important_keywords"))
    if not keywords:
        keywords = as_list(report.get("strengths"))

    if not keywords:
        return

    categories = categorize_keywords(keywords)
    data = [["Category", "Skills / Keywords"]]

    for category, values in categories.items():
        if values:
            data.append([category, ", ".join(values[:8])])

    if len(data) == 1:
        return

    table = Table(data, colWidths=[130, 350])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(KeepTogether([Paragraph("Compact Skills View", styles["SectionHeading"]), divider(), Spacer(1, 9), table]))
    story.append(Spacer(1, 10))


def draw_priority_recommendations(story, styles, report):
    from reportlab.lib import colors
    from reportlab.platypus import KeepTogether, Paragraph, Spacer, Table, TableStyle

    suggestions = as_list(report.get("improvement_suggestions"))
    missing = as_list(report.get("missing_skills"))
    priorities = suggestions[:2] or missing[:2]

    if not priorities:
        priorities = ["No urgent priority improvements were identified."]

    body = [Paragraph(f"&bull; {escape(item)}", styles["BodyClean"]) for item in priorities]
    box = Table([[body]], colWidths=[480])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFBEB")),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#FCD34D")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(KeepTogether([Paragraph("Top Priority Improvements", styles["SectionHeading"]), divider(), Spacer(1, 9), box]))
    story.append(Spacer(1, 10))


def draw_comparison_table(story, styles, reports):
    from reportlab.lib import colors
    from reportlab.platypus import KeepTogether, Paragraph, Spacer, Table, TableStyle

    if len(reports) < 2:
        return

    resume_a, resume_b = reports[0], reports[1]
    data = [
        ["Metric", resume_a.get("label", "Resume A"), resume_b.get("label", "Resume B")],
        ["ATS Score", format_score(resume_a.get("ats_score")), format_score(resume_b.get("ats_score"))],
        ["Skills Match", format_score(get_sub_score(resume_a, "skills_match")), format_score(get_sub_score(resume_b, "skills_match"))],
        ["Experience Match", format_score(get_sub_score(resume_a, "experience_match")), format_score(get_sub_score(resume_b, "experience_match"))],
        ["Formatting", format_score(get_sub_score(resume_a, "resume_formatting")), format_score(get_sub_score(resume_b, "resume_formatting"))],
        ["Keyword Optimization", format_score(get_sub_score(resume_a, "keyword_optimization")), format_score(get_sub_score(resume_b, "keyword_optimization"))],
    ]

    table = Table(data, colWidths=[160, 160, 160])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9CA3AF")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(KeepTogether([Paragraph("Resume Comparison", styles["SectionHeading"]), divider(), Spacer(1, 9), table]))
    story.append(Spacer(1, 14))


def draw_single_report(story, styles, report, add_page_break=False):
    from reportlab.platypus import PageBreak, Paragraph, Spacer

    if add_page_break:
        story.append(PageBreak())

    story.append(Paragraph(escape(str(report.get("label", "Resume"))), styles["ResumeHeading"]))
    story.append(Spacer(1, 4))
    draw_summary_box(story, styles, report.get("resume_summary"))
    draw_ats_card(story, styles, report)
    draw_priority_recommendations(story, styles, report)
    draw_keywords(story, styles, report)
    draw_compact_skills(story, styles, report)
    draw_bullet_section(story, styles, "Strengths", report.get("strengths"), "No strengths available.")
    draw_bullet_section(story, styles, "Missing Skills", report.get("missing_skills"), "No missing skills available.")
    draw_bullet_section(story, styles, "Improvement Suggestions", report.get("improvement_suggestions"), "No improvement suggestions available.")
    draw_bullet_section(story, styles, "Recommended Projects", report.get("recommended_projects"), "No recommended projects available.")


def create_report_pdf(payload):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.platypus import SimpleDocTemplate

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        title="ResumeIQ Report",
        leftMargin=54,
        rightMargin=54,
        topMargin=48,
        bottomMargin=48,
    )
    styles = build_pdf_styles()
    story = []
    job_role = payload.get("job_role", "Target Role")
    reports = [report for report in payload.get("reports", []) if isinstance(report, dict)]

    draw_header(story, styles, job_role)
    draw_comparison_table(story, styles, reports)

    if not reports:
        draw_text_section(story, styles, "Executive Summary", None, "No analysis data available.")
    else:
        for index, report in enumerate(reports):
            draw_single_report(story, styles, report, add_page_break=index > 0)

    def make_canvas(*args, **kwargs):
        return NumberedCanvas(canvas.Canvas(*args, **kwargs), "ResumeIQ | AI Resume Analysis | Generated Automatically")

    doc.build(story, canvasmaker=make_canvas)
    buffer.seek(0)
    return buffer


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    result = None
    comparison = None

    resume = request.files.get("resume")
    compare_resume = request.files.get("compare_resume")
    job_role = request.form.get("job_role", "").strip()

    if not resume or resume.filename == "":
        return jsonify({"success": False, "error": "Please upload a PDF resume."}), 400

    if not allowed_file(resume.filename):
        return jsonify({"success": False, "error": "Only PDF files are supported."}), 400

    if compare_resume and compare_resume.filename and not allowed_file(compare_resume.filename):
        return jsonify({"success": False, "error": "The comparison resume must also be a PDF file."}), 400

    if not job_role:
        return jsonify({"success": False, "error": "Please enter a target job role."}), 400

    filename = secure_filename(resume.filename)
    file_path = app.config["UPLOAD_FOLDER"] / filename
    resume.save(file_path)

    try:
        from utils.analyzer import analyze_resume

        result = analyze_resume(file_path, job_role)
        result["label"] = "Resume A"

        if compare_resume and compare_resume.filename:
            compare_filename = secure_filename(compare_resume.filename)
            compare_path = app.config["UPLOAD_FOLDER"] / compare_filename
            compare_resume.save(compare_path)

            comparison = analyze_resume(compare_path, job_role)
            comparison["label"] = "Resume B"
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception as exc:
        message = str(exc)
        if "Gemini servers are currently busy" in message:
            error = message
        else:
            error = f"Resume analysis failed: {message}"

        return jsonify({"success": False, "error": error}), 500

    export_payload = build_export_payload(job_role, result, comparison)

    return jsonify(
        {
            "success": True,
            "job_role": job_role,
            "result": result,
            "comparison": comparison,
            "export_payload": export_payload,
        }
    )


@app.route("/export-pdf", methods=["POST"])
def export_pdf():
    try:
        payload = request.get_json(silent=True) or json.loads(request.form.get("report_data", "{}"))
        pdf_file = create_report_pdf(payload)
    except Exception:
        return jsonify({"success": False, "error": "Could not export the report PDF. Please analyze the resume again."}), 400

    return send_file(
        pdf_file,
        as_attachment=True,
        download_name="resumeiq-report.pdf",
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    app.run(debug=True)
