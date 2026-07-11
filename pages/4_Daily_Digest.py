from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from app.services.daily_job_digest import (
    load_job_search_config,
    run_daily_digest,
)


st.set_page_config(
    page_title="CareerPilot Daily Digest",
    page_icon="📬",
    layout="wide",
)

st.title("📬 Daily Job Digest")
st.caption(
    "Search all target roles, rank strong opportunities, "
    "save new jobs and generate a daily report."
)

config = load_job_search_config()

with st.expander("Current Search Configuration"):
    st.write("**Roles:**")
    for role in config["roles"]:
        st.write(f"• {role}")

    st.write(f"**Location:** {config['location']}")
    st.write(
        "**Sources:** "
        + ", ".join(config["sites"])
    )
    st.write(
        "**Minimum match score:** "
        f"{config['minimum_match_score']}%"
    )
    st.write(
        "**Maximum report jobs:** "
        f"{config['maximum_digest_jobs']}"
    )

if st.button(
    "Run Daily Job Search",
    type="primary",
    width="stretch",
):
    with st.spinner(
        "Searching all target roles and creating your digest..."
    ):
        try:
            result = run_daily_digest()
            st.session_state["daily_digest_result"] = result

        except Exception as exc:
            st.error(f"Daily job search failed: {exc}")


result = st.session_state.get("daily_digest_result")

if result:
    row1 = st.columns(4)

    row1[0].metric(
        "Jobs Collected",
        result["jobs_collected"],
    )

    row1[1].metric(
        "Strong Matches",
        result["strong_matches"],
    )

    row1[2].metric(
        "New Jobs Saved",
        result["saved_jobs"],
    )

    row1[3].metric(
        "Duplicates Skipped",
        result["duplicate_jobs"],
    )

    if result["errors"]:
        with st.expander(
            f"Source warnings ({len(result['errors'])})"
        ):
            for error in result["errors"]:
                st.warning(error)

    ranked_jobs = result["ranked_jobs"]

    if ranked_jobs.empty:
        st.info(
            "No jobs met the configured minimum match score."
        )
    else:
        st.subheader("Top Daily Matches")

        columns = [
            "match_score",
            "title",
            "company",
            "location",
            "site",
            "resume_version",
            "job_url",
        ]

        available_columns = [
            column
            for column in columns
            if column in ranked_jobs.columns
        ]

        st.dataframe(
            ranked_jobs[available_columns],
            width="stretch",
            hide_index=True,
        )

    st.divider()
    st.subheader("Digest Preview")

    html_path = Path(result["html_path"])

    if html_path.exists():
        html_content = html_path.read_text(
            encoding="utf-8"
        )

        components.html(
            html_content,
            height=900,
            scrolling=True,
        )

        st.download_button(
            label="Download HTML Digest",
            data=html_content,
            file_name=html_path.name,
            mime="text/html",
            width="stretch",
        )

    csv_path = Path(result["csv_path"])

    if csv_path.exists():
        st.download_button(
            label="Download Ranked Jobs CSV",
            data=csv_path.read_bytes(),
            file_name=csv_path.name,
            mime="text/csv",
            width="stretch",
        )