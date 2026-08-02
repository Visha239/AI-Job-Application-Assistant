from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd

from app.services.application_crm import (
    crm_metrics,
    load_crm,
)
from app.services.application_tracking import (
    mark_job_applied,
    track_job,
    track_ranked_jobs,
)


def sample_job(url: str = "https://example.com/jobs/1") -> dict:
    return {
        "title": "Data Analyst",
        "company": "Example Analytics",
        "location": "Bengaluru",
        "site": "company-careers",
        "job_url": url,
        "match_score": 88,
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        crm_path = Path(temp_dir) / "application_crm.json"

        first = track_job(
            sample_job(),
            stage="Saved",
            crm_path=crm_path,
        )
        assert first["created"] is True

        duplicate = track_job(
            sample_job(),
            stage="Saved",
            crm_path=crm_path,
        )
        assert duplicate["created"] is False
        assert duplicate["updated"] is False
        assert len(load_crm(crm_path)) == 1

        applied = mark_job_applied(
            sample_job(),
            crm_path=crm_path,
        )
        assert applied["updated"] is True
        assert applied["record"]["stage"] == "Applied"
        assert applied["record"]["applied_date"]

        frame = pd.DataFrame(
            [
                sample_job(),
                sample_job("https://example.com/jobs/2"),
            ]
        )
        bulk = track_ranked_jobs(
            frame,
            crm_path=crm_path,
        )
        assert bulk["created"] == 1
        assert bulk["existing"] == 1

        records = load_crm(crm_path)
        metrics = crm_metrics(records)
        assert metrics["total"] == 2
        assert metrics["applications_sent"] == 1
        assert metrics["applied_today"] == 1

    print("=" * 72)
    print("CAREERPILOT SPRINT 20 AUTOMATIC APPLICATION TRACKING TEST")
    print("=" * 72)
    print("Automatic discovery tracking: PASS")
    print("Duplicate prevention: PASS")
    print("One-click applied status: PASS")
    print("Dashboard metrics source: PASS")
    print()
    print("SPRINT 20 AUTOMATIC APPLICATION TRACKING TEST PASSED")


if __name__ == "__main__":
    main()
