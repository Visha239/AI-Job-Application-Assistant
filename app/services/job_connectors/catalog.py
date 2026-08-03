from __future__ import annotations

from collections import Counter
from pathlib import Path

import pandas as pd

from app.services.job_connectors.registry import load_connectors


def source_catalog(path: str | Path = "config/job_connectors.json"):
    sources = load_connectors(path)
    rows = []

    for source in sources:
        rows.append(
            {
                "key": source.key,
                "source": source.label,
                "connector": source.connector,
                "group": source.group,
                "company": source.company,
                "enabled": source.enabled,
                "official": source.official_source,
                "priority": source.priority,
            }
        )

    return pd.DataFrame(rows)


def source_coverage_summary(
    path: str | Path = "config/job_connectors.json",
):
    frame = source_catalog(path)

    if frame.empty:
        return {
            "enabled_total": 0,
            "enabled_official": 0,
            "connector_types": {},
            "groups": {},
        }

    enabled = frame[frame["enabled"]].copy()

    return {
        "enabled_total": int(len(enabled)),
        "enabled_official": int(enabled["official"].astype(bool).sum()),
        "connector_types": dict(Counter(enabled["connector"])),
        "groups": dict(Counter(enabled["group"])),
    }
