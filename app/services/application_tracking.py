from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from app.services.application_crm import (
    DEFAULT_CRM_PATH,
    add_application,
    load_crm,
    update_application,
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


def _job_value(job: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = _clean(job.get(key))
        if value:
            return value
    return ""


def find_tracked_application(
    *,
    job_link: str = "",
    company: str = "",
    role: str = "",
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> dict[str, Any] | None:
    records = load_crm(crm_path)
    target_url = _normalise_url(job_link)
    target_company = _clean(company).lower()
    target_role = _clean(role).lower()

    for record in records:
        record_url = _normalise_url(record.get("job_link"))

        if target_url and record_url == target_url:
            return record

        if (
            not target_url
            and target_company
            and target_role
            and _clean(record.get("company")).lower() == target_company
            and _clean(record.get("role")).lower() == target_role
        ):
            return record

    return None


def track_job(
    job: dict[str, Any],
    *,
    stage: str = "Saved",
    notes: str = "",
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> dict[str, Any]:
    company = _job_value(job, "company") or "Unknown Company"
    role = _job_value(job, "title", "role", "job_role") or "Unknown Role"
    location = _job_value(job, "location")
    source = _job_value(job, "site", "source", "source_label")
    job_link = _job_value(job, "job_url", "job_link")
    score_value = job.get("match_score", 0)

    try:
        match_score = int(float(score_value or 0))
    except (TypeError, ValueError):
        match_score = 0

    existing = find_tracked_application(
        job_link=job_link,
        company=company,
        role=role,
        crm_path=crm_path,
    )

    if existing:
        current_stage = _clean(existing.get("stage")) or "Saved"
        updates: dict[str, Any] = {}

        # Never move an application backwards from a meaningful stage.
        if stage == "Applied" and current_stage in {"Saved", "Ready to Apply"}:
            updates["stage"] = "Applied"
            updates["applied_date"] = date.today().isoformat()
        elif stage == "Ready to Apply" and current_stage == "Saved":
            updates["stage"] = "Ready to Apply"

        if match_score > int(existing.get("match_score") or 0):
            updates["match_score"] = match_score

        if notes and not _clean(existing.get("notes")):
            updates["notes"] = notes

        if updates:
            updated = update_application(
                existing["record_id"],
                crm_path=crm_path,
                **updates,
            )
            return {
                "created": False,
                "updated": True,
                "record": updated,
            }

        return {
            "created": False,
            "updated": False,
            "record": existing,
        }

    applied_date = (
        date.today().isoformat()
        if stage not in {"Saved", "Ready to Apply"}
        else ""
    )

    record = add_application(
        company=company,
        role=role,
        location=location,
        source=source,
        job_link=job_link,
        stage=stage,
        match_score=match_score,
        notes=notes,
        applied_date=applied_date,
        crm_path=crm_path,
    )

    return {
        "created": True,
        "updated": False,
        "record": record,
    }


def mark_job_applied(
    job: dict[str, Any],
    *,
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> dict[str, Any]:
    return track_job(
        job,
        stage="Applied",
        notes="Marked as applied from CareerPilot Job Search.",
        crm_path=crm_path,
    )


def track_ranked_jobs(
    ranked_jobs: pd.DataFrame | None,
    *,
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> dict[str, int]:
    summary = {
        "created": 0,
        "updated": 0,
        "existing": 0,
    }

    if ranked_jobs is None or ranked_jobs.empty:
        return summary

    for _, row in ranked_jobs.iterrows():
        result = track_job(
            row.to_dict(),
            stage="Saved",
            notes="Automatically discovered by the CareerPilot daily job search.",
            crm_path=crm_path,
        )

        if result["created"]:
            summary["created"] += 1
        elif result["updated"]:
            summary["updated"] += 1
        else:
            summary["existing"] += 1

    return summary
