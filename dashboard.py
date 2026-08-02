from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from app.services.application_crm import (
    load_crm,
)
from app.services.application_queue import (
    load_queue,
)
from app.services.career_dashboard import (
    build_dashboard_snapshot,
)
from app.services.job_repository import (
    get_saved_jobs,
)
from app.services.outreach_manager import (
    load_records,
)
from app.services.resume_history import (
    get_resume_history,
)


PROFILE_PATH = Path("data/profile.json")


def load_profile() -> dict:
    try:
        with PROFILE_PATH.open(
            "r",
            encoding="utf-8-sig",
        ) as file:
            return json.load(file)
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {
            "name": "Vishal Banakar",
        }


def safe_saved_jobs() -> list[dict]:
    try:
        return get_saved_jobs()
    except Exception:
        return []


def safe_resume_count() -> int:
    try:
        history = get_resume_history()
        return len(history)
    except Exception:
        return 0


st.set_page_config(
    page_title="CareerPilot AI",
    page_icon="🚀",
    layout="wide",
)

profile = load_profile()

snapshot = build_dashboard_snapshot(
    crm_records=load_crm(),
    queue=load_queue(),
    outreach_records=load_records(),
    saved_jobs=safe_saved_jobs(),
    generated_resumes=safe_resume_count(),
)

metrics = snapshot["metrics"]

st.title("🚀 CareerPilot AI")
st.caption(
    f"Welcome, {profile.get('name', 'Vishal')}. "
    "Your complete job-search command center. Counts update automatically "
"when jobs are discovered or marked as applied."
)

primary = st.columns(4)

primary[0].metric(
    "Jobs Collected",
    metrics["saved_jobs"],
)
primary[1].metric(
    "Ready to Apply",
    metrics["queue_ready"],
)
primary[2].metric(
    "Applications Sent",
    metrics["applications_sent"],
)
primary[3].metric(
    "Applied Today",
    metrics["applied_today"],
)

secondary = st.columns(4)

secondary[0].metric(
    "Interviews",
    metrics["interviews"],
)
secondary[1].metric(
    "Offers",
    metrics["offers"],
)
secondary[2].metric(
    "Response Rate",
    f"{metrics['response_rate']}%",
)
secondary[3].metric(
    "Recruiters Contacted",
    metrics["recruiters_contacted"],
)

st.divider()

action1, action2, action3, action4 = st.columns(4)

with action1:
    if st.button(
        "Search Fresh Jobs",
        type="primary",
        width="stretch",
    ):
        st.switch_page(
            "pages/1_Job_Search.py"
        )

with action2:
    if st.button(
        "Open Application Queue",
        width="stretch",
    ):
        st.switch_page(
            "pages/10_Auto_Apply_Assistant.py"
        )

with action3:
    if st.button(
        "Open Application CRM",
        width="stretch",
    ):
        st.switch_page(
            "pages/11_Application_CRM.py"
        )

with action4:
    if st.button(
        "Recruiter Outreach",
        width="stretch",
    ):
        st.switch_page(
            "pages/9_Recruiter_Outreach.py"
        )

left, right = st.columns(
    [3, 2]
)

with left:
    st.subheader(
        "Application Pipeline"
    )

    pipeline_df = pd.DataFrame(
        snapshot["pipeline"]
    )

    if pipeline_df["count"].sum() == 0:
        st.info(
            "Add applications to the CRM to build your pipeline."
        )
    else:
        st.bar_chart(
            pipeline_df.set_index(
                "stage"
            )["count"],
            height=320,
        )

with right:
    st.subheader(
        "Upcoming Follow-ups"
    )

    followups = snapshot[
        "followups"
    ]

    if not followups:
        st.success(
            "No follow-ups are currently scheduled."
        )
    else:
        for item in followups[:6]:
            days = item[
                "days_until"
            ]

            if days < 0:
                timing = (
                    f"{abs(days)} day(s) overdue"
                )
            elif days == 0:
                timing = "Due today"
            else:
                timing = (
                    f"Due in {days} day(s)"
                )

            st.write(
                f"**{item['company']} — "
                f"{item['role']}**"
            )
            st.caption(
                f"{item['type']} · "
                f"{item['date']} · "
                f"{timing}"
            )

st.divider()

trend_col, source_col = st.columns(2)

with trend_col:
    st.subheader(
        "Weekly Application Progress"
    )

    weekly_df = pd.DataFrame(
        snapshot["weekly_trend"]
    )

    st.bar_chart(
        weekly_df.set_index(
            "week"
        )["applications"],
        height=280,
    )

with source_col:
    st.subheader(
        "Job Source Performance"
    )

    source_df = pd.DataFrame(
        snapshot[
            "source_performance"
        ]
    )

    if source_df.empty:
        st.info(
            "Source analytics will appear after applications are tracked."
        )
    else:
        st.dataframe(
            source_df,
            width="stretch",
            hide_index=True,
        )

st.divider()

skill_col, insight_col = st.columns(2)

with skill_col:
    st.subheader(
        "Most Frequent Matched Skills"
    )

    skill_df = pd.DataFrame(
        snapshot["skills"]
    )

    if skill_df.empty:
        st.info(
            "Save or queue jobs to build the skill profile."
        )
    else:
        st.bar_chart(
            skill_df.set_index(
                "skill"
            )["count"],
            height=300,
        )

with insight_col:
    st.subheader(
        "CareerPilot Insights"
    )

    for insight in snapshot[
        "insights"
    ]:
        st.info(insight)

st.divider()

st.subheader(
    "Recent Activity"
)

activity = snapshot[
    "recent_activity"
]

if not activity:
    st.info(
        "Your recent job-search activity will appear here."
    )
else:
    activity_df = pd.DataFrame(
        activity
    )

    st.dataframe(
        activity_df[
            [
                "timestamp",
                "category",
                "activity",
            ]
        ],
        width="stretch",
        hide_index=True,
    )

with st.sidebar:
    st.header(
        "CareerPilot Status"
    )
    st.metric(
        "Generated Resumes",
        metrics[
            "generated_resumes"
        ],
    )
    st.metric(
        "Follow-ups",
        len(
            snapshot[
                "followups"
            ]
        ),
    )
    st.caption(
        "Use the page navigation above to access "
        "Job Search, Application Copilot, Recruiter Outreach, "
        "Auto Apply Assistant, and Application CRM."
    )
