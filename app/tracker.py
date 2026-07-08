import csv
from datetime import date
from pathlib import Path

tracker_file = Path("tracker/applications.csv")
tracker_file.parent.mkdir(exist_ok=True)

if not tracker_file.exists():
    with open(tracker_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Date",
            "Company",
            "Role",
            "Location",
            "Job Link",
            "Status",
            "Notes"
        ])

company = input("Company name: ")
role = input("Job role: ")
location = input("Location: ")
job_link = input("Job link: ")
status = input("Status (Applied/Not Applied/Interview/Rejected): ")
notes = input("Notes: ")

with open(tracker_file, "a", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([
        date.today(),
        company,
        role,
        location,
        job_link,
        status,
        notes
    ])

print("\n✅ Application saved successfully!")
print(f"Saved in: {tracker_file}")