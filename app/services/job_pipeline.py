from __future__ import annotations
from typing import Any
from app.services.multi_job_search import run_multi_role_search
def run_pipeline(**kwargs:Any):
    r=run_multi_role_search(**kwargs)
    return {"jobs":r["filtered_jobs"],"all_ranked_jobs":r["ranked_jobs"],"rejected_jobs":r["rejected_jobs"],"summary":{"searched_roles":len(r["roles"]),"jobs_found":r["jobs_collected"],"duplicates_removed":r["duplicates_removed"],"experience_rejected":r["experience_rejected"],"ranked_jobs":r["jobs_ranked"],"recommended_jobs":r["strong_matches"],"source_counts":r["source_counts"],"source_runs":r["source_runs"],"direct_links":r["direct_links"],"errors":r["errors"]}}
