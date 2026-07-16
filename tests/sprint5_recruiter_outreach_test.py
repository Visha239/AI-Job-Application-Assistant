from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import tempfile

from app.services.outreach_manager import (
    build_follow_up_email,
    build_linkedin_message,
    build_recruiter_email,
    create_outreach_record,
    export_records_csv,
    get_due_follow_ups,
    load_records,
    update_outreach_record,
)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        store_path = Path(temp_dir) / "outreach.json"
        csv_path = Path(temp_dir) / "outreach.csv"

        record = create_outreach_record(
            company="CareerPilot Test Company",
            role="Data Analyst",
            recruiter_name="Test Recruiter",
            recruiter_email="recruiter@example.com",
            recruiter_linkedin=(
                "https://linkedin.com/in/test-recruiter"
            ),
            job_link="https://example.com/job",
            status="Contacted",
            initial_contact_date=date.today().isoformat(),
            follow_up_date=(
                date.today() - timedelta(days=1)
            ).isoformat(),
            last_contact_date=date.today().isoformat(),
            notes="Sprint 5 test",
            store_path=store_path,
        )

        records = load_records(store_path)

        assert len(records) == 1
        assert record["company"] == "CareerPilot Test Company"

        due = get_due_follow_ups(
            records,
            on_date=date.today(),
        )

        assert len(due) == 1

        updated = update_outreach_record(
            record["record_id"],
            status="Replied",
            follow_up_date="",
            store_path=store_path,
        )

        assert updated["status"] == "Replied"

        email = build_recruiter_email(
            candidate_name="Vishal Basavaraj Banakar",
            candidate_email="vishalbanakar321@gmail.com",
            company="CareerPilot Test Company",
            role="Data Analyst",
            matched_skills=[
                "SQL",
                "Power BI",
                "Python",
                "Excel",
            ],
            recruiter_name="Test Recruiter",
            job_link="https://example.com/job",
        )

        linkedin = build_linkedin_message(
            candidate_name="Vishal Basavaraj Banakar",
            company="CareerPilot Test Company",
            role="Data Analyst",
            matched_skills=[
                "SQL",
                "Power BI",
                "Python",
            ],
        )

        follow_up = build_follow_up_email(
            candidate_name="Vishal Basavaraj Banakar",
            candidate_email="vishalbanakar321@gmail.com",
            company="CareerPilot Test Company",
            role="Data Analyst",
            recruiter_name="Test Recruiter",
        )

        assert "Data Analyst" in email
        assert "CareerPilot Test Company" in email
        assert len(linkedin) <= 300
        assert "following up" in follow_up.lower()

        exported = export_records_csv(
            output_path=csv_path,
            store_path=store_path,
        )

        assert Path(exported).exists()

        print("=" * 70)
        print("CAREERPILOT SPRINT 5 RECRUITER OUTREACH TEST")
        print("=" * 70)
        print("Record created:", record["record_id"])
        print("Follow-ups due:", len(due))
        print("Updated status:", updated["status"])
        print("LinkedIn characters:", len(linkedin))
        print("CSV:", exported)
        print(
            "\nSPRINT 5 RECRUITER OUTREACH TEST PASSED"
        )


if __name__ == "__main__":
    main()

