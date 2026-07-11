from app.services.decision_engine import (
    analyze_job_decision,
)


def main() -> None:
    strong_job = {
        "title": "Data Analyst",
        "company": "Strong Match Company",
        "location": "Bengaluru, Karnataka",
        "site": "test",
        "job_url": "https://example.com/strong-job",
        "description": (
            "We are hiring a Data Analyst with SQL, Python, "
            "Excel, Power BI, Tableau, dashboards, reporting, "
            "KPI analysis and data visualization experience. "
            "Candidates with 0 to 2 years of experience may apply."
        ),
        "match_score": 88,
        "matched_skills": (
            "SQL, Python, Excel, Power BI, Tableau, Data Analysis"
        ),
        "missing_profile_skills": (
            "Linux, ServiceNow, Jira"
        ),
    }

    senior_job = {
        "title": "Senior Data Engineering Manager",
        "company": "Senior Company",
        "location": "Hyderabad, India",
        "site": "test",
        "job_url": "https://example.com/senior-job",
        "description": (
            "Requires 8+ years of experience in Spark, "
            "Snowflake, Databricks, Java and team leadership."
        ),
        "match_score": 20,
        "matched_skills": "",
        "missing_profile_skills": (
            "Python, SQL, Power BI"
        ),
    }

    strong_result = analyze_job_decision(strong_job)
    senior_result = analyze_job_decision(senior_job)

    assert strong_result["overall_score"] > (
        senior_result["overall_score"]
    )

    assert strong_result["recommended_resume"] == (
        "Data Analyst Resume"
    )

    assert strong_result["priority"] in {
        "Very High",
        "High",
        "Medium",
    }

    assert senior_result["required_experience"] == 8

    assert senior_result["priority"] in {
        "Low",
        "Very Low",
    }

    print("=" * 60)
    print("CAREERPILOT v0.9 DECISION ENGINE TEST")
    print("=" * 60)

    print("\nSTRONG JOB")
    print(
        "Overall score:",
        strong_result["overall_score"],
    )
    print(
        "Recommendation:",
        strong_result["recommendation"],
    )
    print(
        "Interview probability:",
        strong_result["interview_probability"],
    )
    print(
        "Resume:",
        strong_result["recommended_resume"],
    )

    print("\nSENIOR JOB")
    print(
        "Overall score:",
        senior_result["overall_score"],
    )
    print(
        "Recommendation:",
        senior_result["recommendation"],
    )
    print(
        "Required experience:",
        senior_result["required_experience"],
    )
    print(
        "Risks:",
        senior_result["risks"],
    )

    print("\nCAREERPILOT v0.9 TEST PASSED")


if __name__ == "__main__":
    main()