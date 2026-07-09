import json

with open("data/profile.json", "r") as file:
    profile = json.load(file)

print("Paste the job description below.")
print("When finished, type END and press Enter:\n")

lines = []
while True:
    line = input()
    if line.strip().upper() == "END":
        break
    lines.append(line)

job_description = "\n".join(lines)

skills = profile["skills"]

matched_skills = []
missing_skills = []

for skill in skills:
    if skill.lower() in job_description.lower():
        matched_skills.append(skill)
    else:
        missing_skills.append(skill)

match_score = round((len(matched_skills) / len(skills)) * 100, 2)

print("\n===================================")
print("        JOB MATCH REPORT")
print("===================================")
print(f"\nMatch Score: {match_score}%")

print("\nMatched Skills:")
for skill in matched_skills:
    print(f"✅ {skill}")

print("\nProfile Skills Not Found in Job:")
for skill in missing_skills:
    print(f"❌ {skill}")