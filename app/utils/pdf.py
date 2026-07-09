from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch


def generate_resume_pdf(resume):
    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)

    safe_name = resume["name"].replace(" ", "_")
    role_name = resume["role_type"].replace(" ", "_")
    file_path = exports_dir / f"{safe_name}_{role_name}_Resume.pdf"

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=8
    )

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=10,
        spaceAfter=6
    )

    normal_style = ParagraphStyle(
        "NormalStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14
    )

    story = []

    story.append(Paragraph(resume["name"], title_style))
    story.append(Paragraph(resume["email"], normal_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("PROFESSIONAL SUMMARY", heading_style))
    story.append(Paragraph(resume["summary"], normal_style))

    story.append(Paragraph("SKILLS", heading_style))
    story.append(Paragraph(", ".join(sorted(set(resume["skills"]))), normal_style))

    story.append(Paragraph("PROJECTS", heading_style))
    for project in resume["projects"]:
        story.append(Paragraph(f"- {project}", normal_style))

    story.append(Paragraph("EXPERIENCE", heading_style))
    for exp in resume["experience"]:
        story.append(Paragraph(f"- {exp}", normal_style))

    doc.build(story)

    return str(file_path)