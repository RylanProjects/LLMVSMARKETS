# LLMs vs. Prediction Markets

Do free LLMs forecast real-world events as well as Kalshi's market prices?

Every day this repo automatically:
1. **Collects** ~30 new open Kalshi markets and snapshots their prices (`collect_markets.py`)
2. **Asks** several LLMs for a probability on each one, *without* showing them the price (`forecast.py`)
3. **Records** outcomes for markets that have settled (`resolve.py`)
4. **Scores** each LLM against the market on the same questions: Brier score, log loss, calibration plot (`analyze.py`)

Each forecast is committed to git with a timestamp **before** its question resolves, so anyone can verify the results weren't made with hindsight.

Total cost: $0. It uses Kalshi's free public API, free Gemini and Groq API tiers, and free GitHub Actions on a public repo.

## Setup (about 15 minutes)

1. **Get free API keys** (no credit card needed)
   - Gemini: https://aistudio.google.com → "Get API key"
   - Groq: https://console.groq.com → "API Keys"

2. **Create a public GitHub repo** and upload everything in this folder, including the hidden `.github` folder.

3. **Add your keys as secrets**: repo → Settings → Secrets and variables → Actions → New repository secret
   - `GEMINI_API_KEY`
   - `GROQ_API_KEY`

4. **Allow the workflow to push**: Settings → Actions → General → Workflow permissions → "Read and write permissions".

5. **Check the model names.** Free models change often. On your own computer:
   ```bash
   pip install -r requirements.txt
   export GEMINI_API_KEY=...   # Windows PowerShell: $env:GEMINI_API_KEY="..."
   export GROQ_API_KEY=...
   python check_models.py
   ```
   Then edit `MODELS` in `config.py` to use IDs that appear in that list.

6. **Test it**: in the repo, go to Actions → daily-forecasts → "Run workflow". After it runs, `data/` should contain new CSVs. From then on it runs every day by itself.

## Data files (append-only — never edit old rows)

| file | one row per |
|---|---|
| `data/questions.csv` | question, with market price at collection time |
| `data/forecasts.csv` | (question, model) forecast, with timestamp and the model's raw answer |
| `data/resolutions.csv` | settled question (yes/no) |

A forecast with an empty `probability` means the model's answer couldn't be parsed. Keep those rows: the failure rate is a result too.

## Research rules

- **Don't change `config.py` mid-study.** If you change the prompt, bump `PROMPT_VERSION`. The analysis reports each version separately.
- Questions are chosen randomly among liquid markets, with at most one per event and a few per series, so the sample isn't cherry-picked.
- Look at `analyze.py` output only after a few hundred questions have resolved. Before that, the confidence intervals will be too wide to support conclusions.
- Markets settled as void or 50/50 are excluded. Mention this in your writeup.

## Ideas for the paper

- Results split by category: sports vs. weather vs. economics vs. politics (use the `series` column)
- Results by time to resolution: are LLMs relatively better on longer-horizon questions?
- Questions about events after a model's training cutoff vs. before it
- A second prompt version that *does* show the market price: can the LLM improve on it?
