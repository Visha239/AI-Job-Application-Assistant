CORE_SKILLS = {
    "Data Analyst": [
        "SQL", "Python", "Excel", "Power BI", "Tableau",
        "Data Analysis", "Reporting", "Dashboard", "KPI", "ETL"
    ],
    "Business Analyst": [
        "SQL", "Excel", "Business Analysis", "Requirements Gathering",
        "Documentation", "Gap Analysis", "Stakeholder", "UML",
        "Process Improvement", "Project Management"
    ],
    "Support Engineer": [
        "Linux", "SQL", "ServiceNow", "Jira", "Troubleshooting",
        "Incident Management", "Application Support", "Production Support"
    ]
}

PROJECT_RECOMMENDATIONS = {
    "Data Analyst": [
        "Power BI Manufacturing Dashboard",
        "HR Attendance Dashboard",
        "Loan Risk Analysis"
    ],
    "Business Analyst": [
        "Power BI Manufacturing Dashboard",
        "HR Attendance Dashboard",
        "Process Analysis Project"
    ],
    "Support Engineer": [
        "Enterprise Support Engineer Experience",
        "Incident Management",
        "Linux Troubleshooting"
    ]
}

def analyze_resume_intelligence(job_description, role_type):
    jd = job_description.lower()
    skills = CORE_SKILLS.get(role_type, CORE_SKILLS["Data Analyst"])

    matched = []
    missing = []

    for skill in skills:
        if skill.lower() in jd:
            matched.append(skill)
        else:
            missing.append(skill)

    current_score = round((len(matched) / len(skills)) * 100, 2)

    expected_score = min(current_score + (len(missing[:4]) * 5), 95)

    if current_score >= 80:
        recommendation = "Strong resume fit. Apply with minor tailoring."
    elif current_score >= 60:
        recommendation = "Good fit. Add missing keywords truthfully before applying."
    else:
        recommendation = "Weak fit. Apply only if role is important or update resume strongly."

    return {
        "current_score": current_score,
        "expected_score": expected_score,
        "matched_skills": matched,
        "missing_skills": missing,
        "recommended_projects": PROJECT_RECOMMENDATIONS.get(role_type, []),
        "recommendation": recommendation
    }