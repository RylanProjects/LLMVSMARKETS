"""All study settings in one place. Change these BEFORE you start collecting data,
then leave them alone — changing them mid-study makes your data inconsistent.
If you must change the prompt, bump PROMPT_VERSION so old and new forecasts stay separable."""

# --- Question selection ---------------------------------------------------
QUESTIONS_PER_DAY = 18       # new questions added per daily run
MIN_DAYS_TO_RESOLVE = 1       # skip questions resolving sooner than this
MAX_DAYS_TO_RESOLVE = 60      # skip questions resolving later than this
MAX_SPREAD = 0.10             # skip markets whose bid/ask spread is wider (illiquid)
MIN_VOLUME = 100              # skip markets with fewer contracts traded
MAX_PER_SERIES = 3            # cap per market series per day, so one topic can't dominate
MAX_PAGES = 30                # pages of 1000 markets to scan from Kalshi

# --- Forecasters -------------------------------------------------------------
# provider -> (OpenAI-compatible chat endpoint, env var holding the API key)
PROVIDERS = {
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "GEMINI_API_KEY"),
    "groq": ("https://api.groq.com/openai/v1/chat/completions", "GROQ_API_KEY"),
}

# Free-tier model IDs change over time. Run `python check_models.py` to see what's
# currently available, and edit this list before your first real run.
# seconds_between_calls keeps you under each free tier's per-minute limit.
MODELS = [
    {"provider": "gemini", "model": "gemini-3.5-flash-lite", "seconds_between_calls": 5},
    {"provider": "groq", "model": "openai/gpt-oss-120b", "seconds_between_calls": 12},
    {"provider": "groq", "model": "openai/gpt-oss-20b", "seconds_between_calls": 4},
    {"provider": "groq", "model": "qwen/qwen3.8-27b", "seconds_between_calls": 15},
]
MAX_MINUTES_PER_MODEL = 10
]

# Forecast a question only if it was collected within this many hours,
# so the LLM forecast and the market price snapshot are close in time.
MAX_FORECAST_LAG_HOURS = 6

PROMPT_VERSION = "v1"
MAX_TOKENS = 2048
