from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from app.services.application_context import (
    context_fingerprint,
    get_selected_job,
    update_selected_job,
)
from app.services.application_package import (
    build_application_package,
    export_application_summary,
)
from app.services.jd_capture import resolve_job_description
from app.services.tracker import save_application
from app.utils.config_loader import get_role_names


PROFILE_PATH = Path("data/profile.json")


def load_profile() -> dict:
    with PROFILE_PATH.open(
        "r",
        encoding="utf-8-sig",
    ) as file:
        return json.load(file)


def map_resume_type(
    recommended_resume: str,
) -> str:
    role_names = get_role_names()
    recommended = recommended_resume.lower()

    if "support" in recommended:
        target = "Support Engineer"
    elif "business" in recommended:
        target = "Business Analyst"
    else:
        target = "Data Analyst"

    return target if target in role_names else role_names[0]


def sync_form_with_selected_job(
    selected_job: dict,
) -> None:
    fingerprint = context_fingerprint(
        selected_job
    )

    if (
        st.session_state.get(
            "apply_context_fingerprint"
        )
        == fingerprint
    ):
        return

    st.session_state[
        "apply_context_fingerprint"
    ] = fingerprint

    st.session_state["apply_company"] = (
        selected_job.get("company", "")
    )
    st.session_state["apply_role"] = (
        selected_job.get("job_role", "")
    )
    st.session_state["apply_location"] = (
        selected_job.get(
            "location",
            "Bengaluru, Karnataka",
        )
    )
    st.session_state["apply_job_link"] = (
        selected_job.get("job_link", "")
    )
    st.session_state["application_jd"] = (
        selected_job.get(
            "job_description",
            "",
        )
    )
    st.session_state["application_package"] = None
    st.session_state["jd_capture_message"] = ""
    st.session_state["jd_capture_status"] = ""


st.set_page_config(
    page_title="CareerPilot Application Copilot",
    page_icon="🚀",
    layout="wide",
)

profile = load_profile()
selected_job = get_selected_job(st.session_state)

if selected_job:
    sync_form_with_selected_job(
        selected_job
    )

st.session_state.setdefault(
    "apply_company",
    selected_job.get("company", ""),
)
st.session_state.setdefault(
    "apply_role",
    selected_job.get("job_role", ""),
)
st.session_state.setdefault(
    "apply_location",
    selected_job.get(
        "location",
        "Bengaluru, Karnataka",
    ),
)
st.session_state.setdefault(
    "apply_job_link",
    selected_job.get("job_link", ""),
)
st.session_state.setdefault(
    "application_jd",
    selected_job.get(
        "job_description",
        "",
    ),
)
st.session_state.setdefault(
    "jd_capture_message",
    "",
)
st.session_state.setdefault(
    "jd_capture_status",
    "",
)

default_resume_type = map_resume_type(
    selected_job.get(
        "resume_version",
        "Data Analyst Resume",
    )
)

st.title("🚀 Application Copilot")
st.caption(
    "Capture the JD, calculate a realistic ATS score, "
    "create a truthful resume package, and track the application."
)

if selected_job:
    st.success(
        f"Loaded automatically: "
        f"{selected_job.get('job_role') or 'Unknown Role'} at "
        f"{selected_job.get('company') or 'Unknown Company'}"
    )

    quick1, quick2, quick3 = st.columns(3)

    quick1.metric(
        "Search Match",
        f"{selected_job.get('match_score', 0)}%",
    )
    quick2.metric(
        "Priority",
        selected_job.get("priority") or "Review",
    )
    quick3.metric(
        "Timing",
        selected_job.get(
            "apply_urgency",
            "Review normally",
        ),
    )
else:
    st.info(
        "No job is currently selected. Open Job Search, "
        "expand a job, and click Prepare Application."
    )

st.subheader("Job Description Capture")

capture_col1, capture_col2 = st.columns(
    [1, 2]
)

with capture_col1:
    fetch_button = st.button(
        "Try Automatic JD Capture",
        type="secondary",
        width="stretch",
        disabled=not bool(
            st.session_state[
                "apply_job_link"
            ]
        ),
    )

with capture_col2:
    st.caption(
        "CareerPilot uses the description from Job Search first, "
        "then tries the job page. Some sites may block access, "
        "so manual paste remains available."
    )

if fetch_button:
    with st.spinner(
        "Trying to capture the job description..."
    ):
        result = resolve_job_description(
            existing_description=(
                st.session_state[
                    "application_jd"
                ]
            ),
            job_url=st.session_state[
                "apply_job_link"
            ],
        )

        if result.description:
            st.session_state[
                "application_jd"
            ] = result.description

            selected_job = update_selected_job(
                st.session_state,
                {
                    "company": st.session_state[
                        "apply_company"
                    ],
                    "job_role": st.session_state[
                        "apply_role"
                    ],
                    "location": st.session_state[
                        "apply_location"
                    ],
                    "job_link": st.session_state[
                        "apply_job_link"
                    ],
                    "job_description": (
                        result.description
                    ),
                    "description_status": (
                        result.status
                    ),
                },
            )

        st.session_state[
            "jd_capture_message"
        ] = result.message
        st.session_state[
            "jd_capture_status"
        ] = result.status

capture_status = st.session_state[
    "jd_capture_status"
]
capture_message = st.session_state[
    "jd_capture_message"
]

if capture_message:
    if capture_status in {
        "available",
        "captured",
    }:
        st.success(capture_message)
    elif capture_status == "partial":
        st.warning(capture_message)
    else:
        st.info(capture_message)

with st.form("application_copilot_form"):
    left, right = st.columns(2)

    with left:
        company = st.text_input(
            "Company",
            key="apply_company",
        )
        job_role = st.text_input(
            "Job Role",
            key="apply_role",
        )

        role_names = get_role_names()
        default_index = (
            role_names.index(
                default_resume_type
            )
            if default_resume_type
            in role_names
            else 0
        )

        resume_type = st.selectbox(
            "Resume Version",
            options=role_names,
            index=default_index,
        )

    with right:
        location = st.text_input(
            "Location",
            key="apply_location",
        )
        job_link = st.text_input(
            "Job Link",
            key="apply_job_link",
        )
        status = st.selectbox(
            "Application Status",
            [
                "Ready to Apply",
                "Applied",
                "Recruiter Contacted",
                "Interview",
                "Rejected",
                "Offer",
            ],
        )

    job_description = st.text_area(
        "Complete Job Description",
        key="application_jd",
        height=360,
        help=(
            "Paste the full JD when automatic capture is unavailable. "
            "A complete JD creates a more reliable ATS score."
        ),
    )

    generate_button = st.form_submit_button(
        "Generate Complete Application Package",
        type="primary",
        width="stretch",
    )

if generate_button:
    try:
        with st.spinner(
            "Creating your application package..."
        ):
            package = build_application_package(
                profile=profile,
                company=company,
                role=job_role,
                location=location,
                job_link=job_link,
                job_description=job_description,
                resume_type=resume_type,
                status=status,
            )

            package["summary_path"] = (
                export_application_summary(
                    package
                )
            )

            st.session_state[
                "application_package"
            ] = package

            report = package["report"]

            selected_job = update_selected_job(
                st.session_state,
                {
                    "company": company,
                    "job_role": job_role,
                    "location": location,
                    "job_link": job_link,
                    "job_description": (
                        job_description
                    ),
                    "description_status": (
                        "available"
                    ),
                    "matched_skills": ", ".join(
                        report["matched"]
                    ),
                    "missing_skills": ", ".join(
                        report["missing"]
                    ),
                    "resume_version": (
                        resume_type
                    ),
                },
            )

    except Exception as exc:
        st.error(
            f"Could not prepare the application: {exc}"
        )

package = st.session_state.get(
    "application_package"
)

if package:
    report = package["report"]
    optimized = package["optimized"]

    st.success(
        "Complete application package created."
    )

    metric1, metric2, metric3, metric4 = (
        st.columns(4)
    )

    metric1.metric(
        "ATS Match",
        f"{report['ats_score']}%",
    )
    metric2.metric(
        "Confidence",
        report["confidence"],
    )
    metric3.metric(
        "Matched Skills",
        len(report["matched"]),
    )
    metric4.metric(
        "Missing Skills",
        len(report["missing"]),
    )

    if report["confidence"] == "Low":
        st.warning(
            report["confidence_message"]
        )
    else:
        st.info(
            report["confidence_message"]
        )

    st.subheader("Recommendation")
    st.write(
        f"**{report['recommendation']}**"
    )

    tabs = st.tabs(
        [
            "Resume",
            "ATS Intelligence",
            "Cover Note",
            "Recruiter Email",
            "LinkedIn",
            "Follow-up",
            "Interview Prep",
            "Checklist",
        ]
    )

    with tabs[0]:
        st.subheader(
            "Updated Career Objective"
        )
        st.write(
            optimized["objective"]
        )

        st.subheader("Keywords Used")
        st.write(
            ", ".join(
                optimized["keywords"]
            )
            or "No keywords detected"
        )

        resume_path = Path(
            optimized["output_path"]
        )

        if resume_path.exists():
            st.download_button(
                "Download Optimized Resume DOCX",
                data=resume_path.read_bytes(),
                file_name=resume_path.name,
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
                width="stretch",
            )

        summary_path = Path(
            package["summary_path"]
        )

        if summary_path.exists():
            st.download_button(
                "Download Complete Application Summary",
                data=summary_path.read_bytes(),
                file_name=summary_path.name,
                mime="text/plain",
                width="stretch",
            )

    with tabs[1]:
        a, b, c = st.columns(3)

        with a:
            st.subheader("Job Skills")
            for skill in report[
                "job_skills"
            ]:
                st.write(f"• {skill}")

        with b:
            st.subheader(
                "Matched Skills"
            )
            for skill in report[
                "matched"
            ]:
                st.write(f"✅ {skill}")

        with c:
            st.subheader(
                "Missing - Do Not Invent"
            )
            if report["missing"]:
                for skill in report[
                    "missing"
                ]:
                    st.write(
                        f"⚠️ {skill}"
                    )
            else:
                st.success(
                    "No recognized missing skills."
                )

        st.subheader(
            "Skills to Emphasize"
        )
        st.write(
            ", ".join(
                report["emphasize"]
            )
            or "No extra emphasis identified."
        )

        st.caption(
            f"JD word count: "
            f"{report['description_word_count']} | "
            f"Recognized skills: "
            f"{report['total_keywords']}"
        )

    with tabs[2]:
        st.text_area(
            "Cover Note",
            value=package[
                "cover_note"
            ],
            height=420,
        )

    with tabs[3]:
        st.text_area(
            "Recruiter Email",
            value=package[
                "recruiter_email"
            ],
            height=420,
        )

    with tabs[4]:
        st.text_area(
            "LinkedIn Connection Message",
            value=package[
                "linkedin_message"
            ],
            height=260,
        )

    with tabs[5]:
        st.text_area(
            "Follow-up Message",
            value=package[
                "follow_up_message"
            ],
            height=380,
        )

    with tabs[6]:
        for topic in package[
            "interview_topics"
        ]:
            st.write(f"✅ {topic}")

    with tabs[7]:
        checklist_labels = {
            "resume_ready": (
                "Optimized resume created"
            ),
            "cover_note_ready": (
                "Cover note created"
            ),
            "recruiter_email_ready": (
                "Recruiter email created"
            ),
            "linkedin_message_ready": (
                "LinkedIn message created"
            ),
            "follow_up_ready": (
                "Follow-up message created"
            ),
            "interview_topics_ready": (
                "Interview topics created"
            ),
        }

        for key, label in (
            checklist_labels.items()
        ):
            if package[
                "checklist"
            ].get(key):
                st.write(f"✅ {label}")
            else:
                st.write(f"❌ {label}")

    st.divider()

    action1, action2 = st.columns(2)

    with action1:
        if st.button(
            "Save Application to Tracker",
            type="primary",
            width="stretch",
        ):
            notes = (
                f"ATS score: "
                f"{report['ats_score']}%. "
                f"Confidence: "
                f"{report['confidence']}. "
                f"Recommendation: "
                f"{report['recommendation']}. "
                f"Resume: "
                f"{package['resume_type']}. "
                f"Matched: "
                f"{', '.join(report['matched']) or 'None'}. "
                f"Missing: "
                f"{', '.join(report['missing']) or 'None'}. "
                f"Application package: "
                f"{package['summary_path']}."
            )

            save_application(
                company=package["company"],
                role=package["job_role"],
                location=package["location"],
                job_link=package["job_link"],
                status=package["status"],
                notes=notes,
            )

            st.success(
                "Application saved to CareerPilot tracker."
            )

    with action2:
        if st.button(
            "Open Recruiter Outreach",
            width="stretch",
        ):
            st.switch_page(
                "pages/9_Recruiter_Outreach.py"
            )
