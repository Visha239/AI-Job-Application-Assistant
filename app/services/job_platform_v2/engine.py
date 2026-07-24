from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from app.services.job_platform_v2.adapters import run_adapter
from app.services.job_platform_v2.models import empty_jobs
from app.services.job_platform_v2.registry import enabled_source_map

def resolve_sources(keys: list[str]):
    source_map = enabled_source_map()
    return [source_map[key] for key in keys if key in source_map]

def collect_jobs_v2(
    *, roles: list[str], location: str,
    selected_source_keys: list[str],
    results_per_role: int, hours_old: int,
    fetch_linkedin_description: bool = True,
    max_workers: int = 6,
):
    sources = resolve_sources(selected_source_keys)
    if not sources:
        raise ValueError("Select at least one enabled job source.")

    frames = []
    errors = []
    runs = []

    with ThreadPoolExecutor(max_workers=max(1, min(max_workers, 10))) as pool:
        futures = {}
        for role in roles:
            clean_role = str(role).strip()
            if not clean_role:
                continue
            for source in sources:
                future = pool.submit(
                    run_adapter,
                    source,
                    role=clean_role,
                    location=location,
                    results_wanted=results_per_role,
                    hours_old=hours_old,
                    fetch_linkedin_description=fetch_linkedin_description,
                )
                futures[future] = (source, clean_role)

        for future in as_completed(futures):
            source, role = futures[future]
            try:
                jobs = future.result()
                count = len(jobs)
                runs.append({
                    "source": source.label,
                    "group": source.group,
                    "role": role,
                    "status": "success",
                    "collected": count,
                    "error": "",
                })
                if count:
                    frames.append(jobs)
            except Exception as exc:
                errors.append(f"{source.label} / {role}: {exc}")
                runs.append({
                    "source": source.label,
                    "group": source.group,
                    "role": role,
                    "status": "error",
                    "collected": 0,
                    "error": str(exc),
                })

    jobs = (
        pd.concat(frames, ignore_index=True, sort=False)
        if frames else empty_jobs()
    )

    counts = Counter()
    if not jobs.empty:
        counts.update(jobs["source_group"].fillna("unknown"))

    source_counts = {
        "job_boards": int(counts.get("job_board", 0)),
        "india_boards": int(counts.get("india_board", 0)),
        "company_careers": int(counts.get("company_careers", 0)),
        "ats_platforms": int(counts.get("ats_platform", 0)),
        "total": int(len(jobs)),
    }
    return jobs, errors, source_counts, runs
