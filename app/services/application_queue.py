from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_QUEUE_PATH = Path("data/application_queue.json")
DEFAULT_EXPORT_PATH = Path("exports/application_queue/application_queue.csv")
VALID_STATUSES = {"Queued", "Ready to Apply", "Applied", "Skipped"}

def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"", "none", "nan", "null"} else text

def _as_score(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0

def _safe_key(company: str, role: str, job_link: str) -> str:
    source = job_link or f"{company}|{role}"
    key = re.sub(r"[^a-z0-9]+", "_", source.lower()).strip("_")
    return key or "application"

def normalise_job(job: dict[str, Any]) -> dict[str, Any]:
    company = _clean(job.get("company"))
    role = _clean(job.get("title") or job.get("job_role") or job.get("role"))
    job_link = _clean(job.get("job_url") or job.get("job_link"))
    description = _clean(job.get("description") or job.get("job_description"))
    return {
        "queue_id": _safe_key(company, role, job_link),
        "company": company or "Unknown Company",
        "role": role or "Unknown Role",
        "location": _clean(job.get("location")),
        "job_link": job_link,
        "job_description": description,
        "source": _clean(job.get("site") or job.get("source")),
        "match_score": _as_score(job.get("match_score")),
        "priority": _clean(job.get("priority")),
        "apply_urgency": _clean(job.get("apply_urgency")),
        "freshness_label": _clean(job.get("freshness_label")),
        "matched_skills": _clean(job.get("matched_skills")),
        "missing_skills": _clean(job.get("missing_job_skills") or job.get("missing_profile_skills") or job.get("missing_skills")),
        "resume_version": _clean(job.get("resume_version") or "Data Analyst Resume"),
    }

def load_queue(queue_path: str | Path = DEFAULT_QUEUE_PATH) -> list[dict[str, Any]]:
    path = Path(queue_path)
    if not path.exists():
        return []
    try:
        raw = path.read_text(encoding="utf-8-sig").strip()
        if not raw:
            return []
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return []
    return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []

def save_queue(queue: list[dict[str, Any]], queue_path: str | Path = DEFAULT_QUEUE_PATH) -> None:
    path = Path(queue_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")

def add_jobs_to_queue(jobs: list[dict[str, Any]], *, queue_path: str | Path = DEFAULT_QUEUE_PATH) -> dict[str, Any]:
    queue = load_queue(queue_path)
    existing_ids = {item.get("queue_id") for item in queue}
    added = duplicates = 0
    now = datetime.now().isoformat(timespec="seconds")
    for raw_job in jobs:
        job = normalise_job(raw_job)
        if job["queue_id"] in existing_ids:
            duplicates += 1
            continue
        queue_item = {**job, "status": "Queued", "added_at": now, "updated_at": now, "applied_at": "", "notes": ""}
        queue.append(queue_item)
        existing_ids.add(queue_item["queue_id"])
        added += 1
    save_queue(queue, queue_path)
    return {"added": added, "duplicates": duplicates, "total": len(queue), "queue": queue}

def update_queue_item(queue_id: str, *, status: str | None = None, notes: str | None = None, queue_path: str | Path = DEFAULT_QUEUE_PATH) -> dict[str, Any]:
    queue = load_queue(queue_path)
    if status is not None and status not in VALID_STATUSES:
        raise ValueError(f"Invalid queue status: {status}")
    for item in queue:
        if item.get("queue_id") != queue_id:
            continue
        if status is not None:
            item["status"] = status
            if status == "Applied":
                item["applied_at"] = datetime.now().isoformat(timespec="seconds")
        if notes is not None:
            item["notes"] = _clean(notes)
        item["updated_at"] = datetime.now().isoformat(timespec="seconds")
        save_queue(queue, queue_path)
        return item
    raise ValueError("Application queue item was not found.")

def remove_queue_item(queue_id: str, *, queue_path: str | Path = DEFAULT_QUEUE_PATH) -> bool:
    queue = load_queue(queue_path)
    updated = [item for item in queue if item.get("queue_id") != queue_id]
    if len(updated) == len(queue):
        return False
    save_queue(updated, queue_path)
    return True

def queue_summary(queue: list[dict[str, Any]] | None = None, *, queue_path: str | Path = DEFAULT_QUEUE_PATH) -> dict[str, int]:
    items = queue if queue is not None else load_queue(queue_path)
    summary = {"total": len(items), "queued": 0, "ready": 0, "applied": 0, "skipped": 0}
    mapping = {"Queued": "queued", "Ready to Apply": "ready", "Applied": "applied", "Skipped": "skipped"}
    for item in items:
        key = mapping.get(item.get("status"))
        if key:
            summary[key] += 1
    return summary

def get_active_queue(queue: list[dict[str, Any]] | None = None, *, queue_path: str | Path = DEFAULT_QUEUE_PATH) -> list[dict[str, Any]]:
    items = queue if queue is not None else load_queue(queue_path)
    active = [item for item in items if item.get("status") in {"Queued", "Ready to Apply"}]
    return sorted(active, key=lambda item: (item.get("match_score", 0), item.get("added_at", "")), reverse=True)

def export_queue_csv(*, queue: list[dict[str, Any]] | None = None, output_path: str | Path = DEFAULT_EXPORT_PATH, queue_path: str | Path = DEFAULT_QUEUE_PATH) -> str:
    items = queue if queue is not None else load_queue(queue_path)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["company", "role", "location", "source", "match_score", "priority", "apply_urgency", "freshness_label", "status", "job_link", "resume_version", "matched_skills", "missing_skills", "added_at", "updated_at", "applied_at", "notes"]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow({field: item.get(field, "") for field in fieldnames})
    return str(path)
