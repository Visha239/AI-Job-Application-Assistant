from app.services.email_digest import (
    EmailSettings,
    build_digest_email,
    validate_email_settings,
)


def main() -> None:
    settings = EmailSettings(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        sender_email="sender@example.com",
        app_password="test-app-password",
        recipient_email="recipient@example.com",
    )

    errors = validate_email_settings(settings)

    assert not errors

    html_content = """
    <html>
        <body>
            <h1>CareerPilot Daily Job Digest</h1>
            <p>Test job digest content.</p>
        </body>
    </html>
    """

    message = build_digest_email(
        html_content=html_content,
        subject="CareerPilot Test Digest",
        settings=settings,
        text_summary="CareerPilot test digest.",
    )

    assert message["From"] == "sender@example.com"
    assert message["To"] == "recipient@example.com"
    assert message["Subject"] == "CareerPilot Test Digest"
    assert message.is_multipart()

    invalid_settings = EmailSettings(
        smtp_host="",
        smtp_port=0,
        sender_email="",
        app_password="",
        recipient_email="",
    )

    invalid_errors = validate_email_settings(
        invalid_settings
    )

    assert invalid_errors

    print("=" * 60)
    print("CAREERPILOT v1.0 EMAIL DIGEST TEST")
    print("=" * 60)
    print("Valid configuration errors:", errors)
    print(
        "Invalid configuration error count:",
        len(invalid_errors),
    )
    print("Email subject:", message["Subject"])
    print("\nCAREERPILOT v1.0 TEST PASSED")


if __name__ == "__main__":
    main()