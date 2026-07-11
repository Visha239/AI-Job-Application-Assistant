from __future__ import annotations

from collections import Counter
from typing import Any

from app.database.database import database


def _count(query: str, params: tuple = ()) -> int:
    row = database.fetchone(query, params)
    return int(row["total"]) if row else 0


def get_dashboard_metrics() -> dict[str, Any]:
    total_applications = _count(
        "SELECT COUNT(*) AS total FROM applications"
    )

    applied = _count(
        """
        SELECT COUNT(*) AS total
        FROM applications
        WHERE LOWER(status) = 'applied'
        """
    )

    interviews = _count(
        """
        SELECT COUNT(*) AS total
        FROM applications
        WHERE LOWER(status) = 'interview'
        """
    )

    offers = _count(
        """
        SELECT COUNT(*) AS total
        FROM applications
        WHERE LOWER(status) = 'offer'
        """
    )

    ready_to_apply = _count(
        """
        SELECT COUNT(*) AS total
        FROM applications
        WHERE LOWER(status) = 'ready to apply'
        """
    )

    saved_jobs = _count(
        "SELECT COUNT(*) AS total FROM jobs"
    )

    generated_resumes = _count(
        "SELECT COUNT(*) AS total FROM resumes"
    )

    interview_rate = (
        round((interviews / applied) * 100, 1)
        if applied > 0
        else 0.0
    )

    offer_rate = (
        round((offers / applied) * 100, 1)
        if applied > 0
        else 0.0
    )

    average_match_row = database.fetchone(
        """
        SELECT AVG(match_score) AS average_score
        FROM jobs
        """
    )

    average_match_score = 0.0

    if (
        average_match_row
        and average_match_row["average_score"] is not None
    ):
        average_match_score = round(
            float(average_match_row["average_score"]),
            1,
        )

    return {
        "total_applications": total_applications,
        "applied": applied,
        "interviews": interviews,
        "offers": offers,
        "ready_to_apply": ready_to_apply,
        "saved_jobs": saved_jobs,
        "generated_resumes": generated_resumes,
        "interview_rate": interview_rate,
        "offer_rate": offer_rate,
        "average_match_score": average_match_score,
    }


def get_status_distribution() -> list[dict[str, Any]]:
    rows = database.fetchall(
        """
        SELECT status, COUNT(*) AS total
        FROM applications
        GROUP BY status
        ORDER BY total DESC
        """
    )

    return [dict(row) for row in rows]


def get_recent_applications(limit: int = 10) -> list[dict[str, Any]]:
    rows = database.fetchall(
        """
        SELECT
            company,
            role,
            location,
            status,
            applied_date,
            job_link
        FROM applications
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )

    return [dict(row) for row in rows]


def get_top_matched_skills(limit: int = 8) -> list[dict[str, Any]]:
    rows = database.fetchall(
        """
        SELECT required_skills
        FROM jobs
        WHERE required_skills IS NOT NULL
          AND TRIM(required_skills) != ''
        """
    )

    counter: Counter[str] = Counter()

    for row in rows:
        skill_text = str(row["required_skills"] or "")

        for skill in skill_text.split(","):
            cleaned = skill.strip()

            if cleaned:
                counter[cleaned] += 1

    return [
        {"skill": skill, "count": count}
        for skill, count in counter.most_common(limit)
    ]