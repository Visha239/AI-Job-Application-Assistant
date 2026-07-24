from __future__ import annotations

import sys
import types
from unittest.mock import patch

import pandas as pd


# The isolated package test does not need live JobSpy access.
fake_jobspy = types.ModuleType("jobspy")
fake_jobspy.scrape_jobs = lambda **kwargs: pd.DataFrame()
sys.modules.setdefault("jobspy", fake_jobspy)

from app.services.job_sources.aggregator import collect_all_sources
from app.services.job_sources.indexed_sources import build_naukri_search_url
from app.services.job_sources.source_models import normalise_jobs


def main() -> None:
    url = build_naukri_search_url(
        "Data Analyst",
        "Bengaluru, Karnataka",
    )
    assert "data-analyst-jobs-in-bangalore" in url

    sample = pd.DataFrame(
        [
            {
                "title": "Data Analyst",
                "company": "Example",
                "location": "Bengaluru",
                "job_url": "https://example.com/job/1",
                "description": (
                    "1 year experience with SQL and Power BI"
                ),
            }
        ]
    )

    normalized = normalise_jobs(
        sample,
        site="test",
        source_type="company_careers",
        official_source=True,
        searched_role="Data Analyst",
    )
    assert bool(normalized.iloc[0]["official_source"])
    assert normalized.iloc[0]["source_type"] == "company_careers"

    with patch(
        "app.services.job_sources.aggregator.search_jobs",
        return_value=sample,
    ), patch(
        "app.services.job_sources.aggregator.search_naukri_indexed",
        return_value=normalized.assign(site="naukri-indexed"),
    ):
        jobs, errors, counts = collect_all_sources(
            roles=["Data Analyst"],
            location="Bengaluru",
            jobspy_sites=["indeed"],
            results_per_role=10,
            hours_old=168,
            include_naukri=True,
            include_company_careers=False,
        )

    assert len(jobs) == 2
    assert not errors
    assert counts["jobspy"] == 1
    assert counts["naukri"] == 1

    print("=" * 72)
    print("CAREERPILOT SPRINT 16A COMPANY CAREERS + NAUKRI TEST")
    print("=" * 72)
    print("Naukri URL:", url)
    print("Combined jobs:", len(jobs))
    print("Source counts:", counts)
    print()
    print("SPRINT 16A SOURCE DISCOVERY TEST PASSED")


if __name__ == "__main__":
    main()
