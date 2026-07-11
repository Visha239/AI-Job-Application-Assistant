from __future__ import annotations

import pandas as pd
import streamlit as st

from app.services.analytics import (
    get_dashboard_metrics,
    get_recent_applications,
    get_status_distribution,
    get_top_matched_skills,
)
from app.services.resume_history import get_resume_history


st.set_page_config(
    page_title="CareerPilot Analytics",
    page_icon="📊",
    layout="wide",
)

st.title("📊 CareerPilot Analytics")
st.caption(
    "Track applications, interviews, resumes and skill trends."
)

metrics = get_dashboard_metrics()

row1 = st.columns(4)

row1[0].metric(
    "Applications",
    metrics["total_applications"],
)

row1[1].metric(
    "Interviews",
    metrics["interviews"],
)

row1[2].metric(
    "Offers",
    metrics["offers"],
)

row1[3].metric(
    "Interview Rate",
    f"{metrics['interview_rate']}%",
)

row2 = st.columns(4)

row2[0].metric(
    "Ready to Apply",
    metrics["ready_to_apply"],
)

row2[1].metric(
    "Saved Jobs",
    metrics["saved_jobs"],
)

row2[2].metric(
    "Generated Resumes",
    metrics["generated_resumes"],
)

row2[3].metric(
    "Average Job Match",
    f"{metrics['average_match_score']}%",
)

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Application Status")

    status_data = get_status_distribution()

    if status_data:
        status_df = pd.DataFrame(status_data)

        st.bar_chart(
            status_df.set_index("status")["total"],
        )
    else:
        st.info("No application data yet.")

with right:
    st.subheader("Most Matched Skills")

    skill_data = get_top_matched_skills()

    if skill_data:
        skill_df = pd.DataFrame(skill_data)

        st.bar_chart(
            skill_df.set_index("skill")["count"],
        )
    else:
        st.info("No saved-job skill data yet.")

st.divider()
st.subheader("Recent Applications")

applications = get_recent_applications()

if applications:
    st.dataframe(
        pd.DataFrame(applications),
        width="stretch",
        hide_index=True,
    )
else:
    st.info("No applications saved yet.")

st.divider()
st.subheader("Resume History")

resume_history = get_resume_history()

if resume_history:
    resume_df = pd.DataFrame(resume_history)

    preferred_columns = [
        "resume_name",
        "role_type",
        "ats_score",
        "created_date",
        "file_path",
    ]

    available_columns = [
        column
        for column in preferred_columns
        if column in resume_df.columns
    ]

    st.dataframe(
        resume_df[available_columns],
        width="stretch",
        hide_index=True,
    )
else:
    st.info("No optimized resumes generated yet.")