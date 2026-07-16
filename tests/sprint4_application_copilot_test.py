from __future__ import annotations

from app.services.ats_intelligence import analyze_ats
from app.services.jd_capture import resolve_job_description


def main() -> None:
    profile = {
        "skills": [
            "Python",
            "SQL",
            "Power BI",
            "Excel",
            "Tableau",
            "Linux",
            "ServiceNow",
            "Jira",
            "Data Analysis",
        ]
    }

    full_jd = """
    We are hiring a Data Analyst with 0 to 2 years of experience.
    The candidate will use SQL, Python, Excel, Power BI, DAX,
    Power Query, dashboard development, KPI reporting, ETL,
    data modeling, statistics, and stakeholder communication.
    The role includes building reports, cleaning data, creating
    visualizations, presenting insights, and supporting business
    teams. Experience with Snowflake and Azure is preferred.
    """

    report = analyze_ats(
        job_description=full_jd,
        profile=profile,
    )

    assert report["total_keywords"] >= 8
    assert "SQL" in report["matched"]
    assert "Power BI" in report["matched"]
    assert "Snowflake" in report["missing"]
    assert "Azure" in report["missing"]
    assert report["confidence"] in {
        "Medium",
        "High",
    }
    assert report["ats_score"] < 100

    tiny_report = analyze_ats(
        job_description="SQL required.",
        profile=profile,
    )

    assert tiny_report["ats_score"] <= 55
    assert tiny_report["confidence"] == "Low"

    capture = resolve_job_description(
        existing_description=full_jd,
        job_url="https://example.com/job",
    )

    assert capture.status == "available"
    assert capture.description.strip() == " ".join(
        full_jd.split()
    )

    print("=" * 70)
    print("CAREERPILOT SPRINT 4 APPLICATION COPILOT TEST")
    print("=" * 70)
    print("ATS score:", report["ats_score"])
    print("Confidence:", report["confidence"])
    print("Matched:", report["matched"])
    print("Missing:", report["missing"])
    print("Recommendation:", report["recommendation"])
    print("Capture status:", capture.status)
    print(
        "\nSPRINT 4 APPLICATION COPILOT TEST PASSED"
    )


if __name__ == "__main__":
    main()

