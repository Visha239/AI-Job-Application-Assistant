from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests

from app.services.job_sources.source_models import normalise_jobs


DEFAULT_TIMEOUT = 20


def _matches(text: str, role: str, location: str) -> bool:
    combined = (text or "").lower()
    role_terms = [
        term.strip().lower()
        for term in role.replace("/", " ").split()
        if len(term.strip()) >= 3
    ]
    role_match = not role_terms or any(term in combined for term in role_terms)

    location_text = (location or "").lower().replace("bengaluru", "bangalore")
    combined_location = combined.replace("bengaluru", "bangalore")
    location_terms = [
        term.strip()
        for term in location_text.replace(",", " ").split()
        if len(term.strip()) >= 4
    ]
    location_match = (
        not location_terms
        or any(term in combined_location for term in location_terms)
        or "remote" in combined_location
        or "india" in combined_location
    )
    return role_match and location_match


def search_greenhouse(
    *,
    company: str,
    board_token: str,
    role: str,
    location: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> pd.DataFrame:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
    response = requests.get(
        url,
        params={"content": "true"},
        timeout=timeout,
        headers={"User-Agent": "CareerPilotAI/1.0"},
    )
    response.raise_for_status()
    payload = response.json()

    records: list[dict[str, Any]] = []
    for item in payload.get("jobs", []):
        item_location = (item.get("location") or {}).get("name", "")
        description = item.get("content") or ""
        searchable = " ".join(
            [
                item.get("title") or "",
                item_location,
                description,
            ]
        )
        if not _matches(searchable, role, location):
            continue

        records.append(
            {
                "site": "company-greenhouse",
                "title": item.get("title") or "",
                "company": company,
                "location": item_location,
                "date_posted": item.get("updated_at"),
                "job_type": "",
                "is_remote": "remote" in item_location.lower(),
                "job_url": item.get("absolute_url") or "",
                "description": description,
                "requirements": description,
            }
        )

    return normalise_jobs(
        pd.DataFrame(records),
        site="company-greenhouse",
        source_type="company_careers",
        official_source=True,
        searched_role=role,
    )


def search_lever(
    *,
    company: str,
    site_token: str,
    role: str,
    location: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> pd.DataFrame:
    url = f"https://api.lever.co/v0/postings/{site_token}"
    response = requests.get(
        url,
        params={"mode": "json"},
        timeout=timeout,
        headers={"User-Agent": "CareerPilotAI/1.0"},
    )
    response.raise_for_status()
    payload = response.json()

    records: list[dict[str, Any]] = []
    for item in payload:
        categories = item.get("categories") or {}
        item_location = categories.get("location") or ""
        description = "\n".join(
            [
                item.get("descriptionPlain") or "",
                item.get("additionalPlain") or "",
            ]
        ).strip()
        searchable = " ".join(
            [
                item.get("text") or "",
                item_location,
                description,
            ]
        )
        if not _matches(searchable, role, location):
            continue

        created_at = item.get("createdAt")
        date_posted = None
        if isinstance(created_at, (int, float)):
            date_posted = datetime.fromtimestamp(
                created_at / 1000,
                tz=timezone.utc,
            ).isoformat()

        records.append(
            {
                "site": "company-lever",
                "title": item.get("text") or "",
                "company": company,
                "location": item_location,
                "date_posted": date_posted,
                "job_type": categories.get("commitment") or "",
                "is_remote": "remote" in item_location.lower(),
                "job_url": item.get("hostedUrl") or "",
                "description": description,
                "requirements": description,
            }
        )

    return normalise_jobs(
        pd.DataFrame(records),
        site="company-lever",
        source_type="company_careers",
        official_source=True,
        searched_role=role,
    )
