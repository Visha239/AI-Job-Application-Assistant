from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

import pandas as pd

from app.services.job_discovery.models import FreshnessResult

def parse_posted_date(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    text = str(value).strip()
    if not text or text.lower() in {"none", "nan", "nat"}:
        return None
    parsed = pd.to_datetime(text, errors="coerce", utc=True)
    if pd.isna(parsed):
        return None
    return parsed.to_pydatetime()

def calculate_job_age_hours(date_posted: Any, now: datetime | None = None) -> float | None:
    posted = parse_posted_date(date_posted)
    if posted is None:
        return None
    current = now or datetime.now(timezone.utc)
    current = current.replace(tzinfo=timezone.utc) if current.tzinfo is None else current.astimezone(timezone.utc)
    return max((current - posted).total_seconds() / 3600, 0.0)

def evaluate_freshness(date_posted: Any, now: datetime | None = None) -> FreshnessResult:
    age_hours = calculate_job_age_hours(date_posted, now)
    if age_hours is None:
        return FreshnessResult(None, 0, "Posting date unavailable", "Review normally")
    rounded = round(age_hours, 1)
    if age_hours <= 6:
        return FreshnessResult(rounded, 15, "Posted very recently", "Apply immediately")
    if age_hours <= 24:
        return FreshnessResult(rounded, 12, "Posted today", "Apply today")
    if age_hours <= 72:
        return FreshnessResult(rounded, 8, "Posted within 3 days", "Apply soon")
    if age_hours <= 168:
        return FreshnessResult(rounded, 4, "Posted within 7 days", "Apply this week")
    return FreshnessResult(rounded, 0, "Older posting", "Check whether still active")
