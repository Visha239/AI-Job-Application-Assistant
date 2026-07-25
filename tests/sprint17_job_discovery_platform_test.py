from __future__ import annotations

import ast
from pathlib import Path
import pandas as pd

from app.services.job_platform_v2.models import normalise_jobs
from app.services.job_platform_v2.registry import (
    enabled_source_map, source_options_by_group,
)
from app.services.job_platform_v2.engine import resolve_sources

ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    source_map = enabled_source_map()
    groups = source_options_by_group()

    required = {
        "indeed", "linkedin", "google_jobs", "naukri",
        "foundit", "internshala", "workday_indexed",
        "smartrecruiters_indexed", "amazon_careers",
        "microsoft_careers",
    }
    assert required.issubset(source_map)
    assert len(resolve_sources(["indeed", "naukri"])) == 2

    sample = pd.DataFrame([{
        "title": "Data Analyst",
        "company": "",
        "location": "Bengaluru",
        "job_url": "https://example.com/job/1",
        "description": "SQL and Power BI",
    }])
    normalized = normalise_jobs(
        sample,
        source=source_map["amazon_careers"],
        searched_role="Data Analyst",
    )
    assert normalized.iloc[0]["company"] == "Amazon"
    assert bool(normalized.iloc[0]["official_source"])

    page_text = (ROOT / "pages/1_Job_Search.py").read_text(encoding="utf-8")
    ast.parse(page_text)
    assert "selected_source_keys=selected_source_keys" in page_text
    assert "search_term" not in page_text
    assert "Source run report" in page_text

    print("=" * 72)
    print("CAREERPILOT SPRINT 17 JOB DISCOVERY PLATFORM V2 TEST")
    print("=" * 72)
    print("Enabled sources:", len(source_map))
    print("General boards:", len(groups["job_board"]))
    print("India platforms:", len(groups["india_board"]))
    print("ATS platforms:", len(groups["ats_platform"]))
    print("Company career sites:", len(groups["company_careers"]))
    print()
    print("SPRINT 17 JOB DISCOVERY PLATFORM TEST PASSED")

if __name__ == "__main__":
    main()
