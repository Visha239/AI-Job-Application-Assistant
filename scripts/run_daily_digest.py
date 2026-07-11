from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from app.services.daily_job_digest import run_daily_digest
from app.services.email_digest import (
    load_email_settings,
    send_digest_file,
    validate_email_settings,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run CareerPilot's daily job search and optionally "
            "send the HTML digest by email."
        )
    )

    parser.add_argument(
        "--send-email",
        action="store_true",
        help="Send the generated digest by email.",
    )

    parser.add_argument(
        "--preview-only",
        action="store_true",
        help="Generate the digest without sending email.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    print("=" * 60)
    print("CAREERPILOT DAILY AUTOMATION")
    print("=" * 60)

    try:
        result = run_daily_digest()

    except Exception as exc:
        print(f"Daily digest failed: {exc}")
        return 1

    print("Jobs collected:", result["jobs_collected"])
    print("Strong matches:", result["strong_matches"])
    print("New jobs saved:", result["saved_jobs"])
    print("Duplicates skipped:", result["duplicate_jobs"])
    print("HTML report:", result["html_path"])
    print("CSV report:", result["csv_path"])

    if result["errors"]:
        print("\nWarnings:")

        for error in result["errors"]:
            print("-", error)

    if args.preview_only or not args.send_email:
        print("\nPreview mode complete. No email was sent.")
        return 0

    settings = load_email_settings()
    settings_errors = validate_email_settings(settings)

    if settings_errors:
        print("\nEmail was not sent:")
        for error in settings_errors:
            print("-", error)
        return 1

    subject = (
        "CareerPilot Daily Job Digest - "
        + datetime.now().strftime("%d %b %Y")
    )

    try:
        delivery = send_digest_file(
            html_path=Path(result["html_path"]),
            subject=subject,
            settings=settings,
        )

    except Exception as exc:
        print(f"\nEmail delivery failed: {exc}")
        return 1

    print(
        "\nEmail sent successfully to:",
        delivery["recipient"],
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())