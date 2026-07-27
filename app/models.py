"""Pydantic v2 — the PRD §10.4 extraction schema, written once.

Three uses (STACK.md): Entry.model_json_schema() becomes the `response_format`
sent to sarvam-105b; Entry.model_validate() checks the reply; the same classes
type derive(), the rules and the Jinja template context.

Every extracted field is Optional with NO default, so a model that quietly omits
a field fails validation loudly instead of producing a half-entry. Honest nulls
are load-bearing (PIPELINE §②) — the type system enforces them, not the prompt.
"""

from __future__ import annotations

from typing import ClassVar, Literal, Optional

from pydantic import BaseModel, Field

Severity = Literal["blocking", "material", "informational", "confirmation"]

# UI vocabulary. "blocking/material/informational" is our language and means
# nothing to an advocate. Colour is never the only carrier: glyph + word + colour.
SEVERITY_UI: dict[str, dict[str, str]] = {
    "blocking": {"word": "Resolve", "glyph": "▲", "cls": "sev-resolve"},
    "material": {"word": "Check", "glyph": "●", "cls": "sev-check"},
    "informational": {"word": "Note", "glyph": "⚑", "cls": "sev-note"},
    "confirmation": {"word": "Verified", "glyph": "✓", "cls": "sev-verified"},
}
SEVERITY_ORDER = ["blocking", "material", "informational", "confirmation"]


# ─── §10.4 extraction schema ──────────────────────────────────────────────────

class Party(BaseModel):
    name_native: str
    role_marker: Optional[str]
    name_roman: Optional[str] = None  # filled by names.py, not by the model


class PRNumber(BaseModel):
    doc_no: str
    year: int


class Schedule(BaseModel):
    property_type: Optional[str]
    extent: Optional[str]
    village_street: Optional[str]
    survey_nos: list[str] = Field(default_factory=list)
    door_no: Optional[str]
    boundaries_native: Optional[str]


class Source(BaseModel):
    page_num: int
    block_id: str
    bbox: Optional[list[float]] = None
    confidence: Optional[float] = None


class Entry(BaseModel):
    sr_no: int
    doc_no: Optional[str]
    doc_year: Optional[int]
    date_execution: Optional[str]
    date_presentation: Optional[str]
    date_registration: Optional[str]
    nature: Optional[str]
    executants: list[Party] = Field(default_factory=list)
    claimants: list[Party] = Field(default_factory=list)
    volume_page: Optional[str]
    consideration_value: Optional[str]
    market_value: Optional[str]
    pr_numbers: list[PRNumber] = Field(default_factory=list)
    remarks: Optional[str]
    schedules: list[Schedule] = Field(default_factory=list)
    source: Source

    # not extracted — assigned on persistence, used as the DOM/route id
    db_id: Optional[int] = None

    @property
    def doc_key(self) -> Optional[str]:
        return self.doc_no


class ECHeader(BaseModel):
    sro: Optional[str]
    village: Optional[str]
    survey_details: list[str] = Field(default_factory=list)
    search_period_start: Optional[str]
    search_period_end: Optional[str]
    issue_date: Optional[str]
    declared_entry_count: Optional[int]


# ─── derive() output — the template contract ─────────────────────────────────

class Finding(BaseModel):
    rule_id: str
    severity: Severity
    message: str
    evidence_entry_ids: list[int] = Field(default_factory=list)
    rulebook_version: str = "v1.0"

    @property
    def ui(self) -> dict[str, str]:
        return SEVERITY_UI[self.severity]


class Edge(BaseModel):
    """PR / cancel / succession. `resolved_entry_id is None` IS R4 DANGLING_PARENT."""
    from_entry_id: Optional[int]
    to_doc_no: str
    to_year: Optional[int]
    edge_type: Literal["PR_PARENT", "CANCELS", "SUCCESSION"]
    resolved_entry_id: Optional[int] = None
    label: Optional[str] = None


class Tick(BaseModel):
    """One mark on the coverage ruler."""
    year: int
    label: str
    inside: bool


class Coverage(BaseModel):
    """The 30-second answer. Rendered as a ruler, never as a score."""
    start_year: Optional[int]
    end_year: Optional[int]
    axis_min: int
    axis_max: int
    ticks: list[Tick] = Field(default_factory=list)
    sufficient: Optional[bool]          # None = not evaluable (blank window)
    headline: str
    detail: str

    def pct(self, year: int) -> float:
        span = max(self.axis_max - self.axis_min, 1)
        return round((year - self.axis_min) / span * 100, 2)

    @property
    def band_left(self) -> float:
        return self.pct(self.start_year) if self.start_year else 0.0

    @property
    def band_width(self) -> float:
        if not (self.start_year and self.end_year):
            return 0.0
        return max(self.pct(self.end_year) - self.pct(self.start_year), 1.5)

    # A band narrower than this cannot carry a label at each end: both are
    # translateX(-50%) from their edge, so at 1.5% they land on top of each other
    # and a one-month certificate drew its window as "202025". Below the
    # threshold the band gets ONE centred label instead — which loses nothing,
    # because the range is still stated in full in the sentence underneath.
    NARROW_BAND_PCT: ClassVar[float] = 8.0

    @property
    def band_is_narrow(self) -> bool:
        return self.band_width < self.NARROW_BAND_PCT

    @property
    def band_centre(self) -> float:
        return round(self.band_left + self.band_width / 2, 2)

    @property
    def band_label(self) -> str:
        """The whole window in one label, for a band too narrow to carry two."""
        if self.start_year == self.end_year:
            return str(self.start_year or "")
        return f"{self.start_year}–{self.end_year}"


class OrderBlock(BaseModel):
    """FR-10. The thing that converts bad news into an action."""
    sro: Optional[str]
    village: Optional[str]
    survey_nos: list[str] = Field(default_factory=list)
    date_from: Optional[str]
    date_to: Optional[str]

    @property
    def as_text(self) -> str:
        return (
            f"Encumbrance Certificate request\n"
            f"SRO: {self.sro or '—'}\n"
            f"Village: {self.village or '—'}\n"
            f"Survey numbers: {', '.join(self.survey_nos) or '—'}\n"
            f"Period: {self.date_from or '—'} to {self.date_to or '—'}\n"
        )


class ChainNode(BaseModel):
    doc_no: str
    year: Optional[int]
    nature: Optional[str]
    entry_id: Optional[int]      # None → unexamined, drawn as an open circle
    cancelled_by: Optional[str] = None
    children: list["ChainNode"] = Field(default_factory=list)

    @property
    def examined(self) -> bool:
        return self.entry_id is not None


class DerivedView(BaseModel):
    """Everything the case template needs. One object, one contract."""
    coverage: Optional[Coverage] = None
    findings: list[Finding] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    chain: list[ChainNode] = Field(default_factory=list)
    order: Optional[OrderBlock] = None
    rulebook_version: str = "v1.0"

    def by_severity(self, sev: str) -> list[Finding]:
        return [f for f in self.findings if f.severity == sev]

    @property
    def counts(self) -> dict[str, int]:
        return {s: len(self.by_severity(s)) for s in SEVERITY_ORDER}
