from __future__ import annotations

from typing import Any


SELECTED_JOB_KEY = "careerpilot_selected_job"


def build_job_context(job: dict[str, Any]) -> dict[str, Any]:
    """Normalize a searched job before sending it to Apply Workflow."""

    return {
        "company": str(job.get("company") or "").strip(),
        "job_role": str(job.get("title") or "").strip(),
        "location": str(job.get("location") or "").strip(),
        "job_link": str(job.get("job_url") or "").strip(),
        "job_description": str(job.get("description") or "").strip(),
        "source": str(job.get("site") or "").strip(),
        "match_score": int(float(job.get("match_score") or 0)),
        "matched_skills": str(job.get("matched_skills") or "").strip(),
        "missing_skills": str(
            job.get("missing_profile_skills") or ""
        ).strip(),
        "resume_version": str(
            job.get("resume_version") or "Data Analyst Resume"
        ).strip(),
    }


def save_selected_job(session_state: Any, job: dict[str, Any]) -> None:
    session_state[SELECTED_JOB_KEY] = build_job_context(job)


def get_selected_job(session_state: Any) -> dict[str, Any]:
    return dict(session_state.get(SELECTED_JOB_KEY, {}))


def clear_selected_job(session_state: Any) -> None:
    session_state.pop(SELECTED_JOB_KEY, None)