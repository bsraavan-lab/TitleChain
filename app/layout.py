"""Graph geometry. Pure, deterministic, unit-testable — and no SVG in sight.

The rule this file exists to keep is the same one `derive.py` keeps: code decides,
templates render. So this module answers "where does each node go" and returns
numbers; `_graph_svg.html` turns those numbers into shapes and knows nothing about
title chains.

Two decisions worth stating, because they are what make the drawing readable:

  **x is the year, always.** Not a force-directed blob. The year axis is the whole
  reason a gap is visible at a glance, and it makes the graph and the coverage
  ruler read as the same picture rather than two unrelated diagrams.

  **y is a greedy lane, ties broken by document number.** So the drawing is
  byte-identical across runs — a graph that reshuffles when you reload is a graph
  nobody trusts, and it makes the layout untestable.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .derive import nature_kind
from .models import ECDoc, Edge, Entry

WIDTH = 940            # the drawing scrolls inside its own container
PAD_X = 66            # room for the outermost node's label, not just its shape
PAD_TOP = 46           # room for the year axis and its labels
PAD_BOTTOM = 30
LANE_H = 66
MIN_DX = 92            # horizontal room a node needs before sharing a lane
NODE_R = 12

# nature → the shape the template draws. Shape carries meaning as well as colour,
# so the graph survives being printed in grey or read by someone colour-blind.
SHAPES: dict[Optional[str], str] = {
    "transfer": "square",
    "encumbrance": "diamond",
    "lease": "bar",
    "cancellation": "slash",
    "discharge": "ring",
    None: "circle",
}


class GraphNode(BaseModel):
    doc_no: str
    year: Optional[int]
    nature: Optional[str]
    kind: Optional[str]                  # from the R2 nature taxonomy
    shape: str
    entry_id: Optional[int]
    ec_id: Optional[int]
    ec_label: Optional[str]
    x: float
    y: float
    examined: bool
    cancelled: bool = False
    corrected: bool = False
    open_encumbrance: bool = False

    @property
    def label(self) -> str:
        return self.doc_no

    @property
    def title(self) -> str:
        """The SVG tooltip — the accessible list below carries the same facts."""
        bits = [self.doc_no, self.nature or "not present on this case"]
        if self.ec_label:
            bits.append(self.ec_label)
        if self.cancelled:
            bits.append("cancelled")
        if self.open_encumbrance:
            bits.append("open encumbrance")
        if not self.examined:
            bits.append("unexamined")
        return " · ".join(bits)


class GraphEdge(BaseModel):
    kind: str                            # PR_PARENT | CANCELS
    resolved: bool
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def path(self) -> str:
        """A cubic curve, so two edges between the same lanes stay distinguishable
        and no edge is mistaken for the year axis."""
        mid = (self.x1 + self.x2) / 2
        return (f"M {self.x1:.1f} {self.y1:.1f} "
                f"C {mid:.1f} {self.y1:.1f} {mid:.1f} {self.y2:.1f} "
                f"{self.x2:.1f} {self.y2:.1f}")


class YearTick(BaseModel):
    year: int
    x: float


class GraphLayout(BaseModel):
    width: int = WIDTH
    height: int = 200
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    ticks: list[YearTick] = Field(default_factory=list)
    undated: list[str] = Field(default_factory=list)

    @property
    def empty(self) -> bool:
        return not self.nodes


def _year_of(doc_no: str) -> Optional[int]:
    tail = doc_no.rsplit("/", 1)[-1]
    return int(tail) if tail.isdigit() and len(tail) == 4 else None


def build_layout(docs: list[ECDoc], entries: list[Entry], edges: list[Edge], *,
                 corrected_entry_ids: set[int] | None = None,
                 open_encumbrance_docs: set[str] | None = None) -> GraphLayout:
    """One node per DOCUMENT, examined or not.

    A parent named but absent gets a node exactly like one we hold — drawn hollow.
    Omitting it would hide the hole, and the hole is the product.
    """
    corrected = corrected_entry_ids or set()
    open_enc = open_encumbrance_docs or set()
    ec_of = {e.db_id: d.ec_id for d in docs for e in d.entries}
    label_of = {d.ec_id: d.label for d in docs}

    cancelled_docs = {ed.to_doc_no for ed in edges
                      if ed.edge_type == "CANCELS" and ed.resolved_entry_id}

    # ── collect documents ────────────────────────────────────────────────────
    seen: dict[str, dict] = {}
    for e in entries:
        key = e.doc_no or f"entry {e.sr_no}"
        seen.setdefault(key, {
            "doc_no": key,
            "year": e.doc_year or (_year_of(key) if e.doc_no else None),
            "nature": e.nature, "entry_id": e.db_id,
            "ec_id": ec_of.get(e.db_id), "examined": True,
        })
    for ed in edges:
        if ed.edge_type != "PR_PARENT" or ed.resolved_entry_id is not None:
            continue
        seen.setdefault(ed.to_doc_no, {
            "doc_no": ed.to_doc_no, "year": ed.to_year or _year_of(ed.to_doc_no),
            "nature": None, "entry_id": None, "ec_id": None, "examined": False,
        })

    if not seen:
        return GraphLayout(height=120)

    dated = [d for d in seen.values() if d["year"]]
    undated = sorted(d["doc_no"] for d in seen.values() if not d["year"])
    years = [d["year"] for d in dated]
    ymin, ymax = (min(years), max(years)) if years else (0, 1)
    span = max(ymax - ymin, 1)
    inner = WIDTH - 2 * PAD_X

    def x_of(year: int) -> float:
        return round(PAD_X + (year - ymin) / span * inner, 1)

    # ── lanes: greedy, first-free, ties broken by document number ────────────
    ordered = sorted(dated, key=lambda d: (d["year"], d["doc_no"]))
    lane_last_x: list[float] = []
    placed: list[GraphNode] = []

    for d in ordered:
        x = x_of(d["year"])
        lane = next((i for i, last in enumerate(lane_last_x)
                     if x - last >= MIN_DX), len(lane_last_x))
        if lane == len(lane_last_x):
            lane_last_x.append(x)
        else:
            lane_last_x[lane] = x
        kind = nature_kind(d["nature"])
        placed.append(GraphNode(
            doc_no=d["doc_no"], year=d["year"], nature=d["nature"], kind=kind,
            shape=SHAPES.get(kind, "circle"), entry_id=d["entry_id"],
            ec_id=d["ec_id"], ec_label=label_of.get(d["ec_id"]),
            x=x, y=PAD_TOP + lane * LANE_H, examined=d["examined"],
            cancelled=d["doc_no"] in cancelled_docs,
            corrected=d["entry_id"] in corrected,
            open_encumbrance=d["doc_no"] in open_enc,
        ))

    by_doc = {n.doc_no: n for n in placed}
    by_entry = {n.entry_id: n for n in placed if n.entry_id is not None}

    drawn: list[GraphEdge] = []
    for ed in edges:
        src = by_entry.get(ed.from_entry_id)
        tgt = by_doc.get(ed.to_doc_no)
        if not (src and tgt):
            continue                     # an undated endpoint; listed, not drawn
        drawn.append(GraphEdge(
            kind=ed.edge_type,
            resolved=ed.resolved_entry_id is not None,
            x1=src.x, y1=src.y, x2=tgt.x, y2=tgt.y))

    lanes = max(len(lane_last_x), 1)
    return GraphLayout(
        width=WIDTH,
        height=PAD_TOP + lanes * LANE_H + PAD_BOTTOM,
        nodes=placed, edges=drawn, undated=undated,
        ticks=[YearTick(year=y, x=x_of(y)) for y in sorted(set(years))],
    )
