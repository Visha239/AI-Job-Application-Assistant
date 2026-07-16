from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


DEFAULT_CRM_PATH = Path("data/application_crm.json")
DEFAULT_EXPORT_PATH = Path(
    "exports/application_crm/application_crm.csv"
)

STAGES = [
    "Saved",
    "Ready to Apply",
    "Applied",
    "Recruiter Contacted",
    "HR Round",
    "Technical Round",
    "Manager Round",
    "Offer",
    "Rejected",
    "Joined",
]

ACTIVE_STAGES = {
    "Applied",
    "Recruiter Contacted",
    "HR Round",
    "Technical Round",
    "Manager Round",
    "Offer",
}

CLOSED_STAGES = {
    "Rejected",
    "Joined",
}


def _clean(value: Any) -> str:
    if value is None:
        return ""

    text = str(value).strip()

    if text.lower() in {"", "none", "nan", "null"}:
        return ""

    return text


def _as_score(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _record_id(
    company: str,
    role: str,
    job_link: str,
) -> str:
    raw = job_link or f"{company}|{role}"
    cleaned = "".join(
        char.lower() if char.isalnum() else "_"
        for char in raw
    )

    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")

    cleaned = cleaned.strip("_") or "application"

    return (
        f"{cleaned}_"
        f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    )


def load_crm(
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> list[dict[str, Any]]:
    path = Path(crm_path)

    if not path.exists():
        return []

    try:
        raw = path.read_text(
            encoding="utf-8-sig"
        ).strip()

        if not raw:
            return []

        data = json.loads(raw)

    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(data, list):
        return []

    return [
        item
        for item in data
        if isinstance(item, dict)
    ]


def save_crm(
    records: list[dict[str, Any]],
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> None:
    path = Path(crm_path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        json.dumps(
            records,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def add_application(
    *,
    company: str,
    role: str,
    location: str = "",
    source: str = "",
    job_link: str = "",
    stage: str = "Applied",
    match_score: int = 0,
    recruiter_name: str = "",
    recruiter_email: str = "",
    notes: str = "",
    applied_date: str = "",
    next_follow_up_date: str = "",
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> dict[str, Any]:
    company = _clean(company)
    role = _clean(role)

    if not company:
        raise ValueError("Company is required.")

    if not role:
        raise ValueError("Role is required.")

    if stage not in STAGES:
        raise ValueError(
            f"Invalid stage: {stage}"
        )

    records = load_crm(crm_path)

    if any(
        _clean(record.get("job_link"))
        and _clean(record.get("job_link"))
        == _clean(job_link)
        for record in records
    ):
        raise ValueError(
            "This job link is already tracked."
        )

    today = date.today()

    if not applied_date and stage not in {
        "Saved",
        "Ready to Apply",
    }:
        applied_date = today.isoformat()

    if (
        not next_follow_up_date
        and stage in {
            "Applied",
            "Recruiter Contacted",
        }
    ):
        next_follow_up_date = (
            today + timedelta(days=5)
        ).isoformat()

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    record = {
        "record_id": _record_id(
            company,
            role,
            _clean(job_link),
        ),
        "company": company,
        "role": role,
        "location": _clean(location),
        "source": _clean(source),
        "job_link": _clean(job_link),
        "stage": stage,
        "match_score": _as_score(
            match_score
        ),
        "recruiter_name": _clean(
            recruiter_name
        ),
        "recruiter_email": _clean(
            recruiter_email
        ),
        "notes": _clean(notes),
        "applied_date": _clean(
            applied_date
        ),
        "next_follow_up_date": _clean(
            next_follow_up_date
        ),
        "last_follow_up_date": "",
        "interview_date": "",
        "interview_feedback": "",
        "created_at": now,
        "updated_at": now,
    }

    records.append(record)
    save_crm(records, crm_path)

    return record


def update_application(
    record_id: str,
    *,
    crm_path: str | Path = DEFAULT_CRM_PATH,
    **updates: Any,
) -> dict[str, Any]:
    records = load_crm(crm_path)

    allowed_fields = {
        "company",
        "role",
        "location",
        "source",
        "job_link",
        "stage",
        "match_score",
        "recruiter_name",
        "recruiter_email",
        "notes",
        "applied_date",
        "next_follow_up_date",
        "last_follow_up_date",
        "interview_date",
        "interview_feedback",
    }

    for record in records:
        if record.get("record_id") != record_id:
            continue

        for key, value in updates.items():
            if key not in allowed_fields:
                continue

            if key == "stage":
                if value not in STAGES:
                    raise ValueError(
                        f"Invalid stage: {value}"
                    )
                record[key] = value
            elif key == "match_score":
                record[key] = _as_score(
                    value
                )
            else:
                record[key] = _clean(
                    value
                )

        if (
            record.get("stage")
            not in {
                "Saved",
                "Ready to Apply",
            }
            and not record.get(
                "applied_date"
            )
        ):
            record["applied_date"] = (
                date.today().isoformat()
            )

        record["updated_at"] = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )

        save_crm(records, crm_path)
        return record

    raise ValueError(
        "Application record was not found."
    )


def delete_application(
    record_id: str,
    *,
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> bool:
    records = load_crm(crm_path)

    updated = [
        record
        for record in records
        if record.get("record_id")
        != record_id
    ]

    if len(updated) == len(records):
        return False

    save_crm(updated, crm_path)
    return True


def get_due_follow_ups(
    records: list[dict[str, Any]] | None = None,
    *,
    on_date: date | None = None,
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> list[dict[str, Any]]:
    items = (
        records
        if records is not None
        else load_crm(crm_path)
    )

    target = on_date or date.today()
    due: list[dict[str, Any]] = []

    for record in items:
        if record.get("stage") in CLOSED_STAGES:
            continue

        follow_up_text = _clean(
            record.get(
                "next_follow_up_date"
            )
        )

        if not follow_up_text:
            continue

        try:
            follow_up = date.fromisoformat(
                follow_up_text
            )
        except ValueError:
            continue

        if follow_up <= target:
            due.append(record)

    return sorted(
        due,
        key=lambda item: item.get(
            "next_follow_up_date",
            "",
        ),
    )


def crm_metrics(
    records: list[dict[str, Any]] | None = None,
    *,
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> dict[str, Any]:
    items = (
        records
        if records is not None
        else load_crm(crm_path)
    )

    stage_counts = Counter(
        record.get("stage", "")
        for record in items
    )

    applications_sent = sum(
        1
        for record in items
        if record.get("stage")
        not in {
            "Saved",
            "Ready to Apply",
        }
    )

    responses = sum(
        1
        for record in items
        if record.get("stage")
        in {
            "Recruiter Contacted",
            "HR Round",
            "Technical Round",
            "Manager Round",
            "Offer",
            "Joined",
        }
    )

    interviews = sum(
        1
        for record in items
        if record.get("stage")
        in {
            "HR Round",
            "Technical Round",
            "Manager Round",
            "Offer",
            "Joined",
        }
    )

    today_text = date.today().isoformat()

    applied_today = sum(
        1
        for record in items
        if record.get("applied_date")
        == today_text
    )

    response_rate = (
        round(
            responses
            / applications_sent
            * 100,
            1,
        )
        if applications_sent
        else 0.0
    )

    return {
        "total": len(items),
        "applications_sent": (
            applications_sent
        ),
        "applied_today": (
            applied_today
        ),
        "interviews": interviews,
        "offers": stage_counts[
            "Offer"
        ],
        "rejected": stage_counts[
            "Rejected"
        ],
        "awaiting_reply": sum(
            1
            for record in items
            if record.get("stage")
            in {
                "Applied",
                "Recruiter Contacted",
            }
        ),
        "response_rate": response_rate,
        "stage_counts": dict(
            stage_counts
        ),
    }


def source_analytics(
    records: list[dict[str, Any]] | None = None,
    *,
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> list[dict[str, Any]]:
    items = (
        records
        if records is not None
        else load_crm(crm_path)
    )

    grouped: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(list)

    for record in items:
        source = (
            _clean(record.get("source"))
            or "Unknown"
        )
        grouped[source].append(record)

    analytics: list[dict[str, Any]] = []

    for source, source_records in (
        grouped.items()
    ):
        applications = sum(
            1
            for record in source_records
            if record.get("stage")
            not in {
                "Saved",
                "Ready to Apply",
            }
        )

        responses = sum(
            1
            for record in source_records
            if record.get("stage")
            in {
                "Recruiter Contacted",
                "HR Round",
                "Technical Round",
                "Manager Round",
                "Offer",
                "Joined",
            }
        )

        response_rate = (
            round(
                responses
                / applications
                * 100,
                1,
            )
            if applications
            else 0.0
        )

        analytics.append(
            {
                "source": source,
                "applications": applications,
                "responses": responses,
                "response_rate": (
                    response_rate
                ),
            }
        )

    return sorted(
        analytics,
        key=lambda item: (
            item["response_rate"],
            item["applications"],
        ),
        reverse=True,
    )


def company_history(
    company: str,
    records: list[dict[str, Any]] | None = None,
    *,
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> list[dict[str, Any]]:
    items = (
        records
        if records is not None
        else load_crm(crm_path)
    )

    target = _clean(company).lower()

    return [
        record
        for record in items
        if _clean(
            record.get("company")
        ).lower()
        == target
    ]


def export_crm_csv(
    *,
    records: list[dict[str, Any]] | None = None,
    output_path: str | Path = DEFAULT_EXPORT_PATH,
    crm_path: str | Path = DEFAULT_CRM_PATH,
) -> str:
    items = (
        records
        if records is not None
        else load_crm(crm_path)
    )

    path = Path(output_path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "company",
        "role",
        "location",
        "source",
        "stage",
        "match_score",
        "applied_date",
        "next_follow_up_date",
        "last_follow_up_date",
        "recruiter_name",
        "recruiter_email",
        "interview_date",
        "interview_feedback",
        "job_link",
        "notes",
        "created_at",
        "updated_at",
    ]

    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )
        writer.writeheader()

        for record in items:
            writer.writerow(
                {
                    field: record.get(
                        field,
                        "",
                    )
                    for field in fieldnames
                }
            )

    return str(path)
