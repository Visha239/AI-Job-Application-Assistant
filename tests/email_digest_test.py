from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class EmailSettings:
    smtp_host: str
    smtp_port: int
    sender_email: str
    app_password: str
    recipient_email: str


def load_email_settings() -> EmailSettings:
    smtp_host = os.getenv(
        "CAREERPILOT_SMTP_HOST",
        "smtp.gmail.com",
    ).strip()

    smtp_port_text = os.getenv(
        "CAREERPILOT_SMTP_PORT",
        "587",
    ).strip()

    sender_email = os.getenv(
        "CAREERPILOT_SENDER_EMAIL",
        "",
    ).strip()

    app_password = os.getenv(
        "CAREERPILOT_EMAIL_APP_PASSWORD",
        "",
    ).replace(" ", "").strip()

    recipient_email = os.getenv(
        "CAREERPILOT_RECIPIENT_EMAIL",
        "",
    ).strip()

    try:
        smtp_port = int(smtp_port_text)
    except ValueError as exc:
        raise ValueError(
            "CAREERPILOT_SMTP_PORT must be a valid number."
        ) from exc

    return EmailSettings(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        sender_email=sender_email,
        app_password=app_password,
        recipient_email=recipient_email,
    )


def validate_email_settings(
    settings: EmailSettings,
) -> list[str]:
    errors: list[str] = []

    if not settings.smtp_host:
        errors.append("SMTP host is missing.")

    if settings.smtp_port <= 0:
        errors.append("SMTP port is invalid.")

    if not settings.sender_email:
        errors.append("Sender email is missing.")

    if "@" not in settings.sender_email:
        errors.append("Sender email is invalid.")

    if not settings.app_password:
        errors.append("Email app password is missing.")

    if not settings.recipient_email:
        errors.append("Recipient email is missing.")

    if "@" not in settings.recipient_email:
        errors.append("Recipient email is invalid.")

    return errors


def build_digest_email(
    html_content: str,
    subject: str,
    settings: EmailSettings,
    text_summary: str | None = None,
) -> EmailMessage:
    message = EmailMessage()

    message["From"] = settings.sender_email
    message["To"] = settings.recipient_email
    message["Subject"] = subject

    fallback_text = text_summary or (
        "Your CareerPilot daily job digest is ready. "
        "Open this email in an HTML-compatible email client."
    )

    message.set_content(fallback_text)
    message.add_alternative(
        html_content,
        subtype="html",
    )

    return message


def send_html_email(
    html_content: str,
    subject: str,
    settings: EmailSettings | None = None,
    text_summary: str | None = None,
) -> dict[str, Any]:
    active_settings = settings or load_email_settings()

    errors = validate_email_settings(active_settings)

    if errors:
        raise ValueError(
            "Email configuration error: "
            + " ".join(errors)
        )

    message = build_digest_email(
        html_content=html_content,
        subject=subject,
        settings=active_settings,
        text_summary=text_summary,
    )

    try:
        with smtplib.SMTP(
            active_settings.smtp_host,
            active_settings.smtp_port,
            timeout=30,
        ) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()

            server.login(
                active_settings.sender_email,
                active_settings.app_password,
            )

            server.send_message(message)

    except smtplib.SMTPAuthenticationError as exc:
        raise RuntimeError(
            "Email authentication failed. Use a Gmail app password, "
            "not your normal Gmail password."
        ) from exc

    except (smtplib.SMTPException, OSError) as exc:
        raise RuntimeError(
            f"Email delivery failed: {exc}"
        ) from exc

    return {
        "sent": True,
        "recipient": active_settings.recipient_email,
        "subject": subject,
    }


def send_digest_file(
    html_path: str | Path,
    subject: str,
    settings: EmailSettings | None = None,
) -> dict[str, Any]:
    path = Path(html_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Digest file was not found: {path}"
        )

    html_content = path.read_text(
        encoding="utf-8",
    )

    return send_html_email(
        html_content=html_content,
        subject=subject,
        settings=settings,
    )