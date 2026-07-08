import json
import re

with open("data/profile.json", "r") as file:
    profile = json.load(file)

important_keywords = [
    "SQL", "Python", "Excel", "Power BI", "Tableau", "Data Analysis",
    "Business Analysis", "Requirements Gathering", "Documentation",
    "Dashboard", "Reporting", "KPI", "DAX", "Power Query",
    "ETL", "Data Visualization", "Stakeholder", "UML",
    "Gap Analysis", "Jira", "ServiceNow", "Linux"
]

print("Paste the job description below.")
print("When finished, type END and press Enter:\n")

lines = []
while True:
    line = input()
    if line.strip().upper() == "END":
        break
    lines.append(line)

job_description = "\n".join(lines)

found_keywords = []
missing_keywords = []

for keyword in important_keywords:
    pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
    if re.search(pattern, job_description.lower()):
        found_keywords.append(keyword)
    else:
        missing_keywords.append(keyword)

ats_score = round((len(found_keywords) / len(important_keywords)) * 100, 2)

print("\n===================================")
print("        ATS RESUME TAILOR")
print("===================================")

print(f"\nATS Keyword Score: {ats_score}%")

print("\nKeywords Found in Job Description:")
for keyword in found_keywords:
    print(f"✅ {keyword}")

print("\nKeywords You Can Add If Truthful:")
for keyword in missing_keywords[:8]:
    print(f"➕ {keyword}")

print("\nSuggested Resume Summary:")
print(
    f"Data-focused professional with {profile['experience_years']} years of experience "
    f"in SQL, Python, Excel, Power BI, Tableau, reporting, dashboards, and business analysis. "
    f"Experienced in analyzing data, creating actionable insights, and supporting business decision-making "
    f"through data visualization and structured reporting."
)

print("\nSuggested Project Bullet Points:")
print("• Built interactive Power BI dashboards to track KPIs, trends, and operational performance.")
print("• Used SQL and Excel to clean, analyze, and summarize business data for reporting.")
print("• Created visual reports to support business teams in decision-making.")
print("• Applied data analysis techniques to identify patterns, gaps, and improvement opportunities.")