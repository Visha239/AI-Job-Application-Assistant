from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from app.services.job_platform_v2.models import SourceDefinition

DEFAULT_CONFIG = Path("config/job_sources_v2.json")

def load_source_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8-sig") as file:
        payload = json.load(file)
    payload.setdefault("sources", [])
    payload.setdefault("companies", [])
    return payload

def _definition(item: dict[str, Any], group: str | None = None) -> SourceDefinition:
    return SourceDefinition(
        key=str(item.get("key", "")).strip(),
        label=str(item.get("label", item.get("key", ""))).strip(),
        adapter=str(item.get("adapter", "indexed")).strip(),
        group=str(group or item.get("group", "job_board")).strip(),
        enabled=bool(item.get("enabled", True)),
        official_source=bool(item.get("official_source", False)),
        domain=str(item.get("domain", "")).strip(),
        company=str(item.get("company", item.get("name", ""))).strip(),
        token=str(item.get("token", "")).strip(),
        priority=int(item.get("priority", 50)),
        options=dict(item.get("options", {})),
    )

def get_source_definitions(path: str | Path = DEFAULT_CONFIG) -> list[SourceDefinition]:
    payload = load_source_config(path)
    definitions = [_definition(item) for item in payload["sources"]]
    definitions.extend(
        _definition(item, "company_careers")
        for item in payload["companies"]
    )
    return [item for item in definitions if item.key]

def enabled_source_map(path: str | Path = DEFAULT_CONFIG) -> dict[str, SourceDefinition]:
    return {
        item.key: item
        for item in get_source_definitions(path)
        if item.enabled
    }

def source_options_by_group(path: str | Path = DEFAULT_CONFIG) -> dict[str, list[SourceDefinition]]:
    groups: dict[str, list[SourceDefinition]] = {}
    for source in enabled_source_map(path).values():
        groups.setdefault(source.group, []).append(source)
    for values in groups.values():
        values.sort(key=lambda item: (item.priority, item.label.lower()))
    return groups
