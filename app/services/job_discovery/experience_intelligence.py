from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExperienceRequirement:
    minimum_years: float | None
    maximum_years: float | None
    label: str
    confidence: str
    evidence: str
    is_entry_level: bool


ENTRY_LEVEL_PATTERNS = [
    re.compile(r"\bfreshers?\b", re.I),
    re.compile(r"\bfresh\s+graduates?\b", re.I),
    re.compile(r"\bentry[-\s]?level\b", re.I),
    re.compile(r"\bgraduate\s+(?:role|program|programme|trainee)\b", re.I),
    re.compile(r"\bno\s+(?:prior\s+)?experience\s+(?:required|needed)\b", re.I),
    re.compile(r"\b0\s*(?:-|–|—|to)\s*1\s+years?\b", re.I),
    re.compile(r"\b0\s*(?:-|–|—|to)\s*2\s+years?\b", re.I),
]

RANGE_PATTERNS = [
    re.compile(
        r"\b(?:experience(?:\s+required)?\s*[:\-]?\s*)?"
        r"(\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*(\d+(?:\.\d+)?)"
        r"\s*(?:years?|yrs?)\b",
        re.I,
    ),
]

MINIMUM_PATTERNS = [
    re.compile(
        r"\b(?:minimum(?:\s+of)?|at\s+least|more\s+than|over)\s+"
        r"(\d+(?:\.\d+)?)\s*(?:\+|plus)?\s*(?:years?|yrs?)"
        r"(?:\s+of\s+experience)?\b",
        re.I,
    ),
    re.compile(
        r"\b(\d+(?:\.\d+)?)\s*(?:\+|plus)\s*(?:years?|yrs?)"
        r"(?:\s+of\s+experience)?\b",
        re.I,
    ),
    re.compile(
        r"\b(?:requires?|required|must\s+have|should\s+have|with)\s+"
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)"
        r"(?:\s+of\s+(?:relevant\s+)?experience)?\b",
        re.I,
    ),
]

EXPERIENCE_CONTEXT_PATTERNS = [
    re.compile(
        r"\b(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s+"
        r"(?:of\s+)?(?:relevant\s+|professional\s+|total\s+)?experience\b",
        re.I,
    ),
    re.compile(
        r"\bexperience\s*(?:required|needed|preferred)?\s*[:\-]?\s*"
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\b",
        re.I,
    ),
    re.compile(
        r"\b(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s+(?:in|with)\s+"
        r"(?:sql|python|analytics|data|power\s*bi|reporting|support|software|technology)\b",
        re.I,
    ),
]

MAXIMUM_PATTERNS = [
    re.compile(
        r"\b(?:maximum|max(?:imum)?\s+of|up\s+to|not\s+more\s+than)\s+"
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\b",
        re.I,
    ),
]


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"", "none", "nan", "null", "nat"}:
        return ""
    return text


def combined_job_text(job: dict[str, Any]) -> str:
    fields = [
        job.get("title"),
        job.get("experience"),
        job.get("experience_range"),
        job.get("requirements"),
        job.get("description"),
    ]
    return "\n".join(_clean(value) for value in fields if _clean(value))


def parse_experience_requirement(
    text: str,
) -> ExperienceRequirement:
    clean_text = _clean(text)

    if not clean_text:
        return ExperienceRequirement(
            minimum_years=None,
            maximum_years=None,
            label="Not stated",
            confidence="low",
            evidence="",
            is_entry_level=False,
        )

    entry_matches = [
        pattern.search(clean_text)
        for pattern in ENTRY_LEVEL_PATTERNS
    ]
    entry_match = next(
        (match for match in entry_matches if match),
        None,
    )

    ranges: list[tuple[float, float, str]] = []
    minimums: list[tuple[float, str]] = []
    maximums: list[tuple[float, str]] = []

    for pattern in RANGE_PATTERNS:
        for match in pattern.finditer(clean_text):
            low = float(match.group(1))
            high = float(match.group(2))
            if 0 <= low <= high <= 50:
                ranges.append((low, high, match.group(0)))

    for pattern in MINIMUM_PATTERNS + EXPERIENCE_CONTEXT_PATTERNS:
        for match in pattern.finditer(clean_text):
            value = float(match.group(1))
            if 0 <= value <= 50:
                minimums.append((value, match.group(0)))

    for pattern in MAXIMUM_PATTERNS:
        for match in pattern.finditer(clean_text):
            value = float(match.group(1))
            if 0 <= value <= 50:
                maximums.append((value, match.group(0)))

    if ranges:
        # Use the strictest explicit range when several are present.
        selected = max(ranges, key=lambda item: item[0])
        minimum, maximum, evidence = selected
        return ExperienceRequirement(
            minimum_years=minimum,
            maximum_years=maximum,
            label=f"{minimum:g}-{maximum:g} years",
            confidence="high",
            evidence=evidence,
            is_entry_level=minimum <= 1,
        )

    if minimums:
        # A JD may mention several skill-specific requirements. The highest
        # detected minimum is the safest eligibility interpretation.
        minimum, evidence = max(minimums, key=lambda item: item[0])
        maximum = (
            min(value for value, _ in maximums)
            if maximums
            else None
        )
        label = (
            f"{minimum:g}-{maximum:g} years"
            if maximum is not None and maximum >= minimum
            else f"{minimum:g}+ years"
        )
        return ExperienceRequirement(
            minimum_years=minimum,
            maximum_years=maximum,
            label=label,
            confidence="high",
            evidence=evidence,
            is_entry_level=minimum <= 1,
        )

    if entry_match:
        return ExperienceRequirement(
            minimum_years=0.0,
            maximum_years=2.0,
            label="Fresher / entry level",
            confidence="high",
            evidence=entry_match.group(0),
            is_entry_level=True,
        )

    if maximums:
        maximum, evidence = min(maximums, key=lambda item: item[0])
        return ExperienceRequirement(
            minimum_years=0.0,
            maximum_years=maximum,
            label=f"Up to {maximum:g} years",
            confidence="medium",
            evidence=evidence,
            is_entry_level=maximum <= 2,
        )

    return ExperienceRequirement(
        minimum_years=None,
        maximum_years=None,
        label="Not clearly stated",
        confidence="low",
        evidence="",
        is_entry_level=False,
    )


def analyze_job_experience(
    job: dict[str, Any],
) -> ExperienceRequirement:
    return parse_experience_requirement(
        combined_job_text(job)
    )


def is_experience_eligible(
    requirement: ExperienceRequirement,
    *,
    candidate_experience_years: float,
    maximum_required_experience: float,
) -> tuple[bool, str]:
    if requirement.minimum_years is None:
        return True, "Experience requirement is not clearly stated."

    if requirement.minimum_years <= maximum_required_experience:
        return True, (
            f"Detected minimum {requirement.minimum_years:g} years "
            f"is within the configured {maximum_required_experience:g}-year limit."
        )

    return False, (
        f"Detected minimum {requirement.minimum_years:g} years exceeds "
        f"the configured {maximum_required_experience:g}-year limit."
    )
