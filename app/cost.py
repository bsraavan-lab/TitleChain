"""What a case cost, estimated before and actual after.

Two audiences, and neither is the advocate: whoever prices this product, and anyone
asking what a case costs to run. She is not paying per case and it is not her
decision, so this lives behind the last tab and the advocate-facing surfaces never
mention money.

**The honesty rule, and it is the whole design of this module.** Sarvam's pricing
surface reports billing UNITS per model — Document Intelligence per page, 105B and
30B per million tokens, transliteration per character — but says the exact per-unit
rate depends on the plan. So if `rates.yml` is absent or a rate is unset, this
module returns units and no rupee figure at all. A cost panel that filled its total
column with a rate somebody guessed would be the one fabrication in a codebase that
refuses them everywhere else.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from . import db

RATES_PATH = Path(__file__).resolve().parent.parent / "config" / "rates.yml"

# Stage → (label, the unit it is billed in). The units are Sarvam's; the rates are
# the operator's.
STAGES: dict[str, tuple[str, str]] = {
    "digitise":      ("Document Intelligence", "page"),
    "header":        ("Header typing", "1M tokens"),
    "entries":       ("Entry typing", "1M tokens"),
    "transliterate": ("Transliteration", "character"),
}
STAGE_ORDER = ["digitise", "header", "entries", "transliterate"]

# Fallback medians, used only for the ESTIMATE and only when this machine has no
# history to measure. Derived from the three staged sample certificates, and
# labelled as such wherever they are used — an estimate that does not say what it
# is based on is a guess wearing a suit.
SEED_TOKENS_PER_PAGE = {"header": 3_000, "entries": 11_000}
SEED_CALLS_PER_PAGE = 2.6


@dataclass
class RateCard:
    """Loaded from config/rates.yml. `configured` is false until the operator puts
    real numbers in it, and every rupee column checks that flag."""
    source: Optional[str] = None
    retrieved: Optional[str] = None
    currency: str = "INR"
    per_page: dict[str, float] = field(default_factory=dict)
    per_million_tokens: dict[str, dict[str, float]] = field(default_factory=dict)
    per_character: dict[str, float] = field(default_factory=dict)

    @property
    def configured(self) -> bool:
        return bool(self.per_page or self.per_million_tokens or self.per_character)


def load_rates(path: Path = RATES_PATH) -> RateCard:
    if not path.is_file():
        return RateCard()
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return RateCard()             # a malformed rate card is an unset one
    return RateCard(
        source=raw.get("source"), retrieved=str(raw.get("retrieved") or "") or None,
        currency=raw.get("currency", "INR"),
        per_page={k: float(v) for k, v in (raw.get("per_page") or {}).items()
                  if isinstance(v, (int, float))},
        per_million_tokens={
            model: {k: float(v) for k, v in (vals or {}).items()
                    if isinstance(v, (int, float))}
            for model, vals in (raw.get("per_million_tokens") or {}).items()},
        per_character={k: float(v) for k, v in (raw.get("per_character") or {}).items()
                       if isinstance(v, (int, float))},
    )


@dataclass
class Line:
    stage: str
    label: str
    unit: str
    models: list[str] = field(default_factory=list)
    calls: int = 0
    cached_calls: int = 0
    pages: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    chars: int = 0
    ms: int = 0
    amount: Optional[float] = None       # None → no rate configured for it
    cached_saving: Optional[float] = None

    @property
    def tokens(self) -> int:
        return self.tokens_in + self.tokens_out

    @property
    def quantity(self) -> str:
        if self.stage == "digitise":
            return f"{self.pages} page{'' if self.pages == 1 else 's'}"
        if self.stage == "transliterate":
            return f"{self.chars:,} chars"
        return f"{self.tokens:,} tokens"

    @property
    def ran(self) -> bool:
        return self.calls > 0


@dataclass
class Report:
    lines: list[Line]
    total: Optional[float]
    cached_saving: Optional[float]
    calls: int
    cached_calls: int
    pages: int
    tokens: int
    wall_ms: int
    rates: RateCard
    basis: str                            # what the estimate was computed from
    estimated: bool = False

    @property
    def priced(self) -> bool:
        return self.rates.configured and self.total is not None


def _price(line: Line, rates: RateCard) -> Optional[float]:
    if line.stage == "digitise":
        rate = rates.per_page.get("document-intelligence")
        return None if rate is None else round(line.pages * rate, 4)
    if line.stage == "transliterate":
        rate = rates.per_character.get("mayura") or rates.per_character.get("default")
        return None if rate is None else round(line.chars * rate, 4)
    # token stages are billed per model, so an unpriced model makes the line unpriced
    total = 0.0
    for model in line.models:
        band = rates.per_million_tokens.get(model)
        if not band:
            return None
        rows = db_rows_cache.get((line.stage, model))
        if rows is None:
            return None
        tin = sum(r["tokens_in"] for r in rows)
        tout = sum(r["tokens_out"] for r in rows)
        total += (tin / 1e6) * band.get("input", 0.0)
        total += (tout / 1e6) * band.get("output", 0.0)
    return round(total, 4)


db_rows_cache: dict[tuple[str, str], list[dict]] = {}


def actual(case_id: int, rates: RateCard | None = None) -> Report:
    """What this case really cost, from the ledger. Retries included — the
    truncation ladder in extract.py is the real per-case cost driver, and hiding it
    would make the panel a brochure."""
    rates = rates or load_rates()
    rows = db.q("SELECT * FROM api_calls WHERE case_id = ? ORDER BY id", (case_id,))

    db_rows_cache.clear()
    for r in rows:
        db_rows_cache.setdefault((r["stage"], r["model"] or ""), []).append(r)

    lines: list[Line] = []
    for stage in STAGE_ORDER:
        label, unit = STAGES[stage]
        mine = [r for r in rows if r["stage"] == stage]
        line = Line(stage=stage, label=label, unit=unit,
                    models=sorted({r["model"] or "" for r in mine}),
                    calls=len(mine),
                    cached_calls=sum(1 for r in mine if r["cached"]),
                    pages=sum(r["pages"] or 0 for r in mine),
                    tokens_in=sum(r["tokens_in"] or 0 for r in mine),
                    tokens_out=sum(r["tokens_out"] or 0 for r in mine),
                    chars=sum(r["chars"] or 0 for r in mine),
                    ms=sum(r["ms"] or 0 for r in mine))
        if line.ran and rates.configured:
            line.amount = _price(line, rates)
            # A cache hit costs nothing. What it WOULD have cost is the most
            # interesting number on the panel, so it is computed too.
            if line.cached_calls and line.stage == "digitise":
                rate = rates.per_page.get("document-intelligence")
                if rate is not None:
                    cached_pages = sum(r["pages"] or 0 for r in mine if r["cached"])
                    line.cached_saving = round(cached_pages * rate, 4)
                    line.amount = round(max(line.amount - line.cached_saving, 0.0), 4)
        lines.append(line)

    priced = [ln.amount for ln in lines if ln.amount is not None]
    savings = [ln.cached_saving for ln in lines if ln.cached_saving is not None]
    return Report(
        lines=lines,
        total=round(sum(priced), 4) if priced and rates.configured else None,
        cached_saving=round(sum(savings), 4) if savings else None,
        calls=len(rows), cached_calls=sum(1 for r in rows if r["cached"]),
        pages=sum(r["pages"] or 0 for r in rows),
        tokens=sum((r["tokens_in"] or 0) + (r["tokens_out"] or 0) for r in rows),
        wall_ms=sum(r["ms"] or 0 for r in rows), rates=rates,
        basis="the ledger for this case")


def estimate(pages: int, rates: RateCard | None = None) -> Report:
    """Before processing: page count is the only input we have.

    Token medians come from this machine's own history when it has any, and from
    the staged samples when it does not. Which one was used is reported, because an
    estimate that does not say what it is based on is a guess wearing a suit.
    """
    rates = rates or load_rates()
    pages = max(pages, 1)

    history = db.one(
        "SELECT SUM(tokens_in) ti, SUM(tokens_out) tou, COUNT(*) n, "
        "       COUNT(DISTINCT case_id) cases "
        "FROM api_calls WHERE stage IN ('header','entries') AND cached = 0")
    seen_pages = db.one("SELECT SUM(pages) p FROM api_calls WHERE stage = 'digitise'")
    tokens_per_page: dict[str, float] = dict(SEED_TOKENS_PER_PAGE)
    basis = "medians from the staged sample certificates"
    calls_per_page = SEED_CALLS_PER_PAGE

    if history and (history["n"] or 0) >= 4 and (seen_pages or {}).get("p"):
        per_page = ((history["ti"] or 0) + (history["tou"] or 0)) / seen_pages["p"]
        tokens_per_page = {"header": per_page * 0.2, "entries": per_page * 0.8}
        calls_per_page = (history["n"] or 0) / seen_pages["p"]
        basis = (f"measured medians over {history['cases']} case"
                 f"{'' if history['cases'] == 1 else 's'} on this machine")

    lines: list[Line] = []
    for stage in STAGE_ORDER:
        label, unit = STAGES[stage]
        line = Line(stage=stage, label=label, unit=unit)
        if stage == "digitise":
            line.pages, line.calls = pages, max(1, (pages + 9) // 10)
            line.models = ["document-intelligence"]
        elif stage in tokens_per_page:
            total = int(tokens_per_page[stage] * pages)
            line.tokens_in = int(total * 0.75)
            line.tokens_out = total - line.tokens_in
            line.calls = max(1, round(calls_per_page * pages
                                      * (0.15 if stage == "header" else 0.85)))
            line.models = ["sarvam-105b"]
        lines.append(line)

    if rates.configured:
        db_rows_cache.clear()
        for ln in lines:
            for model in ln.models:
                db_rows_cache[(ln.stage, model)] = [
                    {"tokens_in": ln.tokens_in, "tokens_out": ln.tokens_out}]
            if ln.ran:
                ln.amount = _price(ln, rates)

    priced = [ln.amount for ln in lines if ln.amount is not None]
    return Report(
        lines=lines, total=round(sum(priced), 4) if priced else None,
        cached_saving=None,
        calls=sum(ln.calls for ln in lines), cached_calls=0, pages=pages,
        tokens=sum(ln.tokens for ln in lines), wall_ms=0, rates=rates,
        basis=basis, estimated=True)
