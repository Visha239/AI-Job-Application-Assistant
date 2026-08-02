from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.services.application_crm import DEFAULT_CRM_PATH, load_crm
from app.services.application_tracking import track_job
from app.services.interview_action_dashboard import (
    FRESH_EDITOR_STAGES,
    filter_actionable_search_results,
    persist_fresh_opportunity_statuses,
)


def _clean(value: Any) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    text = str(value).strip()
    if text.lower() in {"", "none", "nan", "null", "nat"}:
        return ""
    return text


def _normalise_url(value: Any) -> str:
    return _clean(value).rstrip("/").lower()


def sync_search_results_to_crm(
    jobs: pd.DataFrame | None,
    *,
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> dict[str, int]:
    summary = {
        "created": 0,
        "updated": 0,
        "existing": 0,
    }

    if jobs is None or jobs.empty:
        return summary

    for _, row in jobs.iterrows():
        result = track_job(
            row.to_dict(),
            stage="Saved",
            notes="Discovered from CareerPilot Job Search.",
            crm_path=crm_path,
        )

        if result["created"]:
            summary["created"] += 1
        elif result["updated"]:
            summary["updated"] += 1
        else:
            summary["existing"] += 1

    return summary


def build_live_search_editor(
    jobs: pd.DataFrame | None,
    *,
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> tuple[pd.DataFrame, int]:
    actionable, hidden = filter_actionable_search_results(
        jobs,
        load_crm(crm_path),
        crm_path=crm_path,
    )

    columns = [
        "record_id",
        "match_score",
        "company",
        "title",
        "site",
        "location",
        "date_posted",
        "job_url",
        "stage",
    ]

    if actionable is None or actionable.empty:
        return pd.DataFrame(columns=columns), hidden

    crm_records = load_crm(crm_path)
    by_url = {
        _normalise_url(record.get("job_link")): record
        for record in crm_records
        if _normalise_url(record.get("job_link"))
    }

    rows: list[dict[str, Any]] = []

    for _, job in actionable.iterrows():
        url = _normalise_url(job.get("job_url") or job.get("job_link"))
        record = by_url.get(url, {})

        rows.append(
            {
                "record_id": _clean(record.get("record_id")),
                "match_score": int(float(job.get("match_score") or 0)),
                "company": _clean(job.get("company")) or "Unknown Company",
                "title": _clean(job.get("title") or job.get("role")) or "Unknown Role",
                "site": _clean(job.get("site") or job.get("source")) or "Unknown",
                "location": _clean(job.get("location")) or "Not provided",
                "date_posted": job.get("date_posted"),
                "job_url": _clean(job.get("job_url") or job.get("job_link")),
                "stage": _clean(record.get("stage")) or "Saved",
            }
        )

    frame = pd.DataFrame(rows)
    frame = frame.sort_values(
        by=["match_score", "date_posted"],
        ascending=[False, False],
        na_position="last",
    ).reset_index(drop=True)

    return frame, hidden


def persist_live_search_statuses(
    original: pd.DataFrame,
    edited: pd.DataFrame,
    *,
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> dict[str, int]:
    return persist_fresh_opportunity_statuses(
        original,
        edited,
        crm_path=crm_path,
    )


__all__ = [
    "FRESH_EDITOR_STAGES",
    "build_live_search_editor",
    "persist_live_search_statuses",
    "sync_search_results_to_crm",
]
