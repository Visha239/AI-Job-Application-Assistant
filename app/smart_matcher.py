import json

with open("data/profile.json", "r") as file:
    profile = json.load(file)

role_skill_map = {
    "data_analyst": [
        "SQL",
        "Python",
        "Excel",
        "Power BI",
        "Tableau",
        "Data Analysis"
    ],
    "business_analyst": [
        "SQL",
        "Excel",
        "Business Analysis",
        "Requirements Gathering",
        "Documentation",
        "Gap Analysis",
        "Stakeholder Communication",
        "UML"
    ],
    "support_engineer": [
        "Linux",
        "ServiceNow",
        "Jira",
        "SQL"
    ]
}

print("Select job type:")
print("1. Data Analyst / Power BI")
print("2. Business Analyst")
print("3. Application Support / Production Support")

choice = input("Enter 1, 2, or 3: ")

if choice == "1":
    selected_role = "data_analyst"
elif choice == "2":
    selected_role = "business_analyst"
elif choice == "3":
    selected_role = "support_engineer"
else:
    print("Invalid choice. Defaulting to Data Analyst.")
    selected_role = "data_analyst"

required_skills = role_skill_map[selected_role]

print("\nPaste the job description below.")
print("When finished, type END and press Enter:\n")

lines = []
while True:
    line = input()
    if line.strip().upper() == "END":
        break
    lines.append(line)

job_description = "\n".join(lines)

matched_skills = []
missing_skills = []

for skill in required_skills:
    if skill.lower() in job_description.lower():
        matched_skills.append(skill)
    else:
        missing_skills.append(skill)

match_score = round((len(matched_skills) / len(required_skills)) * 100, 2)

print("\n===================================")
print("        SMART JOB MATCH REPORT")
print("===================================")

print(f"\nSelected Role Type: {selected_role}")
print(f"Match Score: {match_score}%")

print("\nMatched Skills:")
for skill in matched_skills:
    print(f"✅ {skill}")

print("\nImportant Missing Skills:")
for skill in missing_skills:
    print(f"❌ {skill}")

if match_score >= 75:
    print("\nRecommendation: Strong match. Apply.")
elif match_score >= 50:
    print("\nRecommendation: Medium match. Apply if job looks good.")
else:
    print("\nRecommendation: Low match. Apply only if you really want this company.")