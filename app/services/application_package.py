from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from app.services.ats_intelligence import analyze_ats
from app.services.cover_letter import generate_cover_note
from app.services.recruiter import generate_email
from app.services.resume_history import save_resume_version
from app.services.resume_optimizer import ResumeOptimizer


EXPORT_ROOT = Path("exports/application_packages")


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    return cleaned.strip("_") or "application"


def generate_linkedin_message(
    profile: dict[str, Any],
    company: str,
    role: str,
    matched_skills: list[str],
) -> str:
    skills = ", ".join(matched_skills[:3]) or "SQL, Power BI and Excel"

    return (
        f"Hi, Iâ€™m {profile['name']}. Iâ€™m interested in the {role} role at "
        f"{company}. My background includes {skills}, along with 1.1 years "
        "of enterprise support experience. Iâ€™d appreciate connecting and "
        "learning more about the opportunity."
    )


def generate_follow_up_message(
    profile: dict[str, Any],
    company: str,
    role: str,
) -> str:
    return f"""Subject: Follow-up on {role} application

Dear Hiring Team,

Iâ€™m following up on my application for the {role} position at {company}. I remain very interested in the opportunity and believe my experience in SQL, Power BI, Python, Excel, production support, and business reporting aligns well with the role.

Please let me know if any additional information would be helpful.

Best regards,
{profile['name']}
{profile['email']}
"""


def generate_interview_topics(
    matched_skills: list[str],
    missing_skills: list[str],
) -> list[str]:
    topics: list[str] = []

    topic_map = {
        "SQL": "Revise joins, CTEs, window functions, aggregations, and query optimization.",
        "Power BI": "Revise data modeling, Power Query, DAX, filter context, and dashboard design.",
        "Python": "Revise pandas cleaning, joins, groupby, missing values, and automation examples.",
        "Excel": "Revise PivotTables, lookups, formulas, charts, and data cleaning.",
        "Tableau": "Revise calculated fields, parameters, filters, dashboards, and performance basics.",
        "Linux": "Prepare troubleshooting examples using top, iostat, df, dmesg, and logs.",
        "AWS": "Prepare practical examples involving EC2, S3, Aurora, and monitoring.",
        "ServiceNow": "Prepare incident, SLA, escalation, and ticket-management examples.",
        "Jira": "Prepare examples of issue tracking, reporting, and cross-team coordination.",
        "Data Modeling": "Revise fact tables, dimensions, relationships, star schema, and granularity.",
        "Statistics": "Revise descriptive statistics, hypothesis testing, distributions, and regression basics.",
    }

    for skill in matched_skills:
        guidance = topic_map.get(skill)

        if guidance and guidance not in topics:
            topics.append(guidance)

    if missing_skills:
        topics.append(
            "Review the missing skills at a basic interview level, "
            "but do not claim hands-on experience you do not have."
        )

    topics.extend(
        [
            "Prepare a 60â€“90 second introduction connecting support experience to analytics.",
            "Prepare two STAR stories: one production incident and one analytics/project achievement.",
            "Research the company, its products, customers, and the exact team.",
        ]
    )

    return topics


def build_application_package(
    *,
    profile: dict[str, Any],
    company: str,
    role: str,
    location: str,
    job_link: str,
    job_description: str,
    resume_type: str,
    status: str = "Ready to Apply",
) -> dict[str, Any]:
    company = company.strip()
    role = role.strip()
    job_description = job_description.strip()

    if not company:
        raise ValueError("Company name is required.")

    if not role:
        raise ValueError("Job role is required.")

    if not job_description:
        raise ValueError("Job description is required.")

    report = analyze_ats(
        job_description=job_description,
        profile=profile,
    )

    optimized = ResumeOptimizer().optimize_resume(
        role_type=resume_type,
        job_description=job_description,
    )

    output_path = Path(optimized["output_path"])
    resume_name = f"{company} - {role} - {resume_type}"

    save_resume_version(
        resume_name=resume_name,
        role_type=resume_type,
        file_path=str(output_path),
        ats_score=float(report["ats_score"]),
    )

    cover_note = generate_cover_note(
        profile=profile,
        company=company,
        role=role,
        matched_skills=report["matched"],
    )

    recruiter_email = generate_email(
        profile=profile,
        company=company,
        role=role,
    )

    linkedin_message = generate_linkedin_message(
        profile=profile,
        company=company,
        role=role,
        matched_skills=report["matched"],
    )

    follow_up_message = generate_follow_up_message(
        profile=profile,
        company=company,
        role=role,
    )

    interview_topics = generate_interview_topics(
        matched_skills=report["matched"],
        missing_skills=report["missing"],
    )

    checklist = {
        "resume_ready": output_path.exists(),
        "cover_note_ready": bool(cover_note.strip()),
        "recruiter_email_ready": bool(recruiter_email.strip()),
        "linkedin_message_ready": bool(linkedin_message.strip()),
        "follow_up_ready": bool(follow_up_message.strip()),
        "interview_topics_ready": bool(interview_topics),
    }

    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "company": company,
        "job_role": role,
        "resume_type": resume_type,
        "location": location.strip(),
        "job_link": job_link.strip(),
        "status": status,
        "job_description": job_description,
        "report": report,
        "optimized": optimized,
        "cover_note": cover_note,
        "recruiter_email": recruiter_email,
        "linkedin_message": linkedin_message,
        "follow_up_message": follow_up_message,
        "interview_topics": interview_topics,
        "checklist": checklist,
    }


def export_application_summary(
    package: dict[str, Any],
) -> str:
    folder_name = _safe_filename(
        f"{package['company']}_{package['job_role']}"
    )
    package_dir = EXPORT_ROOT / folder_name
    package_dir.mkdir(parents=True, exist_ok=True)

    summary_path = package_dir / "application_summary.txt"
    metadata_path = package_dir / "application_metadata.json"

    report = package["report"]

    summary = f"""CAREERPILOT APPLICATION PACKAGE
{'=' * 60}
Company: {package['company']}
Role: {package['job_role']}
Location: {package['location']}
Job link: {package['job_link']}
Status: {package['status']}
Resume version: {package['resume_type']}
ATS score: {report['ats_score']}%
ATS confidence: {report['confidence']}
Recommendation: {report['recommendation']}

JOB SKILLS DETECTED
{'-' * 60}
{chr(10).join('- ' + skill for skill in report['job_skills']) or '- None detected'}

MATCHED SKILLS
{'-' * 60}
{chr(10).join('- ' + skill for skill in report['matched']) or '- None detected'}

MISSING SKILLS â€” DO NOT ADD WITHOUT EXPERIENCE
{'-' * 60}
{chr(10).join('- ' + skill for skill in report['missing']) or '- None detected'}

INTERVIEW TOPICS
{'-' * 60}
{chr(10).join('- ' + topic for topic in package['interview_topics'])}

COVER NOTE
{'-' * 60}
{package['cover_note']}

RECRUITER EMAIL
{'-' * 60}
{package['recruiter_email']}

LINKEDIN MESSAGE
{'-' * 60}
{package['linkedin_message']}

FOLLOW-UP MESSAGE
{'-' * 60}
{package['follow_up_message']}
"""

    summary_path.write_text(summary, encoding="utf-8")

    serializable = {
        key: value
        for key, value in package.items()
        if key not in {"job_description"}
    }

    metadata_path.write_text(
        json.dumps(serializable, indent=2, default=str),
        encoding="utf-8",
    )

    return str(summary_path)

