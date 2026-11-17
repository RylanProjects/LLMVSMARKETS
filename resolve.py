"""Step 3: record YES/NO outcomes for questions that have settled on Kalshi."""
import time

from common import (KALSHI_BASE, RESOLUTION_FIELDS, append_csv, get_json, iso,
                    now_utc, read_csv)

CHUNK = 50  # tickers per request


def main():
    resolved = {r["question_id"] for r in read_csv("resolutions.csv")}
    pending = [q["question_id"] for q in read_csv("questions.csv") if q["question_id"] not in resolved]
    print(f"{len(pending)} unresolved questions to check")

    rows, now = [], iso(now_utc())
    for i in range(0, len(pending), CHUNK):
        chunk = pending[i:i + CHUNK]
        data = get_json(f"{KALSHI_BASE}/markets", {"tickers": ",".join(chunk)})
        for m in data.get("markets", []):
            # only clean binary outcomes; voided/scalar ($0.50) settlements are left out
            if m.get("result") in ("yes", "no"):
                rows.append({
                    "question_id": m["ticker"],
                    "result": m["result"],
                    "settled_at": m.get("settlement_ts") or "",
                    "checked_at": now,
                })
        time.sleep(0.5)  # be polite to Kalshi's public API

    append_csv("resolutions.csv", rows, RESOLUTION_FIELDS)
    print(f"Recorded {len(rows)} new resolutions")


if __name__ == "__main__":
    main()
