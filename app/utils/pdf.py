from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)


BLUE = colors.HexColor("#1F4E79")


def _p(text, style):
    text = str(text).replace("&", "&amp;")
    return Paragraph(text, style)


def generate_resume_pdf(resume):
    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)

    safe_name = resume["name"].replace(" ", "_")
    role_name = resume["role_type"].replace(" ", "_")
    file_path = exports_dir / f"{safe_name}_{role_name}_Resume.pdf"

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.35 * inch,
        bottomMargin=0.35 * inch,
    )

    name_style = ParagraphStyle(
        "Name",
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=BLUE,
        alignment=TA_CENTER,
        spaceAfter=2,
    )

    contact_style = ParagraphStyle(
        "Contact",
        fontName="Helvetica",
        fontSize=7.5,
        alignment=TA_CENTER,
        spaceAfter=8,
    )

    section_style = ParagraphStyle(
        "Section",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        textColor=BLUE,
        spaceBefore=7,
        spaceAfter=3,
    )

    normal_style = ParagraphStyle(
        "Normal",
        fontName="Helvetica",
        fontSize=7.3,
        leading=9,
        alignment=TA_LEFT,
    )

    bold_style = ParagraphStyle(
        "Bold",
        fontName="Helvetica-Bold",
        fontSize=7.3,
        leading=9,
    )

    right_style = ParagraphStyle(
        "Right",
        fontName="Helvetica-Bold",
        fontSize=7.3,
        leading=9,
        alignment=TA_RIGHT,
    )

    bullet_style = ParagraphStyle(
        "Bullet",
        fontName="Helvetica",
        fontSize=7.2,
        leading=8.8,
        leftIndent=10,
        firstLineIndent=-6,
    )

    story = []

    story.append(_p(resume["name"], name_style))
    story.append(
        _p(
            "Bengaluru, India | +91-9845909502 | "
            f"{resume['email']} | vishal-banakar",
            contact_style,
        )
    )

    def section(title):
        story.append(_p(title, section_style))
        story.append(
            HRFlowable(
                width="100%",
                thickness=0.8,
                color=BLUE,
                spaceBefore=1,
                spaceAfter=5,
            )
        )

    section("CAREER OBJECTIVE")
    story.append(_p(resume["summary"], normal_style))

    section("EDUCATION")
    edu_table = Table(
        [
            [
                _p("<b>Reva University</b><br/>Computer Science Engineering", normal_style),
                _p("<b>08/2019 - 08/2023</b><br/>Bangalore, India", right_style),
            ]
        ],
        colWidths=[4.8 * inch, 2.0 * inch],
    )
    edu_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(edu_table)

    section("WORK EXPERIENCE")
    exp_table = Table(
        [
            [
                _p("<b>Evertz Microsystem</b><br/>Enterprise Service Engineer", normal_style),
                _p("<b>10/2022 - 10/2023</b><br/>Bangalore, India", right_style),
            ]
        ],
        colWidths=[4.8 * inch, 2.0 * inch],
    )
    exp_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(exp_table)

    experience_bullets = [
        "Provided technical support and troubleshooting for Media Supply Chain and Linear Playout solutions.",
        "Managed L1, L2, and L3 ticket issues using ServiceNow and Jira, ensuring timely resolution.",
        "Worked extensively with AWS services including S3 buckets, EC2 instances, Aurora, and Elasticsearch.",
        "Created and executed SQL reports based on business and customer requirements.",
        "Managed live production systems, handling processes, ORTs, service reboots, and system maintenance.",
    ]

    for bullet in experience_bullets:
        story.append(_p(f"- {bullet}", bullet_style))

    section("PROJECTS")

    project_details = [
        (
            "Manufacturing Process Analysis - Supertech Vacuum Industries | Python, Excel",
            "2026",
            [
                "Analyzed manufacturing and supply chain operations using Excel-based production data.",
                "Cleaned and transformed datasets using Python, Pandas, and NumPy.",
                "Identified bottlenecks in procurement, production scheduling, inventory, and logistics.",
                "Presented recommendations to improve production planning and reduce delivery lead times.",
            ],
        ),
        (
            "Sales & Business Performance Dashboard | Power BI",
            "2026",
            [
                "Built an interactive dashboard using Power BI with a Star Schema data model.",
                "Performed data transformation using Power Query.",
                "Developed DAX measures for Total Sales, Orders, Profit, and Average Sales.",
                "Created KPI cards, slicers, drill-through, and interactive charts.",
            ],
        ),
        (
            "Loan Risk Analysis | Python",
            "2026",
            [
                "Analyzed borrower risk using Python, Pandas, and Excel-based financial data.",
                "Created risk categories using payment and bounce pattern analysis.",
                "Generated insights to support loan risk profiling and reporting.",
            ],
        ),
    ]

    for title, year, bullets in project_details:
        table = Table(
            [[_p(f"<b>{title}</b>", normal_style), _p(f"<b>{year}</b>", right_style)]],
            colWidths=[5.8 * inch, 1.0 * inch],
        )
        table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(table)

        for bullet in bullets:
            story.append(_p(f"- {bullet}", bullet_style))

    section("TECHNICAL SKILLS")
    story.append(
        _p(
            "<b>Languages & Databases:</b> Python, SQL, MySQL, MariaDB, Aurora, Oracle",
            normal_style,
        )
    )
    story.append(
        _p(
            "<b>BI & Analytics:</b> Power BI, Tableau, Excel, DAX, Power Query, KPI Reporting, Data Visualization",
            normal_style,
        )
    )
    story.append(
        _p(
            "<b>Cloud & Tools:</b> AWS, Azure, Docker, Kubernetes, Jenkins, Ansible, CI/CD pipelines",
            normal_style,
        )
    )
    story.append(
        _p(
            "<b>Operating Systems & Tools:</b> Linux, Windows Server, ServiceNow, Jira, Confluence",
            normal_style,
        )
    )

    section("CERTIFICATIONS")
    certifications = [
        "Data Analytics Essentials - Cisco",
        "Problem Solving Intermediate - HackerRank",
        "SQL Intermediate - HackerRank",
        "Data Analytics Certification - ExcelR Academy (In Progress)",
    ]

    for cert in certifications:
        story.append(_p(f"- {cert}", bullet_style))

    doc.build(story)

    return str(file_path)