import json
from pathlib import Path

from app.services.cover_letter import generate_cover_note
from app.services.recruiter import generate_email
from app.services.resume_optimizer import ResumeOptimizer
from app.services.resume_report import ResumeReport


def main() -> None:
    profile_path = Path("data/profile.json")

    with profile_path.open("r", encoding="utf-8") as file:
        profile = json.load(file)

    job_description = """
    We are hiring a Data Analyst with practical experience in SQL,
    Python, Excel, Power BI, Power Query, DAX, dashboard development,
    KPI reporting, ETL and data visualization.

    The candidate will analyze business data, build reports and work
    with stakeholders to support decision-making.
    """

    report = ResumeReport().generate(job_description)

    optimized = ResumeOptimizer().optimize_resume(
        role_type="Data Analyst",
        job_description=job_description,
    )

    cover_note = generate_cover_note(
        profile=profile,
        company="CareerPilot Test Company",
        role="Data Analyst",
        matched_skills=report["matched"],
    )

    recruiter_email = generate_email(
        profile=profile,
        company="CareerPilot Test Company",
        role="Data Analyst",
    )

    output_path = Path(optimized["output_path"])

    assert report["ats_score"] > 0
    assert report["matched"]
    assert output_path.exists()
    assert "CareerPilot Test Company" in cover_note
    assert "CareerPilot Test Company" in recruiter_email

    print("=" * 60)
    print("APPLICATION WORKFLOW TEST")
    print("=" * 60)
    print("ATS score:", report["ats_score"])
    print("Matched:", report["matched"])
    print("Missing:", report["missing"])
    print("Resume:", output_path)
    print("Cover note generated:", bool(cover_note))
    print("Recruiter email generated:", bool(recruiter_email))
    print("\nAPPLICATION WORKFLOW TEST PASSED")


if __name__ == "__main__":
    main()