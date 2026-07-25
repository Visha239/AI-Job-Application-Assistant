from __future__ import annotations

from pathlib import Path
import tempfile

from app.services.application_context import (
    clear_selected_job,
    context_fingerprint,
    get_selected_job,
    load_persisted_job_context,
    save_selected_job,
    update_selected_job,
)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        context_path = (
            Path(temp_dir)
            / "current_job_context.json"
        )

        first_session: dict = {}

        saved = save_selected_job(
            first_session,
            {
                "title": "Data Analyst",
                "company": (
                    "CareerPilot Test Company"
                ),
                "location": (
                    "Bengaluru, Karnataka"
                ),
                "job_url": (
                    "https://example.com/job"
                ),
                "description": (
                    "SQL Power BI Excel " * 30
                ),
                "site": "linkedin",
                "match_score": 88,
                "priority": "High priority",
                "apply_urgency": (
                    "Apply today"
                ),
                "matched_skills": (
                    "SQL, Power BI, Excel"
                ),
                "missing_job_skills": (
                    "Snowflake"
                ),
                "resume_version": (
                    "Data Analyst Resume"
                ),
            },
            context_path=context_path,
        )

        assert saved["company"] == (
            "CareerPilot Test Company"
        )
        assert context_path.exists()

        first_fingerprint = (
            context_fingerprint(saved)
        )

        clear_selected_job(
            first_session,
            remove_persisted=False,
            context_path=context_path,
        )

        second_session: dict = {}

        loaded = get_selected_job(
            second_session,
            context_path=context_path,
        )

        assert loaded["company"] == (
            "CareerPilot Test Company"
        )
        assert loaded["job_role"] == (
            "Data Analyst"
        )
        assert loaded["job_link"] == (
            "https://example.com/job"
        )
        assert loaded[
            "matched_skills"
        ] == "SQL, Power BI, Excel"
        assert (
            context_fingerprint(loaded)
            == first_fingerprint
        )

        updated = update_selected_job(
            second_session,
            {
                "job_description": (
                    "Full detailed job description"
                ),
                "description_status": (
                    "available"
                ),
                "matched_skills": (
                    "SQL, Power BI, Excel, Python"
                ),
            },
            context_path=context_path,
        )

        assert (
            updated["job_description"]
            == "Full detailed job description"
        )
        assert (
            updated["matched_skills"]
            == "SQL, Power BI, Excel, Python"
        )

        persisted = (
            load_persisted_job_context(
                context_path=context_path
            )
        )

        assert persisted["job_role"] == (
            "Data Analyst"
        )
        assert persisted[
            "matched_skills"
        ] == (
            "SQL, Power BI, Excel, Python"
        )

        print("=" * 70)
        print(
            "CAREERPILOT SPRINT 6 "
            "SHARED APPLICATION CONTEXT TEST"
        )
        print("=" * 70)
        print(
            "Company:",
            loaded["company"],
        )
        print(
            "Role:",
            loaded["job_role"],
        )
        print(
            "Job link:",
            loaded["job_link"],
        )
        print(
            "Matched skills:",
            updated["matched_skills"],
        )
        print(
            "\nSPRINT 6 SHARED CONTEXT TEST PASSED"
        )


if __name__ == "__main__":
    main()
