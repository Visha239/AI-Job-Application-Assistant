from __future__ import annotations
from pathlib import Path
import tempfile
from app.services.application_queue import add_jobs_to_queue, export_queue_csv, get_active_queue, load_queue, queue_summary, remove_queue_item, update_queue_item

def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        queue_path = Path(temp_dir) / "application_queue.json"
        csv_path = Path(temp_dir) / "application_queue.csv"
        jobs = [
            {"title": "Data Analyst", "company": "CareerPilot Test Company", "location": "Bengaluru, Karnataka", "job_url": "https://example.com/data", "description": "SQL Power BI Excel Python", "site": "linkedin", "match_score": 88, "priority": "High priority", "apply_urgency": "Apply today", "freshness_label": "Posted today", "matched_skills": "SQL, Power BI, Excel", "missing_job_skills": "Snowflake", "resume_version": "Data Analyst Resume"},
            {"title": "Production Support Analyst", "company": "Support Test Company", "location": "Remote", "job_url": "https://example.com/support", "description": "SQL Linux Jira ServiceNow", "site": "indeed", "match_score": 92, "priority": "Apply immediately", "apply_urgency": "Apply immediately", "freshness_label": "Posted very recently", "matched_skills": "SQL, Linux, Jira, ServiceNow", "resume_version": "Support Engineer Resume"},
        ]
        result = add_jobs_to_queue(jobs, queue_path=queue_path)
        assert result["added"] == 2 and result["duplicates"] == 0
        duplicate_result = add_jobs_to_queue([jobs[0]], queue_path=queue_path)
        assert duplicate_result["duplicates"] == 1
        queue = load_queue(queue_path)
        assert len(queue) == 2
        active = get_active_queue(queue)
        assert active[0]["company"] == "Support Test Company"
        first_id = queue[0]["queue_id"]
        updated = update_queue_item(first_id, status="Applied", notes="Applied using company site.", queue_path=queue_path)
        assert updated["status"] == "Applied" and updated["applied_at"]
        summary = queue_summary(load_queue(queue_path))
        assert summary["applied"] == 1 and summary["total"] == 2
        exported = export_queue_csv(queue_path=queue_path, output_path=csv_path)
        assert Path(exported).exists()
        second_id = load_queue(queue_path)[1]["queue_id"]
        assert remove_queue_item(second_id, queue_path=queue_path)
        assert len(load_queue(queue_path)) == 1
        print("=" * 70)
        print("CAREERPILOT SPRINT 7 AUTO APPLY ASSISTANT TEST")
        print("=" * 70)
        print("Jobs added:", result["added"])
        print("Duplicates skipped:", duplicate_result["duplicates"])
        print("Applied:", summary["applied"])
        print("CSV:", exported)
        print("\nSPRINT 7 AUTO APPLY ASSISTANT TEST PASSED")

if __name__ == "__main__":
    main()
