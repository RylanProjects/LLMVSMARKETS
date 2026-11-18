# Pre-Registered Analysis Plan

**Study:** Do free large language models forecast real-world events as accurately as Kalshi prediction-market prices?

**Plan committed:** November 17th 2026 — before any question had resolved with forecasts attached.


---

## 1. Research questions

**Primary question (RQ1):** For each LLM, is its Brier score lower or higher than the Kalshi market's Brier score on the same questions?

Secondary questions:
- **RQ2: Calibration.** When each forecaster says X%, does the event happen about X% of the time?
- **RQ3: Category.** Does the LLM–market gap differ between sports, weather, economics/finance, politics and other questions?
- **RQ4: Time horizon.** Does the gap change with how far in advance the question was asked?
- **RQ5: Model size.** Does gpt-oss-120b forecast better than gpt-oss-20b?
- **RQ6: Added information.** Does averaging an LLM's forecast with the market price beat the market price alone?

**Expectation (stated in advance):** the market will have a lower Brier score than every LLM overall. LLMs may be closer to the market on questions further in the future than on near-term sports and weather questions.

## 2. Data collection (already running)

- **Source:** Kalshi public API, collected daily by GitHub Actions; all data is in `data/` with git timestamps.
- **Start:** November 16, 2026.
- **End:** questions collected through **December 6th, 2026**. Outcomes recorded until **December 16th, 2026]**, then the data is frozen and analyzed.
- **Question selection:** binary markets resolving 1–60 days out, bid/ask spread ≤ $0.10, volume ≥ 100 contracts, at most one market per event and three per series per day, randomly sampled. See `config.py` and `collect_markets.py`.
- **Market forecast:** midpoint of the yes bid and ask at collection time.
- **LLM forecasts:** one prompt (`PROMPT_VERSION = v1`, see `forecast.py`); the model is **not** shown the market price. Forecasts are made within 6 hours of collection.
- **Models:** `gemini-3.8-flash`, `gemini-3.5-flash-lite`, `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`.

### Changes already made
- Nov 16 (first run): 30 questions; `llama-3.3-70b-versatile` was in the lineup but had been retired by Groq and returned errors, so it is excluded.
- Nov 17: questions per day lowered from 30 to 18 to fit Gemini 3.8 Flash's free daily limit; forecast window lowered from 24 h to 6 h; Groq models changed to the current lineup. The prompt did not change.
- Any further changes will be added to this list with a date.

## 3. Data rules

- **Voided markets** (no clean YES/NO result) are excluded.
- **Unparseable answers** (no probability found) are excluded from that model's scores in the primary analysis. As a sensitivity check, they are also scored as 0.5. The failure rate for each model is reported.
- **Probabilities** are clipped to [0.01, 0.99] for log loss only.
- **Fair comparisons:** each model is compared with the market **only on questions that model answered**, so missing forecasts can't help or hurt it.
- **Minimum sample:** a model with fewer than 100 resolved forecasts is reported descriptively only, with no significance claims. The target is 300+ per model.

## 4. Analyses

**Primary metric:** Brier score (mean squared error of the probability vs. the 0/1 outcome).
**Secondary metric:** log loss.

| Question | Analysis |
|---|---|
| RQ1 | For each model: mean Brier difference (LLM − market) with a 95% confidence interval from a bootstrap that resamples **collection days**, not individual questions (10,000 resamples), because questions from the same day are correlated. Holm correction across the models. |
| RQ2 | Calibration plot with 10 equal-width bins; expected calibration error (ECE). |
| RQ3 | Brier difference by category. Categories are assigned from the Kalshi series prefix using a fixed lookup written **before** looking at outcomes. |
| RQ4 | Brier difference by horizon: 1–3 days, 4–14 days, 15–60 days. |
| RQ5 | Paired Brier difference between gpt-oss-120b and gpt-oss-20b on questions both answered, with the same day-level bootstrap. |
| RQ6 | Brier score of a 50/50 average of each LLM and the market, compared with the market alone. |

**Case studies:** 3–5 questions with the largest LLM–market disagreement, described qualitatively.

## 5. What counts as a result

- An LLM **beats** the market only if the 95% CI of (LLM − market) Brier lies entirely below 0 after correction.
- The market **beats** an LLM if the CI lies entirely above 0.
- Otherwise, the result is **inconclusive**, and the paper says so.

## 6. Known limitations

Mostly sports and weather markets; free models only; one prompt; models have no internet access while the market reflects live information; about two months of data.
