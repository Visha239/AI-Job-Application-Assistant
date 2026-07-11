from __future__ import annotations

import pandas as pd
import streamlit as st

from app.services.job_ranker import rank_jobs
from app.services.job_repository import (
    get_saved_job_count,
    get_saved_jobs,
    save_job,
)
from app.services.job_search import search_jobs


st.set_page_config(
    page_title="CareerPilot Job Search",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 Job Discovery & Ranking")
st.caption(
    "Search current openings, rank them against your profile, "
    "and save the strongest opportunities."
)

with st.sidebar:
    st.header("Search Settings")

    search_term = st.text_input(
        "Role",
        value="Data Analyst",
        placeholder="Data Analyst",
    )

    location = st.text_input(
        "Location",
        value="Bengaluru, Karnataka",
    )

    results_wanted = st.slider(
        "Number of results",
        min_value=5,
        max_value=50,
        value=15,
        step=5,
    )

    date_range = st.selectbox(
        "Posted within",
        options=[
            ("24 hours", 24),
            ("3 days", 72),
            ("7 days", 168),
            ("14 days", 336),
        ],
        format_func=lambda item: item[0],
    )

    selected_sites = st.multiselect(
        "Job sources",
        options=["indeed", "linkedin", "google"],
        default=["indeed", "linkedin"],
    )

    search_button = st.button(
        "Search Jobs",
        type="primary",
        use_container_width=True,
    )


if "ranked_jobs" not in st.session_state:
    st.session_state.ranked_jobs = pd.DataFrame()


if search_button:
    if not search_term.strip():
        st.error("Enter a role to search.")
    elif not selected_sites:
        st.error("Select at least one job source.")
    else:
        with st.spinner("Searching and ranking jobs..."):
            try:
                raw_jobs = search_jobs(
                    search_term=search_term,
                    location=location,
                    results_wanted=results_wanted,
                    hours_old=date_range[1],
                    sites=selected_sites,
                )

                ranked_jobs = rank_jobs(raw_jobs)
                st.session_state.ranked_jobs = ranked_jobs

            except Exception as exc:
                st.session_state.ranked_jobs = pd.DataFrame()
                st.error(f"Job search failed: {exc}")


ranked_jobs = st.session_state.ranked_jobs

saved_count = get_saved_job_count()

metric1, metric2, metric3 = st.columns(3)

metric1.metric(
    "Jobs Found",
    len(ranked_jobs),
)

strong_matches = (
    int((ranked_jobs["match_score"] >= 70).sum())
    if not ranked_jobs.empty
    else 0
)

metric2.metric(
    "Strong Matches",
    strong_matches,
)

metric3.metric(
    "Saved Jobs",
    saved_count,
)


if ranked_jobs.empty:
    st.info(
        "Use the search settings on the left and click **Search Jobs**."
    )
else:
    st.subheader("Ranked Opportunities")

    display_columns = [
        "match_score",
        "title",
        "company",
        "location",
        "site",
        "resume_version",
    ]

    available_columns = [
        column
        for column in display_columns
        if column in ranked_jobs.columns
    ]

    st.dataframe(
        ranked_jobs[available_columns],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    for index, row in ranked_jobs.iterrows():
        title = str(row.get("title") or "Unknown Role")
        company = str(row.get("company") or "Unknown Company")
        score = int(row.get("match_score") or 0)

        with st.expander(
            f"{score}% — {title} at {company}"
        ):
            left, right = st.columns([3, 1])

            with left:
                st.write(
                    f"**Location:** {row.get('location') or 'Not provided'}"
                )
                st.write(
                    f"**Source:** {row.get('site') or 'Not provided'}"
                )
                st.write(
                    f"**Recommended resume:** "
                    f"{row.get('resume_version') or 'Data Analyst Resume'}"
                )

                matched = row.get("matched_skills") or "None detected"
                missing = (
                    row.get("missing_profile_skills")
                    or "None detected"
                )

                st.write(f"**Matched skills:** {matched}")
                st.write(f"**Profile skills not seen in JD:** {missing}")

                description = str(row.get("description") or "").strip()

                if description:
                    preview = (
                        description[:1_500] + "..."
                        if len(description) > 1_500
                        else description
                    )

                    st.markdown("**Job description preview**")
                    st.write(preview)

            with right:
                job_url = str(row.get("job_url") or "")

                if job_url:
                    st.link_button(
                        "Open Job",
                        job_url,
                        use_container_width=True,
                    )

                if st.button(
                    "Save Job",
                    key=f"save_job_{index}_{job_url}",
                    use_container_width=True,
                ):
                    saved = save_job(row.to_dict())

                    if saved:
                        st.success("Job saved to CareerPilot.")
                    else:
                        st.warning("This job is already saved.")


st.divider()
st.subheader("Saved Jobs")

saved_jobs = get_saved_jobs()

if saved_jobs:
    saved_df = pd.DataFrame(saved_jobs)

    preferred_columns = [
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
        for column in preferred_columns
        if column in saved_df.columns
    ]

    st.dataframe(
        saved_df[available_saved_columns],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No jobs saved yet.")