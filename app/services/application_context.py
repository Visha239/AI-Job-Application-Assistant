from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SELECTED_JOB_KEY = "careerpilot_selected_job"
DEFAULT_CONTEXT_PATH = Path("data/current_job_context.json")


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


def build_job_context(job: dict[str, Any]) -> dict[str, Any]:
    description = _clean(
        job.get("description")
        or job.get("job_description")
    )

    return {
        "company": _clean(job.get("company")),
        "job_role": _clean(
            job.get("title")
            or job.get("job_role")
            or job.get("role")
        ),
        "location": _clean(job.get("location")),
        "job_link": _clean(
            job.get("job_url")
            or job.get("job_link")
        ),
        "job_description": description,
        "description_status": _clean(
            job.get("description_status")
        )
        or (
            "available"
            if len(description) >= 250
            else "missing_or_partial"
        ),
        "source": _clean(
            job.get("site")
            or job.get("source")
        ),
        "match_score": _as_score(
            job.get("match_score")
        ),
        "priority": _clean(job.get("priority")),
        "apply_urgency": _clean(
            job.get("apply_urgency")
        ),
        "matched_skills": _clean(
            job.get("matched_skills")
        ),
        "missing_skills": _clean(
            job.get("missing_job_skills")
            or job.get("missing_profile_skills")
            or job.get("missing_skills")
        ),
        "resume_version": _clean(
            job.get("resume_version")
            or "Data Analyst Resume"
        ),
    }


def context_fingerprint(
    context: dict[str, Any],
) -> str:
    return "|".join(
        [
            _clean(context.get("company")),
            _clean(context.get("job_role")),
            _clean(context.get("job_link")),
        ]
    )


def persist_job_context(
    context: dict[str, Any],
    *,
    context_path: str | Path = DEFAULT_CONTEXT_PATH,
) -> None:
    path = Path(context_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            context,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def load_persisted_job_context(
    *,
    context_path: str | Path = DEFAULT_CONTEXT_PATH,
) -> dict[str, Any]:
    path = Path(context_path)

    if not path.exists():
        return {}

    try:
        raw = path.read_text(
            encoding="utf-8-sig"
        ).strip()

        if not raw:
            return {}

        data = json.loads(raw)

    except (OSError, json.JSONDecodeError):
        return {}

    return data if isinstance(data, dict) else {}


def save_selected_job(
    session_state: Any,
    job: dict[str, Any],
    *,
    context_path: str | Path = DEFAULT_CONTEXT_PATH,
) -> dict[str, Any]:
    context = build_job_context(job)
    session_state[SELECTED_JOB_KEY] = context
    persist_job_context(
        context,
        context_path=context_path,
    )
    return context


def get_selected_job(
    session_state: Any,
    *,
    context_path: str | Path = DEFAULT_CONTEXT_PATH,
) -> dict[str, Any]:
    session_context = session_state.get(
        SELECTED_JOB_KEY,
        {},
    )

    if isinstance(session_context, dict) and session_context:
        return dict(session_context)

    persisted = load_persisted_job_context(
        context_path=context_path
    )

    if persisted:
        session_state[SELECTED_JOB_KEY] = persisted

    return dict(persisted)


def update_selected_job(
    session_state: Any,
    updates: dict[str, Any],
    *,
    context_path: str | Path = DEFAULT_CONTEXT_PATH,
) -> dict[str, Any]:
    current = get_selected_job(
        session_state,
        context_path=context_path,
    )

    merged = dict(current)
    merged.update(
        {
            key: value
            for key, value in updates.items()
            if value is not None
        }
    )

    context = build_job_context(merged)
    session_state[SELECTED_JOB_KEY] = context
    persist_job_context(
        context,
        context_path=context_path,
    )

    return context


def clear_selected_job(
    session_state: Any,
    *,
    remove_persisted: bool = False,
    context_path: str | Path = DEFAULT_CONTEXT_PATH,
) -> None:
    session_state.pop(SELECTED_JOB_KEY, None)

    if remove_persisted:
        path = Path(context_path)

        if path.exists():
            path.unlink()
