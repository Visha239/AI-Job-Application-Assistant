from __future__ import annotations

import re
from typing import Any

from app.services.job_discovery.experience_intelligence import (
    analyze_job_experience,
)
from app.services.job_discovery.models import (
    RelevanceResult,
    lower_text,
)


PREFERRED_TITLE_TERMS = [
    "data analyst",
    "power bi analyst",
    "power bi developer",
    "sql analyst",
    "mis analyst",
    "mis executive",
    "reporting analyst",
    "bi analyst",
    "business intelligence analyst",
    "business analyst",
    "operations analyst",
    "data operations analyst",
    "application support analyst",
    "production support analyst",
    "support analyst",
    "l1 support",
    "l2 support",
]

TRANSFERABLE_TITLE_TERMS = [
    "analyst",
    "reporting",
    "business intelligence",
    "application support",
    "production support",
    "technical support",
    "operations",
]

SENIORITY_WORDS = {
    "senior",
    "sr",
    "lead",
    "principal",
    "manager",
    "architect",
    "director",
    "head",
    "vice president",
    "vp",
    "staff",
}

IRRELEVANT_TITLE_TERMS = [
    "sales analyst",
    "marketing manager",
    "financial advisor",
    "clinical analyst",
    "legal analyst",
    "security guard",
    "customer sales",
    "medical coder",
]


def contains_seniority(title: object) -> bool:
    normalized = re.sub(
        r"[^a-z0-9]+",
        " ",
        lower_text(title),
    ).strip()
    words = set(normalized.split())
    return (
        "vice president" in normalized
        or "head of" in normalized
        or any(word in words for word in SENIORITY_WORDS)
    )


def extract_required_experience_years(text: str) -> int | None:
    requirement = analyze_job_experience(
        {"description": text}
    )
    if requirement.minimum_years is None:
        return None
    return int(requirement.minimum_years)


def _is_remote(row: dict[str, Any]) -> bool:
    raw = lower_text(row.get("is_remote"))
    if raw in {"true", "1", "yes", "remote"}:
        return True
    return (
        "remote" in lower_text(row.get("location"))
        or "work from home" in lower_text(row.get("description"))
    )


def evaluate_relevance(
    row: dict[str, Any],
    candidate_experience_years: float = 1.1,
) -> RelevanceResult:
    title = lower_text(row.get("title"))
    location = lower_text(row.get("location"))

    title_score = 0
    experience_score = 0
    location_score = 0
    relevance_penalty = 0
    reasons: list[str] = []
    warnings: list[str] = []

    if any(term in title for term in PREFERRED_TITLE_TERMS):
        title_score = 30
        reasons.append("Title closely matches a target role.")
    elif any(term in title for term in TRANSFERABLE_TITLE_TERMS):
        title_score = 18
        reasons.append("Title has transferable analyst/support alignment.")
    else:
        title_score = 5
        warnings.append("Title is not a close match to the target roles.")

    is_senior_role = contains_seniority(title)

    if is_senior_role:
        relevance_penalty += 35
        warnings.append("Title appears senior for the candidate profile.")

    if any(term in title for term in IRRELEVANT_TITLE_TERMS):
        relevance_penalty += 30
        warnings.append("Title appears unrelated to the preferred roles.")

    requirement = analyze_job_experience(row)
    required_experience = requirement.minimum_years

    if required_experience is None:
        experience_score = 10
        reasons.append("No clear experience requirement was detected.")
    elif required_experience <= candidate_experience_years + 1:
        experience_score = 20
        reasons.append("Experience requirement is suitable.")
    elif required_experience <= candidate_experience_years + 2:
        experience_score = 8
        warnings.append(
            f"Role may stretch the profile at {required_experience:g}+ years."
        )
    else:
        relevance_penalty += 30
        warnings.append(
            f"Role asks for around {required_experience:g}+ years."
        )

    if any(term in location for term in ["bengaluru", "bangalore", "karnataka"]):
        location_score = 15
        reasons.append("Location matches Bengaluru/Karnataka preference.")
    elif _is_remote(row):
        location_score = 15
        reasons.append("Remote work matches the location preference.")
    elif not location:
        location_score = 5
        warnings.append("Location was not provided.")
    else:
        location_score = 2
        warnings.append("Location is outside the preferred area.")

    suitability_score = max(
        0,
        min(
            title_score
            + experience_score
            + location_score
            - relevance_penalty,
            65,
        ),
    )

    return RelevanceResult(
        suitability_score=suitability_score,
        title_score=title_score,
        experience_score=experience_score,
        location_score=location_score,
        relevance_penalty=relevance_penalty,
        is_senior_role=is_senior_role,
        required_experience_years=(
            int(required_experience)
            if required_experience is not None
            else None
        ),
        reasons=reasons,
        warnings=warnings,
    )
