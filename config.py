"""Loads SARVAM_API_KEY from .env, and decides where mutable state lives.

No third-party deps: this module is imported before anything else is installed.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
PLACEHOLDER = "paste-your-key-here"


def data_dir() -> Path:
    """Where the database and uploads live.

    Locally that is the repo root, which is the whole point of the architecture:
    one process, one writer, one SQLite file that survives a restart — the case
    list rendering after `^C` IS the persistence proof.

    On a serverless host the filesystem is read-only apart from `/tmp`, so that is
    where state goes. Be clear about what that costs: `/tmp` is per-instance and
    does not outlive a cold start, so on Vercel the persistence proof degrades to
    "for as long as this instance lives". Honest for a demo; not a production
    posture, and not a defect in the design — ARCHITECTURE.md chose a single
    long-running process precisely to avoid it.

    `TITLECHAIN_DATA_DIR` overrides both, for tests and for a real host with a
    writable volume.
    """
    override = os.environ.get("TITLECHAIN_DATA_DIR")
    if override:
        target = Path(override)
    elif os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        target = Path("/tmp/titlechain")
    else:
        target = ROOT
    target.mkdir(parents=True, exist_ok=True)
    return target


def is_serverless() -> bool:
    return bool(os.environ.get("VERCEL")
                or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))


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
