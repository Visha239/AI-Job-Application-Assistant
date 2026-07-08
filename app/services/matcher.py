ROLE_SKILLS = {
    "Data Analyst": ["SQL", "Python", "Excel", "Power BI", "Tableau", "Data Analysis"],
    "Business Analyst": ["SQL", "Excel", "Business Analysis", "Requirements Gathering", "Documentation", "Gap Analysis", "Stakeholder", "UML"],
    "Support Engineer": ["Linux", "ServiceNow", "Jira", "SQL"]
}

def match_job(job_description, role_type):
    required_skills = ROLE_SKILLS.get(role_type, ROLE_SKILLS["Data Analyst"])

    matched = []
    missing = []

    for skill in required_skills:
        if skill.lower() in job_description.lower():
            matched.append(skill)
        else:
            missing.append(skill)

    score = round((len(matched) / len(required_skills)) * 100, 2)

    if score >= 75:
        recommendation = "Strong match. Apply."
    elif score >= 50:
        recommendation = "Medium match. Apply if the company looks good."
    else:
        recommendation = "Low match. Apply only if you really want this company."

    return {
        "score": score,
        "matched": matched,
        "missing": missing,
        "recommendation": recommendation
    }