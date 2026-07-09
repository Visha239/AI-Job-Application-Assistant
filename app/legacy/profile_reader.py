import json

# Open the profile file
with open("data/profile.json", "r") as file:
    profile = json.load(file)

print("===================================")
print("     AI JOB APPLICATION ASSISTANT")
print("===================================\n")

print(f"Name: {profile['name']}")
print(f"Email: {profile['email']}")
print(f"Experience: {profile['experience_years']} years")

print("\nPreferred Roles:")
for role in profile["preferred_roles"]:
    print(f"• {role}")

print("\nSkills:")
for skill in profile["skills"]:
    print(f"• {skill}")