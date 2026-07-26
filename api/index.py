"""Vercel entry point. The ASGI app, unchanged, reached through one function.

Everything routes here (see vercel.json) — including /static, which FastAPI's own
StaticFiles mount serves. Slightly slower than Vercel's edge for assets, and worth
it: one code path, and the app behaves identically locally and deployed.
"""

from __future__ import annotations

import sys
from pathlib import Path

# The repo root, so `app.*` and the root-level `config` module both import.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402  — must follow the sys.path fix

__all__ = ["app"]
