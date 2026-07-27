"""The case: N certificates, one chain. Plus the layout geometry.

No API calls, no database — `derive_case` and `build_layout` take and return typed
Python objects, which is exactly what makes this possible.
"""

from __future__ import annotations

import copy
import pathlib

import pytest

from app.derive import build_completeness, build_graph, derive_case, required_span
from app.fixtures import EC2_ENTRIES, EC2_HEADER
from app.layout import build_layout
from app.models import ECDoc, ECHeader, Entry, Party, PRNumber, Schedule, Source


def entry(sr_no: int, doc_no: str, year: int, nature: str, *,
          prs: tuple[str, ...] = (), db_id: int | None = None,
          remarks: str | None = None) -> Entry:
    return Entry(
        sr_no=sr_no, doc_no=doc_no, doc_year=year,
        date_execution=None, date_presentation=None,
        date_registration=f"01-Jan-{year}", nature=nature,
        executants=[], claimants=[], volume_page=None,
        consideration_value=None, market_value=None, remarks=remarks,
        pr_numbers=[PRNumber(doc_no=p, year=int(p.split("/")[-1])) for p in prs],
        schedules=[], source=Source(page_num=1, block_id="b", bbox=None,
                                    confidence=0.9),
        db_id=db_id,
    )


def header(start: str, end: str, *, issue: str = "01-Jan-2026") -> ECHeader:
    return ECHeader(sro="Pollachi", village="Puliyampatti", survey_details=["95/2"],
                    search_period_start=start, search_period_end=end,
                    issue_date=issue, declared_entry_count=None)


@pytest.fixture
def ec_a() -> ECDoc:
    entries = copy.deepcopy(EC2_ENTRIES)
    for i, e in enumerate(entries, 1):
        e.db_id = i
    return ECDoc(ec_id=1, label="EC-A", header=EC2_HEADER.model_copy(deep=True),
                 entries=entries)


# ── the merge: what a second certificate actually does ────────────────────────

def test_a_second_certificate_resolves_a_dangling_parent(ec_a):
    """The whole product, in one assertion. 4451/2005 dangles on EC-A alone; the
    moment a certificate containing it joins the case, `nodes.get(key)` finds it."""
    before = derive_case([ec_a])
    assert "R4:parent=4451/2005" in {r.key for r in before.runs}

    ec_b = ECDoc(ec_id=2, label="EC-B", header=header("01-Jan-1993", "31-Dec-2017"),
                 entries=[entry(1, "4451/2005", 2005, "Sale deed", db_id=10)])
    after = derive_case([ec_a, ec_b])

    resolved = next(r for r in after.runs if r.key == "R4:resolved=4451/2005")
    assert resolved.outcome == "PASS"
    assert "R4:parent=4451/2005" not in {r.key for r in after.runs}
    assert after.completeness.links_examined == 2       # 2520/2019 and 4451/2005


def test_the_window_gap_closes_when_a_covering_certificate_arrives(ec_a):
    """R3 is a statement about the CASE, not about one certificate: a parent year is
    covered when it falls inside any window on the case."""
    assert derive_case([ec_a]).run("R3:gap=2005-2017").outcome == "FAIL"

    ec_b = ECDoc(ec_id=2, label="EC-B", header=header("01-Jan-1990", "31-Dec-2017"),
                 entries=[entry(1, "9/1990", 1990, "Sale deed", db_id=10)])
    after = derive_case([ec_a, ec_b])
    assert after.run("R3:covered").outcome == "PASS"
    assert not [r for r in after.runs if r.rule_id == "R3" and r.outcome == "FAIL"]


def test_review_state_survives_a_second_certificate(ec_a):
    """Keys are subject-scoped, so a note the advocate wrote against R1 stays
    attached to R1 when the case grows. This is what makes the workflow feel like
    completing a history rather than restarting an analysis."""
    reviewed = {"R1:cancelled=2520/2019", "R4:parent=4755/2011"}
    before = derive_case([ec_a], reviewed=reviewed)
    assert before.completeness.review_done == 2

    ec_b = ECDoc(ec_id=2, label="EC-B", header=header("01-Jan-1993", "31-Dec-2017"),
                 entries=[entry(1, "4451/2005", 2005, "Sale deed", db_id=10)])
    after = derive_case([ec_a, ec_b], reviewed=reviewed)
    # R1's key is untouched; R4:parent=4755/2011 is still open and still reviewed
    assert "R1:cancelled=2520/2019" in {r.key for r in after.runs}
    assert after.completeness.review_done == 2


def test_per_certificate_rules_stay_attached_to_their_certificate(ec_a):
    """R8, R9 and R10 are statements about ONE document. Two certificates means two
    staleness runs, keyed apart, so a note on one cannot migrate to the other."""
    ec_b = ECDoc(ec_id=2, label="EC-B", header=header("01-Jan-1993", "31-Dec-2017"),
                 entries=[entry(1, "4451/2005", 2005, "Sale deed", db_id=10)])
    keys = {r.key for r in derive_case([ec_a, ec_b]).runs if r.rule_id == "R8"}
    assert keys == {"R8:stale=ec:1", "R8:stale=ec:2"}


def test_the_case_ruler_gets_one_band_per_certificate(ec_a):
    ec_b = ECDoc(ec_id=2, label="EC-B", header=header("01-Jan-1993", "31-Dec-2017"),
                 entries=[entry(1, "4451/2005", 2005, "Sale deed", db_id=10)])
    bands = derive_case([ec_a, ec_b]).coverage.bands
    assert [(b.label, b.start_year, b.end_year) for b in bands] == [
        ("EC-A", 2018, 2023), ("EC-B", 1993, 2017)]


# ── completeness: counts, no weights ──────────────────────────────────────────

def test_chain_completeness_is_a_ratio_of_links_not_a_score(ec_a):
    c = derive_case([ec_a]).completeness
    assert (c.links_examined, c.links_named) == (1, 6)
    assert c.chain_pct == round(1 / 6 * 100)
    assert c.chain_arithmetic == "1 of 6 parent documents examined"


def test_coverage_counts_years_inside_any_window_on_the_case(ec_a):
    c = derive_case([ec_a]).completeness
    assert c.years_covered == 6                 # 2018..2023 inclusive
    assert c.span_from == 2005                  # the earliest parent, not the floor
    assert c.years_required == c.span_to - c.span_from + 1


def test_a_case_with_no_parents_is_not_reported_as_a_broken_chain(ec_a):
    for e in ec_a.entries:
        e.pr_numbers = []
    c = derive_case([ec_a]).completeness
    assert c.links_named == 0
    assert c.chain_pct == 100                   # nothing named, nothing missing
    assert "no parent document" in c.chain_arithmetic


def test_required_span_reaches_back_to_the_earliest_parent():
    """Thirteen years is the convention; a chain does not stop being a chain because
    the convention ran out."""
    e = entry(1, "1/2024", 2024, "Sale deed", prs=("5/1961",), db_id=1)
    start, end = required_span([e], [(2020, 2024, "EC-A")])
    assert start == 1961
    assert end >= 2026


# ── readiness: gates, not a score ─────────────────────────────────────────────

def test_readiness_is_never_a_percentage(ec_a):
    r = derive_case([ec_a]).readiness
    assert r.ready is False
    assert r.label == "Not ready to opine"
    assert [g.id for g in r.gates] == ["G1", "G2", "G3", "G4", "G5"]
    assert not any("%" in g.label for g in r.gates)


def test_a_clean_case_passes_every_gate():
    doc = ECDoc(ec_id=1, label="EC-A", header=header("01-Jan-1990", "31-Dec-2026"),
                entries=[entry(1, "1/2020", 2020, "Sale deed", db_id=1)])
    view = derive_case([doc], reviewed={r.key for r in derive_case([doc]).open_runs})
    assert view.readiness.ready, [g.label for g in view.readiness.unmet]
    assert view.readiness.label == "Ready to opine"


def test_the_verdict_leads_with_a_blocking_finding_not_with_good_news():
    """Coverage used to be the verdict unconditionally, which produced a
    contradiction: the rail said every parent falls inside a window while the gate
    line said a blocking finding remained."""
    doc = ECDoc(ec_id=1, label="EC-A", header=header("01-Jan-1990", "31-Dec-2026"),
                entries=[entry(1, "1/2011", 2011, "Mortgage deed", db_id=1)])
    view = derive_case([doc])
    assert view.coverage.sufficient is not False       # coverage is fine
    assert "still open" in view.verdict                # the mortgage is not


# ── document requests: one errand, not six ────────────────────────────────────

def test_one_certificate_supersedes_the_parents_it_would_examine(ec_a):
    view = derive_case([ec_a])
    live = view.requests_live
    assert len(live) == 1
    assert live[0].kind == "EC_FOR_RANGE"
    assert (live[0].date_from, live[0].date_to) == ("01-Jan-1993", "31-Dec-2017")
    superseded = [r for r in view.requests if r.superseded_by]
    assert {r.doc_no for r in superseded} == {
        "4451/2005", "4453/2005", "4581/2007", "4582/2007", "4755/2011"}


def test_every_dangling_parent_is_closed_by_something(ec_a):
    view = derive_case([ec_a])
    for r in view.runs:
        if r.rule_id == "R4" and r.outcome == "REVIEW":
            assert view.closer_for(r.key) is not None


# ── layout: deterministic geometry ────────────────────────────────────────────

def test_the_layout_is_byte_identical_across_runs(ec_a):
    """A graph that reshuffles on reload is a graph nobody trusts."""
    entries = ec_a.entries
    edges = build_graph(entries)
    a = build_layout([ec_a], entries, edges)
    b = build_layout([ec_a], entries, edges)
    assert a.model_dump() == b.model_dump()


def test_unexamined_parents_get_nodes_drawn_hollow(ec_a):
    entries = ec_a.entries
    g = build_layout([ec_a], entries, build_graph(entries))
    hollow = [n for n in g.nodes if not n.examined]
    assert {n.doc_no for n in hollow} == {
        "4451/2005", "4453/2005", "4581/2007", "4582/2007", "4755/2011"}
    assert all(n.entry_id is None for n in hollow)


def test_x_is_the_year_so_the_gap_is_visible(ec_a):
    entries = ec_a.entries
    g = build_layout([ec_a], entries, build_graph(entries))
    by_doc = {n.doc_no: n for n in g.nodes}
    assert by_doc["4451/2005"].x < by_doc["8756/2020"].x
    assert [t.year for t in g.ticks] == sorted({n.year for n in g.nodes})


def test_a_document_with_no_readable_year_is_listed_not_guessed():
    """Placing an undated document at a guessed point on a year axis invents a
    fact. It is named underneath instead."""
    e = entry(1, "1/2020", 2020, "Sale deed", db_id=1)
    e.pr_numbers = [PRNumber(doc_no="no-year", year=0)]
    doc = ECDoc(ec_id=1, label="EC-A", header=header("01-Jan-2019", "31-Dec-2021"),
                entries=[e])
    g = build_layout([doc], [e], build_graph([e]))
    assert "no-year" in g.undated
    assert "no-year" not in {n.doc_no for n in g.nodes}


def test_node_shape_carries_meaning_alongside_colour(ec_a):
    """So the graph survives grey printing and colour-blindness."""
    entries = ec_a.entries
    entries[0].nature = "Mortgage deed"
    g = build_layout([ec_a], entries, build_graph(entries))
    shapes = {n.doc_no: n.shape for n in g.nodes}
    assert shapes["2520/2019"] == "diamond"          # encumbrance
    assert shapes["8756/2020"] == "slash"            # cancellation
    assert shapes["4451/2005"] == "circle"           # unexamined, nature unknown


# ── the bundle split: one file, two certificates ──────────────────────────────

def _dig(page_texts: dict[int, list[str]]):
    """A Digitised built by hand: {page_num: [block texts]}."""
    from app.digitise import Block, Digitised, Page
    pages = [
        Page(page_num=n, width=100, height=100, blocks=[
            Block(block_id=f"p{n}b{i}", page_num=n, bbox=None, layout_tag="table",
                  confidence=0.9, reading_order=i, text=t)
            for i, t in enumerate(texts)])
        for n, texts in sorted(page_texts.items())
    ]
    return Digitised(pages=pages, markdown="", source_dir=pathlib.Path("."),
                     from_cache=True)


def test_a_single_certificate_is_one_range():
    from app.extract import certificate_ranges
    dig = _dig({1: ["தேடுதல் காலம்: 01-Jan-2018 - 18-Jun-2023"], 2: ["rows"],
                3: ["rows"]})
    assert certificate_ranges(dig) == [(1, 3)]


def test_two_certificates_in_one_file_are_split_by_their_own_headers():
    """The ec5 shape: pages 1–3 are one certificate, pages 4–5 a Nil EC for the same
    property. Mapping the file to ONE certificate files the Nil EC's entries under
    the first one's search period — the product's own central failure mode,
    reproduced inside our data model."""
    from app.extract import certificate_ranges, certificate_starts
    dig = _dig({
        1: ["Search Period: 11-Sep-2023 - 04-Apr-2024"],
        2: ["entry rows"],
        3: ["entry rows"],
        4: ["தேடுதல் காலம்: 01-Apr-2024 - 09-May-2024"],
        5: ["nil"],
    })
    assert certificate_starts(dig) == [1, 4]
    assert certificate_ranges(dig) == [(1, 3), (4, 5)]


def test_a_file_with_no_search_period_is_still_one_certificate():
    """ec6 has a blank search-period field. That is an R3 condition, not a reason to
    produce zero certificates."""
    from app.extract import certificate_ranges
    assert certificate_ranges(_dig({1: ["no header markers"], 2: ["rows"]})) == [(1, 2)]


def test_slicing_keeps_the_page_numbers_the_advocate_will_look_at():
    from app.digitise import slice_pages
    dig = _dig({1: ["Search Period: a - b"], 2: ["x"], 3: ["y"],
                4: ["தேடுதல் காலம்: c - d"], 5: ["z"]})
    part = slice_pages(dig, 4, 5)
    assert [p.page_num for p in part.pages] == [4, 5]
    assert all(b.page_num >= 4 for p in part.pages for b in p.blocks)
