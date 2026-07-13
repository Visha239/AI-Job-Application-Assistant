from __future__ import annotations
from app.services.job_freshness import add_freshness_columns

import json
import re

import pandas as pd


TARGET_ROLE_TERMS = {
    "Data Analyst": [
        "data analyst",
        "business data analyst",
        "reporting analyst",
        "sql analyst",
        "mis analyst",
        "power bi analyst",
        "bi analyst",
    ],
    "Business Analyst": [
        "business analyst",
        "process analyst",
        "functional analyst",
        "business systems analyst",
    ],
    "Support Analyst": [
        "application support",
        "production support",
        "support analyst",
        "technical support",
        "l1 support",
        "l2 support",
    ],
}

EXPERIENCE_PENALTIES = [
    r"\b5\+?\s*years?\b",
    r"\b6\+?\s*years?\b",
    r"\b7\+?\s*years?\b",
    r"\b8\+?\s*years?\b",
    r"\bmanager\b",
    r"\blead\b",
    r"\bprincipal\b",
]


def load_profile(path: str = "data/profile.json") -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).lower()


def _calculate_match_score(row: pd.Series, profile: dict) -> tuple[int, list[str], list[str]]:
    title = _text(row.get("title"))
    description = _text(row.get("description"))
    location = _text(row.get("location"))
    combined = f"{title} {description}"

    profile_skills = profile.get("skills", [])
    preferred_locations = profile.get("preferred_locations", [])
    preferred_roles = profile.get("preferred_roles", [])

    score = 0
    matched_skills: list[str] = []
    missing_skills: list[str] = []

    # Skill score: maximum 55
    for skill in profile_skills:
        if skill.lower() in combined:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    if profile_skills:
        score += round((len(matched_skills) / len(profile_skills)) * 55)

    # Role/title score: maximum 25
    role_match = False

    for preferred_role in preferred_roles:
        if preferred_role.lower() in title:
            role_match = True
            break

    if not role_match:
        for terms in TARGET_ROLE_TERMS.values():
            if any(term in title for term in terms):
                role_match = True
                break

    if role_match:
        score += 25

    # Location score: maximum 15
    location_match = any(
        preferred_location.lower() in location
        for preferred_location in preferred_locations
    )

    if "bengaluru" in location or "bangalore" in location:
        location_match = True

    if _text(row.get("is_remote")) in {"true", "1", "yes"}:
        location_match = True

    if location_match:
        score += 15

    # Recent/listed-job availability score
    if row.get("job_url"):
        score += 5

    # Penalize clearly senior roles
    if any(re.search(pattern, combined) for pattern in EXPERIENCE_PENALTIES):
        score -= 20

    score = max(0, min(score, 100))

    return score, matched_skills, missing_skills


def rank_jobs(jobs: pd.DataFrame, profile_path: str = "data/profile.json") -> pd.DataFrame:
    if jobs is None or jobs.empty:
        return pd.DataFrame()

    profile = load_profile(profile_path)
    ranked = add_freshness_columns(jobs)

    results = ranked.apply(
        lambda row: _calculate_match_score(row, profile),
        axis=1,
    )

    ranked["base_match_score"] = results.apply(lambda item: item[0])

    ranked["match_score"] = (
    ranked["base_match_score"]
    + ranked["freshness_bonus"].fillna(0)
    ).clip(upper=100)
    ranked["matched_skills"] = results.apply(
        lambda item: ", ".join(item[1])
    )
    ranked["missing_profile_skills"] = results.apply(
        lambda item: ", ".join(item[2][:6])
    )

    ranked["resume_version"] = ranked["title"].apply(_recommend_resume)

    ranked = ranked.sort_values(
        by=["match_score", "date_posted"],
        ascending=[False, False],
        na_position="last",
    )

    return ranked.reset_index(drop=True)


def _recommend_resume(title: object) -> str:
    title_text = _text(title)

    if any(
        term in title_text
        for term in [
            "application support",
            "production support",
            "technical support",
            "support analyst",
        ]
    ):
        return "Support Engineer Resume"

    if "business analyst" in title_text or "process analyst" in title_text:
        return "Business Analyst Resume"

    return "Data Analyst Resume"