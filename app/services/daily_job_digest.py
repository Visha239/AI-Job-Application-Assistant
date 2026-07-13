from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from app.services.job_ranker import rank_jobs
from app.services.job_repository import save_job
from app.services.job_search import search_jobs


CONFIG_PATH = Path("config/job_search.json")
REPORTS_DIR = Path("exports/reports")


def load_job_search_config(
    config_path: Path = CONFIG_PATH,
) -> dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(
            f"Job search configuration not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8-sig") as file:
        config = json.load(file)

    required_fields = [
        "roles",
        "location",
        "sites",
        "results_per_role",
        "hours_old",
        "minimum_match_score",
        "maximum_digest_jobs",
    ]

    missing_fields = [
        field for field in required_fields if field not in config
    ]

    if missing_fields:
        raise ValueError(
            "Missing configuration fields: "
            + ", ".join(missing_fields)
        )

    return config


def _empty_jobs_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "site",
            "title",
            "company",
            "location",
            "date_posted",
            "job_type",
            "is_remote",
            "job_url",
            "description",
            "searched_role",
        ]
    )


def collect_jobs(
    config: dict[str, Any],
) -> tuple[pd.DataFrame, list[str]]:
    collected_frames: list[pd.DataFrame] = []
    errors: list[str] = []

    for role in config["roles"]:
        try:
            jobs = search_jobs(
                search_term=role,
                location=config["location"],
                results_wanted=int(config["results_per_role"]),
                hours_old=int(config["hours_old"]),
                sites=config["sites"],
            )

            if jobs is None or jobs.empty:
                continue

            jobs = jobs.copy()
            jobs["searched_role"] = role
            collected_frames.append(jobs)

        except Exception as exc:
            errors.append(f"{role}: {exc}")

    if not collected_frames:
        return _empty_jobs_dataframe(), errors

    combined = pd.concat(
        collected_frames,
        ignore_index=True,
        sort=False,
    )

    if "job_url" in combined.columns:
        with_url = combined[
            combined["job_url"].fillna("").astype(str).str.strip() != ""
        ]

        without_url = combined[
            combined["job_url"].fillna("").astype(str).str.strip() == ""
        ]

        with_url = with_url.drop_duplicates(
            subset=["job_url"],
            keep="first",
        )

        combined = pd.concat(
            [with_url, without_url],
            ignore_index=True,
        )

    combined = combined.drop_duplicates(
        subset=["company", "title", "location"],
        keep="first",
    )

    return combined.reset_index(drop=True), errors


def prepare_ranked_digest(
    jobs: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    if jobs is None or jobs.empty:
        return pd.DataFrame()

    ranked = rank_jobs(jobs)

    if ranked.empty:
        return ranked

    minimum_score = int(config["minimum_match_score"])
    maximum_jobs = int(config["maximum_digest_jobs"])

    ranked = ranked[
        ranked["match_score"] >= minimum_score
    ].copy()

    ranked = ranked.sort_values(
        by=["match_score", "date_posted"],
        ascending=[False, False],
        na_position="last",
    )

    return ranked.head(maximum_jobs).reset_index(drop=True)


def save_new_ranked_jobs(
    ranked_jobs: pd.DataFrame,
) -> dict[str, int]:
    saved_count = 0
    duplicate_count = 0

    if ranked_jobs is None or ranked_jobs.empty:
        return {
            "saved": 0,
            "duplicates": 0,
        }

    for _, row in ranked_jobs.iterrows():
        was_saved = save_job(row.to_dict())

        if was_saved:
            saved_count += 1
        else:
            duplicate_count += 1

    return {
        "saved": saved_count,
        "duplicates": duplicate_count,
    }


def _safe(value: object) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return html.escape(str(value))


def build_html_digest(
    ranked_jobs: pd.DataFrame,
    generated_at: datetime | None = None,
) -> str:
    generated_at = generated_at or datetime.now()

    rows: list[str] = []

    if ranked_jobs is not None and not ranked_jobs.empty:
        for index, row in ranked_jobs.iterrows():
            score = int(float(row.get("match_score") or 0))
            title = _safe(row.get("title") or "Unknown Role")
            company = _safe(
                row.get("company") or "Unknown Company"
            )
            location = _safe(
                row.get("location") or "Not provided"
            )
            source = _safe(row.get("site") or "Unknown")
            resume = _safe(
                row.get("resume_version")
                or "Data Analyst Resume"
            )
            matched = _safe(
                row.get("matched_skills")
                or "No profile skills detected"
            )
            missing = _safe(
                row.get("missing_profile_skills")
                or "None"
            )
            job_url = _safe(row.get("job_url") or "")

            apply_button = ""

            if job_url:
                apply_button = (
                    f'<a href="{job_url}" '
                    'style="display:inline-block;'
                    'padding:10px 16px;'
                    'background:#2563eb;'
                    'color:white;'
                    'text-decoration:none;'
                    'border-radius:6px;">'
                    "Open Job</a>"
                )

            rows.append(
                f"""
                <div class="job-card">
                    <div class="rank">#{index + 1}</div>
                    <div class="score">{score}% match</div>
                    <h2>{title}</h2>
                    <h3>{company}</h3>
                    <p><strong>Location:</strong> {location}</p>
                    <p><strong>Source:</strong> {source}</p>
                    <p>
                        <strong>Recommended resume:</strong>
                        {resume}
                    </p>
                    <p>
                        <strong>Matched skills:</strong>
                        {matched}
                    </p>
                    <p>
                        <strong>Skills not seen:</strong>
                        {missing}
                    </p>
                    {apply_button}
                </div>
                """
            )

    if not rows:
        rows.append(
            """
            <div class="empty">
                No strong job matches were found for this run.
            </div>
            """
        )

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>CareerPilot Daily Job Digest</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 960px;
                margin: 0 auto;
                padding: 30px;
                background: #f4f6f8;
                color: #172033;
            }}

            .header {{
                background: #111827;
                color: white;
                padding: 28px;
                border-radius: 10px;
                margin-bottom: 24px;
            }}

            .job-card {{
                background: white;
                border-radius: 10px;
                padding: 22px;
                margin-bottom: 18px;
                border: 1px solid #dce1e7;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            }}

            .rank {{
                color: #64748b;
                font-weight: bold;
            }}

            .score {{
                display: inline-block;
                margin-top: 8px;
                padding: 5px 10px;
                border-radius: 999px;
                background: #dcfce7;
                color: #166534;
                font-weight: bold;
            }}

            h2 {{
                margin-bottom: 4px;
            }}

            h3 {{
                margin-top: 0;
                color: #475569;
            }}

            .empty {{
                background: white;
                padding: 24px;
                border-radius: 10px;
            }}
        </style>
    </head>

    <body>
        <div class="header">
            <h1>CareerPilot Daily Job Digest</h1>
            <p>
                Generated:
                {generated_at.strftime("%d %B %Y, %I:%M %p")}
            </p>
            <p>
                Strong matches found:
                {0 if ranked_jobs is None else len(ranked_jobs)}
            </p>
        </div>

        {''.join(rows)}
    </body>
    </html>
    """


def export_digest_files(
    ranked_jobs: pd.DataFrame,
) -> dict[str, str]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    html_path = (
        REPORTS_DIR
        / f"careerpilot_daily_digest_{timestamp}.html"
    )

    csv_path = (
        REPORTS_DIR
        / f"careerpilot_daily_jobs_{timestamp}.csv"
    )

    html_content = build_html_digest(ranked_jobs)

    html_path.write_text(
        html_content,
        encoding="utf-8-sig",
    )

    if ranked_jobs is None:
        ranked_jobs = pd.DataFrame()

    ranked_jobs.to_csv(
        csv_path,
        index=False,
        encoding="utf-8-sig",
    )

    return {
        "html_path": str(html_path),
        "csv_path": str(csv_path),
    }


def run_daily_digest() -> dict[str, Any]:
    config = load_job_search_config()

    collected_jobs, errors = collect_jobs(config)

    ranked_jobs = prepare_ranked_digest(
        collected_jobs,
        config,
    )

    save_result = save_new_ranked_jobs(ranked_jobs)

    export_result = export_digest_files(ranked_jobs)

    return {
        "config": config,
        "jobs_collected": len(collected_jobs),
        "ranked_jobs": ranked_jobs,
        "strong_matches": len(ranked_jobs),
        "saved_jobs": save_result["saved"],
        "duplicate_jobs": save_result["duplicates"],
        "errors": errors,
        "html_path": export_result["html_path"],
        "csv_path": export_result["csv_path"],
    }
