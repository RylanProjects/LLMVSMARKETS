"""Step 4: score each LLM against the market on the same resolved questions.

Prints Brier score and log loss (lower = better) for each model next to the market's
score on the exact same questions, plus a 95% bootstrap confidence interval for the
difference. Saves a calibration plot to plots/calibration.png.
"""
import math
import os
import random
from collections import defaultdict

from common import ROOT, read_csv

EPS = 0.01  # clip probabilities so one 0% / 100% miss doesn't make log loss infinite


def brier(p, y):
    return (p - y) ** 2


def logloss(p, y):
    p = min(max(p, EPS), 1 - EPS)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def bootstrap_ci(diffs, n=2000, seed=0):
    rng = random.Random(seed)
    means = sorted(sum(rng.choices(diffs, k=len(diffs))) / len(diffs) for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n)]


def load():
    questions = {q["question_id"]: q for q in read_csv("questions.csv")}
    outcomes = {r["question_id"]: 1 if r["result"] == "yes" else 0 for r in read_csv("resolutions.csv")}
    by_model = defaultdict(dict)  # model -> question_id -> prob
    for f in read_csv("forecasts.csv"):
        if f["probability"] and f["question_id"] in outcomes:
            by_model[f"{f['model']} ({f['prompt_version']})"][f["question_id"]] = float(f["probability"])
    return questions, outcomes, by_model


def main():
    questions, outcomes, by_model = load()
    print(f"{len(questions)} questions collected, {len(outcomes)} resolved\n")
    if not by_model:
        print("No resolved questions with forecasts yet — check back after some markets settle.")
        return

    header = f"{'forecaster':38} {'n':>4} {'Brier':>7} {'mkt':>7} {'diff [95% CI]':>24} {'LogLoss':>8} {'mkt':>7}"
    print(header)
    print("-" * len(header))
    curves = {}
    for model, probs in sorted(by_model.items()):
        ids = list(probs)
        y = [outcomes[i] for i in ids]
        p_llm = [probs[i] for i in ids]
        p_mkt = [float(questions[i]["market_mid"]) for i in ids]
        b_llm = [brier(p, t) for p, t in zip(p_llm, y)]
        b_mkt = [brier(p, t) for p, t in zip(p_mkt, y)]
        diffs = [a - b for a, b in zip(b_llm, b_mkt)]
        lo, hi = bootstrap_ci(diffs)
        n = len(ids)
        print(f"{model:38} {n:4d} {sum(b_llm)/n:7.4f} {sum(b_mkt)/n:7.4f} "
              f"{sum(diffs)/n:+8.4f} [{lo:+.3f},{hi:+.3f}] "
              f"{sum(logloss(p, t) for p, t in zip(p_llm, y))/n:8.4f} "
              f"{sum(logloss(p, t) for p, t in zip(p_mkt, y))/n:7.4f}")
        curves[model] = (p_llm, y)
    # market curve on every resolved question
    mk = [(float(questions[i]["market_mid"]), y) for i, y in outcomes.items() if i in questions]
    curves["market"] = ([p for p, _ in mk], [y for _, y in mk])
    print("\nNegative diff = LLM beat the market. If the CI includes 0, the gap isn't significant yet.")
    plot_calibration(curves)


def plot_calibration(curves, bins=10):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("(install matplotlib for the calibration plot)")
        return
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot([0, 1], [0, 1], color="#999", linestyle="--", linewidth=1, label="perfect calibration")
    for name, (ps, ys) in curves.items():
        buckets = defaultdict(list)
        for p, y in zip(ps, ys):
            buckets[min(int(p * bins), bins - 1)].append((p, y))
        xs = [sum(p for p, _ in b) / len(b) for _, b in sorted(buckets.items())]
        obs = [sum(y for _, y in b) / len(b) for _, b in sorted(buckets.items())]
        ax.plot(xs, obs, marker="o", linewidth=2 if name == "market" else 1.5,
                color="black" if name == "market" else None, label=f"{name} (n={len(ps)})")
    ax.set_xlabel("Forecast probability")
    ax.set_ylabel("Fraction that resolved YES")
    ax.set_title("Calibration: LLMs vs. Kalshi market")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(fontsize=8, loc="upper left")
    os.makedirs(os.path.join(ROOT, "plots"), exist_ok=True)
    out = os.path.join(ROOT, "plots", "calibration.png")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
