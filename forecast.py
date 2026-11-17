"""Step 2: ask each LLM for a probability on newly collected questions.

The model never sees the market price. Each forecast is timestamped and committed
to git before the question resolves — that's what makes the study credible.
"""
import os
import re
import sys
import time
from datetime import timedelta

import config
from common import (FORECAST_FIELDS, append_csv, iso, now_utc, parse_time,
                    post_json, read_csv)

SYSTEM = "You are a careful, well-calibrated forecaster."

PROMPT = """Today's date is {today} (UTC).

Estimate the probability that the following prediction market resolves YES.

Market: {title}
Resolution rules: {question}
Expected resolution date: {resolution}

Reason briefly, then end your answer with one final line in exactly this form:
PROBABILITY: <a number between 0 and 1>"""

PROB_RE = re.compile(r"PROBABILITY:\s*\**\s*([0-9]*\.?[0-9]+)\s*(%?)", re.IGNORECASE)


def parse_probability(text):
    matches = PROB_RE.findall(text or "")
    if not matches:
        return None
    num, pct = matches[-1]
    p = float(num)
    if pct or 1 < p <= 100:
        p /= 100
    return p if 0 <= p <= 1 else None


def ask(provider, model, question, now):
    url, key_env = config.PROVIDERS[provider]
    prompt = PROMPT.format(
        today=now.strftime("%Y-%m-%d"),
        title=question["title"],
        question=question["question"],
        resolution=question["expected_resolution"][:10],
    )
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": prompt}],
        "max_tokens": config.MAX_TOKENS,
    }
    headers = {"Authorization": f"Bearer {os.environ[key_env]}"}
    data = post_json(url, payload, headers)
    return data["choices"][0]["message"].get("content") or ""


def main():
    now = now_utc()
    questions = read_csv("questions.csv")
    done = {(f["question_id"], f["model"], f["prompt_version"]) for f in read_csv("forecasts.csv")}
    cutoff = now - timedelta(hours=config.MAX_FORECAST_LAG_HOURS)

    fresh = [q for q in questions
             if parse_time(q["collected_at"]) >= cutoff
             and parse_time(q["expected_resolution"]) > now]
    print(f"{len(fresh)} fresh questions to forecast")

    failures = 0
    for spec in config.MODELS:
        provider, model = spec["provider"], spec["model"]
        if not os.environ.get(config.PROVIDERS[provider][1]):
            print(f"Skipping {model}: {config.PROVIDERS[provider][1]} not set")
            continue
        todo = [q for q in fresh if (q["question_id"], model, config.PROMPT_VERSION) not in done]
        print(f"{model}: {len(todo)} to forecast")
        for q in todo:
            try:
                text = ask(provider, model, q, now)
            except Exception as e:  # keep going; one bad call shouldn't kill the run
                print(f"  {q['question_id']}: error {e}")
                failures += 1
                time.sleep(spec["seconds_between_calls"])
                continue
            p = parse_probability(text)
            append_csv("forecasts.csv", [{
                "question_id": q["question_id"],
                "provider": provider,
                "model": model,
                "prompt_version": config.PROMPT_VERSION,
                "forecast_at": iso(now_utc()),
                "probability": "" if p is None else f"{p:.4f}",
                "raw_response": text[-1500:],
            }], FORECAST_FIELDS)
            print(f"  {q['question_id']}: {p}")
            time.sleep(spec["seconds_between_calls"])

    if failures:
        print(f"{failures} calls failed (they'll be retried next run if still fresh)")


if __name__ == "__main__":
    main()
