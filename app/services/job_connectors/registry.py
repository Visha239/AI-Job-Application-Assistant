from __future__ import annotations

import json
from pathlib import Path

from app.services.job_connectors.types import ConnectorConfig


DEFAULT_CONFIG = Path("config/job_connectors.json")


def load_connectors(path=DEFAULT_CONFIG):
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    connectors = []

    for raw in payload.get("connectors", []):
        connector = ConnectorConfig(
            key=str(raw.get("key", "")).strip(),
            label=str(raw.get("label", "")).strip(),
            connector=str(raw.get("connector", "")).strip(),
            group=str(raw.get("group", "job_board")).strip(),
            enabled=bool(raw.get("enabled", True)),
            official_source=bool(raw.get("official_source", False)),
            company=str(raw.get("company", "")).strip(),
            token=str(raw.get("token", "")).strip(),
            board_url=str(raw.get("board_url", "")).strip(),
            priority=int(raw.get("priority", 50)),
            options=dict(raw.get("options", {})),
        )
        if connector.key:
            connectors.append(connector)

    return connectors


def enabled_connector_map(path=DEFAULT_CONFIG):
    return {
        connector.key: connector
        for connector in load_connectors(path)
        if connector.enabled
    }


def connector_sort_key(connector: ConnectorConfig):
    # Official company sources always run before aggregators.
    source_tier = 0 if connector.official_source else 1
    return (source_tier, connector.priority, connector.label.lower())


def prioritized_connectors(keys=None, path=DEFAULT_CONFIG):
    source_map = enabled_connector_map(path)
    selected = (
        list(source_map.values())
        if keys is None
        else [source_map[key] for key in keys if key in source_map]
    )
    return sorted(selected, key=connector_sort_key)


def connector_groups(path=DEFAULT_CONFIG):
    groups = {}
    for connector in prioritized_connectors(path=path):
        groups.setdefault(connector.group, []).append(connector)
    return groups
