from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

DEFAULT_STATE_PATH = Path("data/hourly_alert_state.json")


def _clean(value: Any) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return str(value).strip()


def job_fingerprint(job: dict[str, Any]) -> str:
    url = _clean(job.get("job_url") or job.get("job_link")).rstrip("/").lower()
    if url:
        raw = f"url:{url}"
    else:
        company = " ".join(_clean(job.get("company")).lower().split())
        title = " ".join(
            _clean(job.get("title") or job.get("role")).lower().split()
        )
        location = " ".join(_clean(job.get("location")).lower().split())
        raw = f"job:{company}|{title}|{location}"

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_alert_state(
    state_path: str | Path = DEFAULT_STATE_PATH,
) -> dict[str, Any]:
    path = Path(state_path)

    if not path.exists():
        return {
            "seen": [],
            "last_run": "",
        }

    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {
            "seen": [],
            "last_run": "",
        }

    if not isinstance(data, dict):
        return {
            "seen": [],
            "last_run": "",
        }

    seen = data.get("seen", [])
    return {
        "seen": seen if isinstance(seen, list) else [],
        "last_run": _clean(data.get("last_run")),
    }


def save_alert_state(
    state: dict[str, Any],
    state_path: str | Path = DEFAULT_STATE_PATH,
) -> None:
    path = Path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state, indent=2),
        encoding="utf-8",
    )


def select_new_priority_jobs(
    ranked_jobs: pd.DataFrame | None,
    *,
    seen: set[str] | None = None,
    minimum_score: int = 80,
    maximum_jobs: int = 20,
) -> tuple[pd.DataFrame, set[str]]:
    if ranked_jobs is None or ranked_jobs.empty:
        return pd.DataFrame(), set()

    seen_fingerprints = seen or set()
    rows: list[dict[str, Any]] = []
    discovered: set[str] = set()

    for _, row in ranked_jobs.iterrows():
        job = row.to_dict()
        fingerprint = job_fingerprint(job)
        discovered.add(fingerprint)

        try:
            score = int(float(job.get("match_score") or 0))
        except (TypeError, ValueError):
            score = 0

        if score < int(minimum_score):
            continue

        if fingerprint in seen_fingerprints:
            continue

        rows.append(job)

    if not rows:
        return pd.DataFrame(columns=ranked_jobs.columns), discovered

    result = pd.DataFrame(rows)
    result = result.sort_values(
        by=["match_score", "date_posted"],
        ascending=[False, False],
        na_position="last",
    )
    return result.head(maximum_jobs).reset_index(drop=True), discovered


def run_hourly_alert(
    *,
    state_path: str | Path = DEFAULT_STATE_PATH,
    minimum_score: int = 80,
    send_email: bool = True,
) -> dict[str, Any]:
    from app.services.daily_job_digest import (
        build_html_digest,
        run_daily_digest,
    )
    from app.services.email_digest import (
        load_email_settings,
        send_html_email,
        validate_email_settings,
    )

    state = load_alert_state(state_path)
    seen = set(state["seen"])

    digest_result = run_daily_digest()
    ranked_jobs = digest_result["ranked_jobs"]

    new_jobs, discovered = select_new_priority_jobs(
        ranked_jobs,
        seen=seen,
        minimum_score=minimum_score,
    )

    # Retain the newest fingerprints and prevent unbounded state growth.
    combined = list(dict.fromkeys(list(seen) + list(discovered)))[-10000:]
    save_alert_state(
        {
            "seen": combined,
            "last_run": datetime.now().isoformat(timespec="seconds"),
        },
        state_path,
    )

    delivery = None

    if send_email and not new_jobs.empty:
        settings = load_email_settings()
        errors = validate_email_settings(settings)
        if errors:
            raise ValueError(" ".join(errors))

        html_content = build_html_digest(new_jobs)
        subject = (
            f"CareerPilot Alert: {len(new_jobs)} new high-priority job"
            f"{'s' if len(new_jobs) != 1 else ''}"
        )
        delivery = send_html_email(
            html_content=html_content,
            subject=subject,
            settings=settings,
            text_summary=(
                f"CareerPilot found {len(new_jobs)} new job(s) with a "
                f"match score of at least {minimum_score}%."
            ),
        )

    return {
        "jobs_collected": digest_result["jobs_collected"],
        "ranked_jobs": len(ranked_jobs),
        "new_priority_jobs": len(new_jobs),
        "email_sent": bool(delivery),
        "state_path": str(state_path),
        "source_counts": digest_result.get("source_counts", {}),
        "errors": digest_result.get("errors", []),
    }
