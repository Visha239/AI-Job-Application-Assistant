from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

import pandas as pd


def parse_posted_date(value: Any) -> datetime | None:
    """Convert common job-board date values into a datetime."""

    if value is None:
        return None

    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    if isinstance(value, date):
        return datetime(
            value.year,
            value.month,
            value.day,
            tzinfo=timezone.utc,
        )

    text = str(value).strip()

    if not text or text.lower() in {"nan", "none", "nat"}:
        return None

    try:
        parsed = pd.to_datetime(
            text,
            errors="coerce",
            utc=True,
        )

        if pd.isna(parsed):
            return None

        return parsed.to_pydatetime()

    except (TypeError, ValueError):
        return None


def calculate_job_age_hours(
    date_posted: Any,
    now: datetime | None = None,
) -> float | None:
    posted = parse_posted_date(date_posted)

    if posted is None:
        return None

    current_time = now or datetime.now(timezone.utc)

    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    age = current_time - posted

    return max(age.total_seconds() / 3600, 0)


def get_freshness_details(
    date_posted: Any,
    now: datetime | None = None,
) -> dict[str, Any]:
    age_hours = calculate_job_age_hours(date_posted, now)

    if age_hours is None:
        return {
            "age_hours": None,
            "freshness_bonus": 0,
            "freshness_label": "Posting date unavailable",
            "apply_urgency": "Review normally",
        }

    if age_hours <= 6:
        return {
            "age_hours": round(age_hours, 1),
            "freshness_bonus": 15,
            "freshness_label": "Posted very recently",
            "apply_urgency": "Apply immediately",
        }

    if age_hours <= 24:
        return {
            "age_hours": round(age_hours, 1),
            "freshness_bonus": 12,
            "freshness_label": "Posted today",
            "apply_urgency": "Apply today",
        }

    if age_hours <= 72:
        return {
            "age_hours": round(age_hours, 1),
            "freshness_bonus": 8,
            "freshness_label": "Posted within 3 days",
            "apply_urgency": "Apply soon",
        }

    if age_hours <= 168:
        return {
            "age_hours": round(age_hours, 1),
            "freshness_bonus": 4,
            "freshness_label": "Posted within 7 days",
            "apply_urgency": "Apply this week",
        }

    return {
        "age_hours": round(age_hours, 1),
        "freshness_bonus": 0,
        "freshness_label": "Older posting",
        "apply_urgency": "Check whether still active",
    }


def add_freshness_columns(
    jobs: pd.DataFrame,
    now: datetime | None = None,
) -> pd.DataFrame:
    if jobs is None or jobs.empty:
        return pd.DataFrame() if jobs is None else jobs.copy()

    updated = jobs.copy()

    if "date_posted" not in updated.columns:
        updated["date_posted"] = None

    details = updated["date_posted"].apply(
        lambda value: get_freshness_details(value, now)
    )

    updated["job_age_hours"] = details.apply(
        lambda item: item["age_hours"]
    )

    updated["freshness_bonus"] = details.apply(
        lambda item: item["freshness_bonus"]
    )

    updated["freshness_label"] = details.apply(
        lambda item: item["freshness_label"]
    )

    updated["apply_urgency"] = details.apply(
        lambda item: item["apply_urgency"]
    )

    return updated