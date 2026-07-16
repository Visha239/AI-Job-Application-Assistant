from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import tempfile

from app.services.application_crm import (
    add_application,
    company_history,
    crm_metrics,
    export_crm_csv,
    get_due_follow_ups,
    load_crm,
    source_analytics,
    update_application,
)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        crm_path = (
            Path(temp_dir)
            / "application_crm.json"
        )
        csv_path = (
            Path(temp_dir)
            / "application_crm.csv"
        )

        first = add_application(
            company="CareerPilot Test Company",
            role="Data Analyst",
            location="Bengaluru",
            source="linkedin",
            job_link="https://example.com/data",
            stage="Applied",
            match_score=88,
            recruiter_name="Test Recruiter",
            recruiter_email="recruiter@example.com",
            applied_date=date.today().isoformat(),
            next_follow_up_date=(
                date.today()
                - timedelta(days=1)
            ).isoformat(),
            crm_path=crm_path,
        )

        second = add_application(
            company="CareerPilot Test Company",
            role="Business Analyst",
            location="Remote",
            source="indeed",
            job_link="https://example.com/business",
            stage="HR Round",
            match_score=81,
            applied_date=date.today().isoformat(),
            next_follow_up_date="",
            crm_path=crm_path,
        )

        records = load_crm(
            crm_path
        )

        assert len(records) == 2

        due = get_due_follow_ups(
            records,
            on_date=date.today(),
        )

        assert len(due) == 1
        assert due[0]["record_id"] == (
            first["record_id"]
        )

        updated = update_application(
            first["record_id"],
            stage="Recruiter Contacted",
            last_follow_up_date=(
                date.today().isoformat()
            ),
            next_follow_up_date=(
                date.today()
                + timedelta(days=5)
            ).isoformat(),
            crm_path=crm_path,
        )

        assert updated["stage"] == (
            "Recruiter Contacted"
        )

        metrics = crm_metrics(
            load_crm(crm_path)
        )

        assert metrics[
            "applications_sent"
        ] == 2
        assert metrics[
            "applied_today"
        ] == 2
        assert metrics[
            "interviews"
        ] == 1
        assert metrics[
            "response_rate"
        ] == 100.0

        analytics = source_analytics(
            load_crm(crm_path)
        )

        assert len(analytics) == 2

        history = company_history(
            "CareerPilot Test Company",
            load_crm(crm_path),
        )

        assert len(history) == 2

        exported = export_crm_csv(
            crm_path=crm_path,
            output_path=csv_path,
        )

        assert Path(exported).exists()

        print("=" * 70)
        print(
            "CAREERPILOT SPRINT 8 "
            "APPLICATION CRM TEST"
        )
        print("=" * 70)
        print(
            "Applications:",
            metrics[
                "applications_sent"
            ],
        )
        print(
            "Interviews:",
            metrics["interviews"],
        )
        print(
            "Response rate:",
            metrics["response_rate"],
        )
        print(
            "Follow-ups due:",
            len(due),
        )
        print(
            "CSV:",
            exported,
        )
        print(
            "\nSPRINT 8 APPLICATION CRM TEST PASSED"
        )


if __name__ == "__main__":
    main()
