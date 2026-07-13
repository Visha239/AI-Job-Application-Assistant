from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import tempfile

import pandas as pd

from app.services.job_discovery.ranking import rank_jobs
from app.services.multi_job_search import (
    filter_ranked_jobs,
    remove_duplicate_jobs,
)


def main() -> None:
    now = datetime(
        2026,
        7,
        12,
        10,
        0,
        tzinfo=timezone.utc,
    )

    jobs = pd.DataFrame(
        [
            {
                "site": "test",
                "title": "Data Analyst",
                "company": "Fresh Analytics",
                "location": "Bengaluru, Karnataka",
                "date_posted": now - timedelta(hours=3),
                "job_type": "fulltime",
                "is_remote": False,
                "job_url": "https://example.com/data-1",
                "description": (
                    "SQL Excel Power BI Python dashboard "
                    "0 to 2 years experience"
                ),
                "searched_role": "Data Analyst",
            },
            {
                "site": "test",
                "title": "Data Analyst",
                "company": "Fresh Analytics",
                "location": "Bengaluru, Karnataka",
                "date_posted": now - timedelta(hours=3),
                "job_type": "fulltime",
                "is_remote": False,
                "job_url": "https://example.com/data-1",
                "description": (
                    "SQL Excel Power BI Python dashboard "
                    "0 to 2 years experience"
                ),
                "searched_role": "Power BI Analyst",
            },
            {
                "site": "test",
                "title": "Senior Data Engineering Manager",
                "company": "Senior Company",
                "location": "Bengaluru, Karnataka",
                "date_posted": now - timedelta(hours=1),
                "job_type": "fulltime",
                "is_remote": False,
                "job_url": "https://example.com/senior",
                "description": (
                    "8+ years Spark Snowflake leadership"
                ),
                "searched_role": "Data Analyst",
            },
            {
                "site": "test",
                "title": "Production Support Analyst",
                "company": None,
                "location": "Remote",
                "date_posted": now - timedelta(hours=10),
                "job_type": "fulltime",
                "is_remote": True,
                "job_url": "https://example.com/support",
                "description": (
                    "SQL Linux Jira ServiceNow AWS "
                    "1 to 2 years experience"
                ),
                "searched_role": "Production Support Analyst",
            },
        ]
    )

    profile = {
        "skills": [
            "Python",
            "SQL",
            "Power BI",
            "Excel",
            "Tableau",
            "Linux",
            "ServiceNow",
            "Jira",
            "Data Analysis",
            "AWS",
        ],
        "preferred_roles": [
            "Data Analyst",
            "Business Analyst",
            "Application Support Analyst",
            "Production Support Analyst",
        ],
        "preferred_locations": [
            "Bengaluru",
            "Bangalore",
            "Remote",
        ],
        "experience_years": 1.1,
    }

    deduplicated = remove_duplicate_jobs(jobs)

    assert len(deduplicated) == 3

    with tempfile.TemporaryDirectory() as temp_dir:
        profile_path = Path(temp_dir) / "profile.json"
        profile_path.write_text(
            json.dumps(profile),
            encoding="utf-8",
        )

        ranked = rank_jobs(
            deduplicated,
            profile_path=profile_path,
            now=now,
        )

    filtered = filter_ranked_jobs(
        ranked,
        minimum_score=45,
        maximum_jobs=10,
        exclude_senior_roles=True,
    )

    assert not filtered.empty
    assert "Senior Company" not in filtered["company"].tolist()
    assert "Fresh Analytics" in filtered["company"].tolist()
    assert "Unknown Company" in filtered["company"].tolist()
    assert filtered["match_score"].min() >= 45

    print("=" * 70)
    print("CAREERPILOT SMART JOB DISCOVERY INTEGRATION TEST")
    print("=" * 70)

    print(
        filtered[
            [
                "match_score",
                "priority",
                "freshness_label",
                "title",
                "company",
                "location",
                "matched_skills",
                "missing_job_skills",
            ]
        ].to_string(index=False)
    )

    print("\nSMART JOB DISCOVERY INTEGRATION TEST PASSED")


if __name__ == "__main__":
    main()
