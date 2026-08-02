from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from app.services.application_context import save_selected_job
from app.services.live_job_crm import (
    FRESH_EDITOR_STAGES,
    build_live_search_editor,
    persist_live_search_statuses,
    sync_search_results_to_crm,
)
from app.services.job_pipeline import run_pipeline
from app.services.application_tracking import (
    mark_job_applied,
    track_job,
)
from app.services.job_repository import (
    get_saved_job_count,
    get_saved_jobs,
    save_job,
)
from app.services.multi_job_search import load_search_config
from app.services.job_connectors.registry import enabled_connector_map, connector_groups


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
source_groups = connector_groups()
source_map = enabled_connector_map()

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

    st.subheader("Priority 1 — Official company careers")
    company_options = source_groups.get("company_careers", [])
    selected_companies = st.multiselect(
        "Official ATS and company career sites",
        options=[item.key for item in company_options],
        default=[item.key for item in company_options[:8]],
        format_func=lambda key: source_map[key].label,
        help=(
            "These sources are checked before job portals. Start with 5–8 "
            "companies for faster searches."
        ),
    )

    st.subheader("Priority 2 — General job boards")
    board_options = source_groups.get("job_board", [])
    selected_boards = st.multiselect(
        "LinkedIn and Indeed",
        options=[item.key for item in board_options],
        default=[item.key for item in board_options],
        format_func=lambda key: source_map[key].label,
    )

    st.subheader("Priority 3 — Manual India searches")
    india_options = source_groups.get("india_board", [])
    selected_india_boards = st.multiselect(
        "Naukri, Foundit and Internshala",
        options=[item.key for item in india_options],
        default=[item.key for item in india_options[:2]],
        format_func=lambda key: source_map[key].label,
    )

    selected_ats_sources = []

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

    maximum_required_experience = st.slider(
        "Maximum required experience",
        min_value=0.0,
        max_value=5.0,
        value=float(config.get("maximum_required_experience", 2.0)),
        step=0.5,
        help="Jobs with a detected minimum above this value are rejected before ranking.",
    )

    exclude_senior = st.checkbox(
        "Exclude senior roles",
        value=bool(config.get("exclude_senior_roles", True)),
    )

    st.divider()
    selected_source_keys = (
        selected_boards
        + selected_india_boards
        + selected_ats_sources
        + selected_companies
    )

    run_search = st.button(
        "Search and Rank Jobs",
        type="primary",
        width="stretch",
    )


if run_search:
    no_sources_selected = not selected_source_keys

    if no_sources_selected:
        st.error(
            "Select at least one source: a job board, Naukri, "
            "or an official company-careers source."
        )
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
                    sites=[],
                    results_per_role=results_per_role,
                    hours_old=posted_within[1],
                    minimum_match_score=minimum_score,
                    maximum_jobs=maximum_jobs,
                    exclude_senior_roles=exclude_senior,
                    maximum_required_experience=maximum_required_experience,
                    include_naukri=False,
                    include_company_careers=False,
                    selected_companies=[],
                    selected_source_keys=selected_source_keys,
                )

                sync_result = sync_search_results_to_crm(
                    result["jobs"]
                )

                st.session_state["smart_job_results"] = result["jobs"]
                st.session_state["smart_job_all_ranked"] = result[
                    "all_ranked_jobs"
                ]
                st.session_state["smart_job_summary"] = {
                    **result["summary"],
                    "crm_created": sync_result["created"],
                    "crm_existing": sync_result["existing"],
                }

            except Exception as exc:
                st.session_state["smart_job_results"] = pd.DataFrame()
                st.session_state["smart_job_all_ranked"] = pd.DataFrame()
                st.session_state["smart_job_summary"] = {}
                st.error(f"Job search failed: {exc}")


jobs = st.session_state["smart_job_results"]
all_ranked_jobs = st.session_state["smart_job_all_ranked"]
summary = st.session_state["smart_job_summary"]

live_jobs, hidden_applied_jobs = build_live_search_editor(
    jobs
)

if summary:
    summary = dict(summary)
    summary["recommended_jobs"] = len(live_jobs)
    summary["already_applied_hidden"] = hidden_applied_jobs

metric1, metric2, metric3, metric4, metric5 = st.columns(5)

metric1.metric("Roles Searched", summary.get("searched_roles", 0))
metric2.metric("Jobs Collected", summary.get("jobs_found", 0))
metric3.metric("Duplicates Removed", summary.get("duplicates_removed", 0))
metric4.metric("Experience Rejected", summary.get("experience_rejected", 0))
metric5.metric("Recommended Jobs", summary.get("recommended_jobs", 0))

source_counts = summary.get("source_counts", {})
st.caption(
    "Collected — "
    f"General boards: {source_counts.get('job_boards', 0)} | "
    f"India boards: {source_counts.get('india_boards', 0)} | "
    f"Official careers: {source_counts.get('official_total', 0)} | "
    f"ATS platforms: {source_counts.get('ats_platforms', 0)} | "
    f"Already applied hidden: {summary.get('already_applied_hidden', 0)} | "
    f"Saved jobs: {get_saved_job_count()}"
)

direct_links = summary.get("direct_links", [])
if direct_links:
    with st.expander("Open manual job searches"):
        for item in direct_links:
            st.link_button(
                f"Open {item['source']} — {item['role']}",
                item["url"],
            )


search_errors = summary.get("errors", [])
source_runs = summary.get("source_runs", [])

if source_runs:
    with st.expander("Source health and priority report"):
        st.dataframe(
            pd.DataFrame(source_runs),
            width="stretch",
            hide_index=True,
        )

if search_errors:
    with st.expander(
        f"Search warnings ({len(search_errors)})"
    ):
        for error in search_errors:
            st.warning(error)

if summary and live_jobs.empty:
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
        f"Found {len(live_jobs)} recommended job"
        f"{'s' if len(live_jobs) != 1 else ''}."
    )

    st.subheader("Live Job Search Results")
    st.caption(
        "These are the current search results. Change Status to Applied and "
        "click Save Status Changes. The job will disappear here, move to the "
        "Application Tracker, and stay hidden in future searches."
    )

    editor_columns = [
        "record_id",
        "match_score",
        "company",
        "title",
        "site",
        "location",
        "date_posted",
        "job_url",
        "stage",
    ]

    edited_live_jobs = st.data_editor(
        live_jobs[editor_columns],
        width="stretch",
        hide_index=True,
        num_rows="fixed",
        disabled=[
            "record_id",
            "match_score",
            "company",
            "title",
            "site",
            "location",
            "date_posted",
            "job_url",
        ],
        column_config={
            "record_id": None,
            "match_score": st.column_config.ProgressColumn(
                "Match",
                min_value=0,
                max_value=100,
                format="%d%%",
            ),
            "company": st.column_config.TextColumn("Company"),
            "title": st.column_config.TextColumn("Job"),
            "site": st.column_config.TextColumn("Source"),
            "location": st.column_config.TextColumn("Location"),
            "date_posted": st.column_config.DateColumn(
                "Posted",
                format="DD-MM-YYYY",
            ),
            "job_url": st.column_config.LinkColumn(
                "Open Job",
                display_text="Open",
            ),
            "stage": st.column_config.SelectboxColumn(
                "Status",
                options=FRESH_EDITOR_STAGES,
                required=True,
            ),
        },
        key="live_job_search_status_editor",
    )

    if st.button(
        "Save Status Changes",
        type="primary",
        width="stretch",
    ):
        status_result = persist_live_search_statuses(
            live_jobs,
            edited_live_jobs,
        )

        if status_result["errors"]:
            st.error(
                f"Saved {status_result['updated']} change(s), but "
                f"{status_result['errors']} change(s) failed."
            )
        elif status_result["updated"]:
            st.success(
                f"Updated {status_result['updated']} job(s). Applied jobs "
                "moved to the Application Tracker."
            )
            st.rerun()
        else:
            st.info("No status changes were detected.")

    st.divider()
    st.subheader("Job Details")

    for index, row in live_jobs.iterrows():
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

                st.write(
                    f"**Required experience:** "
                    f"{display_value(row.get('experience_label'), 'Not clearly stated')}"
                )
                st.write(
                    f"**Eligibility:** "
                    f"{display_value(row.get('eligibility_status'), 'Eligible')}"
                )
                evidence = display_value(row.get("experience_evidence"), "")
                if evidence:
                    st.caption(f"Detected from JD: {evidence}")

                duplicate_count = int(row.get("duplicate_count") or 1)
                if duplicate_count > 1:
                    st.write(
                        f"**Merged duplicates:** {duplicate_count} listings "
                        f"from {display_value(row.get('available_sources'), 'multiple sources')}"
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
                    job_data = row.to_dict()
                    saved = save_job(job_data)
                    tracked = track_job(
                        job_data,
                        stage="Saved",
                    )

                    if saved or tracked["created"]:
                        st.success(
                            "Job saved and added to your automatic tracker."
                        )
                        st.rerun()
                    else:
                        st.warning(
                            "This job is already saved and tracked."
                        )

                if st.button(
                    "Mark Applied",
                    key=f"applied_{index}_{job_url}",
                    type="primary",
                    width="stretch",
                ):
                    result = mark_job_applied(
                        row.to_dict()
                    )

                    if result["created"] or result["updated"]:
                        st.success(
                            "Application recorded. Dashboard updated automatically."
                        )
                        st.rerun()
                    else:
                        st.info(
                            "This application is already recorded."
                        )

                if st.button(
                    "Prepare Application",
                    key=f"prepare_{index}_{job_url}",
                    type="primary",
                    width="stretch",
                ):
                    job_data = row.to_dict()
                    track_job(
                        job_data,
                        stage="Ready to Apply",
                    )
                    save_selected_job(
                        st.session_state,
                        job_data,
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
