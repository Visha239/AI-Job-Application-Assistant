from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from app.services.job_discovery.freshness import evaluate_freshness
from app.services.job_discovery.models import lower_text
from app.services.job_discovery.relevance import evaluate_relevance


DEFAULT_PROFILE_PATH = Path("data/profile.json")

JOB_SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "SQL": ("sql", "mysql", "mariadb", "oracle", "database query"),
    "Python": ("python", "pandas", "numpy"),
    "Power BI": ("power bi", "powerbi", "dax"),
    "Excel": ("excel", "pivot table", "vlookup", "xlookup"),
    "Tableau": ("tableau",),
    "Linux": ("linux", "unix"),
    "ServiceNow": ("servicenow", "service now"),
    "Jira": ("jira",),
    "AWS": ("aws", "amazon web services", "ec2", "s3", "aurora"),
    "Data Analysis": ("data analysis", "data analytics", "analytical"),
    "Power Query": ("power query", "m language"),
    "ETL": ("etl", "data pipeline", "data integration"),
    "Dashboard": ("dashboard", "visualization", "reporting"),
    "Stakeholder Management": (
        "stakeholder",
        "business requirement",
        "requirements gathering",
    ),
}

ROLE_CORE_SKILLS: dict[str, tuple[str, ...]] = {
    "data": (
        "SQL",
        "Python",
        "Power BI",
        "Excel",
        "Tableau",
        "Data Analysis",
        "Power Query",
        "ETL",
        "Dashboard",
    ),
    "business": (
        "SQL",
        "Excel",
        "Power BI",
        "Data Analysis",
        "Stakeholder Management",
        "Dashboard",
    ),
    "support": (
        "SQL",
        "Linux",
        "ServiceNow",
        "Jira",
        "AWS",
        "Python",
    ),
}


def load_profile(
    profile_path: str | Path = DEFAULT_PROFILE_PATH,
) -> dict[str, Any]:
    path = Path(profile_path)

    with path.open("r", encoding="utf-8") as file:
        profile = json.load(file)

    profile.setdefault("skills", [])
    profile.setdefault("preferred_roles", [])
    profile.setdefault(
        "preferred_locations",
        ["Bengaluru", "Bangalore", "Remote"],
    )
    profile.setdefault("experience_years", 1.1)

    return profile


def _normalise_company(value: object) -> str:
    text = str(value or "").strip()

    if text.lower() in {"", "nan", "none", "null"}:
        return "Unknown Company"

    return text


def _role_family(title: object) -> str:
    text = lower_text(title)

    if any(
        term in text
        for term in [
            "application support",
            "production support",
            "technical support",
            "support analyst",
            "support engineer",
            "l1 support",
            "l2 support",
        ]
    ):
        return "support"

    if any(
        term in text
        for term in [
            "business analyst",
            "process analyst",
            "functional analyst",
        ]
    ):
        return "business"

    return "data"


def _detect_job_skills(text: str) -> list[str]:
    detected: list[str] = []

    for canonical, aliases in JOB_SKILL_ALIASES.items():
        if any(alias in text for alias in aliases):
            detected.append(canonical)

    return detected


def _profile_skill_set(profile: dict[str, Any]) -> set[str]:
    result: set[str] = set()

    for skill in profile.get("skills", []):
        text = str(skill).strip().lower()

        if text:
            result.add(text)

    return result


def _calculate_skill_score(
    row: pd.Series,
    profile: dict[str, Any],
) -> tuple[int, list[str], list[str], list[str]]:
    combined = " ".join(
        [
            lower_text(row.get("title")),
            lower_text(row.get("description")),
        ]
    )

    detected_job_skills = _detect_job_skills(combined)
    family = _role_family(row.get("title"))

    if not detected_job_skills:
        detected_job_skills = list(ROLE_CORE_SKILLS[family])

    profile_skills = _profile_skill_set(profile)

    matched = [
        skill
        for skill in detected_job_skills
        if skill.lower() in profile_skills
    ]

    missing = [
        skill
        for skill in detected_job_skills
        if skill not in matched
    ]

    denominator = max(len(detected_job_skills), 1)
    coverage = len(matched) / denominator

    score = round(coverage * 35)

    # Reward broad practical alignment without demanding every profile skill.
    if len(matched) >= 4:
        score += 5
    elif len(matched) >= 2:
        score += 2

    return min(score, 40), matched, missing, detected_job_skills


def _recommend_resume(title: object) -> str:
    family = _role_family(title)

    if family == "support":
        return "Support Engineer Resume"

    if family == "business":
        return "Business Analyst Resume"

    return "Data Analyst Resume"


def _priority_label(score: int) -> str:
    if score >= 85:
        return "Apply immediately"

    if score >= 72:
        return "High priority"

    if score >= 60:
        return "Good opportunity"

    if score >= 45:
        return "Review carefully"

    return "Low priority"


def rank_jobs(
    jobs: pd.DataFrame,
    profile_path: str | Path = DEFAULT_PROFILE_PATH,
    now=None,
) -> pd.DataFrame:
    if jobs is None or jobs.empty:
        return pd.DataFrame()

    profile = load_profile(profile_path)
    candidate_experience = float(
        profile.get("experience_years", 1.1)
    )

    ranked = jobs.copy()

    for required_column in [
        "title",
        "company",
        "location",
        "date_posted",
        "description",
        "job_url",
        "site",
    ]:
        if required_column not in ranked.columns:
            ranked[required_column] = None

    ranked["company"] = ranked["company"].apply(
        _normalise_company
    )

    freshness_results = ranked["date_posted"].apply(
        lambda value: evaluate_freshness(value, now=now)
    )

    relevance_results = ranked.apply(
        lambda row: evaluate_relevance(
            row.to_dict(),
            candidate_experience_years=candidate_experience,
        ),
        axis=1,
    )

    skill_results = ranked.apply(
        lambda row: _calculate_skill_score(row, profile),
        axis=1,
    )

    ranked["job_age_hours"] = freshness_results.apply(
        lambda result: result.age_hours
    )
    ranked["freshness_bonus"] = freshness_results.apply(
        lambda result: result.bonus
    )
    ranked["freshness_label"] = freshness_results.apply(
        lambda result: result.label
    )
    ranked["apply_urgency"] = freshness_results.apply(
        lambda result: result.urgency
    )

    ranked["suitability_score"] = relevance_results.apply(
        lambda result: result.suitability_score
    )
    ranked["title_score"] = relevance_results.apply(
        lambda result: result.title_score
    )
    ranked["experience_score"] = relevance_results.apply(
        lambda result: result.experience_score
    )
    ranked["location_score"] = relevance_results.apply(
        lambda result: result.location_score
    )
    ranked["relevance_penalty"] = relevance_results.apply(
        lambda result: result.relevance_penalty
    )
    ranked["is_senior_role"] = relevance_results.apply(
        lambda result: result.is_senior_role
    )
    ranked["required_experience_years"] = (
        relevance_results.apply(
            lambda result: result.required_experience_years
        )
    )
    ranked["match_reasons"] = relevance_results.apply(
        lambda result: " | ".join(result.reasons)
    )
    ranked["match_warnings"] = relevance_results.apply(
        lambda result: " | ".join(result.warnings)
    )

    ranked["skill_score"] = skill_results.apply(
        lambda result: result[0]
    )
    ranked["matched_skills"] = skill_results.apply(
        lambda result: ", ".join(result[1])
    )
    ranked["missing_job_skills"] = skill_results.apply(
        lambda result: ", ".join(result[2])
    )
    ranked["detected_job_skills"] = skill_results.apply(
        lambda result: ", ".join(result[3])
    )

    # Retain the old column name for existing pages and services.
    ranked["missing_profile_skills"] = ranked[
        "missing_job_skills"
    ]

    ranked["base_match_score"] = (
        ranked["skill_score"]
        + ranked["suitability_score"]
    ).clip(upper=100)

    ranked["match_score"] = (
        ranked["base_match_score"]
        + ranked["freshness_bonus"]
    ).clip(upper=100)

    ranked["priority"] = ranked["match_score"].apply(
        lambda value: _priority_label(int(value))
    )

    ranked["resume_version"] = ranked["title"].apply(
        _recommend_resume
    )

    ranked = ranked.sort_values(
        by=[
            "match_score",
            "freshness_bonus",
            "date_posted",
        ],
        ascending=[False, False, False],
        na_position="last",
    )

    return ranked.reset_index(drop=True)
