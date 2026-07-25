from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import unescape
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class JDCaptureResult:
    description: str
    source: str
    status: str
    message: str


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _clean_text(value: Any) -> str:
    if value is None:
        return ""

    text = unescape(str(value))
    text = re.sub(r"\s+", " ", text).strip()

    if text.lower() in {"", "none", "nan", "null"}:
        return ""

    return text


def _extract_json_ld(soup: BeautifulSoup) -> str:
    for script in soup.find_all(
        "script",
        attrs={"type": "application/ld+json"},
    ):
        raw = script.string or script.get_text(" ", strip=True)

        if not raw:
            continue

        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue

        candidates = data if isinstance(data, list) else [data]

        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue

            if candidate.get("@type") == "JobPosting":
                description = _clean_text(
                    candidate.get("description")
                )

                if description:
                    return description

            graph = candidate.get("@graph")

            if isinstance(graph, list):
                for item in graph:
                    if (
                        isinstance(item, dict)
                        and item.get("@type") == "JobPosting"
                    ):
                        description = _clean_text(
                            item.get("description")
                        )

                        if description:
                            return description

    return ""


def _extract_from_selectors(soup: BeautifulSoup) -> str:
    selectors = [
        "[data-testid='job-description']",
        ".show-more-less-html__markup",
        ".jobs-description-content__text",
        "#jobDescriptionText",
        ".jobsearch-jobDescriptionText",
        ".description__text",
        ".job-description",
        ".jobDescription",
        "article",
        "main",
    ]

    for selector in selectors:
        node = soup.select_one(selector)

        if node is None:
            continue

        text = _clean_text(node.get_text(" ", strip=True))

        if len(text) >= 250:
            return text

    return ""


def _extract_meta_description(soup: BeautifulSoup) -> str:
    for attributes in [
        {"name": "description"},
        {"property": "og:description"},
        {"name": "twitter:description"},
    ]:
        node = soup.find("meta", attrs=attributes)

        if node and node.get("content"):
            text = _clean_text(node.get("content"))

            if len(text) >= 120:
                return text

    return ""


def fetch_job_description(
    job_url: str,
    *,
    timeout_seconds: int = 15,
) -> JDCaptureResult:
    url = _clean_text(job_url)

    if not url:
        return JDCaptureResult(
            description="",
            source="none",
            status="missing_url",
            message="No job URL was provided.",
        )

    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        return JDCaptureResult(
            description="",
            source="none",
            status="invalid_url",
            message="The job URL is invalid.",
        )

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=timeout_seconds,
            allow_redirects=True,
        )
        response.raise_for_status()

    except requests.RequestException as exc:
        return JDCaptureResult(
            description="",
            source="web",
            status="blocked_or_failed",
            message=(
                "Automatic description capture failed. "
                f"Paste the JD manually. Details: {exc}"
            ),
        )

    soup = BeautifulSoup(response.text, "html.parser")

    description = _extract_json_ld(soup)

    if description:
        return JDCaptureResult(
            description=description,
            source="json_ld",
            status="captured",
            message="Job description captured from structured page data.",
        )

    description = _extract_from_selectors(soup)

    if description:
        return JDCaptureResult(
            description=description,
            source="page_content",
            status="captured",
            message="Job description captured from the page.",
        )

    description = _extract_meta_description(soup)

    if description:
        return JDCaptureResult(
            description=description,
            source="meta_description",
            status="partial",
            message=(
                "Only a short page description was captured. "
                "Review and paste the full JD if needed."
            ),
        )

    return JDCaptureResult(
        description="",
        source="web",
        status="not_found",
        message=(
            "The site did not expose a readable job description. "
            "Paste the JD manually."
        ),
    )


def resolve_job_description(
    *,
    existing_description: str,
    job_url: str,
    minimum_length: int = 250,
) -> JDCaptureResult:
    existing = _clean_text(existing_description)

    if len(existing) >= minimum_length:
        return JDCaptureResult(
            description=existing,
            source="search_result",
            status="available",
            message="The job description was already available.",
        )

    fetched = fetch_job_description(job_url)

    if fetched.description:
        return fetched

    if existing:
        return JDCaptureResult(
            description=existing,
            source="search_result_partial",
            status="partial",
            message=(
                "Only a partial description is available. "
                "Paste the full JD for accurate ATS analysis."
            ),
        )

    return fetched

