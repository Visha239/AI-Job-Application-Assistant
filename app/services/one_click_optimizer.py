from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.application_context import update_selected_job
from app.services.application_package import (
    build_application_package,
    export_application_summary,
)
from app.services.application_queue import update_queue_item
from app.services.application_crm import add_application
from app.services.outreach_manager import create_outreach_record
from app.services.resume_intelligence_v2 import (
    generate_tailored_resume,
)


def _clean(value: Any) -> str:
    if value is None:
        return ""

    text = str(value).strip()

    if text.lower() in {
        "",
        "none",
        "nan",
        "null",
    }:
        return ""

    return text


def _safe_filename(value: str) -> str:
    cleaned = "".join(
        character
        if character.isalnum()
        else "_"
        for character in value
    )

    while "__" in cleaned:
        cleaned = cleaned.replace(
            "__",
            "_",
        )

    return cleaned.strip("_") or "application"


def prepare_one_click_application(
    *,
    session_state: Any,
    profile: dict[str, Any],
    selected_job: dict[str, Any],
    resume_type: str,
    source_resume_path: str | Path,
    status: str = "Ready to Apply",
    queue_id: str = "",
    create_crm_record: bool = True,
    create_outreach_draft: bool = True,
) -> dict[str, Any]:
    company = _clean(
        selected_job.get("company")
    )
    role = _clean(
        selected_job.get("job_role")
        or selected_job.get("role")
        or selected_job.get("title")
    )
    location = _clean(
        selected_job.get("location")
    )
    job_link = _clean(
        selected_job.get("job_link")
        or selected_job.get("job_url")
    )
    job_description = _clean(
        selected_job.get("job_description")
        or selected_job.get("description")
    )

    if not company:
        raise ValueError(
            "Selected job company is missing."
        )

    if not role:
        raise ValueError(
            "Selected job role is missing."
        )

    if not job_description:
        raise ValueError(
            "The selected job does not contain a complete job description."
        )

    package = build_application_package(
        profile=profile,
        company=company,
        role=role,
        location=location,
        job_link=job_link,
        job_description=job_description,
        resume_type=resume_type,
        status=status,
    )

    package["summary_path"] = (
        export_application_summary(
            package
        )
    )

    output_dir = Path(
        "exports/docx/one_click"
    )
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    final_resume_path = (
        output_dir
        / (
            _safe_filename(
                f"{company}_{role}_Final_Resume"
            )
            + ".docx"
        )
    )

    resume_result = (
        generate_tailored_resume(
            source_resume_path=(
                source_resume_path
            ),
            output_path=(
                final_resume_path
            ),
            job_description=(
                job_description
            ),
            role=role,
            profile_skills=profile.get(
                "skills",
                [],
            ),
        )
    )

    report = package["report"]

    context = update_selected_job(
        session_state,
        {
            "company": company,
            "job_role": role,
            "location": location,
            "job_link": job_link,
            "job_description": (
                job_description
            ),
            "description_status": (
                "available"
            ),
            "matched_skills": (
                ", ".join(
                    report["matched"]
                )
            ),
            "missing_skills": (
                ", ".join(
                    report["missing"]
                )
            ),
            "resume_version": resume_type,
        },
    )

    queue_updated = False

    if queue_id:
        try:
            update_queue_item(
                queue_id,
                status="Ready to Apply",
                notes=(
                    "One-click package prepared. "
                    f"ATS score: "
                    f"{report['ats_score']}%."
                ),
            )
            queue_updated = True
        except Exception:
            queue_updated = False

    crm_record = None

    if create_crm_record:
        try:
            crm_record = add_application(
                company=company,
                role=role,
                location=location,
                source=_clean(
                    selected_job.get(
                        "source"
                    )
                ),
                job_link=job_link,
                stage="Ready to Apply",
                match_score=int(
                    selected_job.get(
                        "match_score",
                        0,
                    )
                    or 0
                ),
                notes=(
                    "One-click application package prepared. "
                    f"ATS score: "
                    f"{report['ats_score']}%. "
                    f"Resume: {final_resume_path}."
                ),
            )
        except ValueError as exc:
            if (
                "already tracked"
                not in str(exc).lower()
            ):
                raise

    outreach_record = None

    if create_outreach_draft:
        try:
            outreach_record = (
                create_outreach_record(
                    company=company,
                    role=role,
                    job_link=job_link,
                    status="Not Contacted",
                    notes=(
                        "Outreach draft created "
                        "by One-Click Optimizer."
                    ),
                )
            )
        except Exception:
            outreach_record = None

    return {
        "company": company,
        "role": role,
        "job_link": job_link,
        "application_package": package,
        "resume_result": resume_result,
        "final_resume_path": str(
            final_resume_path
        ),
        "summary_path": package[
            "summary_path"
        ],
        "ats_score": report[
            "ats_score"
        ],
        "matched_skills": report[
            "matched"
        ],
        "missing_skills": report[
            "missing"
        ],
        "context": context,
        "queue_updated": queue_updated,
        "crm_record": crm_record,
        "outreach_record": (
            outreach_record
        ),
    }
