from __future__ import annotations

from urllib.parse import quote_plus
import pandas as pd

from app.services.job_search import search_jobs
from app.services.job_sources.source_models import normalise_jobs


NAUKRI_SEARCH_URL = "https://www.naukri.com/{slug}-jobs-in-{location}"


def build_naukri_search_url(role: str, location: str) -> str:
    role_slug = "-".join(role.lower().strip().split())
    location_slug = "-".join(
        location.lower()
        .replace("bengaluru", "bangalore")
        .split(",")[0]
        .strip()
        .split()
    )
    return NAUKRI_SEARCH_URL.format(
        slug=quote_plus(role_slug).replace("+", "-"),
        location=quote_plus(location_slug).replace("+", "-"),
    )


def search_naukri_indexed(
    *,
    role: str,
    location: str,
    results_wanted: int,
    hours_old: int,
) -> pd.DataFrame:
    query = f'site:naukri.com "{role}"'
    jobs = search_jobs(
        search_term=query,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        sites=["google"],
        fetch_linkedin_description=False,
    )
    if jobs is None or jobs.empty:
        return normalise_jobs(
            None,
            site="naukri-indexed",
            source_type="job_board",
            official_source=False,
            searched_role=role,
        )

    result = jobs.copy()
    result["site"] = "naukri-indexed"
    result["job_url"] = result["job_url"].fillna("")
    result = result[
        result["job_url"].str.contains(
            "naukri.com",
            case=False,
            na=False,
        )
    ]

    return normalise_jobs(
        result,
        site="naukri-indexed",
        source_type="job_board",
        official_source=False,
        searched_role=role,
    )


def search_company_domain_indexed(
    *,
    company: str,
    careers_domain: str,
    role: str,
    location: str,
    results_wanted: int,
    hours_old: int,
) -> pd.DataFrame:
    domain = careers_domain.replace("https://", "").replace("http://", "")
    domain = domain.split("/")[0].strip()
    query = f'site:{domain} "{role}"'

    jobs = search_jobs(
        search_term=query,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        sites=["google"],
        fetch_linkedin_description=False,
    )
    if jobs is None or jobs.empty:
        return normalise_jobs(
            None,
            site=f"company-{company.lower().replace(' ', '-')}",
            source_type="company_careers",
            official_source=True,
            searched_role=role,
        )

    result = jobs.copy()
    result["site"] = f"company-{company.lower().replace(' ', '-')}"
    missing_company = result["company"].fillna("").astype(str).str.strip() == ""
    result.loc[missing_company, "company"] = company
    result["job_url"] = result["job_url"].fillna("")
    result = result[
        result["job_url"].str.contains(
            domain,
            case=False,
            na=False,
        )
    ]

    return normalise_jobs(
        result,
        site=f"company-{company.lower().replace(' ', '-')}",
        source_type="company_careers",
        official_source=True,
        searched_role=role,
    )
