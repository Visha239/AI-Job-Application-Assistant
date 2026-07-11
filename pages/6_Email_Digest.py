from __future__ import annotations

from datetime import datetime
from pathlib import Path

import streamlit as st

from app.services.daily_job_digest import run_daily_digest
from app.services.email_digest import (
    load_email_settings,
    send_digest_file,
    validate_email_settings,
)


st.set_page_config(
    page_title="CareerPilot Email Digest",
    page_icon="✉️",
    layout="wide",
)

st.title("✉️ Email Daily Job Digest")
st.caption(
    "Generate your current job digest and send it to your email."
)

settings = load_email_settings()
settings_errors = validate_email_settings(settings)

with st.expander("Email Configuration Status"):
    st.write(
        "**SMTP host:**",
        settings.smtp_host or "Not configured",
    )
    st.write(
        "**SMTP port:**",
        settings.smtp_port,
    )
    st.write(
        "**Sender:**",
        settings.sender_email or "Not configured",
    )
    st.write(
        "**Recipient:**",
        settings.recipient_email or "Not configured",
    )

    if settings_errors:
        for error in settings_errors:
            st.warning(error)
    else:
        st.success("Email configuration is complete.")

col1, col2 = st.columns(2)

with col1:
    preview_button = st.button(
        "Generate Preview",
        width="stretch",
    )

with col2:
    send_button = st.button(
        "Generate and Send Email",
        type="primary",
        width="stretch",
        disabled=bool(settings_errors),
    )


if preview_button or send_button:
    with st.spinner(
        "Searching jobs and generating the digest..."
    ):
        try:
            result = run_daily_digest()
            st.session_state["email_digest_result"] = result

        except Exception as exc:
            st.error(f"Digest generation failed: {exc}")
            result = None

    if result and send_button:
        subject = (
            "CareerPilot Daily Job Digest - "
            + datetime.now().strftime("%d %b %Y")
        )

        try:
            delivery = send_digest_file(
                html_path=result["html_path"],
                subject=subject,
                settings=settings,
            )

            st.success(
                f"Digest emailed to "
                f"{delivery['recipient']}."
            )

        except Exception as exc:
            st.error(f"Email delivery failed: {exc}")


result = st.session_state.get(
    "email_digest_result"
)

if result:
    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric(
        "Jobs Collected",
        result["jobs_collected"],
    )

    metric2.metric(
        "Strong Matches",
        result["strong_matches"],
    )

    metric3.metric(
        "New Jobs Saved",
        result["saved_jobs"],
    )

    metric4.metric(
        "Duplicates",
        result["duplicate_jobs"],
    )

    html_path = Path(result["html_path"])
    csv_path = Path(result["csv_path"])

    if html_path.exists():
        st.download_button(
            label="Download HTML Digest",
            data=html_path.read_bytes(),
            file_name=html_path.name,
            mime="text/html",
            width="stretch",
        )

    if csv_path.exists():
        st.download_button(
            label="Download Ranked Jobs CSV",
            data=csv_path.read_bytes(),
            file_name=csv_path.name,
            mime="text/csv",
            width="stretch",
        )

    if result["errors"]:
        with st.expander(
            f"Search warnings ({len(result['errors'])})"
        ):
            for error in result["errors"]:
                st.warning(error)