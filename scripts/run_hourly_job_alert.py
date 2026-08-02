from __future__ import annotations

import argparse
import sys

from app.services.hourly_job_alert import run_hourly_alert


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Search all enabled CareerPilot sources and email only "
            "genuinely new high-priority matches."
        )
    )
    parser.add_argument(
        "--minimum-score",
        type=int,
        default=80,
        help="Minimum match percentage required for an immediate alert.",
    )
    parser.add_argument(
        "--preview-only",
        action="store_true",
        help="Run monitoring without sending an email.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    print("=" * 64)
    print("CAREERPILOT HOURLY HIGH-PRIORITY MONITOR")
    print("=" * 64)

    try:
        result = run_hourly_alert(
            minimum_score=args.minimum_score,
            send_email=not args.preview_only,
        )
    except Exception as exc:
        print(f"Hourly monitor failed: {exc}")
        return 1

    print("Jobs collected:", result["jobs_collected"])
    print("Ranked jobs:", result["ranked_jobs"])
    print("New high-priority jobs:", result["new_priority_jobs"])
    print("Email sent:", result["email_sent"])
    print("State file:", result["state_path"])
    print("Source counts:", result["source_counts"])

    if result["errors"]:
        print("Warnings:")
        for error in result["errors"]:
            print("-", error)

    if not result["new_priority_jobs"]:
        print("No new high-priority jobs. No alert email was sent.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
