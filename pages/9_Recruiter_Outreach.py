from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from app.services.application_context import (
    context_fingerprint,
    get_selected_job,
)
from app.services.outreach_manager import (
    build_follow_up_email,
    build_linkedin_message,
    build_recruiter_email,
    build_research_links,
    build_thank_you_email,
    create_outreach_record,
    delete_outreach_record,
    export_records_csv,
    get_due_follow_ups,
    load_records,
    update_outreach_record,
)


PROFILE_PATH = Path("data/profile.json")


def load_profile() -> dict:
    with PROFILE_PATH.open(
        "r",
        encoding="utf-8-sig",
    ) as file:
        return json.load(file)


def csv_list(value: str) -> list[str]:
    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


def sync_outreach_form(
    selected_job: dict,
) -> None:
    fingerprint = context_fingerprint(
        selected_job
    )

    if (
        st.session_state.get(
            "outreach_context_fingerprint"
        )
        == fingerprint
    ):
        return

    st.session_state[
        "outreach_context_fingerprint"
    ] = fingerprint
    st.session_state[
        "outreach_company"
    ] = selected_job.get(
        "company",
        "",
    )
    st.session_state[
        "outreach_role"
    ] = selected_job.get(
        "job_role",
        "",
    )
    st.session_state[
        "outreach_job_link"
    ] = selected_job.get(
        "job_link",
        "",
    )
    st.session_state[
        "outreach_matched_skills"
    ] = selected_job.get(
        "matched_skills",
        "",
    )


st.set_page_config(
    page_title="CareerPilot Recruiter Outreach",
    page_icon="📨",
    layout="wide",
)

profile = load_profile()
selected_job = get_selected_job(
    st.session_state
)

if selected_job:
    sync_outreach_form(
        selected_job
    )

st.session_state.setdefault(
    "outreach_company",
    selected_job.get(
        "company",
        "",
    ),
)
st.session_state.setdefault(
    "outreach_role",
    selected_job.get(
        "job_role",
        "",
    ),
)
st.session_state.setdefault(
    "outreach_job_link",
    selected_job.get(
        "job_link",
        "",
    ),
)
st.session_state.setdefault(
    "outreach_matched_skills",
    selected_job.get(
        "matched_skills",
        "SQL, Power BI, Python, Excel",
    ),
)

st.title(
    "📨 Recruiter Outreach & Follow-up"
)
st.caption(
    "Create personalized outreach, track recruiters, "
    "and never miss a follow-up."
)

if selected_job:
    st.success(
        "Loaded automatically from the selected job: "
        f"{selected_job.get('job_role') or 'Unknown Role'} "
        f"at {selected_job.get('company') or 'Unknown Company'}"
    )
else:
    st.info(
        "No selected job was found. Open Job Search, "
        "choose a job, and click Prepare Application."
    )

records = load_records()
due_records = get_due_follow_ups(
    records
)

metric1, metric2, metric3, metric4 = (
    st.columns(4)
)

metric1.metric(
    "Outreach Records",
    len(records),
)
metric2.metric(
    "Follow-ups Due",
    len(due_records),
)
metric3.metric(
    "Recruiters Contacted",
    sum(
        1
        for record in records
        if record.get("status")
        != "Not Contacted"
    ),
)
metric4.metric(
    "Replies / Interviews",
    sum(
        1
        for record in records
        if record.get("status")
        in {
            "Replied",
            "Interview Scheduled",
        }
    ),
)

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Create Outreach",
        "Follow-ups Due",
        "Outreach Tracker",
        "Research Recruiters",
    ]
)

with tab1:
    st.subheader(
        "Create Recruiter Messages"
    )

    col1, col2 = st.columns(2)

    with col1:
        company = st.text_input(
            "Company",
            key="outreach_company",
        )
        role = st.text_input(
            "Role",
            key="outreach_role",
        )
        recruiter_name = st.text_input(
            "Recruiter Name",
            placeholder="Optional",
        )
        recruiter_email = st.text_input(
            "Recruiter Email",
            placeholder="Optional",
        )

    with col2:
        recruiter_linkedin = (
            st.text_input(
                "Recruiter LinkedIn",
                placeholder="Optional",
            )
        )
        job_link = st.text_input(
            "Job Link",
            key="outreach_job_link",
        )
        matched_skills_text = (
            st.text_input(
                "Matched Skills",
                key=(
                    "outreach_matched_skills"
                ),
            )
        )
        follow_up_date = st.date_input(
            "Follow-up Date",
            value=(
                date.today()
                + timedelta(days=3)
            ),
        )

    matched_skills = csv_list(
        matched_skills_text
    )

    recruiter_email_text = (
        build_recruiter_email(
            candidate_name=profile[
                "name"
            ],
            candidate_email=profile[
                "email"
            ],
            company=(
                company
                or "the company"
            ),
            role=role or "the role",
            matched_skills=(
                matched_skills
            ),
            recruiter_name=(
                recruiter_name
            ),
            job_link=job_link,
        )
    )

    linkedin_text = (
        build_linkedin_message(
            candidate_name=profile[
                "name"
            ],
            company=(
                company
                or "the company"
            ),
            role=role or "the role",
            matched_skills=(
                matched_skills
            ),
        )
    )

    follow_up_text = (
        build_follow_up_email(
            candidate_name=profile[
                "name"
            ],
            candidate_email=profile[
                "email"
            ],
            company=(
                company
                or "the company"
            ),
            role=role or "the role",
            recruiter_name=(
                recruiter_name
            ),
        )
    )

    thank_you_text = (
        build_thank_you_email(
            candidate_name=profile[
                "name"
            ],
            candidate_email=profile[
                "email"
            ],
            company=(
                company
                or "the company"
            ),
            role=role or "the role",
            interviewer_name=(
                recruiter_name
            ),
        )
    )

    message_tabs = st.tabs(
        [
            "Recruiter Email",
            "LinkedIn Message",
            "Follow-up Email",
            "Interview Thank-you",
        ]
    )

    with message_tabs[0]:
        st.text_area(
            "Recruiter Email",
            value=(
                recruiter_email_text
            ),
            height=360,
        )

    with message_tabs[1]:
        st.text_area(
            "LinkedIn Connection Message",
            value=linkedin_text,
            height=180,
        )
        st.caption(
            f"Characters: "
            f"{len(linkedin_text)}/300"
        )

    with message_tabs[2]:
        st.text_area(
            "Follow-up Email",
            value=follow_up_text,
            height=320,
        )

    with message_tabs[3]:
        st.text_area(
            "Interview Thank-you",
            value=thank_you_text,
            height=320,
        )

    status = st.selectbox(
        "Current Status",
        [
            "Not Contacted",
            "Contacted",
            "Follow-up Due",
            "Replied",
            "Interview Scheduled",
            "Rejected",
            "Closed",
        ],
    )

    notes = st.text_area(
        "Notes",
        placeholder=(
            "Example: Found through LinkedIn; "
            "recruiter handles analytics "
            "hiring in Bengaluru."
        ),
        height=100,
    )

    if st.button(
        "Save Outreach Record",
        type="primary",
        width="stretch",
    ):
        try:
            record = (
                create_outreach_record(
                    company=company,
                    role=role,
                    recruiter_name=(
                        recruiter_name
                    ),
                    recruiter_email=(
                        recruiter_email
                    ),
                    recruiter_linkedin=(
                        recruiter_linkedin
                    ),
                    job_link=job_link,
                    status=status,
                    initial_contact_date=(
                        date.today().isoformat()
                        if status
                        != "Not Contacted"
                        else ""
                    ),
                    follow_up_date=(
                        follow_up_date.isoformat()
                    ),
                    last_contact_date=(
                        date.today().isoformat()
                        if status
                        != "Not Contacted"
                        else ""
                    ),
                    notes=notes,
                )
            )
            st.success(
                f"Outreach saved for "
                f"{record['company']}."
            )
            st.rerun()

        except Exception as exc:
            st.error(
                f"Could not save outreach: "
                f"{exc}"
            )

with tab2:
    st.subheader(
        "Follow-ups Requiring Attention"
    )

    if not due_records:
        st.success(
            "No recruiter follow-ups "
            "are due today."
        )
    else:
        for record in due_records:
            with st.expander(
                f"{record['company']} - "
                f"{record['role']} "
                f"(due "
                f"{record['follow_up_date']})"
            ):
                st.write(
                    f"**Recruiter:** "
                    f"{record.get('recruiter_name') or 'Not recorded'}"
                )
                st.write(
                    f"**Email:** "
                    f"{record.get('recruiter_email') or 'Not recorded'}"
                )
                st.write(
                    f"**Status:** "
                    f"{record.get('status')}"
                )

                message = (
                    build_follow_up_email(
                        candidate_name=(
                            profile["name"]
                        ),
                        candidate_email=(
                            profile["email"]
                        ),
                        company=record[
                            "company"
                        ],
                        role=record["role"],
                        recruiter_name=(
                            record.get(
                                "recruiter_name",
                                "",
                            )
                        ),
                    )
                )

                st.text_area(
                    "Follow-up message",
                    value=message,
                    height=300,
                    key=(
                        f"followup_"
                        f"{record['record_id']}"
                    ),
                )

                col_a, col_b = (
                    st.columns(2)
                )

                with col_a:
                    if st.button(
                        "Mark Follow-up Sent",
                        key=(
                            f"sent_"
                            f"{record['record_id']}"
                        ),
                        width="stretch",
                    ):
                        update_outreach_record(
                            record[
                                "record_id"
                            ],
                            status="Contacted",
                            last_contact_date=(
                                date.today()
                                .isoformat()
                            ),
                            follow_up_date=(
                                date.today()
                                + timedelta(
                                    days=4
                                )
                            ).isoformat(),
                        )
                        st.success(
                            "Follow-up recorded."
                        )
                        st.rerun()

                with col_b:
                    if st.button(
                        "Mark Replied",
                        key=(
                            f"replied_"
                            f"{record['record_id']}"
                        ),
                        width="stretch",
                    ):
                        update_outreach_record(
                            record[
                                "record_id"
                            ],
                            status="Replied",
                            last_contact_date=(
                                date.today()
                                .isoformat()
                            ),
                            follow_up_date="",
                        )
                        st.success(
                            "Reply recorded."
                        )
                        st.rerun()

with tab3:
    st.subheader(
        "Outreach Tracker"
    )

    if not records:
        st.info(
            "No outreach records "
            "saved yet."
        )
    else:
        records_df = pd.DataFrame(
            records
        )

        display_columns = [
            "company",
            "role",
            "recruiter_name",
            "recruiter_email",
            "status",
            "initial_contact_date",
            "follow_up_date",
            "last_contact_date",
            "notes",
        ]

        available_columns = [
            column
            for column
            in display_columns
            if column
            in records_df.columns
        ]

        st.dataframe(
            records_df[
                available_columns
            ],
            width="stretch",
            hide_index=True,
        )

        export_path = Path(
            export_records_csv(
                records=records
            )
        )

        st.download_button(
            "Download Outreach Tracker CSV",
            data=export_path.read_bytes(),
            file_name=export_path.name,
            mime="text/csv",
            width="stretch",
        )

        st.subheader(
            "Update or Delete a Record"
        )

        record_options = {
            (
                f"{record['company']} - "
                f"{record['role']} - "
                f"{record.get('recruiter_name') or 'No recruiter'}"
            ): record
            for record in records
        }

        selected_label = st.selectbox(
            "Select record",
            options=list(
                record_options
            ),
        )

        selected_record = (
            record_options[
                selected_label
            ]
        )

        status_options = [
            "Not Contacted",
            "Contacted",
            "Follow-up Due",
            "Replied",
            "Interview Scheduled",
            "Rejected",
            "Closed",
        ]

        selected_status = (
            selected_record.get(
                "status"
            )
        )

        new_status = st.selectbox(
            "New status",
            status_options,
            index=(
                status_options.index(
                    selected_status
                )
                if selected_status
                in status_options
                else 0
            ),
        )

        new_follow_up = (
            st.text_input(
                "Follow-up date "
                "(YYYY-MM-DD)",
                value=(
                    selected_record.get(
                        "follow_up_date",
                        "",
                    )
                ),
            )
        )

        new_notes = st.text_area(
            "Updated notes",
            value=selected_record.get(
                "notes",
                "",
            ),
        )

        update_col, delete_col = (
            st.columns(2)
        )

        with update_col:
            if st.button(
                "Update Record",
                width="stretch",
            ):
                update_outreach_record(
                    selected_record[
                        "record_id"
                    ],
                    status=new_status,
                    follow_up_date=(
                        new_follow_up
                    ),
                    notes=new_notes,
                )
                st.success(
                    "Record updated."
                )
                st.rerun()

        with delete_col:
            if st.button(
                "Delete Record",
                width="stretch",
            ):
                delete_outreach_record(
                    selected_record[
                        "record_id"
                    ]
                )
                st.success(
                    "Record deleted."
                )
                st.rerun()

with tab4:
    st.subheader(
        "Find Relevant Recruiters"
    )

    research_company = (
        st.text_input(
            "Company to research",
            value=st.session_state[
                "outreach_company"
            ],
            key="research_company",
        )
    )

    if research_company.strip():
        links = build_research_links(
            research_company.strip()
        )

        st.write(
            "Use these searches to find "
            "public recruiter and hiring-manager "
            "profiles. Verify that the person "
            "actually recruits for your role "
            "before contacting them."
        )

        for label, link in (
            links.items()
        ):
            st.link_button(
                label,
                link,
                width="stretch",
            )

        st.markdown(
            """
**Recommended order**

1. Talent Acquisition or recruiter for the company  
2. Recruiter specializing in Data/Analytics hiring  
3. Analytics manager or team lead  
4. Employee referral from the relevant team
"""
        )
