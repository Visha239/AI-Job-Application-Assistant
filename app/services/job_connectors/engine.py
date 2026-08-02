from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

from app.services.job_connectors.connectors import CONNECTORS
from app.services.job_connectors.registry import prioritized_connectors
from app.services.job_connectors.types import empty_jobs


def collect_jobs(
    *,
    roles,
    location,
    selected_source_keys,
    results_per_role,
    hours_old,
    max_workers=6,
):
    sources = prioritized_connectors(selected_source_keys)
    if not sources:
        raise ValueError("Select at least one enabled source.")

    frames = []
    errors = []
    runs = []
    direct_links = []

    with ThreadPoolExecutor(
        max_workers=max(1, min(max_workers, 8))
    ) as pool:
        futures = {}

        # Sources are submitted in priority order: official careers first.
        for source in sources:
            connector_class = CONNECTORS.get(source.connector)
            if connector_class is None:
                errors.append(
                    f"{source.label}: unknown connector {source.connector}"
                )
                continue

            for role in roles:
                clean_role = str(role).strip()
                if not clean_role:
                    continue
                future = pool.submit(
                    connector_class(source).search,
                    role=clean_role,
                    location=location,
                    results_wanted=results_per_role,
                    hours_old=hours_old,
                )
                futures[future] = (source, clean_role)

        for future in as_completed(futures):
            source, role = futures[future]
            try:
                result = future.result()
                count = len(result.jobs)
                runs.append(
                    {
                        "priority": source.priority,
                        "official": source.official_source,
                        "source_key": source.key,
                        "source": source.label,
                        "company": source.company,
                        "group": source.group,
                        "role": role,
                        "status": result.status,
                        "collected": count,
                        "error": result.error,
                    }
                )
                if result.direct_url:
                    direct_links.append(
                        {
                            "source": source.label,
                            "role": role,
                            "url": result.direct_url,
                        }
                    )
                if count:
                    frames.append(result.jobs)
                if result.status == "error":
                    errors.append(
                        f"{source.label} / {role}: {result.error}"
                    )
            except Exception as exc:
                errors.append(f"{source.label} / {role}: {exc}")
                runs.append(
                    {
                        "priority": source.priority,
                        "official": source.official_source,
                        "source_key": source.key,
                        "source": source.label,
                        "company": source.company,
                        "group": source.group,
                        "role": role,
                        "status": "error",
                        "collected": 0,
                        "error": str(exc),
                    }
                )

    jobs = (
        pd.concat(frames, ignore_index=True, sort=False)
        if frames
        else empty_jobs()
    )
    group_counts = (
        Counter(jobs["source_group"].fillna("unknown"))
        if not jobs.empty
        else Counter()
    )
    source_counts = (
        Counter(jobs["source_label"].fillna("unknown"))
        if not jobs.empty
        else Counter()
    )

    counts = {
        "job_boards": int(group_counts.get("job_board", 0)),
        "india_boards": int(group_counts.get("india_board", 0)),
        "company_careers": int(group_counts.get("company_careers", 0)),
        "ats_platforms": int(group_counts.get("ats_platform", 0)),
        "official_total": int(
            jobs["official_source"].fillna(False).astype(bool).sum()
        ) if not jobs.empty else 0,
        "total": int(len(jobs)),
        "by_source": dict(source_counts),
    }

    runs.sort(
        key=lambda item: (
            0 if item.get("official") else 1,
            item.get("priority", 999),
            item.get("source", ""),
            item.get("role", ""),
        )
    )

    return jobs, errors, counts, runs, direct_links
