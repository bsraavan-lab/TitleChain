"""Loads SARVAM_API_KEY from .env (no third-party deps)."""

import os
from pathlib import Path

ENV_PATH = Path(__file__).parent / ".env"
PLACEHOLDER = "paste-your-key-here"


def load_env(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def get_api_key() -> str:
    load_env()
    key = os.environ.get("SARVAM_API_KEY", "").strip()
    if not key or key == PLACEHOLDER:
        raise RuntimeError(
            f"SARVAM_API_KEY is not set. Add it to {ENV_PATH} or export it."
        )
    return key
