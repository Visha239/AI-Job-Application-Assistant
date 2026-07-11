from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


PROFILE_PATH = Path("data/profile.json")

ANALYTICS_TERMS = {
    "sql",
    "python",
    "excel",
    "power bi",
    "tableau",
    "data analysis",
    "dashboard",
    "reporting",
    "kpi",
    "dax",
    "power query",
    "etl",
    "data visualization",
}

SUPPORT_TERMS = {
    "linux",
    "servicenow",
    "jira",
    "aws",
    "troubleshooting",
    "incident management",
    "application support",
    "production support",
}

BUSINESS_TERMS = {
    "business analysis",
    "requirements gathering",
    "stakeholder",
    "documentation",
    "gap analysis",
    "process improvement",
    "uat",
}

PROJECT_TERMS = {
    "power bi",
    "dashboard",
    "manufacturing",
    "supply chain",
    "attendance",
    "loan risk",
    "python",
    "sql",
    "reporting",
    "kpi",
}

SENIOR_TITLE_TERMS = {
    "senior",
    "lead",
    "manager",
    "principal",
    "architect",
    "director",
    "head",
}

EXPERIENCE_PATTERNS = [
    r"(\d+)\s*(?:\+|plus)?\s*(?:-|to)?\s*(\d+)?\s*years?",
    r"minimum\s+of\s+(\d+)\s+years?",
]


def load_profile(
    profile_path: str | Path = PROFILE_PATH,
) -> dict[str, Any]:
    path = Path(profile_path)

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _clean(value: object) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _lower(value: object) -> str:
    return _clean(value).lower()


def _split_skills(value: object) -> list[str]:
    text = _clean(value)

    if not text:
        return []

    return [
        item.strip()
        for item in text.split(",")
        if item.strip()
    ]


def _extract_required_experience(text: str) -> int | None:
    text_lower = text.lower()

    for pattern in EXPERIENCE_PATTERNS:
        match = re.search(pattern, text_lower)

        if match:
            try:
                return int(match.group(1))
            except (ValueError, TypeError):
                continue

    return None


def _recommended_resume(title: str) -> str:
    title_lower = title.lower()

    if any(
        term in title_lower
        for term in [
            "application support",
            "production support",
            "support analyst",
            "technical support",
            "l1 support",
            "l2 support",
        ]
    ):
        return "Support Engineer Resume"

    if any(
        term in title_lower
        for term in [
            "business analyst",
            "process analyst",
            "functional analyst",
        ]
    ):
        return "Business Analyst Resume"

    return "Data Analyst Resume"


def _priority_from_score(score: int) -> tuple[str, str, int]:
    if score >= 90:
        return "APPLY TODAY", "Very High", 5

    if score >= 80:
        return "HIGH PRIORITY", "High", 4

    if score >= 70:
        return "GOOD OPPORTUNITY", "Medium", 3

    if score >= 55:
        return "APPLY IF INTERESTED", "Low", 2

    return "LOW PRIORITY", "Very Low", 1


def _interview_probability(
    final_score: int,
    required_experience: int | None,
    candidate_experience: float,
    missing_count: int,
) -> int:
    probability = round(final_score * 0.82)

    if required_experience is not None:
        if required_experience <= candidate_experience + 1:
            probability += 5
        elif required_experience >= candidate_experience + 3:
            probability -= 18

    probability -= min(missing_count * 2, 12)

    return max(5, min(probability, 90))


def analyze_job_decision(
    job: dict[str, Any],
    profile_path: str | Path = PROFILE_PATH,
) -> dict[str, Any]:
    profile = load_profile(profile_path)

    title = _clean(job.get("title"))
    company = _clean(job.get("company")) or "Unknown Company"
    description = _clean(job.get("description"))
    location = _clean(job.get("location"))
    source = _clean(job.get("site"))
    job_url = _clean(job.get("job_url"))

    combined = f"{title} {description}".lower()

    profile_skills = [
        str(skill).strip()
        for skill in profile.get("skills", [])
        if str(skill).strip()
    ]

    matched_skills = _split_skills(job.get("matched_skills"))

    if not matched_skills:
        matched_skills = [
            skill
            for skill in profile_skills
            if skill.lower() in combined
        ]

    missing_profile_skills = _split_skills(
        job.get("missing_profile_skills")
    )

    recognized_job_skills = sorted(
        {
            skill
            for skill in (
                ANALYTICS_TERMS
                | SUPPORT_TERMS
                | BUSINESS_TERMS
            )
            if skill in combined
        }
    )

    profile_skill_lookup = {
        skill.lower()
        for skill in profile_skills
    }

    genuinely_missing = [
        skill.title()
        for skill in recognized_job_skills
        if skill not in profile_skill_lookup
    ]

    base_match_score = int(
        float(job.get("match_score") or 0)
    )

    # 1. Skill match: maximum 40 points
    if recognized_job_skills:
        matched_recognized = [
            skill
            for skill in recognized_job_skills
            if skill in profile_skill_lookup
        ]

        skill_score = round(
            len(matched_recognized)
            / len(recognized_job_skills)
            * 40
        )
    else:
        skill_score = round(base_match_score * 0.40)

    # 2. Role/title match: maximum 20 points
    title_lower = title.lower()

    role_score = 0

    preferred_roles = profile.get("preferred_roles", [])

    if any(
        str(role).lower() in title_lower
        for role in preferred_roles
    ):
        role_score = 20

    elif any(
        term in title_lower
        for term in [
            "data analyst",
            "bi analyst",
            "power bi",
            "sql analyst",
            "mis analyst",
            "business analyst",
            "application support",
            "production support",
            "support analyst",
        ]
    ):
        role_score = 18

    elif "analyst" in title_lower:
        role_score = 12

    # 3. Experience match: maximum 15 points
    candidate_experience = float(
        profile.get("experience_years", 1.1)
    )

    required_experience = _extract_required_experience(
        combined
    )

    experience_score = 10

    if required_experience is None:
        experience_score = 10

    elif required_experience <= candidate_experience + 1:
        experience_score = 15

    elif required_experience <= candidate_experience + 2:
        experience_score = 8

    else:
        experience_score = 2

    if any(term in title_lower for term in SENIOR_TITLE_TERMS):
        experience_score = max(0, experience_score - 7)

    # 4. Project relevance: maximum 10 points
    project_matches = [
        term
        for term in PROJECT_TERMS
        if term in combined
    ]

    project_score = min(len(project_matches) * 2, 10)

    # 5. Location match: maximum 10 points
    location_lower = location.lower()

    if any(
        term in location_lower
        for term in [
            "bengaluru",
            "bangalore",
            "remote",
            "karnataka",
        ]
    ):
        location_score = 10
    elif not location:
        location_score = 5
    else:
        location_score = 2

    # 6. Job completeness: maximum 5 points
    completeness_score = 0

    if company and company != "Unknown Company":
        completeness_score += 2

    if description:
        completeness_score += 2

    if job_url:
        completeness_score += 1

    final_score = (
        skill_score
        + role_score
        + experience_score
        + project_score
        + location_score
        + completeness_score
    )

    final_score = max(0, min(final_score, 100))

    recommendation, priority, stars = _priority_from_score(
        final_score
    )

    interview_probability = _interview_probability(
        final_score=final_score,
        required_experience=required_experience,
        candidate_experience=candidate_experience,
        missing_count=len(genuinely_missing),
    )

    reasons: list[str] = []
    risks: list[str] = []

    if skill_score >= 30:
        reasons.append(
            "Strong overlap between the job requirements and your core skills."
        )
    elif skill_score >= 20:
        reasons.append(
            "Moderate technical skill alignment with the role."
        )

    if role_score >= 18:
        reasons.append(
            "The job title closely matches one of your preferred roles."
        )

    if project_score >= 6:
        reasons.append(
            "Your analytics and dashboard projects are relevant to this job."
        )

    if location_score == 10:
        reasons.append(
            "The location matches your Bengaluru or remote preference."
        )

    if experience_score >= 12:
        reasons.append(
            "The required experience level is suitable for your profile."
        )

    if required_experience is not None:
        if required_experience >= candidate_experience + 3:
            risks.append(
                f"The role appears to ask for around "
                f"{required_experience}+ years of experience."
            )

    if any(term in title_lower for term in SENIOR_TITLE_TERMS):
        risks.append(
            "The title may indicate a senior-level position."
        )

    if genuinely_missing:
        risks.append(
            "Some recognized job skills are not currently listed "
            "in your profile."
        )

    if not reasons:
        reasons.append(
            "The role has limited but potentially transferable alignment."
        )

    suggested_action = (
        "Tailor your resume and apply as soon as possible."
        if final_score >= 80
        else
        "Review the missing skills before applying."
        if final_score >= 55
        else
        "Prioritize stronger matches unless this company is important to you."
    )

    return {
        "company": company,
        "title": title or "Unknown Role",
        "location": location,
        "source": source,
        "job_url": job_url,
        "overall_score": final_score,
        "base_match_score": base_match_score,
        "skill_score": skill_score,
        "role_score": role_score,
        "experience_score": experience_score,
        "project_score": project_score,
        "location_score": location_score,
        "completeness_score": completeness_score,
        "recommendation": recommendation,
        "priority": priority,
        "stars": stars,
        "interview_probability": interview_probability,
        "required_experience": required_experience,
        "candidate_experience": candidate_experience,
        "matched_skills": matched_skills,
        "missing_profile_skills": missing_profile_skills,
        "recognized_missing_skills": genuinely_missing,
        "project_matches": sorted(project_matches),
        "recommended_resume": _recommended_resume(title),
        "reasons": reasons,
        "risks": risks,
        "suggested_action": suggested_action,
    }