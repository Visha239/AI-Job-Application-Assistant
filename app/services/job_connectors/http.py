from __future__ import annotations

import time

import requests


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/150 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,application/xml,text/xml,*/*",
}


def _request(
    method: str,
    url: str,
    *,
    params=None,
    payload=None,
    attempts: int = 3,
    timeout: int = 25,
):
    last_error = None

    for attempt in range(attempts):
        try:
            response = requests.request(
                method,
                url,
                params=params,
                json=payload,
                headers=HEADERS,
                timeout=timeout,
            )
            response.raise_for_status()
            return response
        except Exception as exc:
            last_error = exc
            if attempt < attempts - 1:
                time.sleep(1.5 * (attempt + 1))

    raise last_error


def get_json(url, *, params=None, attempts=3, timeout=25):
    return _request(
        "GET",
        url,
        params=params,
        attempts=attempts,
        timeout=timeout,
    ).json()


def get_text(url, *, params=None, attempts=3, timeout=25):
    response = _request(
        "GET",
        url,
        params=params,
        attempts=attempts,
        timeout=timeout,
    )
    return response.text


def post_json(url, *, payload, attempts=3, timeout=25):
    return _request(
        "POST",
        url,
        payload=payload,
        attempts=attempts,
        timeout=timeout,
    ).json()
