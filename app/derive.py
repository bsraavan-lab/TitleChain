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
from typing import Callable, Iterable

from .models import (
    ChainNode, Completeness, Coverage, CoverageBand, DerivedView, DocumentRequest,
    ECDoc, ECHeader, Edge, Entry, Gate, OrderBlock, PageRef, Readiness, RuleInput,
    RuleOutcome, RuleRun, Severity, Tick,
)

RULEBOOK_VERSION = "v1.0"
STALE_DAYS = 90          # the product's one setting; rendered where it is used
ORDER_BUFFER_YEARS = 12  # earliest parent − 12 → the replacement EC covers 13 years
SEARCH_YEARS = 13        # the Tamil Nadu search convention, in one place

EcFor = Callable[[Entry], "int | None"]


def _fixed_ec(ec_id: int | None) -> EcFor:
    return lambda _entry: ec_id


def _ec_map(docs: list[ECDoc]) -> EcFor:
    """Which certificate an entry came from. Case-level rules span certificates,
    so a page reference has to name the certificate as well as the page."""
    m = {e.db_id: d.ec_id for d in docs for e in d.entries}
    return lambda entry: m.get(entry.db_id)


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

# rule_id → (short name, what the check is looking for, said plainly). The
# checklist and the report render both: the name so a check can be referred to,
# the sentence so nobody has to be told what it means.
RULEBOOK: dict[str, tuple[str, str]] = {
    "R1": ("Cancelled documents",
           "A document that another document cancels must not be treated as a live "
           "claim on the property."),
    "R2": ("Open claims",
           "A mortgage, charge or lien with nothing on record to close it is still "
           "hanging over the property."),
    "R3": ("Years covered",
           "Every earlier document the certificate names should fall inside the "
           "years this case covers."),
    "R4": ("Missing documents",
           "Every earlier document the certificate names should be here, so that "
           "somebody has actually read it."),
    "R5": ("Chain of owners",
           "Whoever received the property in one sale should be the one passing it "
           "on in the next."),
    "R6": ("Survey numbers",
           "Survey numbers should not change from one entry to the next unless a "
           "subdivision or partition explains it."),
    "R7": ("Property size",
           "The extent of the property should not change unless a partition "
           "explains it."),
    "R8": ("Certificate age",
           "A certificate issued a while ago says nothing about what has happened "
           "since."),
    "R9": ("Blank fields",
           "Every field we rely on should actually have been read off the page."),
    "R10": ("Entry count",
            "The number of entries we read should match the number the certificate "
            "says it has."),
}

# Rules with no implementation in this rulebook version. They report
# NOT_EVALUABLE with `implemented=False` rather than silently not appearing —
# "we do not check this" is information the advocate needs before she signs.
UNIMPLEMENTED: dict[str, str] = {
    "R5": "Following one person from a sale into the next one needs name matching "
          "we have not built yet. For now, read the From and To columns yourself — "
          "they are under What we read.",
    "R6": "We do not handle subdivisions and partitions yet, so we will not call a "
          "changed survey number right or wrong. Every number is laid out per entry "
          "under How it connects, for you to read.",
    "R7": "We do not keep the property's extent yet, so there is nothing to compare "
          "it against. Read the schedule against the page crops instead.",
}


def _run(rule_id: str, key: str, outcome: RuleOutcome, title: str, message: str, *,
         reason: str | None = None, severity: Severity | None = None,
         inputs: list[RuleInput] | None = None,
         evidence: tuple | set | list = (), pages: list[PageRef] | None = None,
         implemented: bool = True) -> RuleRun:
    return RuleRun(
        rule_id=rule_id, key=key, outcome=outcome, title=title, message=message,
        reason=reason, severity=severity, inputs=inputs or [],
        evidence_entry_ids=sorted({i for i in evidence if i is not None}),
        pages=pages or [], implemented=implemented,
        rulebook_version=RULEBOOK_VERSION,
    )


def _pages(entries: Iterable[Entry], ec_for: EcFor) -> list[PageRef]:
    seen: list[PageRef] = []
    for e in entries:
        ref = PageRef(ec_id=ec_for(e), page_num=e.source.page_num)
        if ref not in seen:
            seen.append(ref)
    return seen


# ── R1 CANCELLED_INSTRUMENT ───────────────────────────────────────────────────

def r1(entries: list[Entry], edges: list[Edge], ec_for: EcFor) -> list[RuleRun]:
    by_id = {e.db_id: e for e in entries}
    cancels = [ed for ed in edges if ed.edge_type == "CANCELS"]
    runs: list[RuleRun] = []

    for ed in cancels:
        src = by_id.get(ed.from_entry_id)
        if ed.resolved_entry_id is None:
            # The remark says it cancels something we do not hold. That is not a
            # pass — the cancelled instrument is unexamined.
            runs.append(_run(
                "R1", f"R1:unresolved={ed.to_doc_no}", "NOT_EVALUABLE",
                f"We cannot confirm that {ed.to_doc_no} was cancelled",
                f"Entry {src.sr_no if src else '?'} ({src.doc_no if src else '?'}) "
                f"says it cancels {ed.to_doc_no}, but {ed.to_doc_no} is not here — so "
                f"nobody has checked whether it was a live claim in the first place.",
                reason=f"{ed.to_doc_no} is named as cancelled, but it is not one of "
                       f"the entries here, so we cannot read what it did.",
                inputs=[RuleInput(label=f"entry {src.sr_no} remarks" if src else "remarks",
                                  value=(src.remarks or "")[:200] if src else "",
                                  source_entry_id=ed.from_entry_id)],
                evidence=(ed.from_entry_id,),
                pages=_pages([src] if src else [], ec_for)))
            continue

        tgt = by_id.get(ed.resolved_entry_id)
        if not (src and tgt):
            continue
        ev = (src.db_id, tgt.db_id)
        shown = [
            RuleInput(label=f"entry {src.sr_no} remarks",
                      value=(src.remarks or "")[:200], source_entry_id=src.db_id),
            RuleInput(label=f"what entry {tgt.sr_no} is",
                      value=tgt.nature or "not read", source_entry_id=tgt.db_id),
            RuleInput(label="what we looked for",
                      value=f"a remark naming {tgt.doc_no} that says it was "
                            f"cancelled → found"),
        ]
        runs.append(_run(
            "R1", f"R1:cancelled={tgt.doc_no}", "REVIEW",
            f"{tgt.doc_no} was cancelled by {src.doc_no}",
            f"Entry {src.sr_no} ({src.doc_no}) cancels {tgt.doc_no} "
            f"({tgt.nature}). Read straight down the page, {tgt.doc_no} looks like a "
            f"live claim. It is not one.",
            severity="material", inputs=shown, evidence=ev,
            pages=_pages([src, tgt], ec_for)))
        runs.append(_run(
            "R1", f"R1:confirmed={tgt.doc_no}", "PASS",
            f"{tgt.doc_no} was cancelled, and this certificate says so",
            f"{src.doc_no}, on this same certificate, cancels {tgt.doc_no}. That is "
            f"confirmation from the document itself.",
            severity="confirmation", inputs=shown, evidence=ev,
            pages=_pages([src, tgt], ec_for)))

    if not runs:
        remarked = [e for e in entries if e.remarks]
        return [_run(
            "R1", "R1:none", "NOT_APPLICABLE",
            "Nothing here cancels anything else",
            "No entry's remarks say it cancels another document.",
            reason=(f"{len(remarked)} of {len(entries)} entries carry remarks, and "
                    f"none of them mentions a cancellation."
                    if remarked else
                    "No entry here carries remarks at all, and remarks are where a "
                    "cancellation would be noted."),
            inputs=[RuleInput(label="entries with remarks",
                              value=f"{len(remarked)} of {len(entries)}")])]
    return runs


# ── R2 LIVE_ENCUMBRANCE ───────────────────────────────────────────────────────
#
# The nature taxonomy, in one place, bilingual because the corpus is bilingual —
# `ec4` says `சுவாதீனமில்லாத அடைமானம்` and `ec3` says "Mortgage without possession
# deed" for the same instrument. Patterns are deliberately narrow: an unrecognised
# nature must fall through to NOT_EVALUABLE, never to "no encumbrance found".

# Latin terms are anchored on word boundaries and Tamil terms are not, because
# "Release deed" contains "lease" and "surcharge" contains "charge" — an
# unanchored match classifies a mortgage RELEASE as a LEASE, which is how a
# discharged charge gets reported as still open. Tamil script has no \b to anchor
# against and its terms are long enough not to collide.
NATURE_KINDS: list[tuple[str, str]] = [
    # (kind, pattern) — first match wins, so cancellation and discharge are tested
    # before the instruments they act on.
    ("cancellation", r"\bcancel\w*\b|இரத்து|ரத்து"),
    ("discharge",    r"\brelease\b|\breleas\w*\b|\bdischarge\w*\b|\bredemption\b|"
                     r"\bsatisfaction\b|விடுவிப்பு|ரிலீஸ்"),
    ("encumbrance",  r"\bmortgage\w*\b|அடைமான|\bcharge\b|\blien\b|\bhypothec\w*\b|"
                     r"\bdeposit\s+of\s+title\b"),
    ("lease",        r"\blease\w*\b|குத்தகை|வாடகை"),
    ("transfer",     r"\bsale\b|விற்பனை|கிரய|\bgift\b|தான\s*ஆவண|\bsettlement\b|"
                     r"\bpartition\b|பாகப்பிரிவினை|\bwill\b|உயில்|\bexchange\b|"
                     r"பரிமாற்ற"),
]


def nature_kind(nature: str | None) -> str | None:
    """None means "we could not classify this", which is not the same as "none of
    the above" — the caller must treat it as unevaluated, not as clean."""
    if not nature:
        return None
    for kind, pattern in NATURE_KINDS:
        if re.search(pattern, nature, re.I):
            return kind
    return None


def r2(entries: list[Entry], edges: list[Edge], ec_for: EcFor) -> list[RuleRun]:
    """Is a mortgage, charge or lien still open?

    Two conservative choices, both in the safe direction:

      · An instrument is only reported DISCHARGED when a later discharge or
        release instrument on this case actually REFERENCES it — by PR pointer or
        by naming it in remarks. A "release deed" that names nothing may be a
        family release of an interest in land, not a redemption of this mortgage,
        and treating it as one would assert "not a live charge" about a live one.
      · An entry whose nature could not be read is reported NOT_EVALUABLE, per
        entry. Saying "no encumbrance on this case" while a nature cell is blank
        is the false reassurance the whole rulebook exists to prevent.
    """
    by_id = {e.db_id: e for e in entries}
    cancelled_docs = {ed.to_doc_no for ed in edges
                      if ed.edge_type == "CANCELS" and ed.resolved_entry_id}

    unreadable = [e for e in entries if not e.nature]
    kinds = {e.db_id: nature_kind(e.nature) for e in entries}
    encumbrances = [e for e in entries if kinds.get(e.db_id) == "encumbrance"]
    unclassified = [e for e in entries
                    if e.nature and kinds.get(e.db_id) is None]

    runs: list[RuleRun] = []

    for e in encumbrances:
        shown = [
            RuleInput(label="document", value=e.doc_no or f"entry {e.sr_no}",
                      source_entry_id=e.db_id),
            RuleInput(label="what it is", value=e.nature or "not read",
                      source_entry_id=e.db_id),
            RuleInput(label="remarks", value=(e.remarks or "—")[:200],
                      source_entry_id=e.db_id),
        ]
        # A discharge that names this instrument, anywhere on the case.
        dischargers = [
            other for other in entries
            if other.db_id != e.db_id
            and kinds.get(other.db_id) in ("discharge", "cancellation")
            and (
                any(pr.doc_no == e.doc_no for pr in other.pr_numbers)
                or (e.doc_no and other.remarks and e.doc_no in other.remarks)
            )
        ]
        if e.doc_no in cancelled_docs:
            tgt = next((by_id[ed.from_entry_id] for ed in edges
                        if ed.edge_type == "CANCELS" and ed.to_doc_no == e.doc_no
                        and ed.from_entry_id in by_id), None)
            runs.append(_run(
                "R2", f"R2:enc={e.doc_no}", "PASS",
                f"{e.doc_no} was cancelled, not left hanging",
                f"{e.doc_no} ({e.nature}) was cancelled by "
                f"{tgt.doc_no if tgt else 'another document on this case'}, so it is "
                f"not a claim on the property any more.",
                severity="confirmation", inputs=shown,
                evidence=(e.db_id, tgt.db_id if tgt else None),
                pages=_pages([e], ec_for)))
        elif dischargers:
            d = dischargers[0]
            runs.append(_run(
                "R2", f"R2:enc={e.doc_no}", "PASS",
                f"{e.doc_no} has been cleared by {d.doc_no}",
                f"{e.doc_no} ({e.nature}) was discharged or released by {d.doc_no} "
                f"({d.nature}), which names it directly.",
                severity="confirmation",
                inputs=shown + [RuleInput(label="cleared by",
                                          value=f"{d.doc_no} ({d.nature})",
                                          source_entry_id=d.db_id)],
                evidence=(e.db_id, d.db_id), pages=_pages([e, d], ec_for)))
        else:
            runs.append(_run(
                "R2", f"R2:enc={e.doc_no}", "FAIL",
                f"{e.doc_no} is still an open claim",
                f"Entry {e.sr_no} ({e.doc_no}) is a {e.nature}. Nothing on this case "
                f"releases it by name, so on this record it is still open.",
                severity="blocking",
                inputs=shown + [RuleInput(
                    label="what we looked for",
                    value="a later release or discharge naming this document → "
                          "none found")],
                evidence=(e.db_id,), pages=_pages([e], ec_for)))

    for e in unreadable:
        runs.append(_run(
            "R2", f"R2:unread-nature=ec:{ec_for(e) or 0}/sr:{e.sr_no}",
            "NOT_EVALUABLE",
            f"Entry {e.sr_no} — we could not read what kind of document this is",
            f"Entry {e.sr_no} ({e.doc_no or 'document number not read'}) has no "
            f"document type we could read, so we cannot say whether it puts a claim "
            f"on the property.",
            reason="That cell did not come through, so we could not classify this "
                   "entry. Check it against the page before you take 'no claims "
                   "found' at face value.",
            inputs=[RuleInput(label="what it is", value="blank",
                              source_entry_id=e.db_id)],
            evidence=(e.db_id,), pages=_pages([e], ec_for)))

    if runs:
        return runs

    if unclassified:
        return [_run(
            "R2", "R2:unclassified", "NOT_EVALUABLE",
            f"{_n(len(unclassified), 'entry', 'entries')} we could not classify",
            "We did not recognise a mortgage, charge or lien here — but some of "
            "these document types are ones we do not know yet.",
            reason="Types we did not recognise: "
                   + "; ".join(f"{e.doc_no or e.sr_no} — {e.nature}"
                               for e in unclassified[:5])
                   + ". Read these against the page rather than treating our silence "
                     "as a clean result.",
            inputs=[RuleInput(label=f"what entry {e.sr_no} is",
                              value=e.nature or "—", source_entry_id=e.db_id)
                    for e in unclassified],
            evidence={e.db_id for e in unclassified},
            pages=_pages(unclassified, ec_for))]

    return [_run(
        "R2", "R2:none", "NOT_APPLICABLE",
        "Nothing here puts a claim on the property",
        f"None of the {len(entries)} entries is a mortgage, charge, lien or "
        f"deposit of title deeds.",
        reason=f"We read and classified all {len(entries)} entries, and not one of "
               f"them creates a claim on the property.",
        inputs=[RuleInput(label=f"entry {e.sr_no}",
                          value=f"{e.nature} → {kinds.get(e.db_id)}",
                          source_entry_id=e.db_id) for e in entries])]


# ── R3 WINDOW_INSUFFICIENT ────────────────────────────────────────────────────

def windows(docs: list[ECDoc]) -> list[tuple[int, int, str]]:
    """(start, end, label) for every certificate on the case that states a window.
    A parent year is covered when it falls inside ANY of these — which is exactly
    what makes uploading the earlier certificate resolve the finding."""
    out = []
    for d in docs:
        start, end = (_year(d.header.search_period_start),
                      _year(d.header.search_period_end))
        if start and end:
            out.append((start, end, d.label))
    return sorted(out)


def _covered(year: int, wins: list[tuple[int, int, str]]) -> bool:
    return any(s <= year <= e for s, e, _ in wins)


def r3(docs: list[ECDoc], entries: list[Entry], ec_for: EcFor) -> list[RuleRun]:
    """Case-level, not certificate-level.

    The obligation is that every parent document named anywhere on the case falls
    inside a window the case covers — not inside one particular certificate's
    window. That is the difference between a warning and a workflow: uploading the
    earlier certificate is what closes this.
    """
    wins = windows(docs)
    prs = [(e, pr) for e in entries for pr in e.pr_numbers]
    solo = len(docs) <= 1
    first = docs[0] if docs else None
    shown = [RuleInput(label=f"years {d.label} covers", value=d.window) for d in docs]

    if not wins:
        return [_run(
            "R3", "R3:no-window", "NOT_EVALUABLE",
            ("This certificate does not say which years it covers" if solo else
             "None of these certificates says which years it covers"),
            ("We could not read the years this certificate covers, so we cannot tell "
             "you whether the earlier documents fall inside them." if solo else
             "None of the certificates here says which years it covers, so we cannot "
             "place an earlier document inside or outside them."),
            reason="The search-period field is blank, or it did not come through. "
                   "Check the header against the page — without those dates there is "
                   "no way to work out what is covered.",
            inputs=shown,
            pages=[PageRef(ec_id=first.ec_id if first else None, page_num=1)])]

    if not prs:
        return [_run(
            "R3", "R3:no-parents", "NOT_APPLICABLE",
            "This certificate does not point back to any earlier document",
            (f"It covers {first.window} and names no earlier document."
             if solo and first else
             f"None of the {len(docs)} certificates here names an earlier document."),
            reason="There is no earlier year to place inside or outside the window. "
                   "Silence about the chain is not evidence about the chain, so this "
                   "check cannot say anything either way.",
            inputs=shown,
            pages=[PageRef(ec_id=first.ec_id if first else None, page_num=1)])]

    outside = [(e, pr) for e, pr in prs if not _covered(pr.year, wins)]
    earliest_start = min(s for s, _, _ in wins)
    shown += [
        RuleInput(label="years of the earlier documents",
                  value=", ".join(str(pr.year) for _, pr in prs)),
        RuleInput(label="what we looked for",
                  value=(f"anything earlier than {earliest_start} → "
                         f"{len(outside)} found" if solo else
                         f"anything outside every set of years above → "
                         f"{len(outside)} found")),
    ]

    if not outside:
        return [_run(
            "R3", "R3:covered", "PASS",
            ("Every earlier document falls inside the years this certificate covers"
             if solo else
             "Every earlier document falls inside the years you have covered"),
            (f"All {_n(len(prs), 'link')} back to earlier documents sit inside "
             f"{first.window}."
             if solo and first else
             f"All {_n(len(prs), 'link')} back to earlier documents sit inside one of "
             f"the {_n(len(wins), 'window')} you have."),
            inputs=shown, evidence={e.db_id for e, _ in prs},
            pages=_pages([e for e, _ in prs], ec_for))]

    earliest = min(outside, key=lambda t: t[1].year)[1]
    return [_run(
        "R3", f"R3:gap={earliest.year}-{earliest_start - 1}", "FAIL",
        "This certificate does not reach far enough back",
        (f"{_n(len(outside), 'earlier document')} "
         f"{'sits' if len(outside) == 1 else 'sit'} before the years this "
         f"certificate covers. "
         f"{'It is' if len(outside) == 1 else 'The oldest is'} {earliest.doc_no}. "
         f"Nothing here can tell you what happened before {earliest_start}."
         if solo else
         f"{_n(len(outside), 'earlier document')} "
         f"{'falls' if len(outside) == 1 else 'fall'} outside every set of years you "
         f"have. "
         f"{'It is' if len(outside) == 1 else 'The oldest is'} {earliest.doc_no}. "
         f"Nothing on this case can tell you what happened before "
         f"{earliest_start}."),
        severity="blocking", inputs=shown,
        evidence={e.db_id for e, _ in outside},
        pages=_pages([e for e, _ in outside], ec_for))]


# ── R4 DANGLING_PARENT ────────────────────────────────────────────────────────

def r4(entries: list[Entry], edges: list[Edge], ec_for: EcFor) -> list[RuleRun]:
    """One run per parent document, not one run per certificate.

    The aggregate form this rule used to emit ("5 parent documents are named but
    not present: …") cannot be marked reviewed one at a time, cannot be resolved
    one at a time, and cannot have an uploaded certificate attributed to it. One
    dangling parent is one obligation, so it is one row.
    """
    by_id = {e.db_id: e for e in entries}
    pr_edges = [ed for ed in edges if ed.edge_type == "PR_PARENT"]

    if not pr_edges:
        return [_run(
            "R4", "R4:none", "NOT_APPLICABLE",
            "Nothing here points back to an earlier document",
            "No entry names an earlier document, so there is no link to follow.",
            reason="The prior-document column (PR Number / முந்தைய ஆவண எண்) is empty "
                   "on every entry.",
            inputs=[RuleInput(label="links back to earlier documents", value="none")])]

    # Group by target document: two entries naming the same parent is one obligation.
    grouped: dict[str, list[Edge]] = {}
    for ed in pr_edges:
        grouped.setdefault(ed.to_doc_no, []).append(ed)

    runs: list[RuleRun] = []
    for doc_no in sorted(grouped):
        group = grouped[doc_no]
        sources = [by_id[ed.from_entry_id] for ed in group
                   if ed.from_entry_id in by_id]
        named_by = ", ".join(f"entry {s.sr_no}" for s in sources) or "an entry"
        resolved = next((ed for ed in group if ed.resolved_entry_id), None)
        shown = [
            RuleInput(label="pointed to by", value=named_by,
                      source_entry_id=sources[0].db_id if sources else None),
            RuleInput(label="earlier document", value=doc_no),
        ]
        if resolved:
            tgt = by_id.get(resolved.resolved_entry_id)
            runs.append(_run(
                "R4", f"R4:resolved={doc_no}", "PASS",
                f"{doc_no} is here, and it has been read",
                f"The link back to {doc_no} lands on an entry inside this "
                f"certificate. Nothing to chase.",
                severity="confirmation",
                inputs=shown + [RuleInput(
                    label="which lands on",
                    value=f"entry {tgt.sr_no} ({tgt.nature or 'type not read'})"
                          if tgt else "an entry on this case",
                    source_entry_id=resolved.resolved_entry_id)],
                evidence=(resolved.from_entry_id, resolved.resolved_entry_id),
                pages=_pages([*sources, *([tgt] if tgt else [])], ec_for)))
        else:
            runs.append(_run(
                "R4", f"R4:parent={doc_no}", "REVIEW",
                f"{doc_no} is named, but you do not have it",
                f"{named_by.capitalize()} points back to {doc_no} as an earlier "
                f"document. It is not in any certificate here, so nobody has read "
                f"what is inside it.",
                severity="material",
                inputs=shown + [RuleInput(label="what we looked for",
                                          value=f"an entry for {doc_no} → "
                                                f"not found")],
                evidence={ed.from_entry_id for ed in group},
                pages=_pages(sources, ec_for)))
    return runs


# ── R8 STALE_EC ───────────────────────────────────────────────────────────────

def r8(header: ECHeader, ec_id: int | None) -> list[RuleRun]:
    key = f"R8:stale=ec:{ec_id or 0}"
    shown = [
        RuleInput(label="issued on", value=header.issue_date or "not read"),
        RuleInput(label="we flag anything older than", value=f"{STALE_DAYS} days"),
    ]
    issued = _parse_date(header.issue_date)
    if not issued:
        return [_run(
            "R8", f"R8:no-date=ec:{ec_id or 0}", "NOT_EVALUABLE",
            "We could not read when this certificate was issued",
            "Without an issue date, we cannot tell you how much may have happened "
            "since it was produced.",
            reason=(f"The issue date reads {header.issue_date!r}, which is not a date "
                    f"we can make sense of."
                    if header.issue_date else
                    "No issue date came through from this certificate."),
            inputs=shown, pages=[PageRef(ec_id=ec_id, page_num=1)])]

    days = (date.today() - issued).days
    shown.append(RuleInput(label="how old that makes it", value=f"{days} days"))
    if days > STALE_DAYS:
        return [_run(
            "R8", key, "REVIEW", f"This certificate is {days} days old",
            f"Issued {header.issue_date}, {days} days ago. We flag anything past "
            f"{STALE_DAYS} days, because nothing registered since then appears here.",
            severity="informational", inputs=shown,
            pages=[PageRef(ec_id=ec_id, page_num=1)])]
    return [_run(
        "R8", key, "PASS", f"This certificate is recent ({days} days old)",
        f"Issued {header.issue_date}, inside the {STALE_DAYS}-day mark we use.",
        inputs=shown, pages=[PageRef(ec_id=ec_id, page_num=1)])]


# ── R9 STRUCTURAL_GAP ─────────────────────────────────────────────────────────

REQUIRED_FIELDS = ("doc_no", "nature", "date_registration")


def r9(entries: list[Entry], ec_id: int | None) -> list[RuleRun]:
    """One run per missing field, so each is individually correctable and each
    clears on its own when the advocate supplies the value.

    The key is `ec_id` + the certificate's own `sr_no`, never `doc_no` — keying on
    the document number would break precisely when the document number is the
    field that could not be read.
    """
    if not entries:
        return [_run(
            "R9", "R9:no-entries", "NOT_APPLICABLE",
            "We did not read any entries from this certificate",
            "There is nothing here to check for missing fields.",
            reason="No numbered registration entry came through, so there was no "
                   "field to test.")]

    runs: list[RuleRun] = []
    for e in entries:
        for fld in REQUIRED_FIELDS:
            if getattr(e, fld) is not None:
                continue
            label = fld.replace("_", " ")
            runs.append(_run(
                "R9", f"R9:ec:{ec_id or 0}/sr:{e.sr_no}/{fld}", "REVIEW",
                f"Entry {e.sr_no} — we could not read the {label}",
                f"Entry {e.sr_no}: the {label} did not come through. Have a look at "
                f"the page and type in what it says.",
                severity="material",
                inputs=[
                    RuleInput(label="entry", value=f"{e.sr_no} "
                              f"({e.doc_no or 'document number not read'})",
                              source_entry_id=e.db_id),
                    RuleInput(label=label, value="blank", source_entry_id=e.db_id),
                    RuleInput(label="scan quality",
                              value=f"{e.source.confidence:.3f}"
                                    if e.source.confidence is not None else "not reported",
                              source_entry_id=e.db_id),
                ],
                evidence=(e.db_id,), pages=_pages([e], _fixed_ec(ec_id))))

    if runs:
        return runs
    return [_run(
        "R9", f"R9:complete=ec:{ec_id or 0}", "PASS",
        f"Nothing is missing on any of the {len(entries)} entries",
        f"Document number, document type and date of registration are all there, on "
        f"every one of the {len(entries)} entries.",
        inputs=[RuleInput(label="fields we need",
                          value=", ".join(f.replace('_', ' ') for f in REQUIRED_FIELDS)),
                RuleInput(label="entries checked", value=str(len(entries)))],
        pages=_pages(entries, _fixed_ec(ec_id)))]


# ── R10 ENTRY_COUNT_MISMATCH ──────────────────────────────────────────────────

def r10(header: ECHeader, entries: list[Entry], ec_id: int | None) -> list[RuleRun]:
    key = f"R10:count=ec:{ec_id or 0}"
    dec = header.declared_entry_count
    shown = [
        RuleInput(label="the certificate says it has",
                  value=str(dec) if dec is not None else "not stated"),
        RuleInput(label="we read", value=str(len(entries))),
    ]
    if dec is None:
        return [_run(
            "R10", f"R10:no-count=ec:{ec_id or 0}", "NOT_EVALUABLE",
            "This certificate does not say how many entries it has",
            "Without that number, we have no independent way to tell whether a whole "
            "entry was missed.",
            reason="We could not find a 'Number of Entries / பதிவுகளின் எண்ணிக்கை' "
                   "value in the text, so there was nothing to compare against.",
            inputs=shown)]
    if dec != len(entries):
        return [_run(
            "R10", key, "FAIL", "The entry count does not match",
            f"This certificate says it has {dec} entries. We read {len(entries)}. "
            f"Something may have been missed — check the pages before you rely on "
            f"this.",
            severity="blocking", inputs=shown)]
    return [_run(
        "R10", key, "PASS", f"All {dec} entries accounted for",
        f"We read {dec} entries, which is exactly what the certificate says it has.",
        severity="confirmation", inputs=shown)]


# ── rules with no implementation in this version ──────────────────────────────

def unimplemented(rule_id: str) -> RuleRun:
    return _run(
        rule_id, f"{rule_id}:unimplemented", "NOT_EVALUABLE",
        f"{RULEBOOK[rule_id][0]} — we do not check this yet",
        RULEBOOK[rule_id][1],
        reason=UNIMPLEMENTED[rule_id], implemented=False)


def run_rules(docs: list[ECDoc], entries: list[Entry],
              edges: list[Edge]) -> list[RuleRun]:
    """Every rule in the rulebook reports, on every derivation.

    A rule that finds nothing returns PASS, NOT_APPLICABLE or NOT_EVALUABLE — it
    never returns nothing at all. That is the whole point: silence from a rule is
    indistinguishable from a rule that was never run, and this product does not
    get to claim a check it did not make.

    The split matters. R1, R3 and R4 are statements about the CASE — a cancellation
    deed in the second certificate can extinguish an instrument in the first, and a
    parent dangling in one is resolved by the other. R8, R9 and R10 are statements
    about ONE document and stay attached to it.
    """
    ec_for = _ec_map(docs)
    runs: list[RuleRun] = []

    runs += r1(entries, edges, ec_for)
    runs += r2(entries, edges, ec_for)
    runs += r3(docs, entries, ec_for)
    runs += r4(entries, edges, ec_for)
    runs += [unimplemented("R5"), unimplemented("R6"), unimplemented("R7")]

    for d in docs:
        runs += r8(d.header, d.ec_id)
        runs += r9(d.entries, d.ec_id)
        runs += r10(d.header, d.entries, d.ec_id)
    return runs


# ── the two derived surfaces the UI leads with ────────────────────────────────

def build_coverage(header: ECHeader, entries: list[Entry]) -> Coverage:
    start, end = _year(header.search_period_start), _year(header.search_period_end)
    pr_years = sorted({pr.year for e in entries for pr in e.pr_numbers})

    if not start or not end:
        return Coverage(
            start_year=start, end_year=end,
            axis_min=min(pr_years or [date.today().year]) - 1,
            axis_max=date.today().year, ticks=[], sufficient=None,
            headline="This certificate does not say which years it covers.",
            detail="Without those dates there is no way to work out what it covers. "
                   "Check the header against the page.")

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
                        headline="This certificate does not point back to any earlier "
                                 "document.",
                        detail=f"It covers {header.search_period_start} → "
                               f"{header.search_period_end}. That tells you about those "
                               f"years — not about the chain before it.")
    if not outside:
        # Ticks are deduped by year; the sentence counts DOCUMENTS, as the note
        # above requires — five parents sharing two years is five links, not two.
        return Coverage(start_year=start, end_year=end, axis_min=axis_min,
                        axis_max=axis_max, ticks=ticks, sufficient=True,
                        headline="Every earlier document named here falls inside the "
                                 "years this certificate covers.",
                        detail=f"{_n(len(inside_docs), 'link')} back to earlier "
                               f"documents, "
                               f"{'and it sits' if len(inside_docs) == 1 else 'and they all sit'} "
                               f"inside {header.search_period_start} → "
                               f"{header.search_period_end}.")
    return Coverage(
        start_year=start, end_year=end, axis_min=axis_min, axis_max=axis_max,
        ticks=ticks, sufficient=False,
        headline="This certificate cannot support a 13-year search.",
        detail=(f"It covers {header.search_period_start} → {header.search_period_end}. "
                f"{_n(len(outside_docs), 'earlier document')} "
                f"{'is' if len(outside_docs) == 1 else 'are'} named, "
                f"{'from' if len(outside_docs) == 1 else 'the oldest from'} "
                f"{min(t.year for t in outside)}. "
                f"{'It does not fall' if len(outside_docs) == 1 else 'None of them fall'} "
                f"inside that window."))


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


# ── the case: N certificates, one chain ───────────────────────────────────────

def required_span(entries: list[Entry],
                  wins: list[tuple[int, int, str]]) -> tuple[int, int]:
    """The years this case is obliged to cover, and why.

    Thirteen years back from today is the Tamil Nadu search convention. If the
    documents name a parent older than that, the obligation reaches back to it —
    a chain does not stop being a chain because the convention ran out.
    """
    today = date.today().year
    floor = today - SEARCH_YEARS
    years = [pr.year for e in entries for pr in e.pr_numbers]
    years += [s for s, _, _ in wins]
    return (min([floor] + years), today)


def build_coverage_case(docs: list[ECDoc], entries: list[Entry]) -> Coverage:
    """The ruler, drawn for a case rather than for a certificate.

    One band per certificate. The single-certificate wording is delegated to
    `build_coverage` unchanged — that sentence was written carefully and tested,
    and a case with one certificate must read exactly as it did before.
    """
    wins = windows(docs)
    pr_years = sorted({pr.year for e in entries for pr in e.pr_numbers})
    span_from, span_to = required_span(entries, wins)

    bands = [CoverageBand(label=d.label,
                          start_year=_year(d.header.search_period_start),
                          end_year=_year(d.header.search_period_end),
                          ec_id=d.ec_id) for d in docs]

    axis_min = min([span_from] + pr_years + [s for s, _, _ in wins]) - 2
    axis_max = max([span_to] + [e for _, e, _ in wins])

    if len(docs) == 1:
        base = build_coverage(docs[0].header, entries)
        headline, detail, sufficient = base.headline, base.detail, base.sufficient
    else:
        outside = [pr for e in entries for pr in e.pr_numbers
                   if not _covered(pr.year, wins)]
        joined = " · ".join(f"{s}–{e}" for s, e, _ in wins) or "no years we could read"
        if not wins or not pr_years:
            sufficient = None
            headline = (f"{len(docs)} certificates here, and we still cannot work out "
                        f"the years.")
            detail = (f"They cover {joined}. "
                      f"{'No earlier document is named.' if not pr_years else ''} "
                      f"That tells you about those years, not about the chain.")
        elif outside:
            sufficient = False
            headline = (f"Even together, these {len(docs)} certificates do not cover "
                        f"the whole chain.")
            detail = (f"They cover {joined}. "
                      f"{_n(len(outside), 'earlier document')} "
                      f"{'sits' if len(outside) == 1 else 'sit'} outside all of them, "
                      f"the oldest from {min(pr.year for pr in outside)}.")
        else:
            sufficient = True
            headline = ("Every earlier document named here falls inside the years you "
                        "have covered.")
            detail = (f"{_n(len(pr_years), 'earlier year')}, all covered by the "
                      f"{_n(len(wins), 'certificate')} you have ({joined}).")

    return Coverage(
        start_year=bands[0].start_year if bands else None,
        end_year=bands[-1].end_year if bands else None,
        axis_min=axis_min, axis_max=axis_max,
        ticks=[Tick(year=y, label=str(y), inside=_covered(y, wins))
               for y in pr_years],
        sufficient=sufficient, headline=headline, detail=detail,
        bands=bands, required_from=span_from, required_to=span_to,
    )


def build_completeness(docs: list[ECDoc], entries: list[Entry], edges: list[Edge],
                       runs: list[RuleRun], reviewed: frozenset[str] | set[str],
                       *, corrections: int = 0, unread_pages: int = 0,
                       requests_open: int = 0) -> Completeness:
    """Counts. No weights, no coefficients, nothing anybody chose."""
    pr = [ed for ed in edges if ed.edge_type == "PR_PARENT"]
    named = {ed.to_doc_no for ed in pr}
    examined = {ed.to_doc_no for ed in pr if ed.resolved_entry_id is not None}

    wins = windows(docs)
    span_from, span_to = required_span(entries, wins)
    open_runs = [r for r in runs if r.is_open]

    return Completeness(
        links_named=len(named), links_examined=len(examined),
        span_from=span_from, span_to=span_to,
        years_required=max(span_to - span_from + 1, 0),
        years_covered=sum(1 for y in range(span_from, span_to + 1)
                          if _covered(y, wins)),
        review_total=len(open_runs),
        review_done=sum(1 for r in open_runs if r.key in reviewed),
        corrections=corrections, unread_pages=unread_pages,
        documents=len(docs), requests_open=requests_open,
    )


def _plural(n: int, one: str, many: str | None = None) -> str:
    return f"{n} {one if n == 1 else (many or one + 's')}"


def build_readiness(runs: list[RuleRun], c: Completeness) -> Readiness:
    """Gates, not a score. A file is signable or it is not.

    Each gate says one thing when it is met and another when it is not, because a
    single label cannot do both jobs: "0 parent documents unexamined ✓" is how a
    machine reports good news, not how a person does.
    """
    fails = [r for r in runs if r.outcome == "FAIL"]
    unexamined = max(c.links_named - c.links_examined, 0)
    uncovered = max(c.years_required - c.years_covered, 0)
    pending = max(c.review_total - c.review_done, 0)

    def gate(id: str, ok: bool, met: str, unmet: str, tab: str) -> Gate:
        return Gate(id=id, label=met if ok else unmet, passed=ok, tab=tab)

    return Readiness(gates=[
        gate("G1", not fails,
             "nothing is blocking",
             f"{_plural(len(fails), 'thing')} to resolve first", "review"),
        gate("G2", unexamined == 0,
             "every document is here",
             f"{_plural(unexamined, 'document')} nobody has read", "documents"),
        gate("G3", uncovered == 0,
             "all the years are covered",
             f"{_plural(uncovered, 'year')} not covered", "documents"),
        gate("G4", pending == 0,
             "you have been through everything",
             f"{_plural(pending, 'item')} you have not checked", "review"),
        gate("G5", c.unread_pages == 0,
             "every page was read",
             f"{_plural(c.unread_pages, 'page')} we could not read", "entries"),
    ])


def _survey_nos(docs: list[ECDoc], entries: list[Entry]) -> list[str]:
    out: list[str] = []
    for d in docs:
        for sn in d.header.survey_details:
            if sn not in out:
                out.append(sn)
    for e in entries:
        for s in e.schedules:
            for sn in s.survey_nos:
                if sn not in out:
                    out.append(sn)
    return out


def build_requests(docs: list[ECDoc], entries: list[Entry],
                   runs: list[RuleRun]) -> list[DocumentRequest]:
    """Every open hole in the chain, stated as something orderable.

    Two kinds, and the distinction is legally real: a window gap is a DATE RANGE
    (you order another EC); a named-but-absent parent is a DOCUMENT (you order a
    certified copy from the SRO). Where one certificate would examine several
    parents, those parents are marked superseded by it rather than listed as
    separate errands.
    """
    if not docs:
        return []
    sro = next((d.header.sro for d in docs if d.header.sro), None)
    village = next((d.header.village for d in docs if d.header.village), None)
    surveys = _survey_nos(docs, entries)

    gap = next((r for r in runs if r.rule_id == "R3" and r.outcome == "FAIL"), None)
    dangling = [r for r in runs
                if r.rule_id == "R4" and r.outcome == "REVIEW"
                and r.key.startswith("R4:parent=")]
    years = {r.key.removeprefix("R4:parent="): _year(r.key.removeprefix("R4:parent="))
             for r in dangling}

    requests: list[DocumentRequest] = []
    ec_key: str | None = None
    ec_from = ec_to = None

    if gap:
        # The gap key carries the arithmetic: R3:gap=<earliest parent>-<window − 1>.
        span = gap.key.removeprefix("R3:gap=")
        try:
            earliest, before = (int(v) for v in span.split("-"))
        except ValueError:
            earliest, before = None, None
        if earliest and before:
            ec_key, ec_from, ec_to = gap.key, earliest - ORDER_BUFFER_YEARS, before
            covered_parents = [d for d, y in years.items()
                               if y is not None and ec_from <= y <= ec_to]
            requests.append(DocumentRequest(
                key=gap.key, kind="EC_FOR_RANGE",
                because=gap.message,
                closes=[gap.key] + [f"R4:parent={d}" for d in sorted(covered_parents)],
                sro=sro, village=village, survey_nos=surveys,
                date_from=f"01-Jan-{ec_from}", date_to=f"31-Dec-{ec_to}"))

    for r in sorted(dangling, key=lambda r: r.key):
        doc_no = r.key.removeprefix("R4:parent=")
        year = years.get(doc_no)
        inside = (ec_key is not None and year is not None
                  and ec_from <= year <= ec_to)
        requests.append(DocumentRequest(
            key=r.key, kind="CERTIFIED_COPY", doc_no=doc_no,
            because=r.message, closes=[r.key],
            sro=sro, village=village,
            superseded_by=ec_key if inside else None,
            alternative=(f"The certificate above covers {ec_from}–{ec_to}, so "
                         f"ordering that one covers this document too."
                         if inside else None)))
    return requests


def derive_case(docs: list[ECDoc], *,
                reviewed: frozenset[str] | set[str] = frozenset(),
                corrections: int = 0, unread_pages: int = 0) -> DerivedView:
    """The one call the frontend makes. Pure, deterministic, unit-testable.

    A case is N certificates. The graph is built over their union, so the parent
    that dangles in the first certificate resolves the moment the second one
    arrives — that resolution is the product, and it is one `nodes.get(key)`.
    """
    entries = [e for d in docs for e in d.entries]
    edges = build_graph(entries)
    coverage = build_coverage_case(docs, entries) if docs else None
    runs = run_rules(docs, entries, edges)
    requests = build_requests(docs, entries, runs)
    completeness = build_completeness(
        docs, entries, edges, runs, reviewed, corrections=corrections,
        unread_pages=unread_pages,
        requests_open=len([r for r in requests if not r.superseded_by]))
    order = (build_order(docs[0].header, entries, coverage)
             if docs and coverage else None)
    return DerivedView(
        coverage=coverage, runs=runs, edges=edges,
        chain=build_chain(entries, edges), order=order, docs=docs,
        requests=requests, completeness=completeness,
        readiness=build_readiness(runs, completeness),
        rulebook_version=RULEBOOK_VERSION,
    )


def derive(header: ECHeader, entries: list[Entry],
           ec_id: int | None = None) -> DerivedView:
    """Single-certificate entry point. One code path underneath — this is the
    shape the rulebook tests use, and it is a case of one."""
    return derive_case([ECDoc(ec_id=ec_id, label="EC-A", header=header,
                              entries=entries)])
