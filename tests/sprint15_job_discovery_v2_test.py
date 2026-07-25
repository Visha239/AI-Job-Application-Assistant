from __future__ import annotations

import pandas as pd

from app.services.job_discovery.duplicate_detection import merge_duplicate_jobs
from app.services.job_discovery.eligibility import (
    annotate_job_eligibility,
    split_eligible_jobs,
)
from app.services.job_discovery.experience_intelligence import (
    parse_experience_requirement,
)


def main() -> None:
    cases = {
        "Minimum 5 years of experience in analytics": (5.0, None),
        "3-5 years experience required": (3.0, 5.0),
        "Candidates with 4+ yrs in SQL": (4.0, None),
        "Freshers and entry-level candidates can apply": (0.0, 2.0),
        "0 to 2 years of experience": (0.0, 2.0),
        "At least 2 years of relevant experience": (2.0, None),
    }

    for text, expected in cases.items():
        result = parse_experience_requirement(text)
        assert result.minimum_years == expected[0], (text, result)
        assert result.maximum_years == expected[1], (text, result)

    jobs = pd.DataFrame(
        [
            {
                "site": "linkedin",
                "title": "Data Analyst",
                "company": "Example Technologies Pvt Ltd",
                "location": "Bengaluru, Karnataka",
                "job_url": "https://linkedin.example/1",
                "description": (
                    "We need a Data Analyst. Minimum 1 year of experience "
                    "with SQL, Excel and Power BI."
                ),
            },
            {
                "site": "indeed",
                "title": "Data Analyst - Hiring",
                "company": "Example Technologies",
                "location": "Bangalore",
                "job_url": "https://indeed.example/1",
                "description": (
                    "We need a Data Analyst. Minimum 1 year of experience "
                    "with SQL, Excel and Power BI."
                ),
            },
            {
                "site": "linkedin",
                "title": "Senior Data Analyst",
                "company": "Senior Company",
                "location": "Bengaluru",
                "job_url": "https://linkedin.example/2",
                "description": "Requires 6+ years of experience.",
            },
            {
                "site": "indeed",
                "title": "Reporting Analyst",
                "company": "Stretch Company",
                "location": "Bengaluru",
                "job_url": "https://indeed.example/3",
                "description": "Experience required: 3-5 years.",
            },
        ]
    )

    merged, duplicates_removed = merge_duplicate_jobs(jobs)
    assert duplicates_removed == 1
    assert len(merged) == 3

    annotated = annotate_job_eligibility(
        merged,
        candidate_experience_years=1.1,
        maximum_required_experience=2.0,
        exclude_senior_roles=True,
    )
    eligible, rejected = split_eligible_jobs(annotated)

    assert len(eligible) == 1
    assert len(rejected) == 2
    assert eligible.iloc[0]["company"].startswith("Example Technologies")
    assert int(eligible.iloc[0]["duplicate_count"]) == 2
    assert set(rejected["eligibility_status"]) == {"Not eligible"}

    print("=" * 72)
    print("CAREERPILOT SPRINT 15 JOB DISCOVERY ENGINE V2 TEST")
    print("=" * 72)
    print("Experience patterns tested:", len(cases))
    print("Duplicates removed:", duplicates_removed)
    print("Eligible jobs:", len(eligible))
    print("Rejected jobs:", len(rejected))
    print("\nSPRINT 15 JOB DISCOVERY ENGINE V2 TEST PASSED")


if __name__ == "__main__":
    main()
