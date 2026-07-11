from __future__ import annotations

from typing import Any

from app.database.database import database


def is_job_saved(job_url: str) -> bool:
    """Return True when the job URL already exists in the database."""
    if not job_url:
        return False

    row = database.fetchone(
        """
        SELECT id
        FROM jobs
        WHERE job_link = ?
        LIMIT 1
        """,
        (job_url,),
    )

    return row is not None


def save_job(job: dict[str, Any]) -> bool:
    """
    Save one ranked job.

    Returns:
        True when saved.
        False when it already exists.
    """
    job_url = str(job.get("job_url") or "").strip()

    if job_url and is_job_saved(job_url):
        return False

    matched_skills = str(job.get("matched_skills") or "")

    database.add_job(
        company=str(job.get("company") or "Unknown Company"),
        role=str(job.get("title") or "Unknown Role"),
        location=str(job.get("location") or ""),
        job_link=job_url,
        source=str(job.get("site") or ""),
        required_skills=matched_skills,
        match_score=float(job.get("match_score") or 0),
    )

    return True


def get_saved_jobs() -> list[dict[str, Any]]:
    """Return saved jobs as normal dictionaries."""
    rows = database.get_jobs()
    return [dict(row) for row in rows]


def get_saved_job_count() -> int:
    row = database.fetchone(
        """
        SELECT COUNT(*) AS total
        FROM jobs
        """
    )

    return int(row["total"]) if row else 0