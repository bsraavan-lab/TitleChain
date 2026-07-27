"""derive() — the boundary. Models read; code decides.

╔══════════════════════════════════════════════════════════════════════════════╗
║  SEAM. This file is the frontend's contract with the product, and it is       ║
║  deliberately thin. On the floor, graph.py and rulebook.py replace the two    ║
║  marked sections below. Nothing in templates/ changes when they do — the      ║
║  templates render a DerivedView and do not care who built it.                 ║
║                                                                               ║
║  What lives here now is the minimum needed to make the UI real: the graph     ║
║  build (PR + cancel edges) and six of the ten rules — the six that fire on    ║
║  the documents we actually hold.                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

No model call happens inside this function, and none ever will.
"""

from __future__ import annotations

import re
from datetime import date, datetime

from .models import (
    ChainNode, Coverage, DerivedView, ECHeader, Edge, Entry, Finding,
    OrderBlock, Tick,
)

RULEBOOK_VERSION = "v1.0"
STALE_DAYS = 90          # the product's one setting; rendered where it is used
ORDER_BUFFER_YEARS = 12  # earliest parent − 12 → the replacement EC covers 13 years


def _year(text: str | None) -> int | None:
    if not text:
        return None
    m = re.search(r"(19|20)\d{2}", text)
    return int(m.group(0)) if m else None


def _parse_date(text: str | None) -> date | None:
    for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text or "", fmt).date()
        except ValueError:
            continue
    return None


def _n(count: int, singular: str, plural: str | None = None) -> str:
    """"1 parent document" / "5 parent documents".

    Not cosmetic. These sentences are the body of a report an advocate signs, and
    a single-entry certificate — the shortest, most common kind — is exactly the
    case that read "1 parent documents predate this certificate".
    """
    return f"{count} {singular if count == 1 else (plural or singular + 's')}"


# ── graph.py ──────────────────────────────────────────────────────────────────

def build_graph(entries: list[Entry]) -> list[Edge]:
    """Nodes are entries. Edges come from PR pointers and remark cross-references.

    `nodes.get(key)` returning None is the entire product: that is R4.
    """
    nodes = {e.doc_no: e for e in entries if e.doc_no}
    edges: list[Edge] = []

    for e in entries:
        for pr in e.pr_numbers:
            target = nodes.get(pr.doc_no)
            edges.append(Edge(
                from_entry_id=e.db_id,
                to_doc_no=pr.doc_no,
                to_year=pr.year,
                edge_type="PR_PARENT",
                resolved_entry_id=target.db_id if target else None,
                label="parent",
            ))
        # Cancellation grammar: a remark naming another document — but only when
        # the sentence actually SAYS cancellation ("This document cancels…" /
        # இரத்து). A bare document number in remarks is usually a copied-through
        # PR sub-row, and calling that a cancellation asserts "not a live
        # encumbrance" about a deed that may be exactly that. Wrong in the
        # dangerous direction; the keyword is required.
        if e.remarks and re.search(r"cancel|இரத்து|ரத்து", e.remarks, re.I):
            for doc_no in re.findall(r"\b(\d{1,6}/(?:19|20)\d{2})\b", e.remarks):
                if doc_no == e.doc_no:
                    continue
                target = nodes.get(doc_no)
                edges.append(Edge(
                    from_entry_id=e.db_id,
                    to_doc_no=doc_no,
                    to_year=_year(doc_no),
                    edge_type="CANCELS",
                    resolved_entry_id=target.db_id if target else None,
                    label="cancels",
                ))
    return edges


def build_chain(entries: list[Entry], edges: list[Edge]) -> list[ChainNode]:
    """Nested list. Unexamined parents are open circles, never omitted."""
    by_id = {e.db_id: e for e in entries}
    by_doc = {e.doc_no: e for e in entries if e.doc_no}
    referenced = {ed.to_doc_no for ed in edges}

    def node_for(entry: Entry, seen: set[str]) -> ChainNode:
        cancelled_by = next(
            (by_id[ed.from_entry_id].doc_no for ed in edges
             if ed.edge_type == "CANCELS" and ed.to_doc_no == entry.doc_no
             and ed.from_entry_id in by_id),
            None,
        )
        children: list[ChainNode] = []
        for pr in entry.pr_numbers:
            if pr.doc_no in seen:
                continue
            child = by_doc.get(pr.doc_no)
            if child:
                children.append(node_for(child, seen | {pr.doc_no}))
            else:
                children.append(ChainNode(doc_no=pr.doc_no, year=pr.year,
                                          nature=None, entry_id=None))
        return ChainNode(doc_no=entry.doc_no or "—", year=entry.doc_year,
                         nature=entry.nature, entry_id=entry.db_id,
                         cancelled_by=cancelled_by, children=children)

    roots = [e for e in entries if e.doc_no and e.doc_no not in referenced]
    if not roots:
        roots = entries
    return [node_for(e, {e.doc_no or ""}) for e in roots]


# ── rulebook.py ───────────────────────────────────────────────────────────────

def run_rules(header: ECHeader, entries: list[Entry], edges: list[Edge]) -> list[Finding]:
    f: list[Finding] = []
    add = lambda rid, sev, msg, ev=(): f.append(  # noqa: E731
        Finding(rule_id=rid, severity=sev, message=msg,
                evidence_entry_ids=[i for i in ev if i is not None],
                rulebook_version=RULEBOOK_VERSION))

    start_year = _year(header.search_period_start)
    by_id = {e.db_id: e for e in entries}

    # R1 CANCELLED_INSTRUMENT — and its confirmation, which matters just as much
    for ed in edges:
        if ed.edge_type != "CANCELS" or not ed.resolved_entry_id:
            continue
        src, tgt = by_id.get(ed.from_entry_id), by_id.get(ed.resolved_entry_id)
        if not (src and tgt):
            continue
        add("R1", "material",
            f"Entry {src.sr_no} ({src.doc_no}) cancels {tgt.doc_no} "
            f"({tgt.nature}). Read linearly this looks like a live encumbrance; it is not.",
            (src.db_id, tgt.db_id))
        add("R1", "confirmation",
            f"Cancellation of {tgt.doc_no} is confirmed inside this certificate "
            f"by {src.doc_no}.", (src.db_id, tgt.db_id))

    # R3 WINDOW_INSUFFICIENT — the finding that cannot be produced by reading
    if start_year:
        outside = [(e, pr) for e in entries for pr in e.pr_numbers if pr.year < start_year]
        if outside:
            earliest = min(outside, key=lambda t: t[1].year)[1].doc_no
            add("R3", "blocking",
                f"{_n(len(outside), 'parent document')} "
                f"{'predates' if len(outside) == 1 else 'predate'} this certificate's "
                f"search period. "
                f"{'It is' if len(outside) == 1 else 'The earliest is'} {earliest}. "
                f"This certificate cannot evidence the chain before {start_year}.",
                {e.db_id for e, _ in outside})

    # R4 DANGLING_PARENT
    dangling = [ed for ed in edges
                if ed.edge_type == "PR_PARENT" and ed.resolved_entry_id is None]
    if dangling:
        add("R4", "material",
            f"{_n(len(dangling), 'parent document')} "
            f"{'is' if len(dangling) == 1 else 'are'} named but not present in this "
            f"certificate: {', '.join(ed.to_doc_no for ed in dangling)}. "
            f"{'It has' if len(dangling) == 1 else 'They have'} not been examined.",
            {ed.from_entry_id for ed in dangling})
    for ed in edges:
        if ed.edge_type == "PR_PARENT" and ed.resolved_entry_id:
            tgt = by_id.get(ed.resolved_entry_id)
            add("R4", "confirmation",
                f"Parent link to {ed.to_doc_no} resolves to an entry inside this "
                f"certificate. Verified.", (ed.from_entry_id, tgt.db_id if tgt else None))

    # R8 STALE_EC — threshold surfaced in the message, not in a settings screen
    issued = _parse_date(header.issue_date)
    if issued:
        days = (date.today() - issued).days
        if days > STALE_DAYS:
            add("R8", "informational",
                f"Certificate issued {header.issue_date} — {days} days ago "
                f"(flagged beyond {STALE_DAYS}). Transactions since then are not covered.")

    # R9 STRUCTURAL_GAP — our own completeness validator, not the model's confidence
    required = ("doc_no", "nature", "date_registration")
    for e in entries:
        missing = [fld for fld in required if getattr(e, fld) is None]
        if missing:
            add("R9", "material",
                f"Entry {e.sr_no}: {', '.join(m.replace('_', ' ') for m in missing)} "
                f"could not be read. Review against the source.", (e.db_id,))

    # R10 ENTRY_COUNT_MISMATCH — the document's own declared count
    dec = header.declared_entry_count
    if dec is not None:
        if dec != len(entries):
            add("R10", "blocking",
                f"This certificate declares {dec} entries; {len(entries)} were "
                f"extracted. Entries may have been lost.")
        else:
            add("R10", "confirmation",
                f"Entry count matches the certificate's own declaration ({dec}).")

    order = {"blocking": 0, "material": 1, "informational": 2, "confirmation": 3}
    return sorted(f, key=lambda x: order[x.severity])


# ── the two derived surfaces the UI leads with ────────────────────────────────

def build_coverage(header: ECHeader, entries: list[Entry]) -> Coverage:
    start, end = _year(header.search_period_start), _year(header.search_period_end)
    pr_years = sorted({pr.year for e in entries for pr in e.pr_numbers})

    if not start or not end:
        return Coverage(
            start_year=start, end_year=end,
            axis_min=min(pr_years or [date.today().year]) - 1,
            axis_max=date.today().year, ticks=[], sufficient=None,
            headline="This certificate does not state a search period.",
            detail="Coverage cannot be computed. Check the certificate header "
                   "against the source page.")

    axis_min = min([start] + pr_years) - 2
    axis_max = max(end, date.today().year)
    # Ticks are deduped by year — two parents from 2005 are one mark on a ruler.
    # The sentence, however, must count DOCUMENTS, or it contradicts R3.
    ticks = [Tick(year=y, label=str(y), inside=start <= y <= end) for y in pr_years]
    outside = [t for t in ticks if not t.inside]
    outside_docs = [pr for e in entries for pr in e.pr_numbers
                    if not (start <= pr.year <= end)]
    inside_docs = [pr for e in entries for pr in e.pr_numbers
                   if start <= pr.year <= end]

    if not pr_years:
        return Coverage(start_year=start, end_year=end, axis_min=axis_min,
                        axis_max=axis_max, ticks=ticks, sufficient=None,
                        headline="No parent documents are named in this certificate.",
                        detail=f"It covers {header.search_period_start} → "
                               f"{header.search_period_end}. That is a statement about "
                               f"this window, not about the chain before it.")
    if not outside:
        # Ticks are deduped by year; the sentence counts DOCUMENTS, as the note
        # above requires — five parents sharing two years is five links, not two.
        return Coverage(start_year=start, end_year=end, axis_min=axis_min,
                        axis_max=axis_max, ticks=ticks, sufficient=True,
                        headline="Every parent document named here falls inside this "
                                 "certificate's window.",
                        detail=f"{_n(len(inside_docs), 'parent link')} "
                               f"{'resolves' if len(inside_docs) == 1 else 'resolve'} within "
                               f"{header.search_period_start} → {header.search_period_end}.")
    return Coverage(
        start_year=start, end_year=end, axis_min=axis_min, axis_max=axis_max,
        ticks=ticks, sufficient=False,
        headline="This certificate cannot support a 13-year search.",
        detail=(f"It covers {header.search_period_start} → {header.search_period_end}. "
                f"{_n(len(outside_docs), 'parent document')} "
                f"{'is' if len(outside_docs) == 1 else 'are'} named, "
                f"{'from' if len(outside_docs) == 1 else 'the earliest from'} "
                f"{min(t.year for t in outside)}. "
                f"{'It does not fall' if len(outside_docs) == 1 else 'None of them fall'} "
                f"inside this window."))


def build_order(header: ECHeader, entries: list[Entry], coverage: Coverage) -> OrderBlock | None:
    """FR-10. The moment she learns the window is short, her next thought is
    'so what do I order?'. It arrives filled in."""
    if coverage.sufficient is not False:
        return None
    pr_years = [pr.year for e in entries for pr in e.pr_numbers]
    if not (pr_years and coverage.start_year):
        return None

    # The header and the schedule spell the same survey number differently —
    # "94/3b" in the header, "94/3B" in the schedule, both verbatim from the
    # certificate. A case-sensitive check calls those two numbers, and the block
    # she copies into the order goes out asking for a plot that does not exist.
    # First spelling wins, and the header's is first because it is the
    # certificate's own statement of what was searched.
    survey: list[str] = []
    seen: set[str] = set()
    for sn in [*header.survey_details,
               *(s_no for e in entries for s in e.schedules for s_no in s.survey_nos)]:
        key = sn.strip().upper()
        if key and key not in seen:
            seen.add(key)
            survey.append(sn.strip())

    return OrderBlock(
        sro=header.sro, village=header.village, survey_nos=survey,
        date_from=f"01-Jan-{min(pr_years) - ORDER_BUFFER_YEARS}",
        date_to=f"31-Dec-{coverage.start_year - 1}",
    )


def derive(header: ECHeader, entries: list[Entry]) -> DerivedView:
    """The one call the frontend makes. Pure, deterministic, unit-testable."""
    edges = build_graph(entries)
    coverage = build_coverage(header, entries)
    return DerivedView(
        coverage=coverage,
        findings=run_rules(header, entries, edges),
        edges=edges,
        chain=build_chain(entries, edges),
        order=build_order(header, entries, coverage),
        rulebook_version=RULEBOOK_VERSION,
    )
