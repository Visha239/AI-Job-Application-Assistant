from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_SOURCE_CONFIG = Path("config/company_sources.json")


def load_company_sources(
    path: str | Path = DEFAULT_SOURCE_CONFIG,
) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        return {
            "naukri": {"enabled": True},
            "companies": [],
        }

    with config_path.open("r", encoding="utf-8-sig") as file:
        payload = json.load(file)

    payload.setdefault("naukri", {"enabled": True})
    payload.setdefault("companies", [])
    return payload


def enabled_companies(
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        company
        for company in config.get("companies", [])
        if company.get("enabled", True)
    ]
