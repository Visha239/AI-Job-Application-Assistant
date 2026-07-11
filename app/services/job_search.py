from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
from jobspy import scrape_jobs


DISPLAY_COLUMNS = [
    "site",
    "title",
    "company",
    "location",
    "date_posted",
    "job_type",
    "is_remote",
    "job_url",
    "description",
]


def search_jobs(
    search_term: str,
    location: str = "Bengaluru, Karnataka",
    results_wanted: int = 10,
    hours_old: int = 168,
    sites: Iterable[str] | None = None,
) -> pd.DataFrame:
    search_term = search_term.strip()
    location = location.strip()

    if not search_term:
        raise ValueError("Search term cannot be empty.")

    if not 1 <= results_wanted <= 100:
        raise ValueError("Results wanted must be between 1 and 100.")

    selected_sites = list(sites or ["indeed", "linkedin", "google"])

    try:
        jobs = scrape_jobs(
            site_name=selected_sites,
            search_term=search_term,
            google_search_term=(
                f"{search_term} jobs in {location} posted in the last 7 days"
            ),
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            country_indeed="India",
            linkedin_fetch_description=False,
            verbose=0,
        )
    except Exception as exc:
        raise RuntimeError(f"Job search failed: {exc}") from exc

    if jobs is None or jobs.empty:
        return pd.DataFrame(columns=DISPLAY_COLUMNS)

    jobs = jobs.copy()

    if "location" not in jobs.columns:
        city = jobs.get("city", pd.Series("", index=jobs.index)).fillna("")
        state = jobs.get("state", pd.Series("", index=jobs.index)).fillna("")

        jobs["location"] = (
            city.astype(str).str.strip()
            + ", "
            + state.astype(str).str.strip()
        ).str.strip(", ")

    for column in DISPLAY_COLUMNS:
        if column not in jobs.columns:
            jobs[column] = None

    jobs = jobs[DISPLAY_COLUMNS]

    jobs = jobs.drop_duplicates(subset=["job_url"], keep="first")
    jobs = jobs.drop_duplicates(
        subset=["company", "title", "location"],
        keep="first",
    )

    return jobs.reset_index(drop=True)