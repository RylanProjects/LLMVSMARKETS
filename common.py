"""Shared helpers: CSV storage (append-only) and HTTP with retries."""
import csv
import os
import time
from datetime import datetime, timezone

import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(ROOT, "data"))
KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"

QUESTION_FIELDS = [
    "question_id", "event_ticker", "series", "collected_at", "expected_resolution",
    "close_time", "title", "question", "market_yes_bid", "market_yes_ask",
    "market_mid", "volume",
]
FORECAST_FIELDS = [
    "question_id", "provider", "model", "prompt_version", "forecast_at",
    "probability", "raw_response",
]
RESOLUTION_FIELDS = ["question_id", "result", "settled_at", "checked_at"]


def now_utc():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_time(s):
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def read_csv(name):
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def append_csv(name, rows, fields):
    """Append rows. Never rewrites old rows — the data is an append-only record."""
    if not rows:
        return
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, name)
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new:
            w.writeheader()
        w.writerows(rows)


def _request(method, url, retries=5, **kwargs):
    for attempt in range(retries):
        try:
            r = requests.request(method, url, timeout=60, **kwargs)
        except requests.RequestException as e:
            print(f"  network error ({e}); retrying")
            time.sleep(2 ** attempt * 2)
            continue
        if r.status_code == 429 or r.status_code >= 500:
            wait = 2 ** attempt * 5
            print(f"  HTTP {r.status_code}; waiting {wait}s")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"Gave up on {url} after {retries} attempts")


def get_json(url, params=None):
    return _request("GET", url, params=params)


def post_json(url, payload, headers):
    return _request("POST", url, json=payload, headers=headers)
