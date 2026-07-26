"""Pydantic v2 — the PRD §10.4 extraction schema, written once.

Three uses (STACK.md): Entry.model_json_schema() becomes the `response_format`
sent to sarvam-105b; Entry.model_validate() checks the reply; the same classes
type derive(), the rules and the Jinja template context.

Every extracted field is Optional with NO default, so a model that quietly omits
a field fails validation loudly instead of producing a half-entry. Honest nulls
are load-bearing (PIPELINE §②) — the type system enforces them, not the prompt.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

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

# ─── rule outcomes ────────────────────────────────────────────────────────────
# Five, not three. The two the checklist cannot go without are NOT_APPLICABLE
# ("ran; this case has no inputs of the kind it checks") and NOT_EVALUABLE
# ("could not run — the inputs it needs were not readable"). Without them a rule
# that never ran is indistinguishable from a rule that passed, which is the same
# defect the refusal screen already refuses to commit: never claim a check you
# did not make.
RuleOutcome = Literal["FAIL", "REVIEW", "PASS", "NOT_APPLICABLE", "NOT_EVALUABLE"]

OUTCOME_UI: dict[str, dict[str, str]] = {
    "FAIL":           {"word": "Failed", "glyph": "✕", "cls": "out-fail"},
    "REVIEW":         {"word": "Needs review", "glyph": "⚠", "cls": "out-review"},
    "PASS":           {"word": "Passed", "glyph": "✓", "cls": "out-pass"},
    "NOT_EVALUABLE":  {"word": "Could not check", "glyph": "⚠", "cls": "out-unknown"},
    "NOT_APPLICABLE": {"word": "Not applicable", "glyph": "—", "cls": "out-na"},
}
# Worst first. NOT_EVALUABLE ranks above PASS deliberately: "we could not check
# this" is an open item for the advocate, not a clean result.
OUTCOME_ORDER = ["FAIL", "REVIEW", "NOT_EVALUABLE", "PASS", "NOT_APPLICABLE"]

# Outcomes that count as an open obligation on the case.
OPEN_OUTCOMES = ("FAIL", "REVIEW", "NOT_EVALUABLE")


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
    key: str = ""                      # the RuleRun that produced it — see RuleRun.key

    @property
    def ui(self) -> dict[str, str]:
        return SEVERITY_UI[self.severity]


class PageRef(BaseModel):
    """Where to jump when a finding has no entry to anchor on — an R3 window is
    read off the header, which is not an entry."""
    ec_id: Optional[int]
    page_num: int


class RuleInput(BaseModel):
    """One value a rule read, so the checklist can show its working. The rule
    already knows these; it simply never reported them."""
    label: str
    value: str
    source_entry_id: Optional[int] = None


class RuleRun(BaseModel):
    """One rule, evaluated against one subject. Emitted for EVERY rule on every
    derivation — including the ones that did not fire and the ones that could not
    run — because a checklist that shows nine items on one case and four on
    another teaches the reader that absence means 'fine'.
    """
    rule_id: str
    key: str                            # subject-scoped; stable across re-derivation
    outcome: RuleOutcome
    title: str                          # the collapsed row
    message: str                        # the sentence, in her language
    reason: Optional[str] = None        # mandatory when nothing was concluded
    severity: Optional[Severity] = None # set → this run also surfaces as a Finding
    inputs: list[RuleInput] = Field(default_factory=list)
    evidence_entry_ids: list[int] = Field(default_factory=list)
    pages: list[PageRef] = Field(default_factory=list)
    implemented: bool = True            # False → "not in rulebook v1.0", grouped in the UI
    rulebook_version: str = "v1.0"

    @model_validator(mode="after")
    def _reason_required_when_nothing_was_concluded(self) -> "RuleRun":
        if self.outcome in ("NOT_APPLICABLE", "NOT_EVALUABLE") and not self.reason:
            raise ValueError(
                f"{self.rule_id}: outcome {self.outcome} must carry a reason — "
                f"a check that did not run has to say why")
        return self

    @property
    def ui(self) -> dict[str, str]:
        return OUTCOME_UI[self.outcome]

    @property
    def is_open(self) -> bool:
        return self.outcome in OPEN_OUTCOMES

    @property
    def as_finding(self) -> Optional[Finding]:
        """A run becomes a Finding only when it carries a severity. Runs that
        concluded nothing do not enter the findings list — they are checklist rows
        and report rows, and calling them findings would inflate the count."""
        if self.severity is None:
            return None
        return Finding(rule_id=self.rule_id, severity=self.severity,
                       message=self.message,
                       evidence_entry_ids=self.evidence_entry_ids,
                       rulebook_version=self.rulebook_version, key=self.key)


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


class CoverageBand(BaseModel):
    """One certificate's own window, drawn on the shared ruler. A case with three
    certificates has three bands and the gaps between them are the argument."""
    label: str
    start_year: Optional[int]
    end_year: Optional[int]
    ec_id: Optional[int] = None


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
    bands: list[CoverageBand] = Field(default_factory=list)
    required_from: Optional[int] = None   # the 13-year obligation, drawn as a rule
    required_to: Optional[int] = None

    def pct(self, year: int) -> float:
        span = max(self.axis_max - self.axis_min, 1)
        return round(min(max((year - self.axis_min) / span * 100, 0.0), 100.0), 2)

    def left_of(self, band: CoverageBand) -> float:
        return self.pct(band.start_year) if band.start_year else 0.0

    def width_of(self, band: CoverageBand) -> float:
        if not (band.start_year and band.end_year):
            return 0.0
        return max(self.pct(band.end_year) - self.pct(band.start_year), 1.5)

    @property
    def band_left(self) -> float:
        return self.pct(self.start_year) if self.start_year else 0.0

    @property
    def band_width(self) -> float:
        if not (self.start_year and self.end_year):
            return 0.0
        return max(self.pct(self.end_year) - self.pct(self.start_year), 1.5)


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


class DocumentRequest(BaseModel):
    """A hole in the chain, stated as something you can actually order.

    Derived, never stored — a pure function of the current findings, exactly like
    OrderBlock. Nothing to keep in sync and nothing to garbage-collect when a
    correction makes a request unnecessary.
    """
    key: str                            # == the finding_key that generated it
    kind: Literal["EC_FOR_RANGE", "CERTIFIED_COPY"]
    because: str
    closes: list[str] = Field(default_factory=list)
    sro: Optional[str] = None
    village: Optional[str] = None
    survey_nos: list[str] = Field(default_factory=list)
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    doc_no: Optional[str] = None
    # A parent document that the certificate in another request would also examine.
    # This is what stops the app telling her to order six documents when one EC
    # covers five of them.
    superseded_by: Optional[str] = None
    alternative: Optional[str] = None

    @property
    def title(self) -> str:
        if self.kind == "CERTIFIED_COPY":
            return f"Certified copy · document {self.doc_no}"
        return (f"Encumbrance Certificate · {self.sro or '—'} SRO · "
                f"{self.village or '—'}")

    @property
    def as_text(self) -> str:
        if self.kind == "CERTIFIED_COPY":
            return (f"Certified copy request\n"
                    f"Document: {self.doc_no}\n"
                    f"SRO: {self.sro or '—'}\n"
                    f"Village: {self.village or '—'}\n")
        return (f"Encumbrance Certificate request\n"
                f"SRO: {self.sro or '—'}\n"
                f"Village: {self.village or '—'}\n"
                f"Survey numbers: {', '.join(self.survey_nos) or '—'}\n"
                f"Period: {self.date_from or '—'} to {self.date_to or '—'}\n")


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


class ECDoc(BaseModel):
    """One certificate on a case. A case is plural by design from here on: the
    whole missing-document workflow is 'add another one of these'."""
    ec_id: Optional[int]
    label: str                          # EC-A, EC-B … the advocate's handle
    filename: Optional[str] = None
    header: ECHeader
    entries: list[Entry] = Field(default_factory=list)
    page_count: int = 0
    fulfils_request_key: Optional[str] = None

    @property
    def window(self) -> str:
        return (f"{self.header.search_period_start or '—'} → "
                f"{self.header.search_period_end or '—'}")


class Completeness(BaseModel):
    """Counts, not a score. Every figure below is a numerator over a denominator
    the advocate can check against the certificate in front of her — which is the
    only reason a percentage is allowed to exist in this product at all."""
    links_named: int = 0
    links_examined: int = 0
    span_from: Optional[int] = None
    span_to: Optional[int] = None
    years_required: int = 0
    years_covered: int = 0
    review_total: int = 0
    review_done: int = 0
    corrections: int = 0
    unread_pages: int = 0
    documents: int = 0
    requests_open: int = 0

    @property
    def chain_pct(self) -> int:
        if not self.links_named:
            return 100
        return round(self.links_examined / self.links_named * 100)

    @property
    def coverage_pct(self) -> int:
        if not self.years_required:
            return 0
        return round(self.years_covered / self.years_required * 100)

    @property
    def review_pct(self) -> int:
        if not self.review_total:
            return 100
        return round(self.review_done / self.review_total * 100)

    @property
    def chain_arithmetic(self) -> str:
        if not self.links_named:
            return "no parent document is named on this case"
        return (f"{self.links_examined} of {self.links_named} parent documents "
                f"examined")

    @property
    def coverage_arithmetic(self) -> str:
        if not self.years_required:
            return "no search window could be read"
        return (f"{self.years_covered} of {self.years_required} years covered "
                f"({self.span_from}–{self.span_to})")


class Gate(BaseModel):
    """One condition that must hold before an opinion can be signed."""
    id: str
    label: str            # what it says when unmet — "5 parent documents unexamined"
    passed: bool
    tab: str = "review"   # where the work of closing it happens


class Readiness(BaseModel):
    """Never a percentage. A file is signable or it is not, and when it is not the
    first unmet condition is named. There is no 82% of a signature."""
    gates: list[Gate] = Field(default_factory=list)

    @property
    def ready(self) -> bool:
        return all(g.passed for g in self.gates)

    @property
    def unmet(self) -> list[Gate]:
        return [g for g in self.gates if not g.passed]

    @property
    def label(self) -> str:
        """What the rail says. The gate chips beside it carry the detail, so the
        label does not repeat them — a pinned header that restates itself is a
        pinned header that is too tall."""
        return "Ready to opine" if self.ready else "Not ready to opine"

    @property
    def headline(self) -> str:
        """The prose form, for the report and the case list."""
        if self.ready:
            return "Ready to opine"
        return "Not ready to opine — " + ", ".join(g.label for g in self.unmet[:3])


class DerivedView(BaseModel):
    """Everything the case template needs. One object, one contract.

    `runs` is now the source of truth and `findings` is a view over it, so the
    report template and the rulebook tests keep the shape they already had while
    the checklist reads the fuller record.
    """
    coverage: Optional[Coverage] = None
    runs: list[RuleRun] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    chain: list[ChainNode] = Field(default_factory=list)
    order: Optional[OrderBlock] = None
    docs: list[ECDoc] = Field(default_factory=list)
    requests: list[DocumentRequest] = Field(default_factory=list)
    completeness: Completeness = Field(default_factory=Completeness)
    readiness: Readiness = Field(default_factory=Readiness)
    rulebook_version: str = "v1.0"

    @property
    def verdict(self) -> str:
        """The sentence in the rail — the worst true thing about this case.

        Coverage used to be it unconditionally, and that produced a contradiction
        the moment a second certificate closed the window gap: the rail read
        "every parent document falls inside a window it covers" while the gate line
        below said one blocking finding remained. A blocking finding outranks good
        news about coverage, always.
        """
        fails = [r for r in self.runs_ranked if r.outcome == "FAIL"]
        if fails:
            return fails[0].message
        if self.coverage:
            return self.coverage.headline
        return "No entries were read from this case."

    def closer_for(self, key: str) -> Optional[DocumentRequest]:
        """The document that would resolve this finding. A parent superseded by a
        broader certificate points at that certificate, so the checklist never
        tells her to order six things when one covers five of them."""
        matches = [r for r in self.requests if key in r.closes]
        return next((r for r in matches if not r.superseded_by),
                    matches[0] if matches else None)

    @property
    def requests_live(self) -> list[DocumentRequest]:
        """Requests worth acting on: a parent that a broader certificate would
        already examine is shown under that certificate, not as its own errand."""
        return [r for r in self.requests if not r.superseded_by]

    @property
    def entries(self) -> list[Entry]:
        return [e for d in self.docs for e in d.entries]

    def doc(self, ec_id: int | None) -> Optional[ECDoc]:
        return next((d for d in self.docs if d.ec_id == ec_id), None)

    def label_for(self, ec_id: int | None) -> str:
        d = self.doc(ec_id)
        return d.label if d else "this certificate"

    # ── findings: the subset of runs that concluded something ────────────────
    @property
    def findings(self) -> list[Finding]:
        order = {s: i for i, s in enumerate(SEVERITY_ORDER)}
        found = [f for f in (r.as_finding for r in self.runs) if f is not None]
        return sorted(found, key=lambda f: order[f.severity])

    def by_severity(self, sev: str) -> list[Finding]:
        return [f for f in self.findings if f.severity == sev]

    @property
    def counts(self) -> dict[str, int]:
        return {s: len(self.by_severity(s)) for s in SEVERITY_ORDER}

    # ── runs: the checklist ─────────────────────────────────────────────────
    @property
    def runs_ranked(self) -> list[RuleRun]:
        rank = {o: i for i, o in enumerate(OUTCOME_ORDER)}
        return sorted(self.runs, key=lambda r: (rank[r.outcome], r.rule_id, r.key))

    def by_outcome(self, outcome: str) -> list[RuleRun]:
        return [r for r in self.runs if r.outcome == outcome]

    @property
    def outcome_counts(self) -> dict[str, int]:
        return {o: len(self.by_outcome(o)) for o in OUTCOME_ORDER}

    @property
    def open_runs(self) -> list[RuleRun]:
        return [r for r in self.runs_ranked if r.is_open]

    def run(self, key: str) -> Optional[RuleRun]:
        return next((r for r in self.runs if r.key == key), None)
