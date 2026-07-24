from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

import pandas as pd


SOURCE_PRIORITY = {
    "company": 0,
    "company careers": 0,
    "careers": 0,
    "linkedin": 1,
    "indeed": 2,
    "google": 3,
}


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"", "none", "nan", "null", "nat"}:
        return ""
    return text


def _normalise(value: Any) -> str:
    text = _clean(value).lower()
    text = re.sub(r"\b(?:pvt|private|limited|ltd|inc|llp|corp|corporation)\b\.?", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _normalise_title(value: Any) -> str:
    text = _normalise(value)
    removable = {
        "job",
        "opening",
        "hiring",
        "immediate",
        "urgent",
        "remote",
        "hybrid",
    }
    return " ".join(word for word in text.split() if word not in removable)


def _city(value: Any) -> str:
    text = _normalise(value)
    aliases = {
        "bengaluru": "bangalore",
        "bangalore urban": "bangalore",
        "ka": "karnataka",
    }
    for source, target in aliases.items():
        text = text.replace(source, target)
    return text.split(",")[0].strip()


def _description_signature(value: Any) -> str:
    text = _normalise(value)
    words = text.split()
    return " ".join(words[:180])


def _similar(left: str, right: str, threshold: float) -> bool:
    if not left or not right:
        return False
    return SequenceMatcher(None, left, right).ratio() >= threshold


def jobs_are_duplicates(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    left_url = _clean(left.get("job_url")).lower().rstrip("/")
    right_url = _clean(right.get("job_url")).lower().rstrip("/")

    if left_url and right_url and left_url == right_url:
        return True

    company_match = _similar(
        _normalise(left.get("company")),
        _normalise(right.get("company")),
        0.88,
    )
    title_match = _similar(
        _normalise_title(left.get("title")),
        _normalise_title(right.get("title")),
        0.86,
    )

    if not (company_match and title_match):
        return False

    left_location = _city(left.get("location"))
    right_location = _city(right.get("location"))
    location_match = (
        not left_location
        or not right_location
        or left_location in right_location
        or right_location in left_location
        or _similar(left_location, right_location, 0.65)
        or "remote" in {left_location, right_location}
    )

    if not location_match:
        return False

    left_description = _description_signature(left.get("description"))
    right_description = _description_signature(right.get("description"))

    if left_description and right_description:
        return _similar(left_description, right_description, 0.72)

    return True


def _source_rank(value: Any) -> int:
    return SOURCE_PRIORITY.get(
        _clean(value).lower(),
        9,
    )


def _preferred_job(cluster: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(
        cluster,
        key=lambda item: (
            _source_rank(item.get("site")),
            -len(_clean(item.get("description"))),
            0 if _clean(item.get("job_url")) else 1,
        ),
    )[0]


def merge_duplicate_jobs(
    jobs: pd.DataFrame,
) -> tuple[pd.DataFrame, int]:
    if jobs is None or jobs.empty:
        return pd.DataFrame(), 0

    records = jobs.to_dict("records")
    clusters: list[list[dict[str, Any]]] = []

    for record in records:
        matching_cluster = next(
            (
                cluster
                for cluster in clusters
                if jobs_are_duplicates(record, cluster[0])
            ),
            None,
        )

        if matching_cluster is None:
            clusters.append([record])
        else:
            matching_cluster.append(record)

    merged_records: list[dict[str, Any]] = []

    for cluster in clusters:
        preferred = dict(_preferred_job(cluster))
        sources = sorted(
            {
                _clean(item.get("site"))
                for item in cluster
                if _clean(item.get("site"))
            }
        )
        urls = []
        for item in cluster:
            url = _clean(item.get("job_url"))
            if url and url not in urls:
                urls.append(url)

        preferred["duplicate_count"] = len(cluster)
        preferred["available_sources"] = ", ".join(sources)
        preferred["alternate_job_urls"] = " | ".join(urls)
        merged_records.append(preferred)

    removed = len(records) - len(merged_records)
    return pd.DataFrame(merged_records), removed
