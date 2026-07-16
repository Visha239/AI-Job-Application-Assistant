from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any


RESPONSE_STAGES = {
    "Recruiter Contacted",
    "HR Round",
    "Technical Round",
    "Manager Round",
    "Offer",
    "Joined",
}

INTERVIEW_STAGES = {
    "HR Round",
    "Technical Round",
    "Manager Round",
    "Offer",
    "Joined",
}

CLOSED_STAGES = {
    "Rejected",
    "Joined",
}


def _clean(value: Any) -> str:
    if value is None:
        return ""

    text = str(value).strip()

    if text.lower() in {
        "",
        "none",
        "nan",
        "null",
        "nat",
    }:
        return ""

    return text


def _as_score(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _parse_date(value: Any) -> date | None:
    text = _clean(value)

    if not text:
        return None

    try:
        return datetime.fromisoformat(
            text.replace("Z", "+00:00")
        ).date()
    except ValueError:
        try:
            return date.fromisoformat(
                text[:10]
            )
        except ValueError:
            return None


def _split_skills(value: Any) -> list[str]:
    text = _clean(value)

    if not text:
        return []

    return [
        skill.strip()
        for skill in text.split(",")
        if skill.strip()
    ]


def _role_family(role: str) -> str:
    role_text = _clean(role).lower()

    if any(
        term in role_text
        for term in [
            "support",
            "production",
            "application",
            "technical",
        ]
    ):
        return "Support"

    if any(
        term in role_text
        for term in [
            "business analyst",
            "operations analyst",
            "product operations",
        ]
    ):
        return "Business Analysis"

    if any(
        term in role_text
        for term in [
            "power bi",
            "reporting",
            "mis",
            "business intelligence",
        ]
    ):
        return "BI & Reporting"

    if any(
        term in role_text
        for term in [
            "data analyst",
            "analytics",
            "sql analyst",
        ]
    ):
        return "Data Analytics"

    return "Other"


def build_job_explanation(
    selected_job: dict[str, Any],
) -> dict[str, Any]:
    score = _as_score(
        selected_job.get("match_score")
    )
    matched = _split_skills(
        selected_job.get("matched_skills")
    )
    missing = _split_skills(
        selected_job.get("missing_skills")
        or selected_job.get(
            "missing_job_skills"
        )
    )

    priority = (
        _clean(
            selected_job.get("priority")
        )
        or "Review"
    )
    urgency = (
        _clean(
            selected_job.get("apply_urgency")
        )
        or "Review normally"
    )

    if score >= 85:
        fit_label = "Strong fit"
        recommendation = (
            "Apply as soon as possible after reviewing the resume."
        )
    elif score >= 70:
        fit_label = "Good fit"
        recommendation = (
            "Apply after tailoring the resume to the strongest matched skills."
        )
    elif score >= 55:
        fit_label = "Possible fit"
        recommendation = (
            "Apply only if the experience requirement is suitable."
        )
    else:
        fit_label = "Low fit"
        recommendation = (
            "Prioritize stronger matches unless this role is especially important."
        )

    evidence = []

    if matched:
        evidence.append(
            "Matched skills: "
            + ", ".join(matched[:6])
        )

    if priority:
        evidence.append(
            f"Search priority: {priority}"
        )

    if urgency:
        evidence.append(
            f"Recommended timing: {urgency}"
        )

    return {
        "score": score,
        "fit_label": fit_label,
        "recommendation": recommendation,
        "matched_skills": matched,
        "missing_skills": missing,
        "evidence": evidence,
        "role_family": _role_family(
            _clean(
                selected_job.get("job_role")
                or selected_job.get("role")
            )
        ),
    }


def build_skill_gap_plan(
    *,
    selected_job: dict[str, Any],
    saved_jobs: list[dict[str, Any]],
    queue: list[dict[str, Any]],
    limit: int = 8,
) -> list[dict[str, Any]]:
    missing_counter: Counter[str] = Counter()
    matched_counter: Counter[str] = Counter()

    for item in [
        selected_job,
        *saved_jobs,
        *queue,
    ]:
        for skill in _split_skills(
            item.get("missing_skills")
            or item.get(
                "missing_job_skills"
            )
        ):
            missing_counter[skill] += 1

        for skill in _split_skills(
            item.get("matched_skills")
        ):
            matched_counter[skill] += 1

    plan: list[dict[str, Any]] = []

    for skill, frequency in missing_counter.most_common(
        limit
    ):
        if frequency >= 4:
            priority = "High"
            action = (
                "Build a small hands-on project and prepare an interview explanation."
            )
        elif frequency >= 2:
            priority = "Medium"
            action = (
                "Learn the fundamentals and complete one practical exercise."
            )
        else:
            priority = "Low"
            action = (
                "Review only when applying to a role that requires it."
            )

        plan.append(
            {
                "skill": skill,
                "missing_frequency": frequency,
                "matched_frequency": matched_counter.get(
                    skill,
                    0,
                ),
                "priority": priority,
                "recommended_action": action,
            }
        )

    return plan


def application_strategy(
    *,
    crm_records: list[dict[str, Any]],
    queue: list[dict[str, Any]],
    saved_jobs: list[dict[str, Any]],
    today: date | None = None,
) -> dict[str, Any]:
    current = today or date.today()

    applications = [
        record
        for record in crm_records
        if _clean(record.get("stage"))
        not in {
            "",
            "Saved",
            "Ready to Apply",
        }
    ]

    responses = [
        record
        for record in applications
        if _clean(record.get("stage"))
        in RESPONSE_STAGES
    ]

    interviews = [
        record
        for record in applications
        if _clean(record.get("stage"))
        in INTERVIEW_STAGES
    ]

    response_rate = (
        round(
            len(responses)
            / len(applications)
            * 100,
            1,
        )
        if applications
        else 0.0
    )

    high_score_queue = [
        item
        for item in queue
        if _as_score(
            item.get("match_score")
        )
        >= 80
        and _clean(
            item.get("status")
        )
        in {
            "Queued",
            "Ready to Apply",
        }
    ]

    older_saved = 0

    for item in saved_jobs:
        added = _parse_date(
            item.get("created_date")
            or item.get("saved_date")
            or item.get("added_at")
        )

        if (
            added is not None
            and (
                current - added
            ).days >= 7
        ):
            older_saved += 1

    source_groups: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(list)

    for record in applications:
        source_groups[
            _clean(
                record.get("source")
            )
            or "Unknown"
        ].append(record)

    source_results = []

    for source, records in source_groups.items():
        source_responses = sum(
            1
            for record in records
            if _clean(
                record.get("stage")
            )
            in RESPONSE_STAGES
        )

        source_results.append(
            {
                "source": source,
                "applications": len(
                    records
                ),
                "responses": source_responses,
                "response_rate": (
                    round(
                        source_responses
                        / len(records)
                        * 100,
                        1,
                    )
                    if records
                    else 0.0
                ),
            }
        )

    source_results.sort(
        key=lambda item: (
            item["response_rate"],
            item["applications"],
        ),
        reverse=True,
    )

    recommendations: list[str] = []

    if high_score_queue:
        recommendations.append(
            f"Prioritize the {len(high_score_queue)} queued job(s) "
            "with an 80% or higher match score."
        )

    if len(applications) >= 10:
        if response_rate < 5:
            recommendations.append(
                "Your response rate is below 5%. "
                "Reduce low-match applications and tailor each resume more deeply."
            )
        elif response_rate >= 15:
            recommendations.append(
                "Your response rate is healthy. "
                "Continue applying to similar roles and sources."
            )
        else:
            recommendations.append(
                "Your response rate is moderate. "
                "Focus on fresh jobs and stronger recruiter outreach."
            )
    elif applications:
        recommendations.append(
            "There is not enough application history for a strong conclusion yet. "
            "Keep tracking every result."
        )
    else:
        recommendations.append(
            "Start by applying to the highest-match jobs in the queue."
        )

    if older_saved:
        recommendations.append(
            f"Review or remove {older_saved} saved job(s) older than seven days."
        )

    if source_results:
        best = source_results[0]

        if best["applications"]:
            recommendations.append(
                f"{best['source']} is currently your strongest source "
                f"with a {best['response_rate']}% response rate."
            )

    return {
        "applications": len(
            applications
        ),
        "responses": len(
            responses
        ),
        "interviews": len(
            interviews
        ),
        "response_rate": response_rate,
        "high_score_queue": len(
            high_score_queue
        ),
        "older_saved_jobs": older_saved,
        "source_performance": source_results,
        "recommendations": recommendations[:5],
    }


def daily_action_plan(
    *,
    crm_records: list[dict[str, Any]],
    queue: list[dict[str, Any]],
    outreach_records: list[dict[str, Any]],
    today: date | None = None,
) -> list[dict[str, Any]]:
    current = today or date.today()
    actions: list[dict[str, Any]] = []

    due_followups = 0

    for record in crm_records:
        follow_up = _parse_date(
            record.get(
                "next_follow_up_date"
            )
        )

        if (
            follow_up is not None
            and follow_up <= current
            and _clean(
                record.get("stage")
            )
            not in CLOSED_STAGES
        ):
            due_followups += 1

    for record in outreach_records:
        follow_up = _parse_date(
            record.get("follow_up_date")
        )

        if (
            follow_up is not None
            and follow_up <= current
            and _clean(
                record.get("status")
            )
            not in {
                "Replied",
                "Interview Scheduled",
                "Closed",
                "Rejected",
            }
        ):
            due_followups += 1

    if due_followups:
        actions.append(
            {
                "priority": 1,
                "action": (
                    f"Complete {due_followups} due follow-up(s)."
                ),
                "reason": (
                    "Existing applications should be followed up before adding more."
                ),
            }
        )

    strong_queue = sorted(
        [
            item
            for item in queue
            if _clean(
                item.get("status")
            )
            in {
                "Queued",
                "Ready to Apply",
            }
            and _as_score(
                item.get("match_score")
            )
            >= 75
        ],
        key=lambda item: _as_score(
            item.get("match_score")
        ),
        reverse=True,
    )

    if strong_queue:
        actions.append(
            {
                "priority": 2,
                "action": (
                    f"Apply to the top {min(3, len(strong_queue))} "
                    "high-match job(s) in your queue."
                ),
                "reason": (
                    "Strong matches usually deserve attention before broad searching."
                ),
            }
        )

    if not strong_queue:
        actions.append(
            {
                "priority": 2,
                "action": (
                    "Run Smart Job Discovery and add fresh matches to the queue."
                ),
                "reason": (
                    "There are no strong active applications waiting."
                ),
            }
        )

    actions.append(
        {
            "priority": 3,
            "action": (
                "Update CRM stages for any recruiter replies or interview progress."
            ),
            "reason": (
                "Accurate tracking improves the quality of CareerPilot insights."
            ),
        }
    )

    return actions


def build_coach_snapshot(
    *,
    selected_job: dict[str, Any],
    crm_records: list[dict[str, Any]],
    queue: list[dict[str, Any]],
    outreach_records: list[dict[str, Any]],
    saved_jobs: list[dict[str, Any]],
    today: date | None = None,
) -> dict[str, Any]:
    return {
        "job_explanation": build_job_explanation(
            selected_job
        ),
        "strategy": application_strategy(
            crm_records=crm_records,
            queue=queue,
            saved_jobs=saved_jobs,
            today=today,
        ),
        "skill_gap_plan": build_skill_gap_plan(
            selected_job=selected_job,
            saved_jobs=saved_jobs,
            queue=queue,
        ),
        "daily_actions": daily_action_plan(
            crm_records=crm_records,
            queue=queue,
            outreach_records=outreach_records,
            today=today,
        ),
    }
