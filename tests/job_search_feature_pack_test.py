from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import tempfile

import pandas as pd

from app.services.job_ranker import rank_jobs


def main() -> None:
    now = datetime(
        2026,
        7,
        12,
        10,
        0,
        tzinfo=timezone.utc,
    )

    sample_jobs = pd.DataFrame(
        [
            {
                "site": "test",
                "title": "Data Analyst",
                "company": "Fresh Match Company",
                "location": "Bengaluru, Karnataka",
                "date_posted": now - timedelta(hours=2),
                "job_type": "fulltime",
                "is_remote": False,
                "job_url": "https://example.com/fresh-match",
                "description": (
                    "SQL Python Excel Power BI dashboard reporting "
                    "0 to 2 years experience"
                ),
            },
            {
                "site": "test",
                "title": "Data Analyst",
                "company": "Old Match Company",
                "location": "Bengaluru, Karnataka",
                "date_posted": now - timedelta(days=10),
                "job_type": "fulltime",
                "is_remote": False,
                "job_url": "https://example.com/old-match",
                "description": (
                    "SQL Python Excel Power BI dashboard reporting "
                    "0 to 2 years experience"
                ),
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
                    "Requires 8+ years Spark Snowflake leadership"
                ),
            },
            {
                "site": "test",
                "title": "Production Support Analyst",
                "company": "Support Company",
                "location": "Remote",
                "date_posted": now - timedelta(hours=12),
                "job_type": "fulltime",
                "is_remote": True,
                "job_url": "https://example.com/support",
                "description": (
                    "Linux SQL AWS Jira ServiceNow troubleshooting "
                    "1 to 2 years experience"
                ),
            },
        ]
    )

    profile = {
        "skills": [
            "SQL",
            "Python",
            "Excel",
            "Power BI",
            "Linux",
            "AWS",
            "Jira",
            "ServiceNow",
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

    with tempfile.TemporaryDirectory() as temp_dir:
        profile_path = Path(temp_dir) / "profile.json"
        profile_path.write_text(
            json.dumps(profile),
            encoding="utf-8",
        )

        ranked = rank_jobs(
            sample_jobs,
            profile_path=profile_path,
            now=now,
        )

    assert not ranked.empty

    fresh = ranked[
        ranked["company"] == "Fresh Match Company"
    ].iloc[0]

    old = ranked[
        ranked["company"] == "Old Match Company"
    ].iloc[0]

    senior = ranked[
        ranked["company"] == "Senior Company"
    ].iloc[0]

    support = ranked[
        ranked["company"] == "Support Company"
    ].iloc[0]

    # Freshness must improve an otherwise identical job.
    assert fresh["freshness_bonus"] > old["freshness_bonus"]
    assert fresh["match_score"] > old["match_score"]

    # Clearly senior jobs must be penalized.
    assert bool(senior["is_senior_role"]) is True
    assert senior["relevance_penalty"] >= 30
    assert senior["match_score"] < fresh["match_score"]

    # Remote support role should be recognized correctly.
    assert support["resume_version"] == "Support Engineer Resume"
    assert support["location_score"] == 15

    # The top job can legitimately be either the fresh Data Analyst role
    # or the strong remote Production Support role, depending on skill overlap.
    assert ranked.iloc[0]["company"] in {
        "Fresh Match Company",
        "Support Company",
    }

    required_columns = {
        "freshness_label",
        "apply_urgency",
        "suitability_score",
        "required_experience_years",
        "priority",
        "match_score",
    }

    assert required_columns.issubset(ranked.columns)

    print("=" * 70)
    print("CAREERPILOT SMART JOB DISCOVERY FEATURE PACK TEST")
    print("=" * 70)

    print(
        ranked[
            [
                "match_score",
                "priority",
                "freshness_label",
                "apply_urgency",
                "title",
                "company",
                "location",
                "is_senior_role",
                "resume_version",
            ]
        ].to_string(index=False)
    )

    print("\nFEATURE PACK TEST PASSED")


if __name__ == "__main__":
    main()
