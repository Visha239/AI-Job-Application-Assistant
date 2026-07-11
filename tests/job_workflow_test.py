import pandas as pd

from app.services.job_ranker import rank_jobs
from app.services.job_repository import (
    get_saved_job_count,
    save_job,
)


def main() -> None:
    sample_jobs = pd.DataFrame(
        [
            {
                "site": "test",
                "title": "Data Analyst",
                "company": "CareerPilot Test Company",
                "location": "Bengaluru, Karnataka",
                "date_posted": "2026-07-10",
                "job_type": "fulltime",
                "is_remote": False,
                "job_url": "https://example.com/careerpilot-test-job",
                "description": (
                    "We need SQL, Python, Excel, Power BI, "
                    "Tableau and data analysis skills."
                ),
            },
            {
                "site": "test",
                "title": "Senior Data Engineering Lead",
                "company": "Senior Test Company",
                "location": "Bengaluru, Karnataka",
                "date_posted": "2026-07-10",
                "job_type": "fulltime",
                "is_remote": False,
                "job_url": "https://example.com/senior-test-job",
                "description": (
                    "Requires 7+ years of experience, Spark, "
                    "Snowflake and leadership."
                ),
            },
        ]
    )

    ranked = rank_jobs(sample_jobs)

    print("\nRANKED JOBS")
    print(
        ranked[
            [
                "match_score",
                "title",
                "company",
                "resume_version",
            ]
        ].to_string(index=False)
    )

    top_job = ranked.iloc[0].to_dict()

    before_count = get_saved_job_count()
    saved = save_job(top_job)
    after_count = get_saved_job_count()

    print("\nSAVE TEST")
    print("Saved:", saved)
    print("Before count:", before_count)
    print("After count:", after_count)

    assert ranked.iloc[0]["title"] == "Data Analyst"
    assert ranked.iloc[0]["match_score"] > ranked.iloc[1]["match_score"]

    if saved:
        assert after_count == before_count + 1
    else:
        assert after_count == before_count

    print("\nJOB WORKFLOW TEST PASSED")


if __name__ == "__main__":
    main()