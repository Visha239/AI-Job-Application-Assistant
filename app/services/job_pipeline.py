from __future__ import annotations

from typing import Any

from app.services.multi_job_search import run_multi_role_search


def run_pipeline(
    *,
    roles: list[str] | None = None,
    location: str | None = None,
    sites: list[str] | None = None,
    results_per_role: int | None = None,
    hours_old: int | None = None,
    minimum_match_score: int | None = None,
    maximum_jobs: int | None = None,
    exclude_senior_roles: bool = True,
) -> dict[str, Any]:
    result = run_multi_role_search(
        roles=roles,
        location=location,
        sites=sites,
        results_per_role=results_per_role,
        hours_old=hours_old,
        minimum_match_score=minimum_match_score,
        maximum_jobs=maximum_jobs,
        exclude_senior_roles=exclude_senior_roles,
    )

    return {
        "jobs": result["filtered_jobs"],
        "all_ranked_jobs": result["ranked_jobs"],
        "summary": {
            "searched_roles": len(result["roles"]),
            "jobs_found": result["jobs_collected"],
            "ranked_jobs": result["jobs_ranked"],
            "recommended_jobs": result["strong_matches"],
            "errors": result["errors"],
        },
    }
