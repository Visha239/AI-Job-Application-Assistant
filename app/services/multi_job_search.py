from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import pandas as pd
from app.services.job_connectors.engine import collect_jobs
from app.services.job_discovery.duplicate_detection import merge_duplicate_jobs
from app.services.job_discovery.eligibility import annotate_job_eligibility,split_eligible_jobs
from app.services.job_ranker import rank_jobs
DEFAULT_CONFIG_PATH=Path("config/job_search.json")
def load_search_config(path=DEFAULT_CONFIG_PATH):
    with Path(path).open("r",encoding="utf-8-sig") as f:c=json.load(f)
    c.setdefault("maximum_required_experience",2.0);c.setdefault("exclude_senior_roles",True);return c
def filter_ranked_jobs(df,minimum_score=45,maximum_jobs=None):
    if df is None or df.empty:return pd.DataFrame()
    out=df[df["match_score"]>=minimum_score].copy();cols=[c for c in ["match_score","freshness_bonus","date_posted"] if c in out.columns]
    if cols:out=out.sort_values(cols,ascending=[False]*len(cols),na_position="last")
    return out.head(int(maximum_jobs)).reset_index(drop=True) if maximum_jobs is not None else out.reset_index(drop=True)
def run_multi_role_search(config_path=DEFAULT_CONFIG_PATH,*,roles=None,location=None,sites=None,results_per_role=None,hours_old=None,minimum_match_score=None,maximum_jobs=None,exclude_senior_roles=None,maximum_required_experience=None,selected_source_keys=None,**_):
    c=load_search_config(config_path);roles=roles or c["roles"];location=location or c["location"];results=int(results_per_role or c["results_per_role"]);hours=int(hours_old or c["hours_old"]);minscore=int(minimum_match_score if minimum_match_score is not None else c["minimum_match_score"]);maxjobs=int(maximum_jobs if maximum_jobs is not None else c["maximum_digest_jobs"]);exclude=bool(exclude_senior_roles if exclude_senior_roles is not None else c["exclude_senior_roles"]);maxexp=float(maximum_required_experience if maximum_required_experience is not None else c["maximum_required_experience"]);keys=selected_source_keys or list(sites or ["indeed","linkedin"])
    raw,errors,counts,runs,links=collect_jobs(roles=roles,location=location,selected_source_keys=keys,results_per_role=results,hours_old=hours)
    dedup,removed=merge_duplicate_jobs(raw);annotated=annotate_job_eligibility(dedup,candidate_experience_years=1.1,maximum_required_experience=maxexp,exclude_senior_roles=exclude);eligible,rejected=split_eligible_jobs(annotated);ranked=rank_jobs(eligible) if not eligible.empty else pd.DataFrame();filtered=filter_ranked_jobs(ranked,minscore,maxjobs)
    return {"roles":roles,"location":location,"sites":keys,"jobs_collected":len(raw),"duplicates_removed":removed,"jobs_after_deduplication":len(dedup),"experience_rejected":len(rejected),"jobs_ranked":len(ranked),"strong_matches":len(filtered),"raw_jobs":raw,"deduplicated_jobs":dedup,"annotated_jobs":annotated,"rejected_jobs":rejected,"ranked_jobs":ranked,"filtered_jobs":filtered,"source_counts":counts,"source_runs":runs,"direct_links":links,"errors":errors}
