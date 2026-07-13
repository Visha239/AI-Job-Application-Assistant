from __future__ import annotations

import re
from typing import Any

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

EXPERIENCE_PATTERNS = [
    re.compile(
        r"\b(?:minimum\s+of\s+)?(\d+)\s*(?:\+|plus)?\s*years?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(\d+)\s*(?:-|to)\s*(\d+)\s*years?\b",
        re.IGNORECASE,
    ),
]


def extract_required_experience_years(text: str) -> int | None:
    values: list[int] = []

    for pattern in EXPERIENCE_PATTERNS:
        for match in pattern.finditer(text):
            try:
                values.append(int(match.group(1)))
            except (TypeError, ValueError):
                continue

    return min(values) if values else None


def _is_remote(row: dict[str, Any]) -> bool:
    raw = lower_text(row.get("is_remote"))

    if raw in {"true", "1", "yes", "remote"}:
        return True

    location = lower_text(row.get("location"))
    description = lower_text(row.get("description"))

    return (
        "remote" in location
        or "work from home" in description
    )


def _contains_seniority(title: str) -> bool:
    normalized = re.sub(
        r"[^a-z0-9]+",
        " ",
        title.lower(),
    ).strip()

    words = set(normalized.split())

    if "vice president" in normalized:
        return True

    if "head of" in normalized:
        return True

    return any(
        word in words
        for word in SENIORITY_WORDS
    )


def evaluate_relevance(
    row: dict[str, Any],
    candidate_experience_years: float = 1.1,
) -> RelevanceResult:
    title = lower_text(row.get("title"))
    description = lower_text(row.get("description"))
    location = lower_text(row.get("location"))

    combined = f"{title} {description}"

    title_score = 0
    experience_score = 0
    location_score = 0
    relevance_penalty = 0

    reasons: list[str] = []
    warnings: list[str] = []

    if any(
        term in title
        for term in PREFERRED_TITLE_TERMS
    ):
        title_score = 30
        reasons.append(
            "Title closely matches a target role."
        )

    elif any(
        term in title
        for term in TRANSFERABLE_TITLE_TERMS
    ):
        title_score = 18
        reasons.append(
            "Title has transferable analyst/support alignment."
        )

    else:
        title_score = 5
        warnings.append(
            "Title is not a close match to the target roles."
        )

    is_senior_role = _contains_seniority(title)

    if is_senior_role:
        relevance_penalty += 35
        warnings.append(
            "Title appears senior for the candidate profile."
        )

    if any(
        term in title
        for term in IRRELEVANT_TITLE_TERMS
    ):
        relevance_penalty += 30
        warnings.append(
            "Title appears unrelated to the preferred roles."
        )

    required_experience = extract_required_experience_years(
        combined
    )

    if required_experience is None:
        experience_score = 10
        reasons.append(
            "No clear high experience requirement was detected."
        )

    elif required_experience <= candidate_experience_years + 1:
        experience_score = 20
        reasons.append(
            "Experience requirement is suitable."
        )

    elif required_experience <= candidate_experience_years + 2:
        experience_score = 8
        warnings.append(
            f"Role may stretch the profile at "
            f"{required_experience}+ years."
        )

    else:
        experience_score = 0
        relevance_penalty += 30
        warnings.append(
            f"Role asks for around "
            f"{required_experience}+ years."
        )

    if any(
        term in location
        for term in [
            "bengaluru",
            "bangalore",
            "karnataka",
        ]
    ):
        location_score = 15
        reasons.append(
            "Location matches Bengaluru/Karnataka preference."
        )

    elif _is_remote(row):
        location_score = 15
        reasons.append(
            "Remote work matches the location preference."
        )

    elif not location:
        location_score = 5
        warnings.append(
            "Location was not provided."
        )

    else:
        location_score = 2
        warnings.append(
            "Location is outside the preferred area."
        )

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
        required_experience_years=required_experience,
        reasons=reasons,
        warnings=warnings,
    )
