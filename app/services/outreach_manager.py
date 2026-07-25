from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus


DEFAULT_STORE_PATH = Path("data/outreach_records.json")
DEFAULT_EXPORT_PATH = Path("exports/recruiter_outreach/outreach_records.csv")


@dataclass
class OutreachRecord:
    record_id: str
    company: str
    role: str
    recruiter_name: str
    recruiter_email: str
    recruiter_linkedin: str
    job_link: str
    status: str
    initial_contact_date: str
    follow_up_date: str
    last_contact_date: str
    notes: str
    created_at: str
    updated_at: str


def _clean(value: Any) -> str:
    if value is None:
        return ""

    text = str(value).strip()

    if text.lower() in {"", "none", "nan", "null"}:
        return ""

    return text


def _safe_id(company: str, role: str, recruiter_email: str) -> str:
    raw = "_".join(
        part for part in [company, role, recruiter_email] if part
    )
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_").lower()

    if not cleaned:
        cleaned = "outreach"

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")

    return f"{cleaned}_{timestamp}"


def load_records(
    store_path: str | Path = DEFAULT_STORE_PATH,
) -> list[dict[str, Any]]:
    path = Path(store_path)

    if not path.exists():
        return []

    try:
        content = path.read_text(encoding="utf-8-sig").strip()

        if not content:
            return []

        data = json.loads(content)

    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(data, list):
        return []

    return [
        item
        for item in data
        if isinstance(item, dict)
    ]


def save_records(
    records: list[dict[str, Any]],
    store_path: str | Path = DEFAULT_STORE_PATH,
) -> None:
    path = Path(store_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def create_outreach_record(
    *,
    company: str,
    role: str,
    recruiter_name: str = "",
    recruiter_email: str = "",
    recruiter_linkedin: str = "",
    job_link: str = "",
    status: str = "Not Contacted",
    initial_contact_date: str = "",
    follow_up_date: str = "",
    last_contact_date: str = "",
    notes: str = "",
    store_path: str | Path = DEFAULT_STORE_PATH,
) -> dict[str, Any]:
    company = _clean(company)
    role = _clean(role)

    if not company:
        raise ValueError("Company is required.")

    if not role:
        raise ValueError("Role is required.")

    today = date.today()

    if not initial_contact_date and status != "Not Contacted":
        initial_contact_date = today.isoformat()

    if not follow_up_date and status in {
        "Contacted",
        "Follow-up Due",
    }:
        follow_up_date = (
            today + timedelta(days=3)
        ).isoformat()

    now = datetime.now().isoformat(timespec="seconds")

    record = OutreachRecord(
        record_id=_safe_id(
            company,
            role,
            _clean(recruiter_email),
        ),
        company=company,
        role=role,
        recruiter_name=_clean(recruiter_name),
        recruiter_email=_clean(recruiter_email),
        recruiter_linkedin=_clean(recruiter_linkedin),
        job_link=_clean(job_link),
        status=_clean(status) or "Not Contacted",
        initial_contact_date=_clean(initial_contact_date),
        follow_up_date=_clean(follow_up_date),
        last_contact_date=_clean(last_contact_date),
        notes=_clean(notes),
        created_at=now,
        updated_at=now,
    )

    records = load_records(store_path)
    records.append(asdict(record))
    save_records(records, store_path)

    return asdict(record)


def update_outreach_record(
    record_id: str,
    *,
    store_path: str | Path = DEFAULT_STORE_PATH,
    **updates: Any,
) -> dict[str, Any]:
    records = load_records(store_path)

    for record in records:
        if record.get("record_id") != record_id:
            continue

        allowed_fields = {
            "company",
            "role",
            "recruiter_name",
            "recruiter_email",
            "recruiter_linkedin",
            "job_link",
            "status",
            "initial_contact_date",
            "follow_up_date",
            "last_contact_date",
            "notes",
        }

        for key, value in updates.items():
            if key in allowed_fields:
                record[key] = _clean(value)

        record["updated_at"] = datetime.now().isoformat(
            timespec="seconds"
        )

        save_records(records, store_path)
        return record

    raise ValueError("Outreach record was not found.")


def delete_outreach_record(
    record_id: str,
    store_path: str | Path = DEFAULT_STORE_PATH,
) -> bool:
    records = load_records(store_path)
    updated = [
        record
        for record in records
        if record.get("record_id") != record_id
    ]

    if len(updated) == len(records):
        return False

    save_records(updated, store_path)
    return True


def get_due_follow_ups(
    records: list[dict[str, Any]] | None = None,
    *,
    on_date: date | None = None,
    store_path: str | Path = DEFAULT_STORE_PATH,
) -> list[dict[str, Any]]:
    active_records = (
        records
        if records is not None
        else load_records(store_path)
    )

    target_date = on_date or date.today()
    due: list[dict[str, Any]] = []

    completed_statuses = {
        "Replied",
        "Interview Scheduled",
        "Closed",
        "Rejected",
    }

    for record in active_records:
        if record.get("status") in completed_statuses:
            continue

        follow_up_text = _clean(record.get("follow_up_date"))

        if not follow_up_text:
            continue

        try:
            follow_up = date.fromisoformat(follow_up_text)
        except ValueError:
            continue

        if follow_up <= target_date:
            due.append(record)

    return sorted(
        due,
        key=lambda item: item.get("follow_up_date", ""),
    )


def build_recruiter_email(
    *,
    candidate_name: str,
    candidate_email: str,
    company: str,
    role: str,
    matched_skills: list[str],
    recruiter_name: str = "",
    job_link: str = "",
) -> str:
    greeting = (
        f"Dear {recruiter_name},"
        if _clean(recruiter_name)
        else "Dear Hiring Team,"
    )

    skills = ", ".join(matched_skills[:5])

    if not skills:
        skills = "SQL, Power BI, Python, Excel, and data analysis"

    link_line = (
        f"\nJob posting: {job_link}\n"
        if _clean(job_link)
        else ""
    )

    return f"""Subject: Application for {role} - {candidate_name}

{greeting}

I am writing to express my interest in the {role} opportunity at {company}. I have 1.1 years of enterprise support experience and practical analytics experience involving {skills}.

My background includes SQL reporting, production troubleshooting, stakeholder support, and hands-on Power BI and Python projects. I believe this combination of technical support discipline and analytical problem-solving would allow me to contribute effectively to the role.
{link_line}
I would appreciate the opportunity to discuss how my experience aligns with your teamâ€™s requirements. My resume is available for review.

Best regards,
{candidate_name}
{candidate_email}
"""


def build_linkedin_message(
    *,
    candidate_name: str,
    company: str,
    role: str,
    matched_skills: list[str],
) -> str:
    skills = ", ".join(matched_skills[:3])

    if not skills:
        skills = "SQL, Power BI, and Python"

    message = (
        f"Hi, Iâ€™m {candidate_name}. Iâ€™m interested in the {role} "
        f"opportunity at {company}. My background includes {skills} "
        "and 1.1 years of enterprise support experience. "
        "Iâ€™d appreciate connecting and learning more about the role."
    )

    return message[:300]


def build_follow_up_email(
    *,
    candidate_name: str,
    candidate_email: str,
    company: str,
    role: str,
    recruiter_name: str = "",
) -> str:
    greeting = (
        f"Dear {recruiter_name},"
        if _clean(recruiter_name)
        else "Dear Hiring Team,"
    )

    return f"""Subject: Follow-up on {role} application

{greeting}

I am following up on my application for the {role} position at {company}. I remain very interested in the opportunity and believe my experience in SQL, Power BI, Python, Excel, reporting, and enterprise support aligns well with the role.

Please let me know if any additional information would be helpful. I would be grateful for an opportunity to discuss the position.

Best regards,
{candidate_name}
{candidate_email}
"""


def build_thank_you_email(
    *,
    candidate_name: str,
    candidate_email: str,
    company: str,
    role: str,
    interviewer_name: str = "",
) -> str:
    greeting = (
        f"Dear {interviewer_name},"
        if _clean(interviewer_name)
        else "Dear Interviewer,"
    )

    return f"""Subject: Thank you - {role} interview

{greeting}

Thank you for taking the time to discuss the {role} opportunity at {company}. I appreciated learning more about the team, the roleâ€™s priorities, and the problems you are working to solve.

The conversation strengthened my interest in the position. I believe my experience in analytics, SQL reporting, production support, and structured problem-solving would help me contribute effectively.

Thank you again for your time and consideration.

Best regards,
{candidate_name}
{candidate_email}
"""


def build_research_links(
    company: str,
) -> dict[str, str]:
    encoded = quote_plus(company)

    return {
        "LinkedIn recruiters": (
            "https://www.google.com/search?q="
            f"site%3Alinkedin.com%2Fin+{encoded}+recruiter"
        ),
        "Talent acquisition": (
            "https://www.google.com/search?q="
            f"site%3Alinkedin.com%2Fin+{encoded}+talent+acquisition"
        ),
        "Hiring managers": (
            "https://www.google.com/search?q="
            f"site%3Alinkedin.com%2Fin+{encoded}+data+analytics+manager"
        ),
        "Company careers": (
            "https://www.google.com/search?q="
            f"{encoded}+official+careers"
        ),
    }


def export_records_csv(
    *,
    records: list[dict[str, Any]] | None = None,
    output_path: str | Path = DEFAULT_EXPORT_PATH,
    store_path: str | Path = DEFAULT_STORE_PATH,
) -> str:
    active_records = (
        records
        if records is not None
        else load_records(store_path)
    )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "record_id",
        "company",
        "role",
        "recruiter_name",
        "recruiter_email",
        "recruiter_linkedin",
        "job_link",
        "status",
        "initial_contact_date",
        "follow_up_date",
        "last_contact_date",
        "notes",
        "created_at",
        "updated_at",
    ]

    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )
        writer.writeheader()

        for record in active_records:
            writer.writerow(
                {
                    field: record.get(field, "")
                    for field in fieldnames
                }
            )

    return str(path)

