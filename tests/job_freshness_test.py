from datetime import datetime, timedelta, timezone

import pandas as pd

from app.services.job_freshness import add_freshness_columns


def main() -> None:
    now = datetime(2026, 7, 12, 10, 0, tzinfo=timezone.utc)

    jobs = pd.DataFrame(
        [
            {
                "title": "Very New Data Analyst",
                "date_posted": now - timedelta(hours=2),
            },
            {
                "title": "Today Data Analyst",
                "date_posted": now - timedelta(hours=18),
            },
            {
                "title": "Three Day Data Analyst",
                "date_posted": now - timedelta(hours=60),
            },
            {
                "title": "Old Data Analyst",
                "date_posted": now - timedelta(days=10),
            },
        ]
    )

    result = add_freshness_columns(jobs, now=now)

    assert result.iloc[0]["freshness_bonus"] == 15
    assert result.iloc[0]["apply_urgency"] == "Apply immediately"

    assert result.iloc[1]["freshness_bonus"] == 12
    assert result.iloc[2]["freshness_bonus"] == 8
    assert result.iloc[3]["freshness_bonus"] == 0

    print("=" * 60)
    print("CAREERPILOT JOB FRESHNESS TEST")
    print("=" * 60)

    print(
        result[
            [
                "title",
                "job_age_hours",
                "freshness_bonus",
                "freshness_label",
                "apply_urgency",
            ]
        ].to_string(index=False)
    )

    print("\nJOB FRESHNESS TEST PASSED")


if __name__ == "__main__":
    main()