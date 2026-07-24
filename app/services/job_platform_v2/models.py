from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import pandas as pd

STANDARD_COLUMNS = [
    "site", "source_key", "source_group", "source_label",
    "official_source", "title", "company", "location",
    "date_posted", "job_type", "is_remote", "job_url",
    "description", "experience", "requirements", "searched_role",
]

@dataclass(frozen=True)
class SourceDefinition:
    key: str
    label: str
    adapter: str
    group: str
    enabled: bool = True
    official_source: bool = False
    domain: str = ""
    company: str = ""
    token: str = ""
    priority: int = 50
    options: dict[str, Any] = field(default_factory=dict)

def empty_jobs() -> pd.DataFrame:
    return pd.DataFrame(columns=STANDARD_COLUMNS)

def normalise_jobs(
    jobs: pd.DataFrame | None,
    *,
    source: SourceDefinition,
    searched_role: str,
) -> pd.DataFrame:
    if jobs is None or jobs.empty:
        return empty_jobs()

    result = jobs.copy()
    defaults = {
        "site": source.key,
        "source_key": source.key,
        "source_group": source.group,
        "source_label": source.label,
        "official_source": source.official_source,
        "title": "",
        "company": source.company,
        "location": "",
        "date_posted": None,
        "job_type": "",
        "is_remote": False,
        "job_url": "",
        "description": "",
        "experience": "",
        "requirements": "",
        "searched_role": searched_role,
    }

    for column, default in defaults.items():
        if column not in result.columns:
            result[column] = default
        else:
            result[column] = result[column].where(
                result[column].notna(), default
            )

    result["site"] = source.key
    result["source_key"] = source.key
    result["source_group"] = source.group
    result["source_label"] = source.label
    result["official_source"] = bool(source.official_source)
    result["searched_role"] = searched_role

    if source.company:
        missing = result["company"].fillna("").astype(str).str.strip() == ""
        result.loc[missing, "company"] = source.company

    return result[STANDARD_COLUMNS]
