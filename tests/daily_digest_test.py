from datetime import datetime
from pathlib import Path

import pandas as pd

from app.services.daily_job_digest import (
    build_html_digest,
    export_digest_files,
    prepare_ranked_digest,
)


def main() -> None:
    sample_jobs = pd.DataFrame(
        [
            {
                "site": "test",
                "title": "Data Analyst",
                "company": "High Match Company",
                "location": "Bengaluru, Karnataka",
                "date_posted": "2026-07-11",
                "job_type": "fulltime",
                "is_remote": False,
                "job_url": "https://example.com/high-match",
                "description": (
                    "SQL Python Excel Power BI Tableau "
                    "data analysis reporting dashboard"
                ),
                "searched_role": "Data Analyst",
            },
            {
                "site": "test",
                "title": "Senior Engineering Manager",
                "company": "Low Match Company",
                "location": "Bengaluru, Karnataka",
                "date_posted": "2026-07-11",
                "job_type": "fulltime",
                "is_remote": False,
                "job_url": "https://example.com/low-match",
                "description": (
                    "Requires 8+ years of Java leadership "
                    "and engineering management."
                ),
                "searched_role": "Data Analyst",
            },
        ]
    )

    config = {
        "minimum_match_score": 50,
        "maximum_digest_jobs": 10,
    }

    ranked = prepare_ranked_digest(
        sample_jobs,
        config,
    )

    assert not ranked.empty
    assert ranked.iloc[0]["title"] == "Data Analyst"
    assert ranked.iloc[0]["match_score"] >= 50

    html_content = build_html_digest(
        ranked,
        generated_at=datetime(2026, 7, 11, 8, 0),
    )

    assert "CareerPilot Daily Job Digest" in html_content
    assert "High Match Company" in html_content
    assert "Data Analyst" in html_content

    exported = export_digest_files(ranked)

    html_path = Path(exported["html_path"])
    csv_path = Path(exported["csv_path"])

    assert html_path.exists()
    assert csv_path.exists()

    print("=" * 60)
    print("CAREERPILOT v0.8 DAILY DIGEST TEST")
    print("=" * 60)
    print("Strong matches:", len(ranked))
    print("Top role:", ranked.iloc[0]["title"])
    print("Top score:", ranked.iloc[0]["match_score"])
    print("HTML report:", html_path)
    print("CSV report:", csv_path)
    print("\nCAREERPILOT v0.8 TEST PASSED")


if __name__ == "__main__":
    main()