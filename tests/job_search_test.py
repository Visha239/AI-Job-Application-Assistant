from app.services.job_search import search_jobs


def main() -> None:
    jobs = search_jobs(
        search_term="Data Analyst",
        location="Bengaluru, Karnataka",
        results_wanted=5,
        hours_old=168,
        sites=["indeed", "linkedin", "google"],
    )

    print(f"\nJobs found: {len(jobs)}")

    if jobs.empty:
        print("No jobs returned. Try again later or test one site at a time.")
        return

    print(
        jobs[
            ["site", "title", "company", "location", "job_url"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()