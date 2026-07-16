from __future__ import annotations

from datetime import date, timedelta

from app.services.career_dashboard import (
    build_dashboard_snapshot,
)


def main() -> None:
    today = date(
        2026,
        7,
        14,
    )

    crm_records = [
        {
            "company": "Alpha",
            "role": "Data Analyst",
            "stage": "Applied",
            "source": "linkedin",
            "applied_date": (
                today.isoformat()
            ),
            "next_follow_up_date": (
                today
                + timedelta(days=2)
            ).isoformat(),
            "updated_at": (
                "2026-07-14T10:00:00"
            ),
        },
        {
            "company": "Beta",
            "role": "Power BI Analyst",
            "stage": "HR Round",
            "source": "linkedin",
            "applied_date": (
                today
                - timedelta(days=5)
            ).isoformat(),
            "next_follow_up_date": "",
            "updated_at": (
                "2026-07-13T10:00:00"
            ),
        },
        {
            "company": "Gamma",
            "role": "Business Analyst",
            "stage": "Rejected",
            "source": "indeed",
            "applied_date": (
                today
                - timedelta(days=9)
            ).isoformat(),
            "next_follow_up_date": "",
            "updated_at": (
                "2026-07-12T10:00:00"
            ),
        },
    ]

    queue = [
        {
            "company": "Delta",
            "role": "SQL Analyst",
            "status": "Ready to Apply",
            "match_score": 91,
            "matched_skills": (
                "SQL, Excel, Power BI"
            ),
            "updated_at": (
                "2026-07-14T11:00:00"
            ),
        }
    ]

    outreach = [
        {
            "company": "Alpha",
            "role": "Data Analyst",
            "status": "Contacted",
            "follow_up_date": (
                today
                - timedelta(days=1)
            ).isoformat(),
            "updated_at": (
                "2026-07-14T09:00:00"
            ),
        }
    ]

    saved_jobs = [
        {
            "company": "Saved Company",
            "role": "Data Analyst",
            "required_skills": (
                "SQL, Power BI, Excel"
            ),
        }
    ]

    snapshot = build_dashboard_snapshot(
        crm_records=crm_records,
        queue=queue,
        outreach_records=outreach,
        saved_jobs=saved_jobs,
        generated_resumes=4,
        today=today,
    )

    metrics = snapshot["metrics"]

    assert metrics[
        "saved_jobs"
    ] == 1
    assert metrics[
        "queue_ready"
    ] == 1
    assert metrics[
        "applications_sent"
    ] == 3
    assert metrics[
        "applied_today"
    ] == 1
    assert metrics[
        "interviews"
    ] == 1
    assert metrics[
        "offers"
    ] == 0
    assert metrics[
        "response_rate"
    ] == 33.3
    assert metrics[
        "recruiters_contacted"
    ] == 1
    assert metrics[
        "generated_resumes"
    ] == 4

    assert len(
        snapshot["pipeline"]
    ) == 10
    assert len(
        snapshot["weekly_trend"]
    ) == 6
    assert len(
        snapshot["followups"]
    ) == 2
    assert snapshot[
        "followups"
    ][0]["days_until"] == -1
    assert snapshot[
        "source_performance"
    ][0]["source"] == (
        "linkedin"
    )
    assert snapshot[
        "skills"
    ][0]["skill"] in {
        "SQL",
        "Power BI",
        "Excel",
    }
    assert snapshot[
        "recent_activity"
    ]
    assert snapshot["insights"]

    print("=" * 70)
    print(
        "CAREERPILOT SPRINT 9 "
        "CAREER DASHBOARD TEST"
    )
    print("=" * 70)
    print(
        "Applications:",
        metrics[
            "applications_sent"
        ],
    )
    print(
        "Interviews:",
        metrics[
            "interviews"
        ],
    )
    print(
        "Response rate:",
        metrics[
            "response_rate"
        ],
    )
    print(
        "Follow-ups:",
        len(
            snapshot[
                "followups"
            ]
        ),
    )
    print(
        "Insights:",
        len(
            snapshot[
                "insights"
            ]
        ),
    )
    print(
        "\nSPRINT 9 CAREER DASHBOARD TEST PASSED"
    )


if __name__ == "__main__":
    main()
