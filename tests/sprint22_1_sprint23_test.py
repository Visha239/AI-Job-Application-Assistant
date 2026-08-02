from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd

from app.services.application_crm import (
    add_application,
    load_crm,
)
from app.services.hourly_job_alert import (
    job_fingerprint,
    load_alert_state,
    save_alert_state,
    select_new_priority_jobs,
)
from app.services.interview_action_dashboard import (
    build_application_tracker_table,
    build_fresh_opportunity_table,
    filter_actionable_search_results,
    persist_application_statuses,
    persist_fresh_opportunity_statuses,
)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        crm_path = Path(temp_dir) / "application_crm.json"
        state_path = Path(temp_dir) / "hourly_alert_state.json"

        fresh = add_application(
            company="Fresh Analytics",
            role="Data Analyst",
            source="Official Careers",
            job_link="https://example.com/fresh",
            stage="Saved",
            match_score=95,
            crm_path=crm_path,
        )
        ready = add_application(
            company="Ready Systems",
            role="Business Analyst",
            source="LinkedIn",
            job_link="https://example.com/ready",
            stage="Ready to Apply",
            match_score=86,
            crm_path=crm_path,
        )
        applied = add_application(
            company="Applied Company",
            role="Power BI Developer",
            source="Indeed",
            job_link="https://example.com/applied",
            stage="Applied",
            match_score=90,
            crm_path=crm_path,
        )

        fresh_table = build_fresh_opportunity_table(crm_path=crm_path)
        applied_table = build_application_tracker_table(crm_path=crm_path)

        assert set(fresh_table["record_id"]) == {
            fresh["record_id"],
            ready["record_id"],
        }
        assert set(applied_table["record_id"]) == {
            applied["record_id"],
        }

        edited_fresh = fresh_table.copy()
        edited_fresh.loc[
            edited_fresh["record_id"] == fresh["record_id"],
            "stage",
        ] = "Applied"

        result = persist_fresh_opportunity_statuses(
            fresh_table,
            edited_fresh,
            crm_path=crm_path,
        )
        assert result["updated"] == 1

        refreshed_fresh = build_fresh_opportunity_table(crm_path=crm_path)
        refreshed_applied = build_application_tracker_table(crm_path=crm_path)

        assert fresh["record_id"] not in set(refreshed_fresh["record_id"])
        assert fresh["record_id"] in set(refreshed_applied["record_id"])

        edited_applications = refreshed_applied.copy()
        edited_applications.loc[
            edited_applications["record_id"] == fresh["record_id"],
            "stage",
        ] = "HR Round"

        progress_result = persist_application_statuses(
            refreshed_applied,
            edited_applications,
            crm_path=crm_path,
        )
        assert progress_result["updated"] == 1

        search_jobs = pd.DataFrame(
            [
                {
                    "title": "Data Analyst",
                    "company": "Fresh Analytics",
                    "job_url": "https://example.com/fresh",
                    "match_score": 95,
                },
                {
                    "title": "Reporting Analyst",
                    "company": "New Company",
                    "job_url": "https://example.com/new",
                    "match_score": 84,
                },
            ]
        )

        filtered, hidden = filter_actionable_search_results(
            search_jobs,
            load_crm(crm_path),
        )
        assert hidden == 1
        assert len(filtered) == 1
        assert filtered.iloc[0]["company"] == "New Company"

        priority_jobs = pd.DataFrame(
            [
                {
                    "title": "Data Analyst",
                    "company": "Alert One",
                    "job_url": "https://example.com/alert-one",
                    "match_score": 92,
                    "date_posted": "2026-08-02",
                },
                {
                    "title": "MIS Analyst",
                    "company": "Below Threshold",
                    "job_url": "https://example.com/low",
                    "match_score": 72,
                    "date_posted": "2026-08-02",
                },
            ]
        )

        new_jobs, discovered = select_new_priority_jobs(
            priority_jobs,
            minimum_score=80,
        )
        assert len(new_jobs) == 1

        fingerprint = job_fingerprint(new_jobs.iloc[0].to_dict())
        assert fingerprint in discovered

        save_alert_state(
            {
                "seen": [fingerprint],
                "last_run": "2026-08-02T15:00:00",
            },
            state_path,
        )
        restored = load_alert_state(state_path)
        assert fingerprint in restored["seen"]

        repeated, _ = select_new_priority_jobs(
            priority_jobs,
            seen=set(restored["seen"]),
            minimum_score=80,
        )
        assert repeated.empty

    print("=" * 72)
    print("CAREERPILOT SPRINT 22.1 + 23 TEST")
    print("=" * 72)
    print("Fresh opportunities separated from applications: PASS")
    print("Applied jobs move to the tracker: PASS")
    print("Previously applied jobs hidden from search: PASS")
    print("Application stage updates persist: PASS")
    print("Hourly high-priority threshold: PASS")
    print("Repeat alert prevention: PASS")
    print()
    print("SPRINT 22.1 + 23 TEST PASSED")


if __name__ == "__main__":
    main()
