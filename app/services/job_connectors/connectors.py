from __future__ import annotations

from datetime import datetime, timedelta, timezone
from html import unescape
import math
import re
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

import pandas as pd

from app.services.job_connectors.cache import (
    get_json as cache_get,
    set_json as cache_set,
)
from app.services.job_connectors.http import (
    get_json,
    get_text,
    post_json,
)
from app.services.job_connectors.types import (
    ConnectorResult,
    empty_jobs,
    normalize_jobs,
)


def _terms(value: str) -> list[str]:
    return [
        term.lower()
        for term in re.split(r"[^a-zA-Z0-9+#]+", value or "")
        if len(term) >= 2
    ]


def _matches_role(text: str, role: str) -> bool:
    role_terms = _terms(role)
    haystack = " ".join((text or "").lower().split())

    if not role_terms:
        return True

    phrase = " ".join(role_terms)
    if phrase in haystack:
        return True

    matched = sum(term in haystack for term in role_terms)
    required = 1 if len(role_terms) == 1 else math.ceil(len(role_terms) * 0.67)
    return matched >= required


def _matches_location(job_location: str, requested_location: str) -> bool:
    target = (requested_location or "").lower().strip()
    actual = (job_location or "").lower().strip()

    if not target or not actual:
        return True

    if any(value in actual for value in ("remote", "india")):
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


def _parse_datetime(value) -> datetime | None:
    if value is None or value == "":
        return None

    if isinstance(value, (int, float)):
        timestamp = value / 1000 if value > 10_000_000_000 else value
        try:
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except (OSError, ValueError):
            return None

    text = str(value).strip()
    if not text:
        return None

    # Workday often returns relative labels rather than a true timestamp.
    relative = re.search(r"posted\s+(\d+)\s+day", text.lower())
    if relative:
        return datetime.now(timezone.utc) - timedelta(
            days=int(relative.group(1))
        )

    if "today" in text.lower():
        return datetime.now(timezone.utc)

    if "yesterday" in text.lower():
        return datetime.now(timezone.utc) - timedelta(days=1)

    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        pass

    for fmt in (
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%a, %d %b %Y %H:%M:%S %z",
    ):
        try:
            parsed = datetime.strptime(text, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue

    return None


def _within_hours(value, hours_old: int) -> bool:
    if not hours_old or hours_old <= 0:
        return True

    parsed = _parse_datetime(value)
    if parsed is None:
        # Unknown dates remain eligible and are handled by ranking warnings.
        return True

    threshold = datetime.now(timezone.utc) - timedelta(hours=hours_old)
    return parsed >= threshold


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
                posted = item.get("updated_at")
                searchable = " ".join(
                    [item.get("title") or "", job_location, body]
                )
                if not _matches_role(searchable, role):
                    continue
                if not _matches_location(job_location, location):
                    continue
                if not _within_hours(posted, hours_old):
                    continue

                rows.append(
                    {
                        "title": item.get("title") or "",
                        "company": self.config.company,
                        "location": job_location,
                        "date_posted": posted,
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
                created = item.get("createdAt")
                if not _matches_role(searchable, role):
                    continue
                if not _matches_location(job_location, location):
                    continue
                if not _within_hours(created, hours_old):
                    continue

                posted = _parse_datetime(created)
                rows.append(
                    {
                        "title": item.get("text") or "",
                        "company": self.config.company,
                        "location": job_location,
                        "date_posted": (
                            posted.isoformat() if posted is not None else None
                        ),
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
                    params={"includeCompensation": "true"},
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
                posted = item.get("publishedAt")
                searchable = " ".join(
                    [item.get("title") or "", job_location, body]
                )
                if not _matches_role(searchable, role):
                    continue
                if not _matches_location(job_location, location):
                    continue
                if not _within_hours(posted, hours_old):
                    continue

                rows.append(
                    {
                        "title": item.get("title") or "",
                        "company": self.config.company,
                        "location": job_location,
                        "date_posted": posted,
                        "job_type": item.get("employmentType") or "",
                        "is_remote": (
                            "remote" in job_location.lower()
                            or str(item.get("workplaceType", "")).lower()
                            == "remote"
                        ),
                        "job_url": (
                            item.get("jobUrl")
                            or item.get("applyUrl")
                            or ""
                        ),
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
                posted = item.get("releasedDate")
                searchable = " ".join(
                    [item.get("name") or "", job_location]
                )
                if not _matches_role(searchable, role):
                    continue
                if not _matches_location(job_location, location):
                    continue
                if not _within_hours(posted, hours_old):
                    continue

                rows.append(
                    {
                        "title": item.get("name") or "",
                        "company": self.config.company,
                        "location": job_location,
                        "date_posted": posted,
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

    def _request(self, url: str, role: str, results_wanted: int):
        payloads = [
            {
                "appliedFacets": {},
                "limit": min(results_wanted, 20),
                "offset": 0,
                "searchText": role,
            },
            {
                "appliedFacets": {},
                "limit": min(results_wanted, 20),
                "offset": 0,
                "searchText": "",
            },
        ]

        configured_payload = self.config.options.get("payload")
        if isinstance(configured_payload, dict):
            payloads.insert(0, configured_payload)

        last_error = None
        for payload in payloads:
            try:
                return post_json(url, payload=payload, attempts=1)
            except Exception as exc:
                last_error = exc

        raise last_error

    def search(self, *, role, location, results_wanted, hours_old):
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
            url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
            data = self._request(url, role, results_wanted)
            rows = []

            for item in data.get("jobPostings", []):
                job_location = item.get("locationsText") or ""
                title = item.get("title") or ""
                posted = item.get("postedOn")
                if not _matches_role(title, role):
                    continue
                if not _matches_location(job_location, location):
                    continue
                if not _within_hours(posted, hours_old):
                    continue

                external_path = item.get("externalPath") or ""
                rows.append(
                    {
                        "title": title,
                        "company": self.config.company,
                        "location": job_location,
                        "date_posted": posted,
                        "is_remote": "remote" in job_location.lower(),
                        "job_url": (
                            f"https://{host}/{locale}/{site}{external_path}"
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


class RecruiteeXmlConnector:
    """Read a company-provided public Recruitee/job-board XML feed."""

    def __init__(self, config):
        self.config = config

    @staticmethod
    def _value(node, *names):
        for name in names:
            child = node.find(name)
            if child is not None and child.text:
                return child.text.strip()
        return ""

    def search(self, *, role, location, results_wanted, hours_old):
        feed_url = self.config.options.get("feed_url", "")
        if not feed_url:
            return ConnectorResult(
                empty_jobs(),
                "disabled",
                "Public XML feed URL is not configured.",
                self.config.board_url,
            )

        try:
            cache_key = f"recruitee_xml:{feed_url}"
            xml_text = cache_get(cache_key, 900)

            if xml_text is None:
                xml_text = get_text(feed_url)
                cache_set(cache_key, xml_text)

            root = ET.fromstring(xml_text)
            rows = []

            for item in root.findall(".//job"):
                title = self._value(item, "title")
                company = self._value(item, "company") or self.config.company
                city = self._value(item, "city")
                state = self._value(item, "state")
                country = self._value(item, "country")
                job_location = ", ".join(
                    value for value in (city, state, country) if value
                )
                body = _strip_html(
                    self._value(
                        item,
                        "description_requirements",
                        "description",
                    )
                )
                posted = self._value(
                    item,
                    "publication_date",
                    "published_at",
                    "created_at",
                )
                job_url = self._value(
                    item,
                    "url",
                    "careers_url",
                    "apply_url",
                )

                searchable = " ".join([title, job_location, body])
                if not _matches_role(searchable, role):
                    continue
                if not _matches_location(job_location, location):
                    continue
                if not _within_hours(posted, hours_old):
                    continue

                rows.append(
                    {
                        "title": title,
                        "company": company,
                        "location": job_location,
                        "date_posted": posted or None,
                        "is_remote": "remote" in job_location.lower(),
                        "job_url": job_url,
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
                direct_url=self.config.board_url or feed_url,
            )
        except Exception as exc:
            return ConnectorResult(
                empty_jobs(),
                "error",
                str(exc),
                self.config.board_url or feed_url,
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
    "recruitee_xml": RecruiteeXmlConnector,
    "direct_link": DirectLinkConnector,
}
