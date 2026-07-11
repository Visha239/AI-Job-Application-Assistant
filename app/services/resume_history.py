from __future__ import annotations

from pathlib import Path
from typing import Any

from app.database.database import database


def save_resume_version(
    resume_name: str,
    role_type: str,
    file_path: str,
    ats_score: float,
) -> None:
    path = Path(file_path)

    database.add_resume(
        resume_name=resume_name,
        role_type=role_type,
        file_path=str(path),
        ats_score=float(ats_score),
    )


def get_resume_history() -> list[dict[str, Any]]:
    rows = database.get_resumes()
    return [dict(row) for row in rows]


def get_resume_count() -> int:
    row = database.fetchone(
        """
        SELECT COUNT(*) AS total
        FROM resumes
        """
    )

    return int(row["total"]) if row else 0