"""List the model IDs your API keys can currently use, so you can update config.MODELS."""
import os

import requests

import config

for provider, (chat_url, key_env) in config.PROVIDERS.items():
    key = os.environ.get(key_env)
    if not key:
        print(f"{provider}: {key_env} not set\n")
        continue
    url = chat_url.replace("/chat/completions", "/models")
    r = requests.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=30)
    if not r.ok:
        print(f"{provider}: HTTP {r.status_code} {r.text[:200]}\n")
        continue
    ids = sorted(m["id"] for m in r.json().get("data", []))
    print(f"{provider} ({len(ids)} models):")
    for i in ids:
        print("  ", i)
    print()
