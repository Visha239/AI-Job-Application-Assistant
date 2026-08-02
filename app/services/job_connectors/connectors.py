from __future__ import annotations

from datetime import datetime, timezone
from html import unescape
import re
from urllib.parse import quote_plus

import pandas as pd

from app.services.job_connectors.cache import (
    get_json as cache_get,
    set_json as cache_set,
)
from app.services.job_connectors.http import get_json, post_json
from app.services.job_connectors.types import (
    ConnectorResult,
    empty_jobs,
    normalize_jobs,
)


def _terms(value: str) -> list[str]:
    return [
        term.lower()
        for term in re.split(r"[^a-zA-Z0-9+#]+", value or "")
        if len(term) >= 3
    ]


def _matches_role(text: str, role: str) -> bool:
    role_terms = _terms(role)
    haystack = (text or "").lower()
    return not role_terms or any(term in haystack for term in role_terms)


def _matches_location(job_location: str, requested_location: str) -> bool:
    target = (requested_location or "").lower().strip()
    actual = (job_location or "").lower().strip()

    if not target or not actual:
        return True

    if "remote" in actual:
        return True

    aliases = {
        "bengaluru": {"bengaluru", "bangalore"},
        "bangalore": {"bengaluru", "bangalore"},
    }

    city = target.split(",")[0].strip()
    accepted = aliases.get(city, {city})
    return any(alias in actual for alias in accepted)


def _strip_html(value: str) -> str:
    clean = re.sub(r"<[^>]+>", " ", unescape(value or ""))
    return re.sub(r"\s+", " ", clean).strip()


class JobSpyConnector:
    def __init__(self, config):
        self.config = config

    def search(self, *, role, location, results_wanted, hours_old):
        try:
            from app.services.job_search import search_jobs

            jobs = search_jobs(
                search_term=role,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                sites=[self.config.options.get("site", self.config.key)],
                fetch_linkedin_description=True,
            )
            return ConnectorResult(
                normalize_jobs(
                    jobs,
                    source=self.config,
                    searched_role=role,
                ),
                "success",
            )
        except Exception as exc:
            return ConnectorResult(empty_jobs(), "error", str(exc))


class GreenhouseConnector:
    def __init__(self, config):
        self.config = config

    def search(self, *, role, location, results_wanted, hours_old):
        del hours_old
        if not self.config.token:
            return ConnectorResult(
                empty_jobs(),
                "disabled",
                "Greenhouse board token is not configured.",
                self.config.board_url,
            )

        try:
            key = f"greenhouse:{self.config.token}"
            data = cache_get(key, 900)
            if data is None:
                data = get_json(
                    "https://boards-api.greenhouse.io/v1/boards/"
                    f"{self.config.token}/jobs",
                    params={"content": "true"},
                )
                cache_set(key, data)

            rows = []
            for item in data.get("jobs", []):
                job_location = (item.get("location") or {}).get("name", "")
                body = _strip_html(item.get("content") or "")
                searchable = " ".join(
                    [item.get("title") or "", job_location, body]
                )
                if not _matches_role(searchable, role):
                    continue
                if not _matches_location(job_location, location):
                    continue

                rows.append(
                    {
                        "title": item.get("title") or "",
                        "company": self.config.company,
                        "location": job_location,
                        "date_posted": item.get("updated_at"),
                        "is_remote": "remote" in job_location.lower(),
                        "job_url": item.get("absolute_url") or "",
                        "description": body,
                        "requirements": body,
                    }
                )
                if len(rows) >= results_wanted:
                    break

            return ConnectorResult(
                normalize_jobs(
                    pd.DataFrame(rows),
                    source=self.config,
                    searched_role=role,
                ),
                "success",
                direct_url=self.config.board_url,
            )
        except Exception as exc:
            return ConnectorResult(
                empty_jobs(), "error", str(exc), self.config.board_url
            )


class LeverConnector:
    def __init__(self, config):
        self.config = config

    def search(self, *, role, location, results_wanted, hours_old):
        del hours_old
        if not self.config.token:
            return ConnectorResult(
                empty_jobs(),
                "disabled",
                "Lever site token is not configured.",
                self.config.board_url,
            )

        try:
            key = f"lever:{self.config.token}"
            data = cache_get(key, 900)
            if data is None:
                data = get_json(
                    f"https://api.lever.co/v0/postings/{self.config.token}",
                    params={"mode": "json"},
                )
                cache_set(key, data)

            rows = []
            for item in data:
                categories = item.get("categories") or {}
                job_location = categories.get("location") or ""
                body = " ".join(
                    [
                        item.get("descriptionPlain") or "",
                        item.get("additionalPlain") or "",
                    ]
                ).strip()
                searchable = " ".join(
                    [item.get("text") or "", job_location, body]
                )
                if not _matches_role(searchable, role):
                    continue
                if not _matches_location(job_location, location):
                    continue

                created = item.get("createdAt")
                posted = (
                    datetime.fromtimestamp(
                        created / 1000,
                        tz=timezone.utc,
                    ).isoformat()
                    if isinstance(created, (int, float))
                    else None
                )
                rows.append(
                    {
                        "title": item.get("text") or "",
                        "company": self.config.company,
                        "location": job_location,
                        "date_posted": posted,
                        "job_type": categories.get("commitment") or "",
                        "is_remote": "remote" in job_location.lower(),
                        "job_url": item.get("hostedUrl") or "",
                        "description": body,
                        "requirements": body,
                    }
                )
                if len(rows) >= results_wanted:
                    break

            return ConnectorResult(
                normalize_jobs(
                    pd.DataFrame(rows),
                    source=self.config,
                    searched_role=role,
                ),
                "success",
                direct_url=self.config.board_url,
            )
        except Exception as exc:
            return ConnectorResult(
                empty_jobs(), "error", str(exc), self.config.board_url
            )


class AshbyConnector:
    def __init__(self, config):
        self.config = config

    def search(self, *, role, location, results_wanted, hours_old):
        del hours_old
        if not self.config.token:
            return ConnectorResult(
                empty_jobs(),
                "disabled",
                "Ashby job-board name is not configured.",
                self.config.board_url,
            )

        try:
            key = f"ashby:{self.config.token}"
            data = cache_get(key, 900)
            if data is None:
                data = get_json(
                    "https://api.ashbyhq.com/posting-api/job-board/"
                    f"{self.config.token}",
                )
                cache_set(key, data)

            rows = []
            for item in data.get("jobs", []):
                job_location = item.get("location") or ""
                body = _strip_html(
                    item.get("descriptionHtml")
                    or item.get("descriptionPlain")
                    or ""
                )
                searchable = " ".join(
                    [item.get("title") or "", job_location, body]
                )
                if not _matches_role(searchable, role):
                    continue
                if not _matches_location(job_location, location):
                    continue

                rows.append(
                    {
                        "title": item.get("title") or "",
                        "company": self.config.company,
                        "location": job_location,
                        "date_posted": item.get("publishedAt"),
                        "job_type": item.get("employmentType") or "",
                        "is_remote": "remote" in job_location.lower(),
                        "job_url": item.get("jobUrl") or item.get("applyUrl") or "",
                        "description": body,
                        "requirements": body,
                    }
                )
                if len(rows) >= results_wanted:
                    break

            return ConnectorResult(
                normalize_jobs(
                    pd.DataFrame(rows),
                    source=self.config,
                    searched_role=role,
                ),
                "success",
                direct_url=self.config.board_url,
            )
        except Exception as exc:
            return ConnectorResult(
                empty_jobs(), "error", str(exc), self.config.board_url
            )


class SmartRecruitersConnector:
    def __init__(self, config):
        self.config = config

    def search(self, *, role, location, results_wanted, hours_old):
        del hours_old
        if not self.config.token:
            return ConnectorResult(
                empty_jobs(),
                "disabled",
                "SmartRecruiters company identifier is not configured.",
                self.config.board_url,
            )

        try:
            key = f"smartrecruiters:{self.config.token}"
            data = cache_get(key, 900)
            if data is None:
                data = get_json(
                    "https://api.smartrecruiters.com/v1/companies/"
                    f"{self.config.token}/postings",
                    params={"limit": 100, "offset": 0},
                )
                cache_set(key, data)

            rows = []
            for item in data.get("content", []):
                location_data = item.get("location") or {}
                job_location = ", ".join(
                    value
                    for value in [
                        location_data.get("city"),
                        location_data.get("region"),
                        location_data.get("country"),
                    ]
                    if value
                )
                searchable = " ".join(
                    [item.get("name") or "", job_location]
                )
                if not _matches_role(searchable, role):
                    continue
                if not _matches_location(job_location, location):
                    continue

                rows.append(
                    {
                        "title": item.get("name") or "",
                        "company": self.config.company,
                        "location": job_location,
                        "date_posted": item.get("releasedDate"),
                        "job_type": (
                            item.get("typeOfEmployment") or {}
                        ).get("label", ""),
                        "is_remote": "remote" in job_location.lower(),
                        "job_url": (
                            "https://jobs.smartrecruiters.com/"
                            f"{self.config.token}/{item.get('id', '')}"
                        ),
                        "description": "",
                        "requirements": "",
                    }
                )
                if len(rows) >= results_wanted:
                    break

            return ConnectorResult(
                normalize_jobs(
                    pd.DataFrame(rows),
                    source=self.config,
                    searched_role=role,
                ),
                "success",
                direct_url=self.config.board_url,
            )
        except Exception as exc:
            return ConnectorResult(
                empty_jobs(), "error", str(exc), self.config.board_url
            )


class WorkdayConnector:
    def __init__(self, config):
        self.config = config

    def search(self, *, role, location, results_wanted, hours_old):
        del hours_old
        options = self.config.options
        tenant = options.get("tenant", "")
        site = options.get("site", "")
        host = options.get("host", "")
        locale = options.get("locale", "en-US")

        if not all([tenant, site, host]):
            return ConnectorResult(
                empty_jobs(),
                "disabled",
                "Workday tenant, site and host are not configured.",
                self.config.board_url,
            )

        try:
            data = post_json(
                f"https://{host}/wday/cxs/{tenant}/{site}/jobs",
                payload={
                    "appliedFacets": {},
                    "limit": min(results_wanted, 20),
                    "offset": 0,
                    "searchText": role,
                },
            )
            rows = []
            for item in data.get("jobPostings", []):
                job_location = item.get("locationsText") or ""
                if not _matches_location(job_location, location):
                    continue
                external_path = item.get("externalPath") or ""
                rows.append(
                    {
                        "title": item.get("title") or "",
                        "company": self.config.company,
                        "location": job_location,
                        "date_posted": item.get("postedOn"),
                        "is_remote": "remote" in job_location.lower(),
                        "job_url": (
                            f"https://{host}/{locale}/{site}{external_path}"
                        ),
                        "description": "",
                        "requirements": "",
                    }
                )

            return ConnectorResult(
                normalize_jobs(
                    pd.DataFrame(rows),
                    source=self.config,
                    searched_role=role,
                ),
                "success",
                direct_url=self.config.board_url,
            )
        except Exception as exc:
            return ConnectorResult(
                empty_jobs(), "error", str(exc), self.config.board_url
            )


class DirectLinkConnector:
    def __init__(self, config):
        self.config = config

    def search(self, *, role, location, results_wanted, hours_old):
        del results_wanted, hours_old
        template = self.config.options.get(
            "search_url", self.config.board_url
        )
        role_slug = "-".join(role.lower().strip().split())
        location_slug = "-".join(
            location.lower()
            .replace("bengaluru", "bangalore")
            .split(",")[0]
            .strip()
            .split()
        )
        url = (
            template.format(
                role=quote_plus(role),
                location=quote_plus(location),
                role_slug=role_slug,
                location_slug=location_slug,
            )
            if template
            else ""
        )
        return ConnectorResult(
            empty_jobs(),
            "manual",
            "Open this source directly; automated collection is unavailable.",
            url,
        )


CONNECTORS = {
    "jobspy": JobSpyConnector,
    "greenhouse": GreenhouseConnector,
    "lever": LeverConnector,
    "ashby": AshbyConnector,
    "smartrecruiters": SmartRecruitersConnector,
    "workday": WorkdayConnector,
    "direct_link": DirectLinkConnector,
}
