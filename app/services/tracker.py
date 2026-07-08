import csv
from datetime import date
from pathlib import Path

TRACKER_FILE = Path("tracker/applications.csv")

def initialize_tracker():
    TRACKER_FILE.parent.mkdir(exist_ok=True)

    if not TRACKER_FILE.exists():
        with open(TRACKER_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Company", "Role", "Location", "Job Link", "Status", "Notes"])

def save_application(company, role, location, job_link, status, notes):
    initialize_tracker()

    with open(TRACKER_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([date.today(), company, role, location, job_link, status, notes])

def count_applications():
    initialize_tracker()

    with open(TRACKER_FILE, "r") as file:
        rows = list(csv.reader(file))

    return max(len(rows) - 1, 0)