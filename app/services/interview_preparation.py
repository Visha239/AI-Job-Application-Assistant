from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

from app.services.resume_report import ResumeReport


@dataclass(frozen=True)
class InterviewQuestion:
    category: str
    question: str
    answer_guidance: str


SQL_QUESTIONS = [
    InterviewQuestion(
        category="SQL",
        question="Explain the logical execution order of a SQL query.",
        answer_guidance=(
            "Explain FROM and JOIN first, followed by WHERE, GROUP BY, "
            "HAVING, SELECT, DISTINCT, ORDER BY and LIMIT."
        ),
    ),
    InterviewQuestion(
        category="SQL",
        question=(
            "How would you find the second-highest salary from an "
            "employee table?"
        ),
        answer_guidance=(
            "Explain DENSE_RANK or ROW_NUMBER and mention how duplicates "
            "should be handled."
        ),
    ),
    InterviewQuestion(
        category="SQL",
        question="What is the difference between WHERE and HAVING?",
        answer_guidance=(
            "WHERE filters rows before aggregation; HAVING filters grouped "
            "results after aggregation."
        ),
    ),
    InterviewQuestion(
        category="SQL",
        question="How do you optimize a slow SQL query?",
        answer_guidance=(
            "Discuss execution plans, indexes, selective filters, avoiding "
            "unnecessary columns, join conditions and reducing scanned data."
        ),
    ),
    InterviewQuestion(
        category="SQL",
        question="Explain INNER JOIN, LEFT JOIN and FULL OUTER JOIN.",
        answer_guidance=(
            "Use a simple customer and order example and explain unmatched rows."
        ),
    ),
]

POWER_BI_QUESTIONS = [
    InterviewQuestion(
        category="Power BI",
        question="What is the difference between a measure and a calculated column?",
        answer_guidance=(
            "Calculated columns are evaluated row by row and stored; measures "
            "are calculated at query time based on filter context."
        ),
    ),
    InterviewQuestion(
        category="Power BI",
        question="Explain star schema and why it is preferred.",
        answer_guidance=(
            "Explain one central fact table, surrounding dimension tables, "
            "simpler relationships and better analytical performance."
        ),
    ),
    InterviewQuestion(
        category="Power BI",
        question="What is filter context in DAX?",
        answer_guidance=(
            "Explain how slicers, filters and visual selections affect measure "
            "evaluation."
        ),
    ),
    InterviewQuestion(
        category="Power BI",
        question="How would you improve the performance of a Power BI report?",
        answer_guidance=(
            "Discuss model size, star schema, unnecessary columns, efficient "
            "DAX, relationship design and Import versus DirectQuery."
        ),
    ),
    InterviewQuestion(
        category="Power BI",
        question="What is Power Query used for?",
        answer_guidance=(
            "Explain extracting, cleaning, transforming and combining data "
            "before loading it into the model."
        ),
    ),
]

PYTHON_QUESTIONS = [
    InterviewQuestion(
        category="Python",
        question="How do you handle missing values in pandas?",
        answer_guidance=(
            "Discuss isna, dropna, fillna and choosing a method based on the "
            "meaning and distribution of the data."
        ),
    ),
    InterviewQuestion(
        category="Python",
        question="What is the difference between merge, join and concat?",
        answer_guidance=(
            "Explain key-based combination versus index-based joins and "
            "row/column stacking."
        ),
    ),
    InterviewQuestion(
        category="Python",
        question="How would you identify duplicate records?",
        answer_guidance=(
            "Use duplicated and drop_duplicates, and explain selecting the "
            "correct subset of columns."
        ),
    ),
    InterviewQuestion(
        category="Python",
        question="How do you analyze a large dataset efficiently?",
        answer_guidance=(
            "Mention reading selected columns, chunking, vectorized operations, "
            "appropriate dtypes and avoiding Python loops."
        ),
    ),
]

BUSINESS_ANALYST_QUESTIONS = [
    InterviewQuestion(
        category="Business Analysis",
        question="How do you gather and document business requirements?",
        answer_guidance=(
            "Discuss stakeholder interviews, workshops, current-state analysis, "
            "acceptance criteria and requirement validation."
        ),
    ),
    InterviewQuestion(
        category="Business Analysis",
        question="What is gap analysis?",
        answer_guidance=(
            "Explain comparing current and desired states, identifying gaps and "
            "defining actions to close them."
        ),
    ),
    InterviewQuestion(
        category="Business Analysis",
        question="How do you handle conflicting stakeholder requirements?",
        answer_guidance=(
            "Clarify goals, quantify impact, prioritize requirements, document "
            "trade-offs and obtain agreement."
        ),
    ),
    InterviewQuestion(
        category="Business Analysis",
        question="What is the purpose of UAT?",
        answer_guidance=(
            "Explain validating that the solution meets business requirements "
            "before production release."
        ),
    ),
]

SUPPORT_QUESTIONS = [
    InterviewQuestion(
        category="Application Support",
        question="How do you handle a production incident?",
        answer_guidance=(
            "Explain impact assessment, logs and monitoring, containment, "
            "communication, escalation, root-cause analysis and documentation."
        ),
    ),
    InterviewQuestion(
        category="Application Support",
        question="Which Linux commands do you use during troubleshooting?",
        answer_guidance=(
            "Use your real experience: top, iostat, df, dmesg, log inspection "
            "and process/service checks."
        ),
    ),
    InterviewQuestion(
        category="Application Support",
        question="How do you prioritize L1, L2 and L3 tickets?",
        answer_guidance=(
            "Discuss severity, business impact, SLA, available workarounds and "
            "clear escalation."
        ),
    ),
    InterviewQuestion(
        category="Application Support",
        question="Describe a difficult production issue you resolved.",
        answer_guidance=(
            "Answer using STAR: situation, task, actions, tools used and result."
        ),
    ),
]

HR_QUESTIONS = [
    InterviewQuestion(
        category="HR",
        question="Tell me about yourself.",
        answer_guidance=(
            "Give a 60–90 second summary covering education, 1.1 years of "
            "support experience, analytics skills, projects and target role."
        ),
    ),
    InterviewQuestion(
        category="HR",
        question="Why are you moving from support to analytics?",
        answer_guidance=(
            "Connect SQL reporting, troubleshooting and business analysis from "
            "support work to your Power BI and Python projects."
        ),
    ),
    InterviewQuestion(
        category="HR",
        question="Why should we hire you?",
        answer_guidance=(
            "Emphasize your combination of production discipline, SQL, Linux, "
            "analytics projects, problem-solving and immediate availability."
        ),
    ),
    InterviewQuestion(
        category="HR",
        question="What is your greatest weakness?",
        answer_guidance=(
            "Choose a genuine but manageable weakness and explain the actions "
            "you are taking to improve it."
        ),
    ),
]


def _contains_any(text: str, terms: list[str]) -> bool:
    return any(term.lower() in text.lower() for term in terms)


def _select_questions(
    role: str,
    job_description: str,
) -> list[InterviewQuestion]:
    combined = f"{role} {job_description}".lower()

    selected: list[InterviewQuestion] = []

    if _contains_any(combined, ["sql", "database", "query", "reporting"]):
        selected.extend(SQL_QUESTIONS)

    if _contains_any(
        combined,
        ["power bi", "dax", "power query", "dashboard", "business intelligence"],
    ):
        selected.extend(POWER_BI_QUESTIONS)

    if _contains_any(
        combined,
        ["python", "pandas", "numpy", "data analysis", "automation"],
    ):
        selected.extend(PYTHON_QUESTIONS)

    if _contains_any(
        combined,
        [
            "business analyst",
            "requirements",
            "stakeholder",
            "gap analysis",
            "uat",
        ],
    ):
        selected.extend(BUSINESS_ANALYST_QUESTIONS)

    if _contains_any(
        combined,
        [
            "application support",
            "production support",
            "linux",
            "incident",
            "servicenow",
            "jira",
        ],
    ):
        selected.extend(SUPPORT_QUESTIONS)

    selected.extend(HR_QUESTIONS)

    unique: list[InterviewQuestion] = []
    seen: set[str] = set()

    for question in selected:
        if question.question not in seen:
            unique.append(question)
            seen.add(question.question)

    return unique


def _build_research_links(company: str) -> dict[str, str]:
    company_query = quote_plus(company)

    return {
        "Company website search": (
            f"https://www.google.com/search?q={company_query}+official+website"
        ),
        "Company careers": (
            f"https://www.google.com/search?q={company_query}+careers"
        ),
        "Interview experiences": (
            f"https://www.google.com/search?q={company_query}+interview+experience"
        ),
        "Salary research": (
            f"https://www.google.com/search?q={company_query}+salary+India"
        ),
        "Recent company news": (
            f"https://news.google.com/search?q={company_query}"
        ),
        "LinkedIn company search": (
            f"https://www.linkedin.com/search/results/companies/"
            f"?keywords={company_query}"
        ),
    }


def _preparation_priority(
    matched: list[str],
    missing: list[str],
    questions: list[InterviewQuestion],
) -> list[str]:
    priorities: list[str] = []

    if any(skill in matched for skill in ["SQL", "Power BI", "Python", "Excel"]):
        priorities.append(
            "Prepare clear explanations and examples for your matched core skills."
        )

    if missing:
        priorities.append(
            "Review the missing skills honestly; do not add them to the resume "
            "unless you have real experience."
        )

    categories = {question.category for question in questions}

    if "SQL" in categories:
        priorities.append(
            "Practice joins, aggregations, window functions, CTEs and query optimization."
        )

    if "Power BI" in categories:
        priorities.append(
            "Revise data modeling, DAX context, Power Query and dashboard design."
        )

    if "Business Analysis" in categories:
        priorities.append(
            "Prepare requirements-gathering, stakeholder and gap-analysis examples."
        )

    if "Application Support" in categories:
        priorities.append(
            "Prepare two production incident stories using the STAR structure."
        )

    priorities.append(
        "Research the company, its products and the exact team before the interview."
    )

    return priorities


def generate_interview_plan(
    company: str,
    role: str,
    job_description: str,
) -> dict:
    company = company.strip()
    role = role.strip()
    job_description = job_description.strip()

    if not company:
        raise ValueError("Company name is required.")

    if not role:
        raise ValueError("Job role is required.")

    if not job_description:
        raise ValueError("Job description is required.")

    resume_report = ResumeReport().generate(job_description)
    questions = _select_questions(role, job_description)

    return {
        "company": company,
        "role": role,
        "ats_score": resume_report["ats_score"],
        "matched_skills": resume_report["matched"],
        "missing_skills": resume_report["missing"],
        "skills_to_emphasize": resume_report["emphasize"],
        "questions": questions,
        "research_links": _build_research_links(company),
        "preparation_priorities": _preparation_priority(
            matched=resume_report["matched"],
            missing=resume_report["missing"],
            questions=questions,
        ),
    }


def build_interview_report(plan: dict) -> str:
    lines = [
        "CAREERPILOT INTERVIEW PREPARATION REPORT",
        "=" * 60,
        f"Company: {plan['company']}",
        f"Role: {plan['role']}",
        f"Resume/JD Match: {plan['ats_score']}%",
        "",
        "MATCHED SKILLS",
        "-" * 60,
    ]

    lines.extend(
        f"- {skill}" for skill in plan["matched_skills"]
    )

    lines.extend(
        [
            "",
            "MISSING SKILLS",
            "-" * 60,
        ]
    )

    if plan["missing_skills"]:
        lines.extend(
            f"- {skill}" for skill in plan["missing_skills"]
        )
    else:
        lines.append("- No recognized missing skills.")

    lines.extend(
        [
            "",
            "PREPARATION PRIORITIES",
            "-" * 60,
        ]
    )

    lines.extend(
        f"- {priority}"
        for priority in plan["preparation_priorities"]
    )

    current_category = None

    for item in plan["questions"]:
        if item.category != current_category:
            current_category = item.category
            lines.extend(
                [
                    "",
                    current_category.upper(),
                    "-" * 60,
                ]
            )

        lines.append(f"Question: {item.question}")
        lines.append(f"Answer guidance: {item.answer_guidance}")
        lines.append("")

    lines.extend(
        [
            "COMPANY RESEARCH LINKS",
            "-" * 60,
        ]
    )

    for name, link in plan["research_links"].items():
        lines.append(f"{name}: {link}")

    return "\n".join(lines)


def export_interview_report(
    plan: dict,
    output_dir: str | Path = "exports/reports",
) -> str:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    safe_company = "".join(
        character if character.isalnum() else "_"
        for character in plan["company"]
    ).strip("_")

    safe_role = "".join(
        character if character.isalnum() else "_"
        for character in plan["role"]
    ).strip("_")

    output_path = (
        directory
        / f"{safe_company}_{safe_role}_Interview_Preparation.txt"
    )

    output_path.write_text(
        build_interview_report(plan),
        encoding="utf-8",
    )

    return str(output_path)