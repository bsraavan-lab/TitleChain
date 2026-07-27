"""Where mutable state lives.

Locally that is the repo root, which is what every path in this project assumed
until it had to run somewhere the code directory is not writable. One env var —
TITLECHAIN_DATA_DIR — moves all three writable locations at once: the SQLite
file, uploads/, and the stage-① cache in output/. Unset, nothing changes.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("TITLECHAIN_DATA_DIR") or ROOT).resolve()

DB_PATH = DATA_DIR / "titlechain.db"
UPLOADS = DATA_DIR / "uploads"
OUTPUT = DATA_DIR / "output"

SEED_OUTPUT = ROOT / "seed" / "output"


def ensure() -> None:
    """Idempotent. Runs at startup, before db.init()."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)


def seed_cache() -> list[str]:
    """Copy the bundled digitisations for the demo samples onto the data dir.

    A fresh deploy starts with an empty disk, and without this the two sample
    buttons would each trigger a live Sarvam job — slow, and against quota, to
    re-read a document we have already read. Never overwrites: a digitisation
    that is already on the disk is the real one and wins.
    """
    if not SEED_OUTPUT.is_dir():
        return []
    copied: list[str] = []
    for src in sorted(SEED_OUTPUT.iterdir()):
        if not src.is_dir():
            continue
        dest = OUTPUT / src.name
        if dest.exists():
            continue
        shutil.copytree(src, dest)
        copied.append(src.name)
    return copied
