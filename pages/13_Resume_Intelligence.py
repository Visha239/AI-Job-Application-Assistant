from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import streamlit as st

from app.services.application_context import (
    get_selected_job,
)
from app.services.resume_intelligence_v2 import (
    DEFAULT_MASTER_RESUME,
    generate_tailored_resume,
    review_resume,
)


PROFILE_PATH = Path(
    "data/profile.json"
)
UPLOAD_DIR = Path(
    "data/resume_uploads"
)
OUTPUT_DIR = Path(
    "exports/docx/resume_intelligence"
)


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
            "skills": [],
        }


def safe_filename(
    value: str,
) -> str:
    cleaned = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        value.strip(),
    )
    return (
        cleaned.strip("_")
        or "tailored_resume"
    )


st.set_page_config(
    page_title="CareerPilot Resume Intelligence",
    page_icon="📝",
    layout="wide",
)

profile = load_profile()
selected_job = get_selected_job(
    st.session_state
)

st.title(
    "📝 Resume Intelligence"
)
st.caption(
    "Review your resume against the selected JD, identify weak sections, "
    "and generate a truthful job-specific version."
)

st.warning(
    "CareerPilot will not add missing skills or invent achievements. "
    "It only emphasizes verified skills and safely improves wording."
)

if selected_job:
    st.success(
        "Selected job loaded automatically: "
        f"{selected_job.get('job_role') or 'Role'} at "
        f"{selected_job.get('company') or 'Company'}"
    )
else:
    st.info(
        "Select a job from Job Search first, or paste a JD manually below."
    )

left, right = st.columns(2)

with left:
    source_option = st.radio(
        "Resume Source",
        [
            "Use CareerPilot master resume",
            "Upload a DOCX resume",
        ],
    )

    uploaded_file = None

    if source_option == (
        "Upload a DOCX resume"
    ):
        uploaded_file = (
            st.file_uploader(
                "Upload Resume",
                type=["docx"],
            )
        )

with right:
    role = st.text_input(
        "Target Role",
        value=selected_job.get(
            "job_role",
            "Data Analyst",
        ),
    )
    company = st.text_input(
        "Company",
        value=selected_job.get(
            "company",
            "",
        ),
    )

job_description = st.text_area(
    "Complete Job Description",
    value=selected_job.get(
        "job_description",
        "",
    ),
    height=320,
)

analyze_button = st.button(
    "Analyze Resume Against JD",
    type="primary",
    width="stretch",
)

source_path: Path | None = None

if source_option == (
    "Use CareerPilot master resume"
):
    source_path = DEFAULT_MASTER_RESUME
elif uploaded_file is not None:
    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    source_path = (
        UPLOAD_DIR
        / uploaded_file.name
    )
    source_path.write_bytes(
        uploaded_file.getvalue()
    )

if analyze_button:
    try:
        if source_path is None:
            raise ValueError(
                "Choose or upload a resume."
            )

        if not source_path.exists():
            raise FileNotFoundError(
                f"Resume not found: {source_path}"
            )

        if not job_description.strip():
            raise ValueError(
                "A complete job description is required."
            )

        review = review_resume(
            resume_path=source_path,
            job_description=(
                job_description
            ),
            profile_skills=profile.get(
                "skills",
                [],
            ),
        )

        st.session_state[
            "resume_intelligence_review"
        ] = review
        st.session_state[
            "resume_intelligence_source"
        ] = str(source_path)
        st.session_state[
            "resume_intelligence_role"
        ] = role
        st.session_state[
            "resume_intelligence_company"
        ] = company
        st.session_state[
            "resume_intelligence_jd"
        ] = job_description

    except Exception as exc:
        st.error(
            f"Resume analysis failed: {exc}"
        )

review = st.session_state.get(
    "resume_intelligence_review"
)

if review:
    metric1, metric2, metric3, metric4 = (
        st.columns(4)
    )

    metric1.metric(
        "Overall Resume Score",
        f"{review['overall_score']}%",
    )
    metric2.metric(
        "JD Skill Coverage",
        f"{review['skill_coverage']}%",
    )
    metric3.metric(
        "Bullet Quality",
        f"{review['bullet_quality']}%",
    )
    metric4.metric(
        "Section Completeness",
        f"{review['completeness']}%",
    )

    tabs = st.tabs(
        [
            "Skill Match",
            "Section Review",
            "Bullet Review",
            "Recommendations",
            "Generate Final Resume",
        ]
    )

    with tabs[0]:
        col1, col2, col3 = (
            st.columns(3)
        )

        with col1:
            st.subheader(
                "JD Skills"
            )
            for skill in review[
                "job_skills"
            ]:
                st.write(
                    f"• {skill}"
                )

        with col2:
            st.subheader(
                "Verified Matches"
            )
            for skill in review[
                "matched_skills"
            ]:
                st.write(
                    f"✅ {skill}"
                )

        with col3:
            st.subheader(
                "Missing - Do Not Invent"
            )

            if review[
                "missing_skills"
            ]:
                for skill in review[
                    "missing_skills"
                ]:
                    st.write(
                        f"⚠️ {skill}"
                    )
            else:
                st.success(
                    "No recognized gaps."
                )

    with tabs[1]:
        section_df = pd.DataFrame(
            [
                {
                    "section": section,
                    "score": score,
                }
                for section, score in review[
                    "section_scores"
                ].items()
            ]
        )

        st.dataframe(
            section_df,
            width="stretch",
            hide_index=True,
        )
        st.bar_chart(
            section_df.set_index(
                "section"
            )["score"],
            height=300,
        )

    with tabs[2]:
        bullet_reviews = review[
            "bullet_reviews"
        ]

        if not bullet_reviews:
            st.info(
                "No experience or project bullets were detected."
            )
        else:
            bullet_df = pd.DataFrame(
                bullet_reviews
            )

            st.dataframe(
                bullet_df[
                    [
                        "text",
                        "score",
                        "starts_with_action",
                        "contains_metric",
                        "weak_phrases",
                        "word_count",
                    ]
                ],
                width="stretch",
                hide_index=True,
            )

    with tabs[3]:
        for recommendation in review[
            "recommendations"
        ]:
            st.info(
                recommendation
            )

    with tabs[4]:
        st.write(
            "The generated resume will:"
        )
        st.write(
            "✅ Update the objective for the selected role."
        )
        st.write(
            "✅ Move verified matching skills earlier where possible."
        )
        st.write(
            "✅ Replace weak phrases with safer action wording."
        )
        st.write(
            "❌ It will not add unsupported skills."
        )
        st.write(
            "❌ It will not invent numbers, duties, or achievements."
        )

        if st.button(
            "Generate Truthful Tailored Resume",
            type="primary",
            width="stretch",
        ):
            try:
                source = Path(
                    st.session_state[
                        "resume_intelligence_source"
                    ]
                )
                target_role = (
                    st.session_state[
                        "resume_intelligence_role"
                    ]
                    or "Data Analyst"
                )
                target_company = (
                    st.session_state[
                        "resume_intelligence_company"
                    ]
                    or "Company"
                )

                output_name = safe_filename(
                    f"{target_company}_{target_role}_Final_Resume"
                ) + ".docx"

                output_path = (
                    OUTPUT_DIR
                    / output_name
                )

                result = (
                    generate_tailored_resume(
                        source_resume_path=(
                            source
                        ),
                        output_path=(
                            output_path
                        ),
                        job_description=(
                            st.session_state[
                                "resume_intelligence_jd"
                            ]
                        ),
                        role=target_role,
                        profile_skills=(
                            profile.get(
                                "skills",
                                [],
                            )
                        ),
                    )
                )

                st.session_state[
                    "resume_intelligence_result"
                ] = result
                st.success(
                    "Truthful tailored resume created."
                )

            except Exception as exc:
                st.error(
                    f"Could not create resume: {exc}"
                )

        result = st.session_state.get(
            "resume_intelligence_result"
        )

        if result:
            st.write(
                f"**Objective updated:** "
                f"{result['objective_updated']}"
            )
            st.write(
                f"**Skills reordered:** "
                f"{result['skills_reordered']}"
            )
            st.write(
                f"**Weak bullets safely improved:** "
                f"{result['bullets_improved']}"
            )

            output_path = Path(
                result["output_path"]
            )

            if output_path.exists():
                st.download_button(
                    "Download Final Tailored Resume",
                    data=(
                        output_path.read_bytes()
                    ),
                    file_name=(
                        output_path.name
                    ),
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "wordprocessingml.document"
                    ),
                    width="stretch",
                )
