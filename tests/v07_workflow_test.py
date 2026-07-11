from app.services.analytics import get_dashboard_metrics
from app.services.application_context import (
    build_job_context,
)
from app.services.resume_history import (
    get_resume_count,
)


def main() -> None:
    sample_job = {
        "company": "CareerPilot Test Company",
        "title": "Data Analyst",
        "location": "Bengaluru, Karnataka",
        "job_url": "https://example.com/job",
        "description": "SQL Python Power BI Excel",
        "site": "test",
        "match_score": 85,
        "matched_skills": "SQL, Python, Power BI, Excel",
        "missing_profile_skills": "Tableau",
        "resume_version": "Data Analyst Resume",
    }

    context = build_job_context(sample_job)

    assert context["company"] == "CareerPilot Test Company"
    assert context["job_role"] == "Data Analyst"
    assert context["match_score"] == 85
    assert context["resume_version"] == "Data Analyst Resume"

    metrics = get_dashboard_metrics()
    resume_count = get_resume_count()

    print("=" * 60)
    print("CAREERPILOT v0.7 TEST")
    print("=" * 60)
    print("Context company:", context["company"])
    print("Context role:", context["job_role"])
    print("Context score:", context["match_score"])
    print("Applications:", metrics["total_applications"])
    print("Saved jobs:", metrics["saved_jobs"])
    print("Generated resumes:", resume_count)
    print("\nCAREERPILOT v0.7 TEST PASSED")


if __name__ == "__main__":
    main()