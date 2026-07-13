from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from app.services.job_ranker import rank_jobs
from app.services.job_search import search_jobs


DEFAULT_CONFIG_PATH = Path("config/job_search.json")

RESULT_COLUMNS = [
    "site",
    "title",
    "company",
    "location",
    "date_posted",
    "job_type",
    "is_remote",
    "job_url",
    "description",
    "searched_role",
]


def load_search_config(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Job-search configuration was not found: {path}"
        )

    with path.open("r", encoding="utf-8-sig") as file:
        config = json.load(file)

    required_fields = [
        "roles",
        "location",
        "sites",
        "results_per_role",
        "hours_old",
        "minimum_match_score",
        "maximum_digest_jobs",
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in config
    ]

    if missing_fields:
        raise ValueError(
            "Missing job-search configuration fields: "
            + ", ".join(missing_fields)
        )

    if not isinstance(config["roles"], list) or not config["roles"]:
        raise ValueError("'roles' must be a non-empty list.")

    if not isinstance(config["sites"], list) or not config["sites"]:
        raise ValueError("'sites' must be a non-empty list.")

    return config


def _empty_jobs() -> pd.DataFrame:
    return pd.DataFrame(columns=RESULT_COLUMNS)


def _ensure_columns(jobs: pd.DataFrame) -> pd.DataFrame:
    updated = jobs.copy()

    for column in RESULT_COLUMNS:
        if column not in updated.columns:
            updated[column] = None

    return updated


def _normalise_key(value: object) -> str:
    if value is None:
        return ""

    text = str(value).strip().lower()

    if text in {"nan", "none", "null"}:
        return ""

    return " ".join(text.split())


def remove_duplicate_jobs(
    jobs: pd.DataFrame,
) -> pd.DataFrame:
    if jobs is None or jobs.empty:
        return _empty_jobs()

    updated = _ensure_columns(jobs)

    updated["_normalised_url"] = updated["job_url"].apply(
        _normalise_key
    )
    updated["_normalised_company"] = updated["company"].apply(
        _normalise_key
    )
    updated["_normalised_title"] = updated["title"].apply(
        _normalise_key
    )
    updated["_normalised_location"] = updated["location"].apply(
        _normalise_key
    )

    with_url = updated[
        updated["_normalised_url"] != ""
    ].drop_duplicates(
        subset=["_normalised_url"],
        keep="first",
    )

    without_url = updated[
        updated["_normalised_url"] == ""
    ]

    combined = pd.concat(
        [with_url, without_url],
        ignore_index=True,
        sort=False,
    )

    combined = combined.drop_duplicates(
        subset=[
            "_normalised_company",
            "_normalised_title",
            "_normalised_location",
        ],
        keep="first",
    )

    combined = combined.drop(
        columns=[
            "_normalised_url",
            "_normalised_company",
            "_normalised_title",
            "_normalised_location",
        ],
        errors="ignore",
    )

    return combined.reset_index(drop=True)


def search_multiple_roles(
    roles: list[str],
    location: str,
    sites: list[str],
    results_per_role: int = 15,
    hours_old: int = 168,
) -> tuple[pd.DataFrame, list[str]]:
    if not roles:
        raise ValueError("At least one role is required.")

    if not sites:
        raise ValueError("At least one source is required.")

    collected_frames: list[pd.DataFrame] = []
    errors: list[str] = []

    for role in roles:
        clean_role = str(role).strip()

        if not clean_role:
            continue

        try:
            jobs = search_jobs(
                search_term=clean_role,
                location=location,
                results_wanted=results_per_role,
                hours_old=hours_old,
                sites=sites,
            )
        except Exception as exc:
            errors.append(f"{clean_role}: {exc}")
            continue

        if jobs is None or jobs.empty:
            continue

        jobs = jobs.copy()
        jobs["searched_role"] = clean_role
        collected_frames.append(jobs)

    if not collected_frames:
        return _empty_jobs(), errors

    combined = pd.concat(
        collected_frames,
        ignore_index=True,
        sort=False,
    )

    return remove_duplicate_jobs(combined), errors


def filter_ranked_jobs(
    ranked_jobs: pd.DataFrame,
    minimum_score: int = 45,
    maximum_jobs: int | None = None,
    exclude_senior_roles: bool = True,
) -> pd.DataFrame:
    if ranked_jobs is None or ranked_jobs.empty:
        return pd.DataFrame()

    filtered = ranked_jobs.copy()

    if exclude_senior_roles and "is_senior_role" in filtered.columns:
        filtered = filtered[
            filtered["is_senior_role"].fillna(False) == False
        ]

    if "match_score" in filtered.columns:
        filtered = filtered[
            filtered["match_score"] >= minimum_score
        ]

    filtered = filtered.sort_values(
        by=[
            "match_score",
            "freshness_bonus",
            "date_posted",
        ],
        ascending=[False, False, False],
        na_position="last",
    )

    if maximum_jobs is not None:
        filtered = filtered.head(int(maximum_jobs))

    return filtered.reset_index(drop=True)


def run_multi_role_search(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    *,
    roles: list[str] | None = None,
    location: str | None = None,
    sites: list[str] | None = None,
    results_per_role: int | None = None,
    hours_old: int | None = None,
    minimum_match_score: int | None = None,
    maximum_jobs: int | None = None,
    exclude_senior_roles: bool = True,
) -> dict[str, Any]:
    config = load_search_config(config_path)

    selected_roles = roles if roles is not None else config["roles"]
    selected_location = (
        location if location is not None else config["location"]
    )
    selected_sites = sites if sites is not None else config["sites"]
    selected_results_per_role = int(
        results_per_role
        if results_per_role is not None
        else config["results_per_role"]
    )
    selected_hours_old = int(
        hours_old
        if hours_old is not None
        else config["hours_old"]
    )
    selected_minimum_score = int(
        minimum_match_score
        if minimum_match_score is not None
        else config.get("minimum_match_score", 45)
    )
    selected_maximum_jobs = int(
        maximum_jobs
        if maximum_jobs is not None
        else config["maximum_digest_jobs"]
    )

    raw_jobs, errors = search_multiple_roles(
        roles=selected_roles,
        location=selected_location,
        sites=selected_sites,
        results_per_role=selected_results_per_role,
        hours_old=selected_hours_old,
    )

    ranked_jobs = (
        rank_jobs(raw_jobs)
        if not raw_jobs.empty
        else pd.DataFrame()
    )

    filtered_jobs = filter_ranked_jobs(
        ranked_jobs=ranked_jobs,
        minimum_score=selected_minimum_score,
        maximum_jobs=selected_maximum_jobs,
        exclude_senior_roles=exclude_senior_roles,
    )

    return {
        "roles": selected_roles,
        "location": selected_location,
        "sites": selected_sites,
        "jobs_collected": len(raw_jobs),
        "jobs_ranked": len(ranked_jobs),
        "strong_matches": len(filtered_jobs),
        "raw_jobs": raw_jobs,
        "ranked_jobs": ranked_jobs,
        "filtered_jobs": filtered_jobs,
        "errors": errors,
    }
