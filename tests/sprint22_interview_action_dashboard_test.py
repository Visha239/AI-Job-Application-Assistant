from __future__ import annotations

import tempfile
from pathlib import Path

from app.services.application_crm import (
    add_application,
    crm_metrics,
    load_crm,
)
from app.services.interview_action_dashboard import (
    build_opportunity_table,
    build_status_editor,
    persist_status_editor,
)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        crm_path = Path(temp_dir) / "application_crm.json"

        first = add_application(
            company="Alpha Analytics",
            role="Data Analyst",
            source="Official Careers",
            job_link="https://example.com/alpha",
            stage="Saved",
            match_score=94,
            crm_path=crm_path,
        )
        second = add_application(
            company="Beta Systems",
            role="Business Analyst",
            source="LinkedIn",
            job_link="https://example.com/beta",
            stage="Ready to Apply",
            match_score=82,
            crm_path=crm_path,
        )
        add_application(
            company="Closed Company",
            role="Reporting Analyst",
            source="Indeed",
            job_link="https://example.com/closed",
            stage="Rejected",
            match_score=70,
            crm_path=crm_path,
        )

        opportunities = build_opportunity_table(
            crm_path=crm_path,
            limit=10,
        )
        assert len(opportunities) == 2
        assert opportunities.iloc[0]["match_score"] == 94
        assert opportunities.iloc[0]["job_link"] == "https://example.com/alpha"
        assert "source" in opportunities.columns
        assert "stage" in opportunities.columns

        original = build_status_editor(crm_path=crm_path)
        edited = original.copy()

        edited.loc[
            edited["record_id"] == first["record_id"],
            "applied",
        ] = True
        edited.loc[
            edited["record_id"] == second["record_id"],
            "stage",
        ] = "HR Round"

        result = persist_status_editor(
            original,
            edited,
            crm_path=crm_path,
        )
        assert result["updated"] == 2
        assert result["errors"] == 0

        records = load_crm(crm_path)
        by_id = {
            record["record_id"]: record
            for record in records
        }
        assert by_id[first["record_id"]]["stage"] == "Applied"
        assert by_id[first["record_id"]]["applied_date"]
        assert by_id[second["record_id"]]["stage"] == "HR Round"

        metrics = crm_metrics(records)
        assert metrics["applications_sent"] == 3
        assert metrics["interviews"] == 1

    print("=" * 72)
    print("CAREERPILOT SPRINT 22 INTERVIEW ACTION DASHBOARD TEST")
    print("=" * 72)
    print("Opportunity ranking table: PASS")
    print("Direct job link and source fields: PASS")
    print("Applied checkbox persistence: PASS")
    print("Status dropdown persistence: PASS")
    print("Dashboard metrics reflection: PASS")
    print()
    print("SPRINT 22 INTERVIEW ACTION DASHBOARD TEST PASSED")


if __name__ == "__main__":
    main()
