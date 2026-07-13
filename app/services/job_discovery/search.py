from __future__ import annotations

from collections.abc import Iterable
import pandas as pd
from jobspy import scrape_jobs

DISPLAY_COLUMNS = ["site", "title", "company", "location", "date_posted", "job_type", "is_remote", "job_url", "description"]

def _normalise_location(jobs: pd.DataFrame) -> pd.DataFrame:
    updated = jobs.copy()
    if "location" in updated.columns:
        return updated
    city = updated.get("city", pd.Series("", index=updated.index)).fillna("")
    state = updated.get("state", pd.Series("", index=updated.index)).fillna("")
    updated["location"] = (city.astype(str).str.strip() + ", " + state.astype(str).str.strip()).str.strip(", ")
    return updated

def _ensure_columns(jobs: pd.DataFrame) -> pd.DataFrame:
    updated = jobs.copy()
    for column in DISPLAY_COLUMNS:
        if column not in updated.columns:
            updated[column] = None
    return updated[DISPLAY_COLUMNS]

def _deduplicate(jobs: pd.DataFrame) -> pd.DataFrame:
    if jobs.empty: return jobs.copy()
    updated = jobs.copy()
    job_url = updated["job_url"].fillna("").astype(str).str.strip()
    with_url = updated[job_url != ""].drop_duplicates(subset=["job_url"], keep="first")
    without_url = updated[job_url == ""]
    combined = pd.concat([with_url, without_url], ignore_index=True, sort=False)
    return combined.drop_duplicates(subset=["company", "title", "location"], keep="first").reset_index(drop=True)

def search_jobs(search_term: str, location: str = "Bengaluru, Karnataka", results_wanted: int = 15, hours_old: int = 168, sites: Iterable[str] | None = None) -> pd.DataFrame:
    search_term, location = search_term.strip(), location.strip()
    if not search_term: raise ValueError("Search term cannot be empty.")
    if not 1 <= results_wanted <= 100: raise ValueError("Results wanted must be between 1 and 100.")
    selected_sites = list(sites or ["indeed", "linkedin", "google"])
    try:
        jobs = scrape_jobs(
            site_name=selected_sites,
            search_term=search_term,
            google_search_term=f"{search_term} jobs in {location} posted in the last 7 days",
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            country_indeed="India",
            linkedin_fetch_description=False,
            verbose=0,
        )
    except Exception as exc:
        raise RuntimeError(f"Job search failed for '{search_term}': {exc}") from exc
    if jobs is None or jobs.empty:
        return pd.DataFrame(columns=DISPLAY_COLUMNS)
    return _deduplicate(_ensure_columns(_normalise_location(jobs)))
