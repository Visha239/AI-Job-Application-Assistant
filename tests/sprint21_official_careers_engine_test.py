from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from app.services.job_connectors.connectors import (
    AshbyConnector,
    GreenhouseConnector,
    LeverConnector,
)
from app.services.job_connectors.registry import prioritized_connectors
from app.services.job_connectors.types import ConnectorConfig

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    config_path = ROOT / "config" / "job_connectors.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    enabled = [item for item in payload["connectors"] if item["enabled"]]
    official = [item for item in enabled if item.get("official_source")]

    assert len(official) >= 10
    assert {"greenhouse", "lever", "smartrecruiters", "workday"} <= {
        item["connector"] for item in official
    }

    ordered = prioritized_connectors(
        ["linkedin", "paytm", "indeed", "kyndryl"]
    )
    assert [item.key for item in ordered[:2]] == ["paytm", "kyndryl"]
    assert all(item.official_source for item in ordered[:2])
    assert not any(item.official_source for item in ordered[2:])

    greenhouse_config = ConnectorConfig(
        key="test_greenhouse",
        label="Test Greenhouse",
        connector="greenhouse",
        group="company_careers",
        official_source=True,
        company="Test Company",
        token="test-company",
    )
    greenhouse_payload = {
        "jobs": [
            {
                "title": "Data Analyst",
                "location": {"name": "Bengaluru, India"},
                "updated_at": "2026-08-02T08:00:00Z",
                "absolute_url": "https://example.com/data-analyst",
                "content": "SQL Power BI entry level",
            },
            {
                "title": "Data Analyst",
                "location": {"name": "New York"},
                "absolute_url": "https://example.com/us-job",
                "content": "SQL",
            },
        ]
    }
    with patch(
        "app.services.job_connectors.connectors.cache_get",
        return_value=None,
    ), patch(
        "app.services.job_connectors.connectors.get_json",
        return_value=greenhouse_payload,
    ), patch(
        "app.services.job_connectors.connectors.cache_set",
    ):
        result = GreenhouseConnector(greenhouse_config).search(
            role="Data Analyst",
            location="Bengaluru, Karnataka",
            results_wanted=10,
            hours_old=72,
        )
    assert result.status == "success"
    assert len(result.jobs) == 1
    assert bool(result.jobs.iloc[0]["official_source"])

    lever_config = ConnectorConfig(
        key="test_lever",
        label="Test Lever",
        connector="lever",
        group="company_careers",
        official_source=True,
        company="Test Lever Company",
        token="testlever",
    )
    lever_payload = [
        {
            "text": "Business Analyst",
            "categories": {
                "location": "Bangalore, India",
                "commitment": "Full-time",
            },
            "descriptionPlain": "SQL reporting dashboard",
            "additionalPlain": "",
            "createdAt": 1785657600000,
            "hostedUrl": "https://jobs.lever.co/test/1",
        }
    ]
    with patch(
        "app.services.job_connectors.connectors.cache_get",
        return_value=lever_payload,
    ):
        result = LeverConnector(lever_config).search(
            role="Business Analyst",
            location="Bengaluru, Karnataka",
            results_wanted=10,
            hours_old=72,
        )
    assert len(result.jobs) == 1

    assert "ashby" in __import__(
        "app.services.job_connectors.connectors",
        fromlist=["CONNECTORS"],
    ).CONNECTORS

    search_config = json.loads(
        (ROOT / "config" / "job_search.json").read_text(encoding="utf-8")
    )
    assert search_config["source_strategy"] == "official_first"
    assert "paytm" in search_config["daily_source_keys"]
    assert "linkedin" in search_config["daily_source_keys"]

    print("=" * 72)
    print("CAREERPILOT SPRINT 21 OFFICIAL CAREERS ENGINE TEST")
    print("=" * 72)
    print(f"Enabled official sources: {len(official)}")
    print("Official-first ordering: PASS")
    print("Greenhouse connector: PASS")
    print("Lever connector: PASS")
    print("Ashby connector registered: PASS")
    print("Daily digest source configuration: PASS")
    print()
    print("SPRINT 21 OFFICIAL CAREERS ENGINE TEST PASSED")


if __name__ == "__main__":
    main()
