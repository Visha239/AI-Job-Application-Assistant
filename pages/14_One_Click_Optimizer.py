from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from app.services.application_context import (
    get_selected_job,
)
from app.services.one_click_optimizer import (
    prepare_one_click_application,
)
from app.services.resume_intelligence_v2 import (
    DEFAULT_MASTER_RESUME,
)
from app.utils.config_loader import (
    get_role_names,
)


PROFILE_PATH = Path(
    "data/profile.json"
)


def load_profile() -> dict:
    with PROFILE_PATH.open(
        "r",
        encoding="utf-8-sig",
    ) as file:
        return json.load(file)


def recommended_resume_type(
    selected_job: dict,
) -> str:
    available = get_role_names()
    recommended = str(
        selected_job.get(
            "resume_version",
            "",
        )
    ).lower()

    if "support" in recommended:
        target = "Support Engineer"
    elif "business" in recommended:
        target = "Business Analyst"
    else:
        target = "Data Analyst"

    return (
        target
        if target in available
        else available[0]
    )


st.set_page_config(
    page_title=(
        "CareerPilot One-Click Optimizer"
    ),
    page_icon="⚡",
    layout="wide",
)

profile = load_profile()
selected_job = get_selected_job(
    st.session_state
)

st.title(
    "⚡ One-Click Resume Optimizer"
)
st.caption(
    "Prepare the resume, ATS package, CRM entry, queue status, "
    "and recruiter outreach draft in one workflow."
)

st.warning(
    "CareerPilot prepares the application package but does not "
    "submit the application automatically. Review everything first."
)

if not selected_job:
    st.info(
        "No job is selected. Open Job Search and click Prepare Application."
    )

    if st.button(
        "Open Job Search",
        type="primary",
        width="stretch",
    ):
        st.switch_page(
            "pages/1_Job_Search.py"
        )

    st.stop()

company = selected_job.get(
    "company",
    "Unknown Company",
)
role = selected_job.get(
    "job_role",
    "Unknown Role",
)
job_link = selected_job.get(
    "job_link",
    "",
)
job_description = selected_job.get(
    "job_description",
    "",
)

st.success(
    f"Selected automatically: "
    f"{role} at {company}"
)

metric1, metric2, metric3 = (
    st.columns(3)
)

metric1.metric(
    "Search Match",
    f"{selected_job.get('match_score', 0)}%",
)
metric2.metric(
    "Priority",
    selected_job.get(
        "priority",
        "Review",
    ),
)
metric3.metric(
    "JD Status",
    (
        "Ready"
        if len(
            job_description.strip()
        )
        >= 100
        else "Incomplete"
    ),
)

with st.expander(
    "Review Selected Job"
):
    st.write(
        f"**Company:** {company}"
    )
    st.write(
        f"**Role:** {role}"
    )
    st.write(
        f"**Location:** "
        f"{selected_job.get('location') or 'Not provided'}"
    )
    st.write(
        f"**Job Link:** "
        f"{job_link or 'Not provided'}"
    )
    st.text_area(
        "Job Description",
        value=job_description,
        height=260,
        disabled=True,
    )

available_resumes = get_role_names()
default_resume = (
    recommended_resume_type(
        selected_job
    )
)

resume_type = st.selectbox(
    "Resume Version",
    options=available_resumes,
    index=available_resumes.index(
        default_resume
    ),
)

source_resume = st.text_input(
    "Source Resume",
    value=str(
        DEFAULT_MASTER_RESUME
    ),
    help=(
        "CareerPilot will tailor this DOCX file. "
        "The original file is not overwritten."
    ),
)

option1, option2 = st.columns(2)

with option1:
    create_crm = st.checkbox(
        "Create CRM record",
        value=True,
    )

with option2:
    create_outreach = st.checkbox(
        "Create recruiter outreach draft",
        value=True,
    )

if len(
    job_description.strip()
) < 100:
    st.error(
        "The selected job description is incomplete. "
        "Open Application Copilot and capture or paste the full JD first."
    )

    if st.button(
        "Open Application Copilot",
        type="primary",
        width="stretch",
    ):
        st.switch_page(
            "pages/2_Apply_Workflow.py"
        )

    st.stop()

if st.button(
    "Prepare Complete Application in One Click",
    type="primary",
    width="stretch",
):
    try:
        with st.spinner(
            "Preparing resume and application package..."
        ):
            result = (
                prepare_one_click_application(
                    session_state=(
                        st.session_state
                    ),
                    profile=profile,
                    selected_job=(
                        selected_job
                    ),
                    resume_type=resume_type,
                    source_resume_path=(
                        source_resume
                    ),
                    status=(
                        "Ready to Apply"
                    ),
                    queue_id=str(
                        selected_job.get(
                            "queue_id",
                            "",
                        )
                    ),
                    create_crm_record=(
                        create_crm
                    ),
                    create_outreach_draft=(
                        create_outreach
                    ),
                )
            )

            st.session_state[
                "one_click_result"
            ] = result

    except Exception as exc:
        st.error(
            f"One-click preparation failed: {exc}"
        )

result = st.session_state.get(
    "one_click_result"
)

if result:
    st.success(
        "Complete application package prepared."
    )

    result1, result2, result3 = (
        st.columns(3)
    )

    result1.metric(
        "ATS Score",
        f"{result['ats_score']}%",
    )
    result2.metric(
        "Matched Skills",
        len(
            result[
                "matched_skills"
            ]
        ),
    )
    result3.metric(
        "Missing Skills",
        len(
            result[
                "missing_skills"
            ]
        ),
    )

    st.subheader(
        "Completed Actions"
    )

    st.write(
        "✅ Application package generated"
    )
    st.write(
        "✅ Truthful tailored resume generated"
    )
    st.write(
        "✅ Shared job context updated"
    )
    st.write(
        (
            "✅ Queue updated"
            if result[
                "queue_updated"
            ]
            else "ℹ️ Queue was not linked"
        )
    )
    st.write(
        (
            "✅ CRM record created or already existed"
            if create_crm
            else "ℹ️ CRM creation skipped"
        )
    )
    st.write(
        (
            "✅ Recruiter outreach draft created"
            if (
                create_outreach
                and result[
                    "outreach_record"
                ]
            )
            else "ℹ️ Outreach draft skipped or already unavailable"
        )
    )

    st.subheader(
        "Skill Summary"
    )

    left, right = st.columns(2)

    with left:
        st.write(
            "**Verified Matches**"
        )

        for skill in result[
            "matched_skills"
        ]:
            st.write(
                f"✅ {skill}"
            )

    with right:
        st.write(
            "**Missing - Do Not Invent**"
        )

        if result[
            "missing_skills"
        ]:
            for skill in result[
                "missing_skills"
            ]:
                st.write(
                    f"⚠️ {skill}"
                )
        else:
            st.success(
                "No recognized missing skills."
            )

    resume_path = Path(
        result[
            "final_resume_path"
        ]
    )
    summary_path = Path(
        result[
            "summary_path"
        ]
    )

    download1, download2 = (
        st.columns(2)
    )

    with download1:
        if resume_path.exists():
            st.download_button(
                "Download Final Tailored Resume",
                data=(
                    resume_path.read_bytes()
                ),
                file_name=(
                    resume_path.name
                ),
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
                width="stretch",
            )

    with download2:
        if summary_path.exists():
            st.download_button(
                "Download Application Summary",
                data=(
                    summary_path.read_bytes()
                ),
                file_name=(
                    summary_path.name
                ),
                mime="text/plain",
                width="stretch",
            )

    action1, action2, action3 = (
        st.columns(3)
    )

    with action1:
        if job_link:
            st.link_button(
                "Open Official Job Page",
                job_link,
                width="stretch",
            )

    with action2:
        if st.button(
            "Open Recruiter Outreach",
            width="stretch",
        ):
            st.switch_page(
                "pages/9_Recruiter_Outreach.py"
            )

    with action3:
        if st.button(
            "Open Application CRM",
            width="stretch",
        ):
            st.switch_page(
                "pages/11_Application_CRM.py"
            )
