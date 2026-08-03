from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

from app.services.job_connectors.connectors import CONNECTORS
from app.services.job_connectors.registry import prioritized_connectors
from app.services.job_connectors.types import empty_jobs


def _deduplicate_source_jobs(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return empty_jobs()

    result = frame.copy()
    urls = result["job_url"].fillna("").astype(str).str.strip().str.lower()
    with_url = result.loc[urls != ""].drop_duplicates(
        subset=["job_url"],
        keep="first",
    )

    without_url = result.loc[urls == ""].drop_duplicates(
        subset=["company", "title", "location"],
        keep="first",
    )
    return pd.concat(
        [with_url, without_url],
        ignore_index=True,
        sort=False,
    )


def _search_source(
    source,
    *,
    roles,
    location,
    results_per_role,
    hours_old,
):
    connector_class = CONNECTORS.get(source.connector)
    if connector_class is None:
        return {
            "frames": [],
            "runs": [],
            "errors": [
                f"{source.label}: unknown connector {source.connector}"
            ],
            "direct_links": [],
        }

    connector = connector_class(source)
    frames = []
    runs = []
    errors = []
    direct_links = []

    for role in roles:
        try:
            result = connector.search(
                role=role,
                location=location,
                results_wanted=results_per_role,
                hours_old=hours_old,
            )
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

    combined = (
        _deduplicate_source_jobs(
            pd.concat(frames, ignore_index=True, sort=False)
        )
        if frames
        else empty_jobs()
    )

    return {
        "frames": [combined] if not combined.empty else [],
        "runs": runs,
        "errors": errors,
        "direct_links": direct_links,
    }


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

    clean_roles = [
        str(role).strip()
        for role in roles
        if str(role).strip()
    ]

    frames = []
    errors = []
    runs = []
    direct_links = []

    # One future per source. Each official board is downloaded once and reused
    # for all roles through its connector cache, which is much faster and avoids
    # inflated duplicate counts.
    with ThreadPoolExecutor(
        max_workers=max(1, min(max_workers, 8))
    ) as pool:
        futures = {
            pool.submit(
                _search_source,
                source,
                roles=clean_roles,
                location=location,
                results_per_role=results_per_role,
                hours_old=hours_old,
            ): source
            for source in sources
        }

        for future in as_completed(futures):
            source = futures[future]
            try:
                result = future.result()
                frames.extend(result["frames"])
                errors.extend(result["errors"])
                runs.extend(result["runs"])
                direct_links.extend(result["direct_links"])
            except Exception as exc:
                errors.append(f"{source.label}: {exc}")

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
        "company_careers": int(
            group_counts.get("company_careers", 0)
        ),
        "ats_platforms": int(group_counts.get("ats_platform", 0)),
        "official_total": (
            int(
                jobs["official_source"]
                .fillna(False)
                .astype(bool)
                .sum()
            )
            if not jobs.empty
            else 0
        ),
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
