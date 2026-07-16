from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from app.services.application_context import (
    get_selected_job,
)
from app.services.application_crm import (
    STAGES,
    add_application,
    company_history,
    crm_metrics,
    delete_application,
    export_crm_csv,
    get_due_follow_ups,
    load_crm,
    source_analytics,
    update_application,
)


st.set_page_config(
    page_title="CareerPilot Application CRM",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Application Tracker & Follow-up CRM")
st.caption(
    "Track every application, manage stages, follow up on time, "
    "and learn which job sources produce responses."
)

selected_job = get_selected_job(
    st.session_state
)
records = load_crm()
metrics = crm_metrics(records)
due_follow_ups = get_due_follow_ups(
    records
)

top1, top2, top3, top4 = st.columns(4)

top1.metric(
    "Applications Sent",
    metrics["applications_sent"],
)
top2.metric(
    "Applied Today",
    metrics["applied_today"],
)
top3.metric(
    "Interviews",
    metrics["interviews"],
)
top4.metric(
    "Response Rate",
    f"{metrics['response_rate']}%",
)

second1, second2, second3, second4 = (
    st.columns(4)
)

second1.metric(
    "Awaiting Reply",
    metrics["awaiting_reply"],
)
second2.metric(
    "Offers",
    metrics["offers"],
)
second3.metric(
    "Rejected",
    metrics["rejected"],
)
second4.metric(
    "Follow-ups Due",
    len(due_follow_ups),
)

tabs = st.tabs(
    [
        "Add Application",
        "Pipeline",
        "Follow-ups",
        "Company History",
        "Source Analytics",
        "Export",
    ]
)

with tabs[0]:
    st.subheader(
        "Add an Application"
    )

    if selected_job:
        st.success(
            "Selected job loaded automatically: "
            f"{selected_job.get('job_role') or 'Unknown Role'} at "
            f"{selected_job.get('company') or 'Unknown Company'}"
        )

    with st.form(
        "add_application_form"
    ):
        left, right = st.columns(2)

        with left:
            company = st.text_input(
                "Company",
                value=selected_job.get(
                    "company",
                    "",
                ),
            )
            role = st.text_input(
                "Role",
                value=selected_job.get(
                    "job_role",
                    "",
                ),
            )
            location = st.text_input(
                "Location",
                value=selected_job.get(
                    "location",
                    "",
                ),
            )
            source = st.text_input(
                "Source",
                value=selected_job.get(
                    "source",
                    "",
                ),
            )

        with right:
            job_link = st.text_input(
                "Job Link",
                value=selected_job.get(
                    "job_link",
                    "",
                ),
            )
            match_score = st.number_input(
                "Match Score",
                min_value=0,
                max_value=100,
                value=int(
                    selected_job.get(
                        "match_score",
                        0,
                    )
                ),
            )
            stage = st.selectbox(
                "Current Stage",
                STAGES,
                index=STAGES.index(
                    "Applied"
                ),
            )
            applied_date = st.date_input(
                "Applied Date",
                value=date.today(),
            )

        recruiter_name = st.text_input(
            "Recruiter Name",
            placeholder="Optional",
        )
        recruiter_email = st.text_input(
            "Recruiter Email",
            placeholder="Optional",
        )
        next_follow_up = st.date_input(
            "Next Follow-up Date",
            value=(
                date.today()
                + timedelta(days=5)
            ),
        )
        notes = st.text_area(
            "Notes",
            placeholder=(
                "Example: Applied through company careers page "
                "using the Data Analyst resume."
            ),
        )

        submitted = st.form_submit_button(
            "Add to CRM",
            type="primary",
            width="stretch",
        )

    if submitted:
        try:
            add_application(
                company=company,
                role=role,
                location=location,
                source=source,
                job_link=job_link,
                stage=stage,
                match_score=match_score,
                recruiter_name=(
                    recruiter_name
                ),
                recruiter_email=(
                    recruiter_email
                ),
                notes=notes,
                applied_date=(
                    applied_date.isoformat()
                ),
                next_follow_up_date=(
                    next_follow_up.isoformat()
                ),
            )

            st.success(
                "Application added to CRM."
            )
            st.rerun()

        except Exception as exc:
            st.error(
                f"Could not add application: {exc}"
            )

with tabs[1]:
    st.subheader(
        "Application Pipeline"
    )

    if not records:
        st.info(
            "No applications are tracked yet."
        )
    else:
        stage_columns = st.columns(
            len(STAGES)
        )

        for stage_name, column in zip(
            STAGES,
            stage_columns,
        ):
            count = metrics[
                "stage_counts"
            ].get(
                stage_name,
                0,
            )

            with column:
                st.metric(
                    stage_name,
                    count,
                )

        st.divider()

        for record in sorted(
            records,
            key=lambda item: (
                item.get(
                    "applied_date",
                    "",
                ),
                item.get(
                    "match_score",
                    0,
                ),
            ),
            reverse=True,
        ):
            with st.expander(
                f"{record.get('stage')} - "
                f"{record.get('role')} at "
                f"{record.get('company')}"
            ):
                col1, col2, col3 = (
                    st.columns(3)
                )

                col1.write(
                    f"**Match:** "
                    f"{record.get('match_score', 0)}%"
                )
                col1.write(
                    f"**Source:** "
                    f"{record.get('source') or 'Unknown'}"
                )

                col2.write(
                    f"**Applied:** "
                    f"{record.get('applied_date') or 'Not recorded'}"
                )
                col2.write(
                    f"**Follow-up:** "
                    f"{record.get('next_follow_up_date') or 'Not scheduled'}"
                )

                col3.write(
                    f"**Recruiter:** "
                    f"{record.get('recruiter_name') or 'Not recorded'}"
                )
                col3.write(
                    f"**Location:** "
                    f"{record.get('location') or 'Not recorded'}"
                )

                new_stage = st.selectbox(
                    "Move to stage",
                    STAGES,
                    index=STAGES.index(
                        record.get(
                            "stage",
                            "Saved",
                        )
                    ),
                    key=(
                        f"stage_"
                        f"{record['record_id']}"
                    ),
                )

                notes = st.text_area(
                    "Notes",
                    value=record.get(
                        "notes",
                        "",
                    ),
                    key=(
                        f"notes_"
                        f"{record['record_id']}"
                    ),
                )

                action1, action2, action3 = (
                    st.columns(3)
                )

                with action1:
                    if st.button(
                        "Update",
                        key=(
                            f"update_"
                            f"{record['record_id']}"
                        ),
                        width="stretch",
                    ):
                        update_application(
                            record["record_id"],
                            stage=new_stage,
                            notes=notes,
                        )
                        st.success(
                            "Application updated."
                        )
                        st.rerun()

                with action2:
                    job_link = record.get(
                        "job_link",
                        "",
                    )

                    if job_link:
                        st.link_button(
                            "Open Job",
                            job_link,
                            width="stretch",
                        )
                    else:
                        st.button(
                            "Open Job",
                            disabled=True,
                            key=(
                                f"disabled_"
                                f"{record['record_id']}"
                            ),
                            width="stretch",
                        )

                with action3:
                    if st.button(
                        "Delete",
                        key=(
                            f"delete_"
                            f"{record['record_id']}"
                        ),
                        width="stretch",
                    ):
                        delete_application(
                            record["record_id"]
                        )
                        st.rerun()

with tabs[2]:
    st.subheader(
        "Follow-ups Requiring Attention"
    )

    if not due_follow_ups:
        st.success(
            "No follow-ups are due today."
        )
    else:
        for record in due_follow_ups:
            with st.expander(
                f"{record.get('company')} - "
                f"{record.get('role')} "
                f"(due "
                f"{record.get('next_follow_up_date')})"
            ):
                st.write(
                    f"**Stage:** "
                    f"{record.get('stage')}"
                )
                st.write(
                    f"**Recruiter:** "
                    f"{record.get('recruiter_name') or 'Not recorded'}"
                )
                st.write(
                    f"**Email:** "
                    f"{record.get('recruiter_email') or 'Not recorded'}"
                )
                st.write(
                    f"**Notes:** "
                    f"{record.get('notes') or 'None'}"
                )

                col_a, col_b = (
                    st.columns(2)
                )

                with col_a:
                    if st.button(
                        "Follow-up Sent",
                        key=(
                            f"followup_"
                            f"{record['record_id']}"
                        ),
                        width="stretch",
                    ):
                        update_application(
                            record["record_id"],
                            last_follow_up_date=(
                                date.today()
                                .isoformat()
                            ),
                            next_follow_up_date=(
                                date.today()
                                + timedelta(days=5)
                            ).isoformat(),
                            stage=(
                                "Recruiter Contacted"
                            ),
                        )
                        st.rerun()

                with col_b:
                    if st.button(
                        "Mark Replied",
                        key=(
                            f"reply_"
                            f"{record['record_id']}"
                        ),
                        width="stretch",
                    ):
                        update_application(
                            record["record_id"],
                            stage="HR Round",
                            next_follow_up_date="",
                        )
                        st.rerun()

with tabs[3]:
    st.subheader(
        "Company Application History"
    )

    companies = sorted(
        {
            record.get("company")
            for record in records
            if record.get("company")
        }
    )

    if not companies:
        st.info(
            "No companies are available yet."
        )
    else:
        selected_company = (
            st.selectbox(
                "Select company",
                companies,
            )
        )

        history = company_history(
            selected_company,
            records,
        )

        st.write(
            f"**Applications:** "
            f"{len(history)}"
        )

        history_df = pd.DataFrame(
            history
        )

        columns = [
            "role",
            "stage",
            "source",
            "applied_date",
            "match_score",
            "recruiter_name",
            "notes",
        ]

        available = [
            column
            for column in columns
            if column
            in history_df.columns
        ]

        st.dataframe(
            history_df[available],
            width="stretch",
            hide_index=True,
        )

with tabs[4]:
    st.subheader(
        "Job Source Performance"
    )

    analytics = source_analytics(
        records
    )

    if not analytics:
        st.info(
            "No source analytics are available yet."
        )
    else:
        analytics_df = pd.DataFrame(
            analytics
        )

        st.dataframe(
            analytics_df,
            width="stretch",
            hide_index=True,
        )

        st.caption(
            "Response rate is based on applications that reached "
            "Recruiter Contacted, HR Round, Technical Round, "
            "Manager Round, Offer, or Joined."
        )

with tabs[5]:
    st.subheader(
        "Export Application CRM"
    )

    if not records:
        st.info(
            "No application data is available to export."
        )
    else:
        export_path = Path(
            export_crm_csv(
                records=records
            )
        )

        st.download_button(
            "Download Application CRM CSV",
            data=export_path.read_bytes(),
            file_name=export_path.name,
            mime="text/csv",
            width="stretch",
        )
