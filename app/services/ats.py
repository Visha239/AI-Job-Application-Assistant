import re

IMPORTANT_KEYWORDS = [
    "SQL", "Python", "Excel", "Power BI", "Tableau", "Data Analysis",
    "Business Analysis", "Requirements Gathering", "Documentation",
    "Dashboard", "Reporting", "KPI", "DAX", "Power Query",
    "ETL", "Data Visualization", "Stakeholder", "UML",
    "Gap Analysis", "Jira", "ServiceNow", "Linux"
]

def analyze_ats(job_description):
    found = []
    missing = []

    for keyword in IMPORTANT_KEYWORDS:
        pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
        if re.search(pattern, job_description.lower()):
            found.append(keyword)
        else:
            missing.append(keyword)

    score = round((len(found) / len(IMPORTANT_KEYWORDS)) * 100, 2)

    return {
        "score": score,
        "found_keywords": found,
        "missing_keywords": missing
    }