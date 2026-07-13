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
    page_icon="ðŸ”",
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

st.title("ðŸ” Smart Job Discovery")
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
            f"{score}% â€” {title} at {company} â€” {priority}"
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
                            st.write(f"âœ… {reason.strip()}")

                warnings = display_value(
                    row.get("match_warnings"),
                    "",
                )

                if warnings:
                    st.markdown("**Warnings**")
                    for warning in warnings.split("|"):
                        if warning.strip():
                            st.write(f"âš ï¸ {warning.strip()}")

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
