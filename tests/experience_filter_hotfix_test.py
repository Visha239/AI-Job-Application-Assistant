from __future__ import annotations

import pandas as pd

from app.services.job_discovery.relevance import extract_required_experience_years
from app.services.job_ranker import rank_jobs
from app.services.multi_job_search import filter_ranked_jobs


def main() -> None:
    examples = {
        "Minimum 5 years of experience": 5.0,
        "3-5 years experience": 3.0,
        "At least 4 yrs": 4.0,
        "Experience: 2 years": 2.0,
        "1+ years of experience": 1.0,
    }
    for text, expected in examples.items():
        assert extract_required_experience_years(text) == expected, text

    jobs = pd.DataFrame([
        {
            "title": "Data Analyst",
            "company": "Entry Company",
            "location": "Bengaluru",
            "description": "SQL Power BI. 0-2 years experience.",
            "date_posted": "2026-07-16",
            "job_url": "https://example.com/entry",
            "site": "linkedin",
        },
        {
            "title": "Data Analyst",
            "company": "Senior Requirement Company",
            "location": "Bengaluru",
            "description": "SQL Power BI. Minimum 5 years of experience required.",
            "date_posted": "2026-07-16",
            "job_url": "https://example.com/senior",
            "site": "linkedin",
        },
        {
            "title": "Senior Data Analyst",
            "company": "Senior Title Company",
            "location": "Bengaluru",
            "description": "SQL Power BI. 2 years experience.",
            "date_posted": "2026-07-16",
            "job_url": "https://example.com/title",
            "site": "linkedin",
        },
    ])

    ranked = rank_jobs(jobs)
    filtered = filter_ranked_jobs(
        ranked,
        minimum_score=0,
        maximum_jobs=20,
        exclude_senior_roles=True,
        maximum_required_experience_years=2.0,
    )

    assert list(filtered["company"]) == ["Entry Company"]
    assert float(filtered.iloc[0]["required_experience_years"]) == 0.0

    print("=" * 70)
    print("CAREERPILOT EXPERIENCE FILTER HOTFIX TEST")
    print("=" * 70)
    print(filtered[["company", "required_experience_years", "is_senior_role"]].to_string(index=False))
    print("\nEXPERIENCE FILTER HOTFIX TEST PASSED")


if __name__ == "__main__":
    main()
