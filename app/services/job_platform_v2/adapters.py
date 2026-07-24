from __future__ import annotations

from urllib.parse import quote_plus
from typing import Any
import pandas as pd
from app.services.job_platform_v2.models import (
    SourceDefinition, empty_jobs, normalise_jobs
)

def _job_search(**kwargs: Any) -> pd.DataFrame:
    from app.services.job_search import search_jobs
    jobs = search_jobs(**kwargs)
    return jobs if jobs is not None else pd.DataFrame()

def search_jobspy(
    source: SourceDefinition, *, role: str, location: str,
    results_wanted: int, hours_old: int,
    fetch_linkedin_description: bool,
) -> pd.DataFrame:
    jobs = _job_search(
        search_term=role,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        sites=[source.options.get("site", source.key)],
        fetch_linkedin_description=fetch_linkedin_description,
    )
    return normalise_jobs(jobs, source=source, searched_role=role)

def search_indexed(
    source: SourceDefinition, *, role: str, location: str,
    results_wanted: int, hours_old: int,
    fetch_linkedin_description: bool,
) -> pd.DataFrame:
    del fetch_linkedin_description
    domain = source.domain.replace("https://", "").replace("http://", "")
    domain = domain.split("/")[0].strip()
    if not domain:
        return empty_jobs()

    jobs = _job_search(
        search_term=f'site:{domain} "{role}"',
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        sites=["google"],
        fetch_linkedin_description=False,
    )
    if jobs.empty:
        return empty_jobs()

    jobs = jobs.copy()
    if "job_url" not in jobs.columns:
        return empty_jobs()
    jobs["job_url"] = jobs["job_url"].fillna("")
    jobs = jobs[
        jobs["job_url"].astype(str).str.contains(
            domain, case=False, na=False
        )
    ]
    return normalise_jobs(jobs, source=source, searched_role=role)

ADAPTERS = {"jobspy": search_jobspy, "indexed": search_indexed}

def run_adapter(
    source: SourceDefinition, *, role: str, location: str,
    results_wanted: int, hours_old: int,
    fetch_linkedin_description: bool,
) -> pd.DataFrame:
    adapter = ADAPTERS.get(source.adapter)
    if adapter is None:
        raise ValueError(f"Unsupported source adapter: {source.adapter}")
    return adapter(
        source,
        role=role,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        fetch_linkedin_description=fetch_linkedin_description,
    )

def build_direct_search_url(
    source: SourceDefinition,
    role: str,
    location: str,
) -> str:
    template = str(source.options.get("search_url", "")).strip()
    if not template:
        return ""
    role_slug = "-".join(role.lower().strip().split())
    location_slug = "-".join(
        location.lower().replace("bengaluru", "bangalore")
        .split(",")[0].strip().split()
    )
    return template.format(
        role=quote_plus(role),
        location=quote_plus(location),
        role_slug=quote_plus(role_slug).replace("+", "-"),
        location_slug=quote_plus(location_slug).replace("+", "-"),
    )
