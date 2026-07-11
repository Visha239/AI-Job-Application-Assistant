from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from app.services.cover_letter import generate_cover_note
from app.services.recruiter import generate_email
from app.services.resume_optimizer import ResumeOptimizer
from app.services.resume_report import ResumeReport
from app.services.tracker import save_application
from app.utils.config_loader import get_role_names


PROFILE_PATH = Path("data/profile.json")


def load_profile() -> dict:
    with PROFILE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


st.set_page_config(
    page_title="CareerPilot Apply Workflow",
    page_icon="🚀",
    layout="wide",
)

profile = load_profile()

st.title("🚀 Job Application Workflow")
st.caption(
    "Analyze a job, generate your same-format optimized resume, "
    "prepare outreach and track the application."
)

with st.form("job_application_workflow"):
    left, right = st.columns(2)

    with left:
        company = st.text_input(
            "Company",
            placeholder="Example: EY",
        )

        job_role = st.text_input(
            "Job Role",
            placeholder="Example: Data Analyst",
        )

        resume_type = st.selectbox(
            "Resume Version",
            options=get_role_names(),
        )

    with right:
        location = st.text_input(
            "Location",
            value="Bengaluru, Karnataka",
        )

        job_link = st.text_input(
            "Job Link",
            placeholder="https://...",
        )

        status = st.selectbox(
            "Application Status",
            options=[
                "Ready to Apply",
                "Applied",
                "Interview",
                "Rejected",
                "Offer",
            ],
        )

    job_description = st.text_area(
        "Paste Complete Job Description",
        height=320,
        placeholder="Paste the complete role description here...",
    )

    generate_button = st.form_submit_button(
        "Analyze and Prepare Application",
        type="primary",
        width="stretch",
    )


if generate_button:
    errors: list[str] = []

    if not company.strip():
        errors.append("Enter the company name.")

    if not job_role.strip():
        errors.append("Enter the job role.")

    if not job_description.strip():
        errors.append("Paste the job description.")

    if errors:
        for error in errors:
            st.error(error)
    else:
        with st.spinner("Preparing your application package..."):
            try:
                report = ResumeReport().generate(job_description)

                optimizer = ResumeOptimizer()

                optimized = optimizer.optimize_resume(
                    role_type=resume_type,
                    job_description=job_description,
                )

                cover_note = generate_cover_note(
                    profile=profile,
                    company=company.strip(),
                    role=job_role.strip(),
                    matched_skills=report["matched"],
                )

                recruiter_email = generate_email(
                    profile=profile,
                    company=company.strip(),
                    role=job_role.strip(),
                )

                st.session_state["application_package"] = {
                    "company": company.strip(),
                    "job_role": job_role.strip(),
                    "resume_type": resume_type,
                    "location": location.strip(),
                    "job_link": job_link.strip(),
                    "status": status,
                    "job_description": job_description,
                    "report": report,
                    "optimized": optimized,
                    "cover_note": cover_note,
                    "recruiter_email": recruiter_email,
                }

            except Exception as exc:
                st.error(f"Could not prepare the application: {exc}")


package = st.session_state.get("application_package")

if package:
    report = package["report"]
    optimized = package["optimized"]

    st.success("Application package created successfully.")

    metric1, metric2, metric3 = st.columns(3)

    metric1.metric(
        "ATS Match Score",
        f"{report['ats_score']}%",
    )

    metric2.metric(
        "Matched Skills",
        len(report["matched"]),
    )

    metric3.metric(
        "Missing Skills",
        len(report["missing"]),
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Resume Analysis",
            "Optimized Resume",
            "Cover Note",
            "Recruiter Email",
        ]
    )

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Matched Skills")

            if report["matched"]:
                for skill in report["matched"]:
                    st.write(f"✅ {skill}")
            else:
                st.info("No target skills detected.")

            st.subheader("Skills to Emphasize")

            if report["emphasize"]:
                for skill in report["emphasize"]:
                    st.write(f"➕ {skill}")
            else:
                st.info("No additional emphasis suggested.")

        with col2:
            st.subheader("Missing Skills")

            if report["missing"]:
                for skill in report["missing"]:
                    st.write(f"⚠️ {skill}")
            else:
                st.success("No recognized skills are missing.")

            st.subheader("Sections to Improve")

            for section in report["improve"]:
                st.write(f"• {section}")

    with tab2:
        st.subheader("Updated Career Objective")
        st.write(optimized["objective"])

        st.subheader("Keywords Used")
        st.write(", ".join(optimized["keywords"]))

        output_path = Path(optimized["output_path"])

        if output_path.exists():
            resume_bytes = output_path.read_bytes()

            st.download_button(
                label="Download Optimized Resume DOCX",
                data=resume_bytes,
                file_name=output_path.name,
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
                width="stretch",
            )
        else:
            st.error("The generated resume file could not be found.")

    with tab3:
        st.text_area(
            "Application Cover Note",
            value=package["cover_note"],
            height=360,
        )

    with tab4:
        st.text_area(
            "Recruiter Email Draft",
            value=package["recruiter_email"],
            height=360,
        )

    st.divider()

    if st.button(
        "Save to Application Tracker",
        type="primary",
        width="stretch",
    ):
        notes = (
            f"ATS score: {report['ats_score']}%. "
            f"Resume version: {package['resume_type']}. "
            f"Matched skills: {', '.join(report['matched']) or 'None'}. "
            f"Missing skills: {', '.join(report['missing']) or 'None'}."
        )

        save_application(
            company=package["company"],
            role=package["job_role"],
            location=package["location"],
            job_link=package["job_link"],
            status=package["status"],
            notes=notes,
        )

        st.success("Application saved to the CareerPilot tracker.")