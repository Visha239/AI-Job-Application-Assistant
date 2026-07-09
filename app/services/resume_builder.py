def generate_resume(profile, role_type, missing_keywords=None):
    if missing_keywords is None:
        missing_keywords = []

    summary = (
        f"Data-focused professional with {profile['experience_years']} years of experience "
        "in SQL, Python, Excel, Power BI, Tableau, dashboards, reporting, and business analysis. "
        "Experienced in analyzing data, creating insights, and supporting business decision-making."
    )

    if role_type == "Business Analyst":
        summary = (
            f"Business-focused analyst with {profile['experience_years']} years of experience "
            "in SQL, Excel, documentation, stakeholder communication, requirement understanding, "
            "gap analysis, reporting, and process improvement."
        )

    if role_type == "Support Engineer":
        summary = (
            f"Technical support professional with {profile['experience_years']} years of experience "
            "in Linux, SQL, ServiceNow, Jira, incident management, troubleshooting, and production support."
        )

    resume = {
        "name": profile["name"],
        "email": profile["email"],
        "role_type": role_type,
        "summary": summary,
        "skills": profile["skills"] + missing_keywords[:5],
        "projects": profile["projects"],
        "experience": [
            "Enterprise Support Engineer at Evertz India Pvt Ltd",
            "Worked on SQL queries, Linux troubleshooting, ServiceNow tickets, Jira reports, and production issue resolution."
        ]
    }

    return resume