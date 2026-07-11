from pathlib import Path

from app.services.interview_preparation import (
    export_interview_report,
    generate_interview_plan,
)


def main() -> None:
    job_description = """
    We are hiring a Data Analyst with SQL, Python, Excel,
    Power BI, Power Query, DAX, dashboard development,
    KPI reporting and data visualization experience.

    The candidate will work with stakeholders, gather requirements,
    analyze business data and present insights.
    """

    plan = generate_interview_plan(
        company="CareerPilot Test Company",
        role="Data Analyst",
        job_description=job_description,
    )

    assert plan["company"] == "CareerPilot Test Company"
    assert plan["role"] == "Data Analyst"
    assert plan["ats_score"] > 0
    assert plan["questions"]
    assert plan["research_links"]
    assert any(
        question.category == "SQL"
        for question in plan["questions"]
    )
    assert any(
        question.category == "Power BI"
        for question in plan["questions"]
    )

    output_path = Path(export_interview_report(plan))

    assert output_path.exists()

    print("=" * 60)
    print("CAREERPILOT v1.1 INTERVIEW PREPARATION TEST")
    print("=" * 60)
    print("ATS score:", plan["ats_score"])
    print("Matched skills:", plan["matched_skills"])
    print("Missing skills:", plan["missing_skills"])
    print("Questions generated:", len(plan["questions"]))
    print("Report:", output_path)
    print("\nCAREERPILOT v1.1 TEST PASSED")


if __name__ == "__main__":
    main()