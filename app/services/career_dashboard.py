from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta
from typing import Any


PIPELINE_ORDER = [
    "Saved",
    "Ready to Apply",
    "Applied",
    "Recruiter Contacted",
    "HR Round",
    "Technical Round",
    "Manager Round",
    "Offer",
    "Rejected",
    "Joined",
]

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


def _clean(value: Any) -> str:
    if value is None:
        return ""

    text = str(value).strip()

    if text.lower() in {"", "none", "nan", "null", "nat"}:
        return ""

    return text


def _as_int(value: Any) -> int:
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
            return date.fromisoformat(text[:10])
        except ValueError:
            return None


def _skill_counter(
    saved_jobs: list[dict[str, Any]],
    queue: list[dict[str, Any]],
    limit: int = 10,
) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()

    for item in [*saved_jobs, *queue]:
        raw = _clean(
            item.get("matched_skills")
            or item.get("required_skills")
        )

        for skill in raw.split(","):
            cleaned = skill.strip()

            if cleaned:
                counter[cleaned] += 1

    return [
        {
            "skill": skill,
            "count": count,
        }
        for skill, count in counter.most_common(limit)
    ]


def _weekly_trend(
    crm_records: list[dict[str, Any]],
    weeks: int = 6,
    today: date | None = None,
) -> list[dict[str, Any]]:
    current = today or date.today()
    current_week_start = current - timedelta(
        days=current.weekday()
    )

    week_starts = [
        current_week_start - timedelta(
            weeks=offset
        )
        for offset in reversed(
            range(weeks)
        )
    ]

    counts = {
        week_start: 0
        for week_start in week_starts
    }

    for record in crm_records:
        applied = _parse_date(
            record.get("applied_date")
        )

        if applied is None:
            continue

        applied_week = applied - timedelta(
            days=applied.weekday()
        )

        if applied_week in counts:
            counts[applied_week] += 1

    return [
        {
            "week": week_start.strftime(
                "%d %b"
            ),
            "applications": counts[
                week_start
            ],
        }
        for week_start in week_starts
    ]


def _pipeline_distribution(
    crm_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    counts = Counter(
        _clean(record.get("stage"))
        for record in crm_records
    )

    return [
        {
            "stage": stage,
            "count": counts.get(
                stage,
                0,
            ),
        }
        for stage in PIPELINE_ORDER
    ]


def _source_performance(
    crm_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_groups: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for record in crm_records:
        source = (
            _clean(record.get("source"))
            or "Unknown"
        )
        source_groups.setdefault(
            source,
            [],
        ).append(record)

    rows: list[dict[str, Any]] = []

    for source, records in source_groups.items():
        applications = sum(
            1
            for record in records
            if _clean(record.get("stage"))
            not in {
                "Saved",
                "Ready to Apply",
                "",
            }
        )

        responses = sum(
            1
            for record in records
            if _clean(record.get("stage"))
            in RESPONSE_STAGES
        )

        rate = (
            round(
                responses
                / applications
                * 100,
                1,
            )
            if applications
            else 0.0
        )

        rows.append(
            {
                "source": source,
                "applications": applications,
                "responses": responses,
                "response_rate": rate,
            }
        )

    return sorted(
        rows,
        key=lambda item: (
            item["response_rate"],
            item["applications"],
        ),
        reverse=True,
    )


def _upcoming_followups(
    crm_records: list[dict[str, Any]],
    outreach_records: list[dict[str, Any]],
    limit: int = 8,
    today: date | None = None,
) -> list[dict[str, Any]]:
    current = today or date.today()
    items: list[dict[str, Any]] = []

    for record in crm_records:
        follow_up = _parse_date(
            record.get(
                "next_follow_up_date"
            )
        )

        if follow_up is None:
            continue

        stage = _clean(
            record.get("stage")
        )

        if stage in {
            "Rejected",
            "Joined",
        }:
            continue

        items.append(
            {
                "date": follow_up.isoformat(),
                "days_until": (
                    follow_up - current
                ).days,
                "company": _clean(
                    record.get("company")
                ),
                "role": _clean(
                    record.get("role")
                ),
                "type": "Application follow-up",
                "status": stage,
            }
        )

    for record in outreach_records:
        follow_up = _parse_date(
            record.get("follow_up_date")
        )

        if follow_up is None:
            continue

        status = _clean(
            record.get("status")
        )

        if status in {
            "Replied",
            "Interview Scheduled",
            "Closed",
            "Rejected",
        }:
            continue

        items.append(
            {
                "date": follow_up.isoformat(),
                "days_until": (
                    follow_up - current
                ).days,
                "company": _clean(
                    record.get("company")
                ),
                "role": _clean(
                    record.get("role")
                ),
                "type": "Recruiter follow-up",
                "status": status,
            }
        )

    return sorted(
        items,
        key=lambda item: (
            item["date"],
            item["company"],
        ),
    )[:limit]


def _recent_activity(
    crm_records: list[dict[str, Any]],
    queue: list[dict[str, Any]],
    outreach_records: list[dict[str, Any]],
    limit: int = 10,
) -> list[dict[str, Any]]:
    activity: list[dict[str, Any]] = []

    for record in crm_records:
        timestamp = (
            _clean(record.get("updated_at"))
            or _clean(record.get("created_at"))
            or _clean(record.get("applied_date"))
        )

        activity.append(
            {
                "timestamp": timestamp,
                "activity": (
                    f"{_clean(record.get('stage')) or 'Updated'}: "
                    f"{_clean(record.get('role')) or 'Role'} at "
                    f"{_clean(record.get('company')) or 'Company'}"
                ),
                "category": "Application",
            }
        )

    for item in queue:
        timestamp = (
            _clean(item.get("updated_at"))
            or _clean(item.get("added_at"))
        )

        activity.append(
            {
                "timestamp": timestamp,
                "activity": (
                    f"Queue {_clean(item.get('status')) or 'updated'}: "
                    f"{_clean(item.get('role')) or 'Role'} at "
                    f"{_clean(item.get('company')) or 'Company'}"
                ),
                "category": "Queue",
            }
        )

    for record in outreach_records:
        timestamp = (
            _clean(record.get("updated_at"))
            or _clean(record.get("created_at"))
        )

        activity.append(
            {
                "timestamp": timestamp,
                "activity": (
                    f"Outreach {_clean(record.get('status')) or 'updated'}: "
                    f"{_clean(record.get('role')) or 'Role'} at "
                    f"{_clean(record.get('company')) or 'Company'}"
                ),
                "category": "Recruiter",
            }
        )

    return sorted(
        activity,
        key=lambda item: item[
            "timestamp"
        ],
        reverse=True,
    )[:limit]


def _insights(
    *,
    metrics: dict[str, Any],
    source_performance: list[dict[str, Any]],
    skills: list[dict[str, Any]],
    followups: list[dict[str, Any]],
    queue_ready: int,
) -> list[str]:
    insights: list[str] = []

    if followups:
        overdue = sum(
            1
            for item in followups
            if item["days_until"] < 0
        )

        if overdue:
            insights.append(
                f"{overdue} follow-up(s) are overdue. "
                "Handle these before adding more applications."
            )
        else:
            insights.append(
                f"{len(followups)} follow-up(s) are scheduled. "
                "Keep recruiter communication consistent."
            )

    if source_performance:
        best = source_performance[0]

        if best["applications"] > 0:
            insights.append(
                f"{best['source']} currently has the best response rate "
                f"at {best['response_rate']}%."
            )

    if skills:
        top_skills = ", ".join(
            item["skill"]
            for item in skills[:3]
        )
        insights.append(
            f"Your most frequently matched skills are {top_skills}. "
            "Prioritize jobs where these are core requirements."
        )

    if queue_ready:
        insights.append(
            f"{queue_ready} application(s) are ready in your queue. "
            "Review and submit the strongest ones first."
        )

    if metrics["applications_sent"] >= 10:
        if metrics["response_rate"] < 5:
            insights.append(
                "Your response rate is below 5%. "
                "Tighten role targeting and tailor the resume more deeply."
            )
        elif metrics["response_rate"] >= 15:
            insights.append(
                "Your response rate is healthy. "
                "Continue focusing on the same roles and sources."
            )

    if not insights:
        insights.append(
            "Start by adding high-match jobs, applying consistently, "
            "and recording every result in the CRM."
        )

    return insights[:5]


def build_dashboard_snapshot(
    *,
    crm_records: list[dict[str, Any]],
    queue: list[dict[str, Any]],
    outreach_records: list[dict[str, Any]],
    saved_jobs: list[dict[str, Any]],
    generated_resumes: int = 0,
    today: date | None = None,
) -> dict[str, Any]:
    current = today or date.today()

    applications_sent = sum(
        1
        for record in crm_records
        if _clean(record.get("stage"))
        not in {
            "",
            "Saved",
            "Ready to Apply",
        }
    )

    responses = sum(
        1
        for record in crm_records
        if _clean(record.get("stage"))
        in RESPONSE_STAGES
    )

    interviews = sum(
        1
        for record in crm_records
        if _clean(record.get("stage"))
        in INTERVIEW_STAGES
    )

    offers = sum(
        1
        for record in crm_records
        if _clean(record.get("stage"))
        in {"Offer", "Joined"}
    )

    applied_today = sum(
        1
        for record in crm_records
        if _parse_date(
            record.get("applied_date")
        )
        == current
    )

    queue_ready = sum(
        1
        for item in queue
        if _clean(item.get("status"))
        in {
            "Queued",
            "Ready to Apply",
        }
    )

    recruiters_contacted = sum(
        1
        for record in outreach_records
        if _clean(record.get("status"))
        not in {
            "",
            "Not Contacted",
        }
    )

    response_rate = (
        round(
            responses
            / applications_sent
            * 100,
            1,
        )
        if applications_sent
        else 0.0
    )

    metrics = {
        "saved_jobs": len(saved_jobs),
        "queue_ready": queue_ready,
        "applications_sent": applications_sent,
        "applied_today": applied_today,
        "interviews": interviews,
        "offers": offers,
        "response_rate": response_rate,
        "recruiters_contacted": recruiters_contacted,
        "generated_resumes": generated_resumes,
    }

    pipeline = _pipeline_distribution(
        crm_records
    )
    sources = _source_performance(
        crm_records
    )
    skills = _skill_counter(
        saved_jobs,
        queue,
    )
    followups = _upcoming_followups(
        crm_records,
        outreach_records,
        today=current,
    )

    return {
        "metrics": metrics,
        "pipeline": pipeline,
        "weekly_trend": _weekly_trend(
            crm_records,
            today=current,
        ),
        "source_performance": sources,
        "skills": skills,
        "followups": followups,
        "recent_activity": _recent_activity(
            crm_records,
            queue,
            outreach_records,
        ),
        "insights": _insights(
            metrics=metrics,
            source_performance=sources,
            skills=skills,
            followups=followups,
            queue_ready=queue_ready,
        ),
    }
