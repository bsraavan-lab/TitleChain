"""One test per rule. No API calls, no database — derive() takes and returns
typed Python objects, which is exactly what makes this possible.

Run: .venv/bin/pytest -q
"""

from __future__ import annotations

import copy

import pytest

from app.derive import build_coverage, build_graph, derive
from app.fixtures import EC2_ENTRIES, EC2_HEADER
from app.models import ECHeader, Entry, PRNumber, Source


def numbered(entries: list[Entry]) -> list[Entry]:
    out = copy.deepcopy(entries)
    for i, e in enumerate(out, 1):
        e.db_id = i
    return out


@pytest.fixture
def ec2() -> tuple[ECHeader, list[Entry]]:
    return EC2_HEADER.model_copy(deep=True), numbered(EC2_ENTRIES)


def rules(view, rid: str, sev: str | None = None):
    return [f for f in view.findings
            if f.rule_id == rid and (sev is None or f.severity == sev)]


# ── the six that fire on documents we actually hold ──────────────────────────

def test_r1_cancellation_is_found_across_pages(ec2):
    """Entry 2's remarks name 2520/2019, which is entry 1. Read linearly, a dead
    lease looks like a live encumbrance."""
    view = derive(*ec2)
    fired = rules(view, "R1", "material")
    assert len(fired) == 1
    assert "8756/2020" in fired[0].message and "2520/2019" in fired[0].message


def test_r1_also_emits_a_confirmation(ec2):
    """The reassurance half. A tool that only reports problems becomes noise."""
    assert rules(derive(*ec2), "R1", "confirmation")


def test_r3_window_insufficiency(ec2):
    header, entries = ec2
    fired = rules(derive(header, entries), "R3", "blocking")
    assert len(fired) == 1
    # five parent documents, 2005–2011, against a 2018–2023 window
    assert "5 parent documents" in fired[0].message
    assert "4451/2005" in fired[0].message


def test_r3_is_silent_when_every_parent_is_inside_the_window(ec2):
    """The clean case. A detector firing on 2 of 2 inputs looks rigged."""
    header, entries = ec2
    header.search_period_start = "01-Jan-1990"
    assert not rules(derive(header, entries), "R3")
    assert derive(header, entries).coverage.sufficient is True


def test_r4_dangling_parents_are_counted_not_dropped(ec2):
    view = derive(*ec2)
    fired = rules(view, "R4", "material")
    assert "5 parent documents are named but not present" in fired[0].message
    # and the one that DOES resolve is confirmed out loud
    assert any("2520/2019" in f.message for f in rules(view, "R4", "confirmation"))


def test_r8_stale_certificate(ec2):
    assert rules(derive(*ec2), "R8", "informational")


def test_r9_catches_the_real_cell_drop(ec2):
    """The actual stage-① failure: three date cells lost inside a 0.96-confidence
    block. Sarvam's confidence is layout detection, not per-cell fidelity, so the
    completeness signal has to be ours."""
    fired = rules(derive(*ec2), "R9", "material")
    assert len(fired) == 1
    assert "Entry 2" in fired[0].message and "date registration" in fired[0].message


def test_r9_clears_when_the_advocate_supplies_the_value(ec2):
    header, entries = ec2
    entries[1].date_registration = "14-Aug-2020"
    assert not rules(derive(header, entries), "R9")


def test_r10_entry_count_checksum(ec2):
    header, entries = ec2
    assert rules(derive(header, entries), "R10", "confirmation")
    assert rules(derive(header, entries[:1]), "R10", "blocking")


# ── graph ────────────────────────────────────────────────────────────────────

def test_unresolved_pr_pointer_is_the_whole_product(ec2):
    _, entries = ec2
    edges = build_graph(entries)
    pr = [e for e in edges if e.edge_type == "PR_PARENT"]
    assert len(pr) == 6
    assert sum(1 for e in pr if e.resolved_entry_id is None) == 5


def test_unexamined_parents_appear_in_the_chain_as_open_nodes(ec2):
    view = derive(*ec2)
    flat: list = []

    def walk(n):
        flat.append(n)
        for c in n.children:
            walk(c)

    for n in view.chain:
        walk(n)
    assert sum(1 for n in flat if not n.examined) == 5
    assert any(n.cancelled_by == "8756/2020" for n in flat)


# ── coverage and the order block ─────────────────────────────────────────────

def test_order_block_matches_the_certificate_we_would_actually_order(ec2):
    view = derive(*ec2)
    assert view.order.sro == "Pollachi"
    assert view.order.village == "Puliyampatti"
    # earliest parent 2005, less the 12-year buffer, to the day before the window
    assert view.order.date_from == "01-Jan-1993"
    assert view.order.date_to == "31-Dec-2017"


def test_no_order_block_when_the_evidence_is_sufficient(ec2):
    header, entries = ec2
    header.search_period_start = "01-Jan-1990"
    assert derive(header, entries).order is None


def test_coverage_sentence_counts_documents_not_distinct_years(ec2):
    """Two parents from 2005 are one tick on a ruler but two documents in prose;
    if these disagree the verdict contradicts R3."""
    header, entries = ec2
    c = build_coverage(header, entries)
    assert "5 parent documents" in c.detail


def test_blank_search_period_is_not_evaluable(ec2):
    """ec6_thiruchengode has a blank window. Never guess — say so."""
    header, entries = ec2
    header.search_period_start = None
    c = build_coverage(header, entries)
    assert c.sufficient is None
    assert "does not state a search period" in c.headline


def test_certificate_with_no_parents_is_not_reported_as_clean(ec2):
    """The nil-EC trap: silence about the chain is not evidence about the chain."""
    header, entries = ec2
    for e in entries:
        e.pr_numbers = []
    c = build_coverage(header, entries)
    assert c.sufficient is None
    assert "not about the chain before it" in c.detail


def test_ruler_band_stays_inside_the_axis(ec2):
    c = build_coverage(*ec2)
    assert 0 <= c.band_left <= 100
    assert 0 < c.band_left + c.band_width <= 100
    assert all(0 <= c.pct(t.year) <= 100 for t in c.ticks)


# ── the null discipline ──────────────────────────────────────────────────────

def test_an_omitted_field_fails_validation_rather_than_half_typing(ec2):
    """Every extracted field is Optional with NO default, so a model that quietly
    drops one is rejected instead of producing a half-entry."""
    with pytest.raises(Exception):
        Entry(sr_no=1, doc_no="1/2020",  # doc_year and the rest omitted
              source=Source(page_num=1, block_id="b"))


def test_pr_pointers_survive_a_round_trip_through_the_schema(ec2):
    _, entries = ec2
    again = Entry.model_validate(entries[0].model_dump())
    assert again.pr_numbers == [PRNumber(doc_no=p.doc_no, year=p.year)
                                for p in entries[0].pr_numbers]
