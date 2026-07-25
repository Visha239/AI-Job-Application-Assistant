from __future__ import annotations

import pandas as pd
import streamlit as st

from app.services.application_context import (
    get_selected_job,
)
from app.services.application_crm import (
    load_crm,
)
from app.services.application_queue import (
    load_queue,
)
from app.services.career_coach import (
    build_coach_snapshot,
)
from app.services.job_repository import (
    get_saved_jobs,
)
from app.services.outreach_manager import (
    load_records,
)


def safe_saved_jobs() -> list[dict]:
    try:
        return get_saved_jobs()
    except Exception:
        return []


st.set_page_config(
    page_title="CareerPilot Career Coach",
    page_icon="🧭",
    layout="wide",
)

selected_job = get_selected_job(
    st.session_state
)

snapshot = build_coach_snapshot(
    selected_job=selected_job,
    crm_records=load_crm(),
    queue=load_queue(),
    outreach_records=load_records(),
    saved_jobs=safe_saved_jobs(),
)

job = snapshot[
    "job_explanation"
]
strategy = snapshot[
    "strategy"
]

st.title(
    "🧭 Career Coach & Application Intelligence"
)
st.caption(
    "Turn your job-search data into clear priorities and practical actions."
)

st.warning(
    "CareerPilot recommendations are based only on your saved local data. "
    "They are guidance, not guarantees of interviews, salary, or hiring outcomes."
)

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Selected Job",
        "Application Strategy",
        "Skill Gap Plan",
        "Today's Actions",
    ]
)

with tab1:
    if not selected_job:
        st.info(
            "No job is selected. Open Job Search and click Prepare Application."
        )
    else:
        st.subheader(
            f"{selected_job.get('job_role') or 'Role'} at "
            f"{selected_job.get('company') or 'Company'}"
        )

        metric1, metric2, metric3 = (
            st.columns(3)
        )

        metric1.metric(
            "Match Score",
            f"{job['score']}%",
        )
        metric2.metric(
            "Fit",
            job["fit_label"],
        )
        metric3.metric(
            "Role Family",
            job["role_family"],
        )

        st.success(
            job["recommendation"]
        )

        left, right = st.columns(2)

        with left:
            st.subheader(
                "Why It Matches"
            )

            if job["matched_skills"]:
                for skill in job[
                    "matched_skills"
                ]:
                    st.write(
                        f"✅ {skill}"
                    )
            else:
                st.info(
                    "No matched skills are currently recorded."
                )

        with right:
            st.subheader(
                "Gaps to Review"
            )

            if job["missing_skills"]:
                for skill in job[
                    "missing_skills"
                ]:
                    st.write(
                        f"⚠️ {skill}"
                    )
            else:
                st.success(
                    "No recorded skill gaps."
                )

        st.subheader(
            "Supporting Evidence"
        )

        for evidence in job[
            "evidence"
        ]:
            st.write(
                f"• {evidence}"
            )

with tab2:
    st.subheader(
        "Application Strategy"
    )

    metric1, metric2, metric3, metric4 = (
        st.columns(4)
    )

    metric1.metric(
        "Applications",
        strategy["applications"],
    )
    metric2.metric(
        "Responses",
        strategy["responses"],
    )
    metric3.metric(
        "Interviews",
        strategy["interviews"],
    )
    metric4.metric(
        "Response Rate",
        f"{strategy['response_rate']}%",
    )

    st.subheader(
        "Recommended Changes"
    )

    for recommendation in strategy[
        "recommendations"
    ]:
        st.info(
            recommendation
        )

    source_df = pd.DataFrame(
        strategy[
            "source_performance"
        ]
    )

    if not source_df.empty:
        st.subheader(
            "Source Performance"
        )
        st.dataframe(
            source_df,
            width="stretch",
            hide_index=True,
        )

with tab3:
    st.subheader(
        "Skill Gap Learning Priorities"
    )

    skill_plan = snapshot[
        "skill_gap_plan"
    ]

    if not skill_plan:
        st.success(
            "CareerPilot has not detected recurring missing skills yet."
        )
    else:
        skill_df = pd.DataFrame(
            skill_plan
        )

        st.dataframe(
            skill_df,
            width="stretch",
            hide_index=True,
        )

        st.caption(
            "Only claim a skill on your resume after gaining genuine knowledge "
            "or practical experience."
        )

with tab4:
    st.subheader(
        "Today's Action Plan"
    )

    for item in snapshot[
        "daily_actions"
    ]:
        st.markdown(
            f"### {item['priority']}. {item['action']}"
        )
        st.caption(
            item["reason"]
        )

    st.divider()

    action1, action2, action3 = (
        st.columns(3)
    )

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
