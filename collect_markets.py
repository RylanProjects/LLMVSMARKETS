"""Step 1: pick new open Kalshi markets and snapshot their current prices.

Rules for picking questions (see config.py):
- binary markets resolving in MIN..MAX days
- liquid enough (tight spread, some volume) that the price means something
- at most one market per event (avoids 10 near-duplicate "temperature above X" questions)
- at most MAX_PER_SERIES per series per day, for topic variety
- random sample of what's left, so you're not cherry-picking
"""
import random
import time
from collections import defaultdict
from datetime import timedelta

import config
from common import (KALSHI_BASE, QUESTION_FIELDS, append_csv, get_json, iso,
                    now_utc, parse_time, read_csv)


def fetch_open_markets():
    markets, cursor = [], None
    for page in range(config.MAX_PAGES):
        params = {"status": "open", "limit": 1000, "mve_filter": "exclude"}
        if cursor:
            params["cursor"] = cursor
        data = get_json(f"{KALSHI_BASE}/markets", params)
        markets.extend(data.get("markets", []))
        cursor = data.get("cursor")
        if not cursor:
            break
        time.sleep(0.5)  # be polite to Kalshi's public API
    print(f"Fetched {len(markets)} open markets")
    return markets


def to_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def eligible(m, now):
    if m.get("market_type") != "binary" or not m.get("rules_primary"):
        return None
    resolves = parse_time(m.get("expected_expiration_time") or m.get("close_time"))
    if resolves is None:
        return None
    days = (resolves - now).total_seconds() / 86400
    if not (config.MIN_DAYS_TO_RESOLVE <= days <= config.MAX_DAYS_TO_RESOLVE):
        return None
    bid, ask = to_float(m.get("yes_bid_dollars")), to_float(m.get("yes_ask_dollars"))
    vol = to_float(m.get("volume_fp")) or 0
    if bid is None or ask is None or bid <= 0 or ask >= 1 or ask <= bid:
        return None
    if ask - bid > config.MAX_SPREAD or vol < config.MIN_VOLUME:
        return None
    return {
        "question_id": m["ticker"],
        "event_ticker": m["event_ticker"],
        "series": m["event_ticker"].split("-")[0],
        "collected_at": iso(now),
        "expected_resolution": iso(resolves),
        "close_time": m.get("close_time", ""),
        "title": m.get("title") or m.get("yes_sub_title") or "",
        "question": m["rules_primary"],
        "market_yes_bid": f"{bid:.4f}",
        "market_yes_ask": f"{ask:.4f}",
        "market_mid": f"{(bid + ask) / 2:.4f}",
        "volume": f"{vol:.0f}",
    }


def main():
    now = now_utc()
    existing = read_csv("questions.csv")
    seen_events = {q["event_ticker"] for q in existing}

    # one candidate per event: the most-traded market in that event
    by_event = {}
    for m in fetch_open_markets():
        row = eligible(m, now)
        if not row or row["event_ticker"] in seen_events:
            continue
        best = by_event.get(row["event_ticker"])
        if best is None or float(row["volume"]) > float(best["volume"]):
            by_event[row["event_ticker"]] = row

    candidates = list(by_event.values())
    random.Random(now.strftime("%Y-%m-%d")).shuffle(candidates)  # reproducible per day

    picked, per_series = [], defaultdict(int)
    for row in candidates:
        if per_series[row["series"]] >= config.MAX_PER_SERIES:
            continue
        per_series[row["series"]] += 1
        picked.append(row)
        if len(picked) >= config.QUESTIONS_PER_DAY:
            break

    append_csv("questions.csv", picked, QUESTION_FIELDS)
    print(f"{len(candidates)} eligible events; added {len(picked)} questions "
          f"from {len(per_series)} series")


if __name__ == "__main__":
    main()
