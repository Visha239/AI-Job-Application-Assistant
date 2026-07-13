
param(
    [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

function Write-Utf8File {
    param(
        [string]$RelativePath,
        [string]$Content
    )

    $FullPath = Join-Path $ProjectRoot $RelativePath
    $Parent = Split-Path $FullPath -Parent

    if (-not (Test-Path $Parent)) {
        New-Item -ItemType Directory -Path $Parent -Force | Out-Null
    }

    Set-Content -Path $FullPath -Value $Content -Encoding UTF8
    Write-Host "Updated: $RelativePath"
}

Write-Utf8File "app\services\job_discovery\ranking.py" @'
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from app.services.job_discovery.freshness import evaluate_freshness
from app.services.job_discovery.models import lower_text
from app.services.job_discovery.relevance import evaluate_relevance


DEFAULT_PROFILE_PATH = Path("data/profile.json")

JOB_SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "SQL": ("sql", "mysql", "mariadb", "oracle", "database query"),
    "Python": ("python", "pandas", "numpy"),
    "Power BI": ("power bi", "powerbi", "dax"),
    "Excel": ("excel", "pivot table", "vlookup", "xlookup"),
    "Tableau": ("tableau",),
    "Linux": ("linux", "unix"),
    "ServiceNow": ("servicenow", "service now"),
    "Jira": ("jira",),
    "AWS": ("aws", "amazon web services", "ec2", "s3", "aurora"),
    "Data Analysis": ("data analysis", "data analytics", "analytical"),
    "Power Query": ("power query", "m language"),
    "ETL": ("etl", "data pipeline", "data integration"),
    "Dashboard": ("dashboard", "visualization", "reporting"),
    "Stakeholder Management": (
        "stakeholder",
        "business requirement",
        "requirements gathering",
    ),
}

ROLE_CORE_SKILLS: dict[str, tuple[str, ...]] = {
    "data": (
        "SQL",
        "Python",
        "Power BI",
        "Excel",
        "Tableau",
        "Data Analysis",
        "Power Query",
        "ETL",
        "Dashboard",
    ),
    "business": (
        "SQL",
        "Excel",
        "Power BI",
        "Data Analysis",
        "Stakeholder Management",
        "Dashboard",
    ),
    "support": (
        "SQL",
        "Linux",
        "ServiceNow",
        "Jira",
        "AWS",
        "Python",
    ),
}


def load_profile(
    profile_path: str | Path = DEFAULT_PROFILE_PATH,
) -> dict[str, Any]:
    path = Path(profile_path)

    with path.open("r", encoding="utf-8") as file:
        profile = json.load(file)

    profile.setdefault("skills", [])
    profile.setdefault("preferred_roles", [])
    profile.setdefault(
        "preferred_locations",
        ["Bengaluru", "Bangalore", "Remote"],
    )
    profile.setdefault("experience_years", 1.1)

    return profile


def _normalise_company(value: object) -> str:
    text = str(value or "").strip()

    if text.lower() in {"", "nan", "none", "null"}:
        return "Unknown Company"

    return text


def _role_family(title: object) -> str:
    text = lower_text(title)

    if any(
        term in text
        for term in [
            "application support",
            "production support",
            "technical support",
            "support analyst",
            "support engineer",
            "l1 support",
            "l2 support",
        ]
    ):
        return "support"

    if any(
        term in text
        for term in [
            "business analyst",
            "process analyst",
            "functional analyst",
        ]
    ):
        return "business"

    return "data"


def _detect_job_skills(text: str) -> list[str]:
    detected: list[str] = []

    for canonical, aliases in JOB_SKILL_ALIASES.items():
        if any(alias in text for alias in aliases):
            detected.append(canonical)

    return detected


def _profile_skill_set(profile: dict[str, Any]) -> set[str]:
    result: set[str] = set()

    for skill in profile.get("skills", []):
        text = str(skill).strip().lower()

        if text:
            result.add(text)

    return result


def _calculate_skill_score(
    row: pd.Series,
    profile: dict[str, Any],
) -> tuple[int, list[str], list[str], list[str]]:
    combined = " ".join(
        [
            lower_text(row.get("title")),
            lower_text(row.get("description")),
        ]
    )

    detected_job_skills = _detect_job_skills(combined)
    family = _role_family(row.get("title"))

    if not detected_job_skills:
        detected_job_skills = list(ROLE_CORE_SKILLS[family])

    profile_skills = _profile_skill_set(profile)

    matched = [
        skill
        for skill in detected_job_skills
        if skill.lower() in profile_skills
    ]

    missing = [
        skill
        for skill in detected_job_skills
        if skill not in matched
    ]

    denominator = max(len(detected_job_skills), 1)
    coverage = len(matched) / denominator

    score = round(coverage * 35)

    # Reward broad practical alignment without demanding every profile skill.
    if len(matched) >= 4:
        score += 5
    elif len(matched) >= 2:
        score += 2

    return min(score, 40), matched, missing, detected_job_skills


def _recommend_resume(title: object) -> str:
    family = _role_family(title)

    if family == "support":
        return "Support Engineer Resume"

    if family == "business":
        return "Business Analyst Resume"

    return "Data Analyst Resume"


def _priority_label(score: int) -> str:
    if score >= 85:
        return "Apply immediately"

    if score >= 72:
        return "High priority"

    if score >= 60:
        return "Good opportunity"

    if score >= 45:
        return "Review carefully"

    return "Low priority"


def rank_jobs(
    jobs: pd.DataFrame,
    profile_path: str | Path = DEFAULT_PROFILE_PATH,
    now=None,
) -> pd.DataFrame:
    if jobs is None or jobs.empty:
        return pd.DataFrame()

    profile = load_profile(profile_path)
    candidate_experience = float(
        profile.get("experience_years", 1.1)
    )

    ranked = jobs.copy()

    for required_column in [
        "title",
        "company",
        "location",
        "date_posted",
        "description",
        "job_url",
        "site",
    ]:
        if required_column not in ranked.columns:
            ranked[required_column] = None

    ranked["company"] = ranked["company"].apply(
        _normalise_company
    )

    freshness_results = ranked["date_posted"].apply(
        lambda value: evaluate_freshness(value, now=now)
    )

    relevance_results = ranked.apply(
        lambda row: evaluate_relevance(
            row.to_dict(),
            candidate_experience_years=candidate_experience,
        ),
        axis=1,
    )

    skill_results = ranked.apply(
        lambda row: _calculate_skill_score(row, profile),
        axis=1,
    )

    ranked["job_age_hours"] = freshness_results.apply(
        lambda result: result.age_hours
    )
    ranked["freshness_bonus"] = freshness_results.apply(
        lambda result: result.bonus
    )
    ranked["freshness_label"] = freshness_results.apply(
        lambda result: result.label
    )
    ranked["apply_urgency"] = freshness_results.apply(
        lambda result: result.urgency
    )

    ranked["suitability_score"] = relevance_results.apply(
        lambda result: result.suitability_score
    )
    ranked["title_score"] = relevance_results.apply(
        lambda result: result.title_score
    )
    ranked["experience_score"] = relevance_results.apply(
        lambda result: result.experience_score
    )
    ranked["location_score"] = relevance_results.apply(
        lambda result: result.location_score
    )
    ranked["relevance_penalty"] = relevance_results.apply(
        lambda result: result.relevance_penalty
    )
    ranked["is_senior_role"] = relevance_results.apply(
        lambda result: result.is_senior_role
    )
    ranked["required_experience_years"] = (
        relevance_results.apply(
            lambda result: result.required_experience_years
        )
    )
    ranked["match_reasons"] = relevance_results.apply(
        lambda result: " | ".join(result.reasons)
    )
    ranked["match_warnings"] = relevance_results.apply(
        lambda result: " | ".join(result.warnings)
    )

    ranked["skill_score"] = skill_results.apply(
        lambda result: result[0]
    )
    ranked["matched_skills"] = skill_results.apply(
        lambda result: ", ".join(result[1])
    )
    ranked["missing_job_skills"] = skill_results.apply(
        lambda result: ", ".join(result[2])
    )
    ranked["detected_job_skills"] = skill_results.apply(
        lambda result: ", ".join(result[3])
    )

    # Retain the old column name for existing pages and services.
    ranked["missing_profile_skills"] = ranked[
        "missing_job_skills"
    ]

    ranked["base_match_score"] = (
        ranked["skill_score"]
        + ranked["suitability_score"]
    ).clip(upper=100)

    ranked["match_score"] = (
        ranked["base_match_score"]
        + ranked["freshness_bonus"]
    ).clip(upper=100)

    ranked["priority"] = ranked["match_score"].apply(
        lambda value: _priority_label(int(value))
    )

    ranked["resume_version"] = ranked["title"].apply(
        _recommend_resume
    )

    ranked = ranked.sort_values(
        by=[
            "match_score",
            "freshness_bonus",
            "date_posted",
        ],
        ascending=[False, False, False],
        na_position="last",
    )

    return ranked.reset_index(drop=True)
'@

Write-Utf8File "app\services\multi_job_search.py" @'
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from app.services.job_ranker import rank_jobs
from app.services.job_search import search_jobs


DEFAULT_CONFIG_PATH = Path("config/job_search.json")

RESULT_COLUMNS = [
    "site",
    "title",
    "company",
    "location",
    "date_posted",
    "job_type",
    "is_remote",
    "job_url",
    "description",
    "searched_role",
]


def load_search_config(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Job-search configuration was not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    required_fields = [
        "roles",
        "location",
        "sites",
        "results_per_role",
        "hours_old",
        "minimum_match_score",
        "maximum_digest_jobs",
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in config
    ]

    if missing_fields:
        raise ValueError(
            "Missing job-search configuration fields: "
            + ", ".join(missing_fields)
        )

    if not isinstance(config["roles"], list) or not config["roles"]:
        raise ValueError("'roles' must be a non-empty list.")

    if not isinstance(config["sites"], list) or not config["sites"]:
        raise ValueError("'sites' must be a non-empty list.")

    return config


def _empty_jobs() -> pd.DataFrame:
    return pd.DataFrame(columns=RESULT_COLUMNS)


def _ensure_columns(jobs: pd.DataFrame) -> pd.DataFrame:
    updated = jobs.copy()

    for column in RESULT_COLUMNS:
        if column not in updated.columns:
            updated[column] = None

    return updated


def _normalise_key(value: object) -> str:
    if value is None:
        return ""

    text = str(value).strip().lower()

    if text in {"nan", "none", "null"}:
        return ""

    return " ".join(text.split())


def remove_duplicate_jobs(
    jobs: pd.DataFrame,
) -> pd.DataFrame:
    if jobs is None or jobs.empty:
        return _empty_jobs()

    updated = _ensure_columns(jobs)

    updated["_normalised_url"] = updated["job_url"].apply(
        _normalise_key
    )
    updated["_normalised_company"] = updated["company"].apply(
        _normalise_key
    )
    updated["_normalised_title"] = updated["title"].apply(
        _normalise_key
    )
    updated["_normalised_location"] = updated["location"].apply(
        _normalise_key
    )

    with_url = updated[
        updated["_normalised_url"] != ""
    ].drop_duplicates(
        subset=["_normalised_url"],
        keep="first",
    )

    without_url = updated[
        updated["_normalised_url"] == ""
    ]

    combined = pd.concat(
        [with_url, without_url],
        ignore_index=True,
        sort=False,
    )

    combined = combined.drop_duplicates(
        subset=[
            "_normalised_company",
            "_normalised_title",
            "_normalised_location",
        ],
        keep="first",
    )

    combined = combined.drop(
        columns=[
            "_normalised_url",
            "_normalised_company",
            "_normalised_title",
            "_normalised_location",
        ],
        errors="ignore",
    )

    return combined.reset_index(drop=True)


def search_multiple_roles(
    roles: list[str],
    location: str,
    sites: list[str],
    results_per_role: int = 15,
    hours_old: int = 168,
) -> tuple[pd.DataFrame, list[str]]:
    if not roles:
        raise ValueError("At least one role is required.")

    if not sites:
        raise ValueError("At least one source is required.")

    collected_frames: list[pd.DataFrame] = []
    errors: list[str] = []

    for role in roles:
        clean_role = str(role).strip()

        if not clean_role:
            continue

        try:
            jobs = search_jobs(
                search_term=clean_role,
                location=location,
                results_wanted=results_per_role,
                hours_old=hours_old,
                sites=sites,
            )
        except Exception as exc:
            errors.append(f"{clean_role}: {exc}")
            continue

        if jobs is None or jobs.empty:
            continue

        jobs = jobs.copy()
        jobs["searched_role"] = clean_role
        collected_frames.append(jobs)

    if not collected_frames:
        return _empty_jobs(), errors

    combined = pd.concat(
        collected_frames,
        ignore_index=True,
        sort=False,
    )

    return remove_duplicate_jobs(combined), errors


def filter_ranked_jobs(
    ranked_jobs: pd.DataFrame,
    minimum_score: int = 45,
    maximum_jobs: int | None = None,
    exclude_senior_roles: bool = True,
) -> pd.DataFrame:
    if ranked_jobs is None or ranked_jobs.empty:
        return pd.DataFrame()

    filtered = ranked_jobs.copy()

    if exclude_senior_roles and "is_senior_role" in filtered.columns:
        filtered = filtered[
            filtered["is_senior_role"].fillna(False) == False
        ]

    if "match_score" in filtered.columns:
        filtered = filtered[
            filtered["match_score"] >= minimum_score
        ]

    filtered = filtered.sort_values(
        by=[
            "match_score",
            "freshness_bonus",
            "date_posted",
        ],
        ascending=[False, False, False],
        na_position="last",
    )

    if maximum_jobs is not None:
        filtered = filtered.head(int(maximum_jobs))

    return filtered.reset_index(drop=True)


def run_multi_role_search(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
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
    config = load_search_config(config_path)

    selected_roles = roles if roles is not None else config["roles"]
    selected_location = (
        location if location is not None else config["location"]
    )
    selected_sites = sites if sites is not None else config["sites"]
    selected_results_per_role = int(
        results_per_role
        if results_per_role is not None
        else config["results_per_role"]
    )
    selected_hours_old = int(
        hours_old
        if hours_old is not None
        else config["hours_old"]
    )
    selected_minimum_score = int(
        minimum_match_score
        if minimum_match_score is not None
        else config.get("minimum_match_score", 45)
    )
    selected_maximum_jobs = int(
        maximum_jobs
        if maximum_jobs is not None
        else config["maximum_digest_jobs"]
    )

    raw_jobs, errors = search_multiple_roles(
        roles=selected_roles,
        location=selected_location,
        sites=selected_sites,
        results_per_role=selected_results_per_role,
        hours_old=selected_hours_old,
    )

    ranked_jobs = (
        rank_jobs(raw_jobs)
        if not raw_jobs.empty
        else pd.DataFrame()
    )

    filtered_jobs = filter_ranked_jobs(
        ranked_jobs=ranked_jobs,
        minimum_score=selected_minimum_score,
        maximum_jobs=selected_maximum_jobs,
        exclude_senior_roles=exclude_senior_roles,
    )

    return {
        "roles": selected_roles,
        "location": selected_location,
        "sites": selected_sites,
        "jobs_collected": len(raw_jobs),
        "jobs_ranked": len(ranked_jobs),
        "strong_matches": len(filtered_jobs),
        "raw_jobs": raw_jobs,
        "ranked_jobs": ranked_jobs,
        "filtered_jobs": filtered_jobs,
        "errors": errors,
    }
'@

Write-Utf8File "app\services\job_pipeline.py" @'
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
'@

Write-Utf8File "pages\1_Job_Search.py" @'
from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from app.services.application_context import save_selected_job
from app.services.job_pipeline import run_pipeline
from app.services.job_repository import (
    get_saved_job_count,
    get_saved_jobs,
    save_job,
)
from app.services.multi_job_search import load_search_config


st.set_page_config(
    page_title="CareerPilot Smart Job Discovery",
    page_icon="🔍",
    layout="wide",
)


def display_value(value: object, fallback: str = "Not provided") -> str:
    if value is None:
        return fallback

    try:
        if pd.isna(value):
            return fallback
    except (TypeError, ValueError):
        pass

    text = str(value).strip()

    if text.lower() in {"", "nan", "none", "null"}:
        return fallback

    return text


config = load_search_config()

st.title("🔍 Smart Job Discovery")
st.caption(
    "Find fresh, suitable jobs; penalize senior roles; "
    "and prioritize opportunities worth applying to."
)

if "smart_job_results" not in st.session_state:
    st.session_state["smart_job_results"] = pd.DataFrame()

if "smart_job_all_ranked" not in st.session_state:
    st.session_state["smart_job_all_ranked"] = pd.DataFrame()

if "smart_job_summary" not in st.session_state:
    st.session_state["smart_job_summary"] = {}


with st.sidebar:
    st.header("Search Settings")

    search_mode = st.radio(
        "Search mode",
        ["Custom role", "All configured roles"],
        index=0,
    )

    custom_role = st.text_input(
        "Custom role",
        value="Data Analyst",
        disabled=search_mode != "Custom role",
    )

    location = st.text_input(
        "Location",
        value=config.get(
            "location",
            "Bengaluru, Karnataka",
        ),
    )

    selected_sites = st.multiselect(
        "Job sources",
        ["indeed", "linkedin", "google"],
        default=["indeed", "linkedin"],
    )

    posted_within = st.selectbox(
        "Posted within",
        [
            ("24 hours", 24),
            ("3 days", 72),
            ("7 days", 168),
            ("14 days", 336),
        ],
        format_func=lambda item: item[0],
        index=1,
    )

    results_per_role = st.slider(
        "Results per role",
        min_value=5,
        max_value=30,
        value=15,
        step=5,
    )

    minimum_score = st.slider(
        "Minimum match score",
        min_value=0,
        max_value=100,
        value=45,
        step=5,
    )

    maximum_jobs = st.slider(
        "Maximum jobs to show",
        min_value=5,
        max_value=100,
        value=30,
        step=5,
    )

    exclude_senior = st.checkbox(
        "Exclude senior roles",
        value=True,
    )

    run_search = st.button(
        "Search and Rank Jobs",
        type="primary",
        width="stretch",
    )


if run_search:
    if not selected_sites:
        st.error("Select at least one job source.")
    elif search_mode == "Custom role" and not custom_role.strip():
        st.error("Enter a role to search.")
    else:
        roles = (
            [custom_role.strip()]
            if search_mode == "Custom role"
            else config["roles"]
        )

        with st.spinner(
            "Searching, deduplicating, and ranking jobs..."
        ):
            try:
                result = run_pipeline(
                    roles=roles,
                    location=location.strip(),
                    sites=selected_sites,
                    results_per_role=results_per_role,
                    hours_old=posted_within[1],
                    minimum_match_score=minimum_score,
                    maximum_jobs=maximum_jobs,
                    exclude_senior_roles=exclude_senior,
                )

                st.session_state["smart_job_results"] = result["jobs"]
                st.session_state["smart_job_all_ranked"] = result[
                    "all_ranked_jobs"
                ]
                st.session_state["smart_job_summary"] = result["summary"]

            except Exception as exc:
                st.session_state["smart_job_results"] = pd.DataFrame()
                st.session_state["smart_job_all_ranked"] = pd.DataFrame()
                st.session_state["smart_job_summary"] = {}
                st.error(f"Job search failed: {exc}")


jobs = st.session_state["smart_job_results"]
all_ranked_jobs = st.session_state["smart_job_all_ranked"]
summary = st.session_state["smart_job_summary"]

metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric(
    "Roles Searched",
    summary.get("searched_roles", 0),
)
metric2.metric(
    "Jobs Collected",
    summary.get("jobs_found", 0),
)
metric3.metric(
    "Recommended Jobs",
    summary.get("recommended_jobs", 0),
)
metric4.metric(
    "Saved Jobs",
    get_saved_job_count(),
)

search_errors = summary.get("errors", [])

if search_errors:
    with st.expander(
        f"Search warnings ({len(search_errors)})"
    ):
        for error in search_errors:
            st.warning(error)

if summary and jobs.empty:
    st.warning(
        "The search worked, but no job met the current filters. "
        "Reduce the minimum score or include older postings."
    )

    if not all_ranked_jobs.empty:
        preview_columns = [
            "match_score",
            "priority",
            "freshness_label",
            "title",
            "company",
            "location",
            "is_senior_role",
        ]

        available_preview_columns = [
            column
            for column in preview_columns
            if column in all_ranked_jobs.columns
        ]

        st.caption(
            "Top collected jobs before the minimum-score "
            "and senior-role filters:"
        )
        st.dataframe(
            all_ranked_jobs[available_preview_columns].head(10),
            width="stretch",
            hide_index=True,
        )

elif not summary:
    st.info(
        "Choose the settings and click "
        "**Search and Rank Jobs**."
    )

else:
    st.success(
        f"Found {len(jobs)} recommended job"
        f"{'s' if len(jobs) != 1 else ''}."
    )

    table_columns = [
        "match_score",
        "priority",
        "freshness_label",
        "apply_urgency",
        "date_posted",
        "title",
        "company",
        "location",
        "site",
        "required_experience_years",
        "matched_skills",
        "resume_version",
    ]

    available_columns = [
        column
        for column in table_columns
        if column in jobs.columns
    ]

    st.subheader("Best Opportunities")
    st.dataframe(
        jobs[available_columns],
        width="stretch",
        hide_index=True,
    )

    st.divider()
    st.subheader("Job Details")

    for index, row in jobs.iterrows():
        score = int(row.get("match_score") or 0)
        title = display_value(row.get("title"), "Unknown Role")
        company = display_value(
            row.get("company"),
            "Unknown Company",
        )
        priority = display_value(
            row.get("priority"),
            "Review",
        )
        job_url = display_value(row.get("job_url"), "")

        with st.expander(
            f"{score}% — {title} at {company} — {priority}"
        ):
            left, right = st.columns([3, 1])

            with left:
                st.write(
                    f"**Location:** "
                    f"{display_value(row.get('location'))}"
                )
                st.write(
                    f"**Source:** "
                    f"{display_value(row.get('site'))}"
                )
                st.write(
                    f"**Posted:** "
                    f"{display_value(row.get('date_posted'), 'Unknown')}"
                )
                st.write(
                    f"**Freshness:** "
                    f"{display_value(row.get('freshness_label'), 'Unknown')}"
                )
                st.write(
                    f"**Recommended timing:** "
                    f"{display_value(row.get('apply_urgency'), 'Review normally')}"
                )

                required_experience = row.get(
                    "required_experience_years"
                )

                if (
                    required_experience is not None
                    and not pd.isna(required_experience)
                ):
                    st.write(
                        "**Detected minimum experience:** "
                        f"{int(required_experience)}+ years"
                    )
                else:
                    st.write(
                        "**Detected minimum experience:** "
                        "Not clearly stated"
                    )

                st.write(
                    f"**Matched skills:** "
                    f"{display_value(row.get('matched_skills'), 'None detected')}"
                )
                st.write(
                    f"**Missing job skills:** "
                    f"{display_value(row.get('missing_job_skills'), 'None detected')}"
                )
                st.write(
                    f"**Recommended resume:** "
                    f"{display_value(row.get('resume_version'), 'Data Analyst Resume')}"
                )

                reasons = display_value(
                    row.get("match_reasons"),
                    "",
                )

                if reasons:
                    st.markdown("**Why it matches**")
                    for reason in reasons.split("|"):
                        if reason.strip():
                            st.write(f"✅ {reason.strip()}")

                warnings = display_value(
                    row.get("match_warnings"),
                    "",
                )

                if warnings:
                    st.markdown("**Warnings**")
                    for warning in warnings.split("|"):
                        if warning.strip():
                            st.write(f"⚠️ {warning.strip()}")

                description = display_value(
                    row.get("description"),
                    "",
                )

                if description:
                    st.markdown("**Job description preview**")
                    st.write(
                        description[:2000]
                        + ("..." if len(description) > 2000 else "")
                    )

            with right:
                if job_url:
                    st.link_button(
                        "Open Job",
                        job_url,
                        width="stretch",
                    )

                if st.button(
                    "Save Job",
                    key=f"save_{index}_{job_url}",
                    width="stretch",
                ):
                    saved = save_job(row.to_dict())

                    if saved:
                        st.success("Job saved.")
                        st.rerun()
                    else:
                        st.warning("This job is already saved.")

                if st.button(
                    "Prepare Application",
                    key=f"prepare_{index}_{job_url}",
                    type="primary",
                    width="stretch",
                ):
                    save_selected_job(
                        st.session_state,
                        row.to_dict(),
                    )
                    st.switch_page(
                        "pages/2_Apply_Workflow.py"
                    )


st.divider()
st.subheader("Saved Jobs")

saved_jobs = get_saved_jobs()

if not saved_jobs:
    st.info("No jobs saved yet.")
else:
    saved_df = pd.DataFrame(saved_jobs)

    if "company" in saved_df.columns:
        saved_df["company"] = saved_df["company"].apply(
            lambda value: display_value(
                value,
                "Unknown Company",
            )
        )

    saved_columns = [
        "match_score",
        "role",
        "company",
        "location",
        "source",
        "status",
        "created_date",
        "job_link",
    ]

    available_saved_columns = [
        column
        for column in saved_columns
        if column in saved_df.columns
    ]

    st.dataframe(
        saved_df[available_saved_columns],
        width="stretch",
        hide_index=True,
    )
'@

Write-Utf8File "tests\smart_job_discovery_integration_test.py" @'
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import tempfile

import pandas as pd

from app.services.job_discovery.ranking import rank_jobs
from app.services.multi_job_search import (
    filter_ranked_jobs,
    remove_duplicate_jobs,
)


def main() -> None:
    now = datetime(
        2026,
        7,
        12,
        10,
        0,
        tzinfo=timezone.utc,
    )

    jobs = pd.DataFrame(
        [
            {
                "site": "test",
                "title": "Data Analyst",
                "company": "Fresh Analytics",
                "location": "Bengaluru, Karnataka",
                "date_posted": now - timedelta(hours=3),
                "job_type": "fulltime",
                "is_remote": False,
                "job_url": "https://example.com/data-1",
                "description": (
                    "SQL Excel Power BI Python dashboard "
                    "0 to 2 years experience"
                ),
                "searched_role": "Data Analyst",
            },
            {
                "site": "test",
                "title": "Data Analyst",
                "company": "Fresh Analytics",
                "location": "Bengaluru, Karnataka",
                "date_posted": now - timedelta(hours=3),
                "job_type": "fulltime",
                "is_remote": False,
                "job_url": "https://example.com/data-1",
                "description": (
                    "SQL Excel Power BI Python dashboard "
                    "0 to 2 years experience"
                ),
                "searched_role": "Power BI Analyst",
            },
            {
                "site": "test",
                "title": "Senior Data Engineering Manager",
                "company": "Senior Company",
                "location": "Bengaluru, Karnataka",
                "date_posted": now - timedelta(hours=1),
                "job_type": "fulltime",
                "is_remote": False,
                "job_url": "https://example.com/senior",
                "description": (
                    "8+ years Spark Snowflake leadership"
                ),
                "searched_role": "Data Analyst",
            },
            {
                "site": "test",
                "title": "Production Support Analyst",
                "company": None,
                "location": "Remote",
                "date_posted": now - timedelta(hours=10),
                "job_type": "fulltime",
                "is_remote": True,
                "job_url": "https://example.com/support",
                "description": (
                    "SQL Linux Jira ServiceNow AWS "
                    "1 to 2 years experience"
                ),
                "searched_role": "Production Support Analyst",
            },
        ]
    )

    profile = {
        "skills": [
            "Python",
            "SQL",
            "Power BI",
            "Excel",
            "Tableau",
            "Linux",
            "ServiceNow",
            "Jira",
            "Data Analysis",
            "AWS",
        ],
        "preferred_roles": [
            "Data Analyst",
            "Business Analyst",
            "Application Support Analyst",
            "Production Support Analyst",
        ],
        "preferred_locations": [
            "Bengaluru",
            "Bangalore",
            "Remote",
        ],
        "experience_years": 1.1,
    }

    deduplicated = remove_duplicate_jobs(jobs)

    assert len(deduplicated) == 3

    with tempfile.TemporaryDirectory() as temp_dir:
        profile_path = Path(temp_dir) / "profile.json"
        profile_path.write_text(
            json.dumps(profile),
            encoding="utf-8",
        )

        ranked = rank_jobs(
            deduplicated,
            profile_path=profile_path,
            now=now,
        )

    filtered = filter_ranked_jobs(
        ranked,
        minimum_score=45,
        maximum_jobs=10,
        exclude_senior_roles=True,
    )

    assert not filtered.empty
    assert "Senior Company" not in filtered["company"].tolist()
    assert "Fresh Analytics" in filtered["company"].tolist()
    assert "Unknown Company" in filtered["company"].tolist()
    assert filtered["match_score"].min() >= 45

    print("=" * 70)
    print("CAREERPILOT SMART JOB DISCOVERY INTEGRATION TEST")
    print("=" * 70)

    print(
        filtered[
            [
                "match_score",
                "priority",
                "freshness_label",
                "title",
                "company",
                "location",
                "matched_skills",
                "missing_job_skills",
            ]
        ].to_string(index=False)
    )

    print("\nSMART JOB DISCOVERY INTEGRATION TEST PASSED")


if __name__ == "__main__":
    main()
'@

Write-Host ""
Write-Host "Smart Job Discovery integrated sprint installed."
Write-Host "Next command:"
Write-Host ".\venv\Scripts\python.exe -m tests.smart_job_discovery_integration_test"
