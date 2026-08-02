from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd

from app.services.application_crm import load_crm
from app.services.interview_action_dashboard import (
    build_application_tracker_table,
)
from app.services.live_job_crm import (
    build_live_search_editor,
    persist_live_search_statuses,
    sync_search_results_to_crm,
)


def main() -> None:
    jobs = pd.DataFrame(
        [
            {
                "title": "Data Analyst",
                "company": "Alpha Analytics",
                "site": "Official Careers",
                "location": "Bengaluru",
                "date_posted": "2026-08-02",
                "job_url": "https://example.com/alpha",
                "match_score": 94,
            },
            {
                "title": "Business Analyst",
                "company": "Beta Systems",
                "site": "LinkedIn",
                "location": "Bengaluru",
                "date_posted": "2026-08-02",
                "job_url": "https://example.com/beta",
                "match_score": 87,
            },
        ]
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        crm_path = Path(temp_dir) / "application_crm.json"

        synced = sync_search_results_to_crm(jobs, crm_path=crm_path)
        assert synced["created"] == 2
        assert len(load_crm(crm_path)) == 2

        live, hidden = build_live_search_editor(jobs, crm_path=crm_path)
        assert hidden == 0
        assert len(live) == 2
        assert set(live["stage"]) == {"Saved"}

        edited = live.copy()
        edited.loc[
            edited["company"] == "Alpha Analytics",
            "stage",
        ] = "Applied"

        saved = persist_live_search_statuses(
            live,
            edited,
            crm_path=crm_path,
        )
        assert saved["updated"] == 1

        refreshed, hidden = build_live_search_editor(
            jobs,
            crm_path=crm_path,
        )
        assert hidden == 1
        assert len(refreshed) == 1
        assert refreshed.iloc[0]["company"] == "Beta Systems"

        tracker = build_application_tracker_table(crm_path=crm_path)
        assert len(tracker) == 1
        assert tracker.iloc[0]["company"] == "Alpha Analytics"
        assert tracker.iloc[0]["stage"] == "Applied"
        assert tracker.iloc[0]["applied_date"]

        synced_again = sync_search_results_to_crm(jobs, crm_path=crm_path)
        assert synced_again["created"] == 0
        assert len(load_crm(crm_path)) == 2

    print("=" * 72)
    print("CAREERPILOT LIVE JOB SEARCH CRM TEST")
    print("=" * 72)
    print("Search results sync to CRM: PASS")
    print("Live status editor: PASS")
    print("Applied jobs disappear from search: PASS")
    print("Applied jobs move to tracker: PASS")
    print("Repeat searches do not duplicate records: PASS")
    print()
    print("LIVE JOB SEARCH CRM TEST PASSED")


if __name__ == "__main__":
    main()
