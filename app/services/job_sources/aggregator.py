from __future__ import annotations

from typing import Any
import pandas as pd

from app.services.job_search import search_jobs
from app.services.job_sources.ats_connectors import (
    search_greenhouse,
    search_lever,
)
from app.services.job_sources.indexed_sources import (
    search_company_domain_indexed,
    search_naukri_indexed,
)
from app.services.job_sources.registry import (
    enabled_companies,
    load_company_sources,
)
from app.services.job_sources.source_models import normalise_jobs


def collect_all_sources(
    *,
    roles: list[str],
    location: str,
    jobspy_sites: list[str],
    results_per_role: int,
    hours_old: int,
    include_naukri: bool,
    include_company_careers: bool,
    selected_companies: list[str] | None = None,
    fetch_linkedin_description: bool = True,
) -> tuple[pd.DataFrame, list[str], dict[str, int]]:
    frames: list[pd.DataFrame] = []
    errors: list[str] = []
    counts: dict[str, int] = {
        "jobspy": 0,
        "naukri": 0,
        "company_careers": 0,
    }

    source_config = load_company_sources()
    companies = enabled_companies(source_config)

    if selected_companies:
        wanted = {name.lower() for name in selected_companies}
        companies = [
            company for company in companies
            if str(company.get("name", "")).lower() in wanted
        ]

    for role in roles:
        clean_role = str(role).strip()
        if not clean_role:
            continue

        if jobspy_sites:
            try:
                jobs = search_jobs(
                    search_term=clean_role,
                    location=location,
                    results_wanted=results_per_role,
                    hours_old=hours_old,
                    sites=jobspy_sites,
                    fetch_linkedin_description=fetch_linkedin_description,
                )
                jobs = normalise_jobs(
                    jobs,
                    site="jobspy",
                    source_type="job_board",
                    official_source=False,
                    searched_role=clean_role,
                )
                if not jobs.empty:
                    counts["jobspy"] += len(jobs)
                    frames.append(jobs)
            except Exception as exc:
                errors.append(f"JobSpy / {clean_role}: {exc}")

        if include_naukri and source_config.get("naukri", {}).get("enabled", True):
            try:
                jobs = search_naukri_indexed(
                    role=clean_role,
                    location=location,
                    results_wanted=results_per_role,
                    hours_old=hours_old,
                )
                if not jobs.empty:
                    counts["naukri"] += len(jobs)
                    frames.append(jobs)
            except Exception as exc:
                errors.append(f"Naukri indexed / {clean_role}: {exc}")

        if include_company_careers:
            for company in companies:
                name = str(company.get("name") or "").strip()
                platform = str(company.get("platform") or "indexed").lower()

                if not name:
                    continue

                try:
                    if platform == "greenhouse":
                        jobs = search_greenhouse(
                            company=name,
                            board_token=str(company.get("board_token") or ""),
                            role=clean_role,
                            location=location,
                        )
                    elif platform == "lever":
                        jobs = search_lever(
                            company=name,
                            site_token=str(company.get("site_token") or ""),
                            role=clean_role,
                            location=location,
                        )
                    else:
                        jobs = search_company_domain_indexed(
                            company=name,
                            careers_domain=str(company.get("careers_domain") or ""),
                            role=clean_role,
                            location=location,
                            results_wanted=max(5, results_per_role // 2),
                            hours_old=hours_old,
                        )

                    if not jobs.empty:
                        counts["company_careers"] += len(jobs)
                        frames.append(jobs)
                except Exception as exc:
                    errors.append(f"{name} / {clean_role}: {exc}")

    if not frames:
        return pd.DataFrame(), errors, counts

    return (
        pd.concat(frames, ignore_index=True, sort=False),
        errors,
        counts,
    )
