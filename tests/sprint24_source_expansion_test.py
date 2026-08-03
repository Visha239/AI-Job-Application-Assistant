from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pandas as pd

from app.services.job_connectors.catalog import source_coverage_summary
from app.services.job_connectors.connectors import (
    CONNECTORS,
    RecruiteeXmlConnector,
    _matches_role,
    _within_hours,
)
from app.services.job_connectors.engine import _deduplicate_source_jobs
from app.services.job_connectors.registry import load_connectors
from app.services.job_connectors.types import ConnectorConfig


def main() -> None:
    config_path = Path("config/job_connectors.json")
    sources = load_connectors(config_path)
    enabled = [source for source in sources if source.enabled]
    official = [source for source in enabled if source.official_source]

    assert len(official) >= 25
    assert {"greenhouse", "lever", "ashby", "smartrecruiters", "workday"}.issubset(
        {source.connector for source in official}
    )
    assert "recruitee_xml" in CONNECTORS

    keys = {source.key for source in official}
    expected = {
        "jfrog",
        "inovalon",
        "certifyos",
        "commure",
        "novo",
        "nielsen_company",
        "wns",
        "sopra_steria",
        "sandisk",
    }
    assert expected.issubset(keys)

    # Senior / unrelated roles should no longer match merely because one generic
    # word appears. Relevant multi-word roles should still match.
    assert _matches_role(
        "Data Analyst - SQL, Power BI and reporting",
        "Data Analyst",
    )
    assert not _matches_role(
        "Data Engineer - build distributed data pipelines",
        "Data Analyst",
    )
    assert _matches_role(
        "Application Support Analyst",
        "Application Support Analyst",
    )

    assert _within_hours("2099-01-01T00:00:00+00:00", 24)
    assert not _within_hours("2020-01-01T00:00:00+00:00", 24)
    assert _within_hours(None, 24)

    frame = pd.DataFrame(
        [
            {
                "job_url": "https://example.com/1",
                "company": "A",
                "title": "Data Analyst",
                "location": "Bengaluru",
            },
            {
                "job_url": "https://example.com/1",
                "company": "A",
                "title": "Data Analyst",
                "location": "Bengaluru",
            },
        ]
    )
    deduped = _deduplicate_source_jobs(frame)
    assert len(deduped) == 1

    # Validate Recruitee XML parsing without touching the network.
    xml_text = """
    <jobs>
      <job>
        <reference>123</reference>
        <company>Example Company</company>
        <title>Data Analyst</title>
        <description_requirements>
          SQL Power BI reporting and dashboards
        </description_requirements>
        <city>Bengaluru</city>
        <country>IN</country>
        <publication_date>2099-01-01</publication_date>
        <url>https://example.com/jobs/123</url>
      </job>
    </jobs>
    """

    source = ConnectorConfig(
        key="example_recruitee",
        label="Example Recruitee",
        connector="recruitee_xml",
        group="ats_platform",
        enabled=True,
        official_source=True,
        company="Example Company",
        board_url="https://example.com/careers",
        priority=1,
        options={"feed_url": "https://example.com/feed.xml"},
    )

    import app.services.job_connectors.connectors as connector_module

    original_get_text = connector_module.get_text
    original_cache_get = connector_module.cache_get
    original_cache_set = connector_module.cache_set

    try:
        connector_module.cache_get = lambda *_args, **_kwargs: None
        connector_module.cache_set = lambda *_args, **_kwargs: None
        connector_module.get_text = lambda *_args, **_kwargs: xml_text

        result = RecruiteeXmlConnector(source).search(
            role="Data Analyst",
            location="Bengaluru",
            results_wanted=10,
            hours_old=24,
        )
    finally:
        connector_module.get_text = original_get_text
        connector_module.cache_get = original_cache_get
        connector_module.cache_set = original_cache_set

    assert result.status == "success"
    assert len(result.jobs) == 1
    assert result.jobs.iloc[0]["company"] == "Example Company"

    coverage = source_coverage_summary(config_path)
    assert coverage["enabled_official"] >= 25
    assert coverage["connector_types"]["ashby"] >= 4
    assert coverage["connector_types"]["smartrecruiters"] >= 5

    search_config = json.loads(
        Path("config/job_search.json").read_text(encoding="utf-8")
    )
    daily_keys = set(search_config["daily_source_keys"])
    assert expected.issubset(daily_keys)
    assert "lilly" not in daily_keys
    assert {"indeed", "linkedin"}.issubset(daily_keys)

    print("=" * 72)
    print("CAREERPILOT SPRINT 24 SOURCE EXPANSION TEST")
    print("=" * 72)
    print(f"Enabled official sources: {len(official)}")
    print("Greenhouse expansion: PASS")
    print("Ashby expansion: PASS")
    print("SmartRecruiters expansion: PASS")
    print("Recruitee public feed connector: PASS")
    print("Official-source freshness filter: PASS")
    print("Stricter role matching: PASS")
    print("Per-source duplicate cleanup: PASS")
    print("Daily/hourly source configuration: PASS")
    print()
    print("SPRINT 24 SOURCE EXPANSION TEST PASSED")


if __name__ == "__main__":
    main()
