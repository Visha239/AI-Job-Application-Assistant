from app.utils.config_loader import get_role_config


def analyze_resume_intelligence(job_description, role_type):
    role_config = get_role_config(role_type)

    if not role_config:
        return {
            "current_score": 0,
            "expected_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "recommended_projects": [],
            "resume_version": "Default Resume",
            "recommendation": "Invalid role selected."
        }

    jd = job_description.lower()
    skills = role_config["core_skills"]

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
        "recommended_projects": role_config["recommended_projects"],
        "resume_version": role_config["resume_version"],
        "recommendation": recommendation
    }