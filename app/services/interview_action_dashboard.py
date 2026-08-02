from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from app.services.application_crm import (
    DEFAULT_CRM_PATH,
    STAGES,
    load_crm,
    update_application,
)


FRESH_STAGES = {
    "Saved",
    "Ready to Apply",
}

APPLICATION_STAGES = {
    "Applied",
    "Recruiter Contacted",
    "HR Round",
    "Technical Round",
    "Manager Round",
    "Offer",
    "Rejected",
    "Joined",
}

FRESH_EDITOR_STAGES = [
    "Saved",
    "Ready to Apply",
    "Applied",
]

APPLICATION_EDITOR_STAGES = [
    "Applied",
    "Recruiter Contacted",
    "HR Round",
    "Technical Round",
    "Manager Round",
    "Offer",
    "Rejected",
    "Joined",
]


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


def _normalise_text(value: Any) -> str:
    return " ".join(_clean(value).lower().split())


def _score(value: Any) -> int:
    try:
        return max(0, min(100, int(float(value or 0))))
    except (TypeError, ValueError):
        return 0


def _record_row(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": _clean(record.get("record_id")),
        "match_score": _score(record.get("match_score")),
        "company": _clean(record.get("company")) or "Unknown Company",
        "role": _clean(record.get("role")) or "Unknown Role",
        "source": _clean(record.get("source")) or "Unknown",
        "location": _clean(record.get("location")) or "Not provided",
        "stage": _clean(record.get("stage")) or "Saved",
        "job_link": _clean(record.get("job_link")),
        "applied_date": _clean(record.get("applied_date")),
        "updated_at": _clean(record.get("updated_at")),
    }


def build_fresh_opportunity_table(
    records: list[dict[str, Any]] | None = None,
    *,
    crm_path: str | Path = DEFAULT_CRM_PATH,
    limit: int = 30,
) -> pd.DataFrame:
    items = records if records is not None else load_crm(crm_path)
    rows = [
        _record_row(record)
        for record in items
        if (_clean(record.get("stage")) or "Saved") in FRESH_STAGES
        and _clean(record.get("job_link"))
    ]

    rows.sort(
        key=lambda item: (
            item["match_score"],
            item["updated_at"],
        ),
        reverse=True,
    )
    return pd.DataFrame(rows[: max(1, int(limit))])


def build_application_tracker_table(
    records: list[dict[str, Any]] | None = None,
    *,
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> pd.DataFrame:
    items = records if records is not None else load_crm(crm_path)
    rows = [
        _record_row(record)
        for record in items
        if (_clean(record.get("stage")) or "Saved") in APPLICATION_STAGES
    ]

    rows.sort(
        key=lambda item: (
            item["applied_date"],
            item["updated_at"],
        ),
        reverse=True,
    )
    return pd.DataFrame(rows)


def application_summary(
    records: list[dict[str, Any]] | None = None,
    *,
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> dict[str, int]:
    items = records if records is not None else load_crm(crm_path)
    today = date.today().isoformat()

    return {
        "fresh": sum(
            1
            for record in items
            if (_clean(record.get("stage")) or "Saved") in FRESH_STAGES
        ),
        "applied_total": sum(
            1
            for record in items
            if (_clean(record.get("stage")) or "Saved")
            in APPLICATION_STAGES
        ),
        "applied_today": sum(
            1
            for record in items
            if _clean(record.get("applied_date")) == today
        ),
        "interviews": sum(
            1
            for record in items
            if _clean(record.get("stage"))
            in {
                "HR Round",
                "Technical Round",
                "Manager Round",
                "Offer",
                "Joined",
            }
        ),
        "offers": sum(
            1
            for record in items
            if _clean(record.get("stage")) == "Offer"
        ),
    }


def _persist_editor(
    original: pd.DataFrame,
    edited: pd.DataFrame,
    *,
    allowed_stages: list[str],
    crm_path: str | Path,
) -> dict[str, int]:
    summary = {
        "updated": 0,
        "unchanged": 0,
        "errors": 0,
    }

    if original is None or original.empty:
        return summary

    original_map = {
        _clean(row["record_id"]): row
        for _, row in original.iterrows()
    }

    for _, edited_row in edited.iterrows():
        record_id = _clean(edited_row.get("record_id"))
        old_row = original_map.get(record_id)

        if old_row is None:
            summary["errors"] += 1
            continue

        old_stage = _clean(old_row.get("stage")) or "Saved"
        new_stage = _clean(edited_row.get("stage")) or old_stage

        if new_stage not in allowed_stages or new_stage not in STAGES:
            summary["errors"] += 1
            continue

        if new_stage == old_stage:
            summary["unchanged"] += 1
            continue

        updates: dict[str, Any] = {"stage": new_stage}

        if new_stage in APPLICATION_STAGES:
            updates["applied_date"] = (
                _clean(old_row.get("applied_date"))
                or date.today().isoformat()
            )

        try:
            update_application(
                record_id,
                crm_path=crm_path,
                **updates,
            )
            summary["updated"] += 1
        except (OSError, ValueError):
            summary["errors"] += 1

    return summary


def persist_fresh_opportunity_statuses(
    original: pd.DataFrame,
    edited: pd.DataFrame,
    *,
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> dict[str, int]:
    return _persist_editor(
        original,
        edited,
        allowed_stages=FRESH_EDITOR_STAGES,
        crm_path=crm_path,
    )


def persist_application_statuses(
    original: pd.DataFrame,
    edited: pd.DataFrame,
    *,
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> dict[str, int]:
    return _persist_editor(
        original,
        edited,
        allowed_stages=APPLICATION_EDITOR_STAGES,
        crm_path=crm_path,
    )


def filter_actionable_search_results(
    jobs: pd.DataFrame | None,
    records: list[dict[str, Any]] | None = None,
    *,
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> tuple[pd.DataFrame, int]:
    if jobs is None or jobs.empty:
        return pd.DataFrame() if jobs is None else jobs.copy(), 0

    items = records if records is not None else load_crm(crm_path)

    blocked_urls = {
        _normalise_url(record.get("job_link"))
        for record in items
        if (_clean(record.get("stage")) or "Saved") in APPLICATION_STAGES
        and _normalise_url(record.get("job_link"))
    }

    blocked_company_roles = {
        (
            _normalise_text(record.get("company")),
            _normalise_text(record.get("role")),
        )
        for record in items
        if (_clean(record.get("stage")) or "Saved") in APPLICATION_STAGES
    }

    keep_indices: list[Any] = []

    for index, row in jobs.iterrows():
        url = _normalise_url(
            row.get("job_url")
            or row.get("job_link")
        )
        company_role = (
            _normalise_text(row.get("company")),
            _normalise_text(
                row.get("title")
                or row.get("role")
            ),
        )

        already_applied = (
            bool(url and url in blocked_urls)
            or (
                company_role[0]
                and company_role[1]
                and company_role in blocked_company_roles
            )
        )

        if not already_applied:
            keep_indices.append(index)

    filtered = jobs.loc[keep_indices].copy().reset_index(drop=True)
    return filtered, len(jobs) - len(filtered)
