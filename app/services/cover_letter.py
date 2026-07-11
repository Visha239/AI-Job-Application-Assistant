from __future__ import annotations


def generate_cover_note(
    profile: dict,
    company: str,
    role: str,
    matched_skills: list[str] | None = None,
) -> str:
    """Generate a concise, truthful application cover note."""

    matched_skills = matched_skills or []
    skills_text = ", ".join(matched_skills[:6])

    if not skills_text:
        skills_text = "SQL, Python, Power BI, Excel and data analysis"

    return f"""Dear Hiring Team,

I am writing to express my interest in the {role} position at {company}.

I have 1.1 years of experience as an Enterprise Support Engineer, where I worked with SQL, Linux, AWS, ServiceNow, Jira, production systems and operational reporting. I have also developed practical analytics experience through Power BI, Python and Excel projects focused on dashboards, KPI reporting, manufacturing analysis and business insights.

My relevant skills for this opportunity include {skills_text}. I believe my combination of technical support experience and data analytics skills would allow me to contribute effectively to your team.

Thank you for considering my application. I would welcome the opportunity to discuss my experience and suitability for the role.

Best regards,
{profile["name"]}
{profile["email"]}
"""