from __future__ import annotations

from typing import Any

import pandas as pd

from app.services.job_discovery.experience_intelligence import (
    analyze_job_experience,
    is_experience_eligible,
)
from app.services.job_discovery.relevance import contains_seniority


def annotate_job_eligibility(
    jobs: pd.DataFrame,
    *,
    candidate_experience_years: float,
    maximum_required_experience: float,
    exclude_senior_roles: bool,
) -> pd.DataFrame:
    if jobs is None or jobs.empty:
        return pd.DataFrame()

    annotated = jobs.copy()

    requirements = annotated.apply(
        lambda row: analyze_job_experience(row.to_dict()),
        axis=1,
    )

    annotated["experience_min_years"] = requirements.apply(
        lambda result: result.minimum_years
    )
    annotated["experience_max_years"] = requirements.apply(
        lambda result: result.maximum_years
    )
    annotated["experience_label"] = requirements.apply(
        lambda result: result.label
    )
    annotated["experience_confidence"] = requirements.apply(
        lambda result: result.confidence
    )
    annotated["experience_evidence"] = requirements.apply(
        lambda result: result.evidence
    )

    annotated["is_senior_role"] = annotated["title"].apply(
        contains_seniority
    )

    eligibility = requirements.apply(
        lambda requirement: is_experience_eligible(
            requirement,
            candidate_experience_years=candidate_experience_years,
            maximum_required_experience=maximum_required_experience,
        )
    )

    annotated["experience_eligible"] = eligibility.apply(
        lambda result: result[0]
    )
    annotated["eligibility_reason"] = eligibility.apply(
        lambda result: result[1]
    )

    if exclude_senior_roles:
        annotated["eligible"] = (
            annotated["experience_eligible"]
            & ~annotated["is_senior_role"]
        )
    else:
        annotated["eligible"] = annotated["experience_eligible"]

    annotated["eligibility_status"] = annotated["eligible"].map(
        {True: "Eligible", False: "Not eligible"}
    )

    return annotated


def split_eligible_jobs(
    jobs: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if jobs is None or jobs.empty:
        return pd.DataFrame(), pd.DataFrame()

    eligible = jobs[
        jobs["eligible"].fillna(False)
    ].copy()
    rejected = jobs[
        ~jobs["eligible"].fillna(False)
    ].copy()

    return (
        eligible.reset_index(drop=True),
        rejected.reset_index(drop=True),
    )
