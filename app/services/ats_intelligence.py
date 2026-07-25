from __future__ import annotations

import re
from typing import Any


SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "SQL": ("sql", "structured query language"),
    "Python": ("python", "pandas", "numpy"),
    "Excel": (
        "excel",
        "pivot table",
        "pivot tables",
        "vlookup",
        "xlookup",
        "power pivot",
    ),
    "Power BI": ("power bi", "powerbi"),
    "DAX": ("dax", "data analysis expressions"),
    "Power Query": ("power query", "m language"),
    "Tableau": ("tableau",),
    "Data Analysis": (
        "data analysis",
        "data analytics",
        "analyze data",
        "analytical insights",
    ),
    "Data Visualization": (
        "data visualization",
        "visualisation",
        "visualization",
        "charts",
    ),
    "Dashboard": ("dashboard", "dashboards"),
    "Reporting": ("reporting", "reports", "report automation"),
    "KPI": ("kpi", "key performance indicator"),
    "ETL": ("etl", "extract transform load"),
    "Data Modeling": (
        "data modeling",
        "data modelling",
        "star schema",
        "dimensional model",
    ),
    "Statistics": (
        "statistics",
        "statistical analysis",
        "hypothesis testing",
        "regression",
    ),
    "Business Analysis": (
        "business analysis",
        "business analyst",
        "requirements gathering",
        "gap analysis",
    ),
    "Stakeholder Management": (
        "stakeholder",
        "cross functional",
        "cross-functional",
    ),
    "UAT": (
        "uat",
        "user acceptance testing",
        "acceptance testing",
    ),
    "Linux": ("linux", "unix"),
    "ServiceNow": ("servicenow", "service now"),
    "Jira": ("jira",),
    "AWS": (
        "aws",
        "amazon web services",
        "ec2",
        "s3",
        "aurora",
    ),
    "Azure": (
        "azure",
        "azure data factory",
        "adf",
        "synapse",
    ),
    "Snowflake": ("snowflake",),
    "Spark": ("spark", "pyspark"),
    "dbt": ("dbt", "data build tool"),
    "MySQL": ("mysql",),
    "Oracle": ("oracle",),
    "MariaDB": ("mariadb", "maria db"),
    "Git": ("git", "github"),
    "Machine Learning": (
        "machine learning",
        "scikit-learn",
        "sklearn",
    ),
}

EMPHASIS_SKILLS = {
    "Power BI",
    "DAX",
    "Power Query",
    "Dashboard",
    "Reporting",
    "KPI",
    "Data Visualization",
    "Data Modeling",
    "Stakeholder Management",
}

PROFILE_FALLBACK_SKILLS = {
    "Python",
    "SQL",
    "Power BI",
    "Excel",
    "Tableau",
    "Linux",
    "ServiceNow",
    "Jira",
    "Data Analysis",
    "AWS",
    "MySQL",
    "Oracle",
    "MariaDB",
    "Dashboard",
    "Reporting",
    "KPI",
    "Power Query",
    "DAX",
    "ETL",
    "Data Visualization",
}


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def extract_job_skills(job_description: str) -> list[str]:
    text = _normalise(job_description)
    found: list[str] = []

    for skill, aliases in SKILL_ALIASES.items():
        if any(alias in text for alias in aliases):
            found.append(skill)

    return found


def _profile_skills(profile: dict[str, Any]) -> set[str]:
    skills = {
        str(skill).strip()
        for skill in profile.get("skills", [])
        if str(skill).strip()
    }

    skills.update(PROFILE_FALLBACK_SKILLS)

    return skills


def analyze_ats(
    *,
    job_description: str,
    profile: dict[str, Any],
) -> dict[str, Any]:
    description = job_description.strip()

    if not description:
        raise ValueError("Job description is required.")

    job_skills = extract_job_skills(description)
    owned_skills = _profile_skills(profile)

    matched = [
        skill
        for skill in job_skills
        if skill in owned_skills
    ]

    missing = [
        skill
        for skill in job_skills
        if skill not in owned_skills
    ]

    emphasize = [
        skill
        for skill in matched
        if skill in EMPHASIS_SKILLS
    ]

    description_words = len(description.split())

    if not job_skills:
        score = 0
        confidence = "Low"
        confidence_message = (
            "No recognized skills were detected. "
            "Paste a more complete job description."
        )

    else:
        coverage = len(matched) / len(job_skills)
        score = round(coverage * 85)

        if len(matched) >= 5:
            score += 10
        elif len(matched) >= 3:
            score += 6
        elif len(matched) >= 2:
            score += 3

        if description_words >= 180:
            score += 5

        score = min(score, 100)

        if len(job_skills) >= 10 and description_words >= 100:
            confidence = "High"
            confidence_message = (
                "The score is based on a detailed JD "
                "with many recognized skills."
            )
        elif len(job_skills) >= 4 or description_words >= 80:
            confidence = "Medium"
            confidence_message = (
                "The score is based on several recognized skills. "
                "A more detailed JD would improve accuracy further."
            )
        else:
            confidence = "Low"
            confidence_message = (
                "The JD is short or contains too few recognized skills. "
                "Do not rely on the score alone."
            )

    if len(job_skills) <= 1:
        score = min(score, 55)

    if len(job_skills) == 2:
        score = min(score, 70)

    recommendation = "Review carefully"

    if confidence == "High" and score >= 80:
        recommendation = "Strong fit â€” apply now"
    elif score >= 65:
        recommendation = "Good fit â€” apply"
    elif score >= 45:
        recommendation = "Possible fit â€” review gaps"
    elif job_skills:
        recommendation = "Low fit â€” prioritize better matches"

    return {
        "ats_score": score,
        "confidence": confidence,
        "confidence_message": confidence_message,
        "recommendation": recommendation,
        "total_keywords": len(job_skills),
        "job_skills": job_skills,
        "matched": matched,
        "emphasize": emphasize,
        "missing": missing,
        "do_not_add": missing,
        "improve": [
            "Career Objective",
            "Technical Skills",
            "Projects",
            "Work Experience",
        ],
        "description_word_count": description_words,
    }

