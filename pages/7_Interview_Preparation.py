from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.services.interview_preparation import (
    export_interview_report,
    generate_interview_plan,
)


st.set_page_config(
    page_title="CareerPilot Interview Preparation",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 Interview Preparation")
st.caption(
    "Generate a role-specific preparation plan from the job description."
)

with st.form("interview_preparation_form"):
    col1, col2 = st.columns(2)

    with col1:
        company = st.text_input(
            "Company",
            placeholder="Example: EY",
        )

    with col2:
        role = st.text_input(
            "Job Role",
            placeholder="Example: Data Analyst",
        )

    job_description = st.text_area(
        "Paste Complete Job Description",
        height=350,
    )

    generate_button = st.form_submit_button(
        "Generate Interview Plan",
        type="primary",
        width="stretch",
    )


if generate_button:
    try:
        plan = generate_interview_plan(
            company=company,
            role=role,
            job_description=job_description,
        )

        output_path = export_interview_report(plan)

        st.session_state["interview_plan"] = plan
        st.session_state["interview_report_path"] = output_path

    except Exception as exc:
        st.error(f"Could not create interview plan: {exc}")


plan = st.session_state.get("interview_plan")

if plan:
    metric1, metric2, metric3 = st.columns(3)

    metric1.metric(
        "Resume/JD Match",
        f"{plan['ats_score']}%",
    )

    metric2.metric(
        "Matched Skills",
        len(plan["matched_skills"]),
    )

    metric3.metric(
        "Questions Generated",
        len(plan["questions"]),
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Preparation Priorities",
            "Interview Questions",
            "Skill Analysis",
            "Company Research",
        ]
    )

    with tab1:
        for priority in plan["preparation_priorities"]:
            st.write(f"✅ {priority}")

    with tab2:
        categories = sorted(
            {question.category for question in plan["questions"]}
        )

        selected_category = st.selectbox(
            "Question Category",
            categories,
        )

        filtered_questions = [
            question
            for question in plan["questions"]
            if question.category == selected_category
        ]

        for index, question in enumerate(
            filtered_questions,
            start=1,
        ):
            with st.expander(
                f"{index}. {question.question}"
            ):
                st.write("**Answer guidance**")
                st.write(question.answer_guidance)

    with tab3:
        left, right = st.columns(2)

        with left:
            st.subheader("Matched Skills")

            for skill in plan["matched_skills"]:
                st.write(f"✅ {skill}")

            st.subheader("Skills to Emphasize")

            for skill in plan["skills_to_emphasize"]:
                st.write(f"➕ {skill}")

        with right:
            st.subheader("Missing Skills")

            if plan["missing_skills"]:
                for skill in plan["missing_skills"]:
                    st.write(f"⚠️ {skill}")
            else:
                st.success("No recognized missing skills.")

    with tab4:
        st.warning(
            "These links help you research current public information. "
            "Verify facts before using them in an interview."
        )

        for name, link in plan["research_links"].items():
            st.link_button(
                name,
                link,
                width="stretch",
            )

    report_path = Path(
        st.session_state["interview_report_path"]
    )

    if report_path.exists():
        st.download_button(
            label="Download Interview Preparation Report",
            data=report_path.read_bytes(),
            file_name=report_path.name,
            mime="text/plain",
            width="stretch",
        )