from __future__ import annotations

from datetime import date, timedelta

from app.services.career_coach import (
    build_coach_snapshot,
)


def main() -> None:
    today = date(
        2026,
        7,
        15,
    )

    selected_job = {
        "company": "CareerPilot Test Company",
        "job_role": "Data Analyst",
        "match_score": 88,
        "priority": "Apply immediately",
        "apply_urgency": "Apply today",
        "matched_skills": (
            "SQL, Power BI, Python, Excel"
        ),
        "missing_skills": (
            "Snowflake, Azure"
        ),
    }

    crm_records = [
        {
            "company": "Alpha",
            "role": "Data Analyst",
            "source": "linkedin",
            "stage": "HR Round",
            "applied_date": (
                today
                - timedelta(days=5)
            ).isoformat(),
            "next_follow_up_date": "",
        },
        {
            "company": "Beta",
            "role": "Power BI Analyst",
            "source": "indeed",
            "stage": "Applied",
            "applied_date": (
                today
                - timedelta(days=2)
            ).isoformat(),
            "next_follow_up_date": (
                today
                - timedelta(days=1)
            ).isoformat(),
        },
    ]

    queue = [
        {
            "company": "Queue Company",
            "role": "SQL Analyst",
            "status": "Ready to Apply",
            "match_score": 91,
            "matched_skills": (
                "SQL, Excel, Power BI"
            ),
            "missing_skills": (
                "Snowflake"
            ),
        }
    ]

    outreach_records = [
        {
            "company": "Recruiter Company",
            "role": "Data Analyst",
            "status": "Contacted",
            "follow_up_date": (
                today
                - timedelta(days=1)
            ).isoformat(),
        }
    ]

    saved_jobs = [
        {
            "role": "Data Analyst",
            "matched_skills": (
                "SQL, Power BI"
            ),
            "missing_skills": (
                "Snowflake, Azure"
            ),
        },
        {
            "role": "Power BI Analyst",
            "matched_skills": (
                "Power BI, Excel"
            ),
            "missing_skills": (
                "Azure"
            ),
        },
    ]

    snapshot = build_coach_snapshot(
        selected_job=selected_job,
        crm_records=crm_records,
        queue=queue,
        outreach_records=outreach_records,
        saved_jobs=saved_jobs,
        today=today,
    )

    job = snapshot[
        "job_explanation"
    ]
    strategy = snapshot[
        "strategy"
    ]
    skills = snapshot[
        "skill_gap_plan"
    ]
    actions = snapshot[
        "daily_actions"
    ]

    assert job["fit_label"] == (
        "Strong fit"
    )
    assert job["role_family"] == (
        "Data Analytics"
    )
    assert strategy[
        "applications"
    ] == 2
    assert strategy[
        "responses"
    ] == 1
    assert strategy[
        "response_rate"
    ] == 50.0
    assert strategy[
        "high_score_queue"
    ] == 1
    assert skills[0]["skill"] in {
        "Snowflake",
        "Azure",
    }
    assert skills[0][
        "priority"
    ] in {
        "High",
        "Medium",
    }
    assert actions[0][
        "priority"
    ] == 1
    assert (
        "follow-up"
        in actions[0][
            "action"
        ].lower()
    )

    print("=" * 70)
    print(
        "CAREERPILOT SPRINT 10 "
        "CAREER COACH TEST"
    )
    print("=" * 70)
    print(
        "Selected job fit:",
        job["fit_label"],
    )
    print(
        "Applications:",
        strategy[
            "applications"
        ],
    )
    print(
        "Response rate:",
        strategy[
            "response_rate"
        ],
    )
    print(
        "Skill gaps:",
        len(skills),
    )
    print(
        "Daily actions:",
        len(actions),
    )
    print(
        "\nSPRINT 10 CAREER COACH TEST PASSED"
    )


if __name__ == "__main__":
    main()
