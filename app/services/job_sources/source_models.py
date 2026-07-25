from __future__ import annotations

from typing import Any
import pandas as pd


STANDARD_COLUMNS = [
    "site",
    "title",
    "company",
    "location",
    "date_posted",
    "job_type",
    "is_remote",
    "job_url",
    "description",
    "experience",
    "requirements",
    "searched_role",
    "source_type",
    "official_source",
]


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"", "none", "nan", "null", "nat"}:
        return ""
    return text


def normalise_jobs(
    jobs: pd.DataFrame | None,
    *,
    site: str,
    source_type: str,
    official_source: bool,
    searched_role: str = "",
) -> pd.DataFrame:
    if jobs is None or jobs.empty:
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    result = jobs.copy()
    defaults = {
        "site": site,
        "title": "",
        "company": "",
        "location": "",
        "date_posted": None,
        "job_type": "",
        "is_remote": False,
        "job_url": "",
        "description": "",
        "experience": "",
        "requirements": "",
        "searched_role": searched_role,
        "source_type": source_type,
        "official_source": official_source,
    }

    for column, default in defaults.items():
        if column not in result.columns:
            result[column] = default
        else:
            result[column] = result[column].where(
                result[column].notna(),
                default,
            )

    if searched_role:
        result["searched_role"] = searched_role

    result["site"] = result["site"].replace("", site)
    result["source_type"] = source_type
    result["official_source"] = bool(official_source)

    return result[STANDARD_COLUMNS]
