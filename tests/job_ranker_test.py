from app.services.job_ranker import rank_jobs
from app.services.job_search import search_jobs


def main() -> None:
    jobs = search_jobs(
        search_term="Data Analyst",
        location="Bengaluru, Karnataka",
        results_wanted=10,
        hours_old=168,
        sites=["indeed", "linkedin"],
    )

    ranked = rank_jobs(jobs)

    print(f"\nJobs found: {len(ranked)}")

    if ranked.empty:
        print("No jobs were returned.")
        return

    columns = [
        "match_score",
        "title",
        "company",
        "location",
        "matched_skills",
        "resume_version",
        "job_url",
    ]

    print(ranked[columns].to_string(index=False))


if __name__ == "__main__":
    main()