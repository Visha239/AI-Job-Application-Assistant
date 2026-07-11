from __future__ import annotations

import pandas as pd
import streamlit as st

from app.services.decision_engine import analyze_job_decision
from app.services.job_ranker import rank_jobs
from app.services.job_search import search_jobs


st.set_page_config(
    page_title="CareerPilot Decision Engine",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Job Decision Engine")
st.caption(
    "Evaluate a job before applying and decide where to spend your time."
)

with st.form("decision_search_form"):
    left, right = st.columns(2)

    with left:
        search_term = st.text_input(
            "Role",
            value="Data Analyst",
        )

        location = st.text_input(
            "Location",
            value="Bengaluru, Karnataka",
        )

    with right:
        results_wanted = st.slider(
            "Jobs to evaluate",
            min_value=5,
            max_value=30,
            value=10,
            step=5,
        )

        selected_sites = st.multiselect(
            "Sources",
            options=[
                "indeed",
                "linkedin",
                "google",
            ],
            default=[
                "indeed",
                "linkedin",
            ],
        )

    evaluate_button = st.form_submit_button(
        "Search and Evaluate Jobs",
        type="primary",
        width="stretch",
    )


if evaluate_button:
    if not search_term.strip():
        st.error("Enter a role.")
    elif not selected_sites:
        st.error("Select at least one source.")
    else:
        with st.spinner(
            "Searching and evaluating opportunities..."
        ):
            try:
                jobs = search_jobs(
                    search_term=search_term,
                    location=location,
                    results_wanted=results_wanted,
                    hours_old=168,
                    sites=selected_sites,
                )

                ranked_jobs = rank_jobs(jobs)

                decisions = [
                    analyze_job_decision(row.to_dict())
                    for _, row in ranked_jobs.iterrows()
                ]

                decisions = sorted(
                    decisions,
                    key=lambda item: item["overall_score"],
                    reverse=True,
                )

                st.session_state["decision_results"] = decisions

            except Exception as exc:
                st.error(f"Could not evaluate jobs: {exc}")


decisions = st.session_state.get(
    "decision_results",
    [],
)

if not decisions:
    st.info(
        "Search for jobs to see CareerPilot recommendations."
    )

else:
    apply_today_count = sum(
        decision["overall_score"] >= 90
        for decision in decisions
    )

    high_priority_count = sum(
        80 <= decision["overall_score"] < 90
        for decision in decisions
    )

    average_score = round(
        sum(
            decision["overall_score"]
            for decision in decisions
        )
        / len(decisions),
        1,
    )

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric(
        "Jobs Evaluated",
        len(decisions),
    )

    metric2.metric(
        "Apply Today",
        apply_today_count,
    )

    metric3.metric(
        "High Priority",
        high_priority_count,
    )

    metric4.metric(
        "Average Score",
        f"{average_score}%",
    )

    st.divider()

    summary_rows = [
        {
            "score": decision["overall_score"],
            "company": decision["company"],
            "role": decision["title"],
            "priority": decision["priority"],
            "recommendation": decision["recommendation"],
            "interview_probability": (
                f"{decision['interview_probability']}%"
            ),
            "resume": decision["recommended_resume"],
        }
        for decision in decisions
    ]

    st.dataframe(
        pd.DataFrame(summary_rows),
        width="stretch",
        hide_index=True,
    )

    st.divider()
    st.subheader("Detailed Recommendations")

    for index, decision in enumerate(decisions):
        stars = "⭐" * decision["stars"]

        heading = (
            f"{decision['overall_score']}% — "
            f"{decision['title']} at "
            f"{decision['company']}"
        )

        with st.expander(heading):
            top1, top2, top3, top4 = st.columns(4)

            top1.metric(
                "Overall Score",
                f"{decision['overall_score']}%",
            )

            top2.metric(
                "Interview Estimate",
                f"{decision['interview_probability']}%",
            )

            top3.metric(
                "Priority",
                decision["priority"],
            )

            top4.metric(
                "Rating",
                stars,
            )

            st.success(
                f"{decision['recommendation']}: "
                f"{decision['suggested_action']}"
            )

            left, right = st.columns(2)

            with left:
                st.subheader("Why This Job Matches")

                for reason in decision["reasons"]:
                    st.write(f"✅ {reason}")

                st.subheader("Matched Skills")

                if decision["matched_skills"]:
                    for skill in decision["matched_skills"]:
                        st.write(f"• {skill}")
                else:
                    st.info("No matched skills were detected.")

                st.subheader("Recommended Resume")

                st.write(
                    decision["recommended_resume"]
                )

            with right:
                st.subheader("Risks")

                if decision["risks"]:
                    for risk in decision["risks"]:
                        st.write(f"⚠️ {risk}")
                else:
                    st.success(
                        "No major risks were identified."
                    )

                st.subheader("Recognized Missing Skills")

                if decision["recognized_missing_skills"]:
                    for skill in decision[
                        "recognized_missing_skills"
                    ]:
                        st.write(f"• {skill}")
                else:
                    st.success(
                        "No recognized required skills are missing."
                    )

                st.subheader("Score Breakdown")

                breakdown = pd.DataFrame(
                    [
                        {
                            "Component": "Skills",
                            "Score": decision[
                                "skill_score"
                            ],
                            "Maximum": 40,
                        },
                        {
                            "Component": "Role",
                            "Score": decision[
                                "role_score"
                            ],
                            "Maximum": 20,
                        },
                        {
                            "Component": "Experience",
                            "Score": decision[
                                "experience_score"
                            ],
                            "Maximum": 15,
                        },
                        {
                            "Component": "Projects",
                            "Score": decision[
                                "project_score"
                            ],
                            "Maximum": 10,
                        },
                        {
                            "Component": "Location",
                            "Score": decision[
                                "location_score"
                            ],
                            "Maximum": 10,
                        },
                        {
                            "Component": "Completeness",
                            "Score": decision[
                                "completeness_score"
                            ],
                            "Maximum": 5,
                        },
                    ]
                )

                st.dataframe(
                    breakdown,
                    width="stretch",
                    hide_index=True,
                )

            if decision["job_url"]:
                st.link_button(
                    "Open Job",
                    decision["job_url"],
                    width="stretch",
                )