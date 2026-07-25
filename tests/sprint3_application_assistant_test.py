from __future__ import annotations

import json
from pathlib import Path

from app.services.application_package import (
    build_application_package,
    export_application_summary,
)


def main() -> None:
    profile = json.loads(
        Path("data/profile.json").read_text(encoding="utf-8-sig")
    )

    package = build_application_package(
        profile=profile,
        company="CareerPilot Test Company",
        role="Data Analyst",
        location="Bengaluru, Karnataka",
        job_link="https://example.com/data-analyst",
        job_description=(
            "We are hiring a Data Analyst with SQL, Python, Excel, "
            "Power BI, DAX, Power Query, dashboard development, "
            "reporting and KPI experience."
        ),
        resume_type="Data Analyst",
    )

    summary_path = Path(export_application_summary(package))
    resume_path = Path(package["optimized"]["output_path"])

    assert package["company"] == "CareerPilot Test Company"
    assert package["job_role"] == "Data Analyst"
    assert package["report"]["ats_score"] > 0
    assert resume_path.exists()
    assert summary_path.exists()
    assert package["cover_note"].strip()
    assert package["recruiter_email"].strip()
    assert package["linkedin_message"].strip()
    assert package["follow_up_message"].strip()
    assert package["interview_topics"]
    assert all(package["checklist"].values())

    print("=" * 70)
    print("CAREERPILOT SPRINT 3 APPLICATION ASSISTANT TEST")
    print("=" * 70)
    print("ATS score:", package["report"]["ats_score"])
    print("Resume:", resume_path)
    print("Summary:", summary_path)
    print("Checklist:", package["checklist"])
    print("\nSPRINT 3 APPLICATION ASSISTANT TEST PASSED")


if __name__ == "__main__":
    main()
