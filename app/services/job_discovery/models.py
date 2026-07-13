from __future__ import annotations

from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class FreshnessResult:
    age_hours: float | None
    bonus: int
    label: str
    urgency: str

@dataclass(frozen=True)
class RelevanceResult:
    suitability_score: int
    title_score: int
    experience_score: int
    location_score: int
    relevance_penalty: int
    is_senior_role: bool
    required_experience_years: int | None
    reasons: list[str]
    warnings: list[str]

def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"none", "nan", "nat"}:
        return ""
    return text

def lower_text(value: Any) -> str:
    return clean_text(value).lower()
