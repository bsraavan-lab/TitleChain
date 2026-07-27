"""One test per rule. No API calls, no database — derive() takes and returns
typed Python objects, which is exactly what makes this possible.

Run: .venv/bin/pytest -q
"""

from __future__ import annotations

import copy

import pytest

from app.derive import RULEBOOK, build_coverage, build_graph, derive
from app.fixtures import EC2_ENTRIES, EC2_HEADER
from app.models import OPEN_OUTCOMES, ECHeader, Entry, PRNumber, Source


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
    # five earlier documents, 2005–2011, against a 2018–2023 window
    assert "5 earlier documents" in fired[0].message
    assert "4451/2005" in fired[0].message


def test_r3_is_silent_when_every_parent_is_inside_the_window(ec2):
    """The clean case. A detector firing on 2 of 2 inputs looks rigged."""
    header, entries = ec2
    header.search_period_start = "01-Jan-1990"
    assert not rules(derive(header, entries), "R3")
    assert derive(header, entries).coverage.sufficient is True


def test_r4_dangling_parents_are_counted_not_dropped(ec2):
    """One dangling parent is one obligation, so it is one finding.

    This rule used to emit a single aggregate ("5 parent documents are named but
    not present: …"). That form cannot be marked reviewed one at a time, resolved
    one at a time, or have an uploaded certificate attributed to it — so it is now
    one run per parent document, keyed on the document number.
    """
    view = derive(*ec2)
    fired = rules(view, "R4", "material")
    assert len(fired) == 5
    assert {f.key for f in fired} == {
        "R4:parent=4451/2005", "R4:parent=4453/2005", "R4:parent=4581/2007",
        "R4:parent=4582/2007", "R4:parent=4755/2011",
    }
    assert all("nobody has read what is inside it" in f.message
               for f in fired)
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
    assert "5 earlier documents" in c.detail


def test_blank_search_period_is_not_evaluable(ec2):
    """ec6_thiruchengode has a blank window. Never guess — say so."""
    header, entries = ec2
    header.search_period_start = None
    c = build_coverage(header, entries)
    assert c.sufficient is None
    assert "does not say which years it covers" in c.headline


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


# ── the rule-run contract: every rule reports, on every derivation ────────────

def test_every_rule_in_the_rulebook_reports_an_outcome(ec2):
    """A rule that returns nothing is indistinguishable from a rule that passed.
    Ten rules in, ten rules accounted for — on any input."""
    blank = ECHeader(sro=None, village=None, survey_details=[],
                     search_period_start=None, search_period_end=None,
                     issue_date=None, declared_entry_count=None)
    for header, entries in (ec2, (ec2[0], []), (blank, [])):
        reported = {r.rule_id for r in derive(header, entries).runs}
        assert reported == set(RULEBOOK), f"missing: {set(RULEBOOK) - reported}"


def test_a_check_that_did_not_run_must_say_why(ec2):
    """NOT_APPLICABLE / NOT_EVALUABLE without a reason is the refusal screen's
    forbidden move — claiming a check you did not make."""
    header, entries = ec2
    header.search_period_start = header.search_period_end = None
    header.issue_date = None
    header.declared_entry_count = None
    for run in derive(header, entries).runs:
        if run.outcome in ("NOT_APPLICABLE", "NOT_EVALUABLE"):
            assert run.reason, f"{run.rule_id} {run.key} concluded nothing silently"


def test_unimplemented_rules_are_not_reported_as_passing(ec2):
    """R5, R6 and R7 have no implementation in v1.0. Showing them as passed would
    tell an advocate we checked something we did not."""
    runs = {r.rule_id: r for r in derive(*ec2).runs}
    for rid in ("R5", "R6", "R7"):
        assert runs[rid].outcome == "NOT_EVALUABLE"
        assert runs[rid].implemented is False
        assert runs[rid].severity is None       # never enters the findings list


def test_findings_are_exactly_the_runs_that_concluded_something(ec2):
    view = derive(*ec2)
    assert {f.key for f in view.findings} == {
        r.key for r in view.runs if r.severity is not None}


def test_r3_pass_does_not_manufacture_a_duplicate_finding(ec2):
    """The coverage headline already says every parent falls inside the window, so
    R3's PASS carries no severity — a checklist row, not a second sentence."""
    header, entries = ec2
    header.search_period_start = "01-Jan-1990"
    view = derive(header, entries)
    assert view.run("R3:covered").outcome == "PASS"
    assert not rules(view, "R3")


def test_open_items_are_the_ones_needing_a_human(ec2):
    view = derive(*ec2)
    assert all(r.outcome in OPEN_OUTCOMES for r in view.open_runs)
    assert view.open_runs[0].rule_id == "R3"        # ranked worst-first
    assert view.open_runs[0].outcome == "FAIL"


# ── finding_key stability: what makes review notes survive ────────────────────

def test_correcting_a_field_leaves_every_unrelated_key_untouched(ec2):
    """Review state keys on finding_key. If a correction reshuffled keys, the
    advocate's notes would silently reattach to different obligations."""
    header, entries = ec2
    before = {r.key for r in derive(header, entries).runs}

    entries[1].date_registration = "14-Aug-2020"           # clears one R9 row
    after = {r.key for r in derive(header, entries).runs}

    resolved, appeared = before - after, after - before
    assert resolved == {"R9:ec:0/sr:2/date_registration"}
    assert appeared == {"R9:complete=ec:0"}
    assert before - resolved == after - appeared            # everything else identical


def test_r9_keys_on_the_certificates_own_numbering_not_the_document_number(ec2):
    """doc_no is unusable as a key here: it may itself be the unreadable field."""
    header, entries = ec2
    entries[1].doc_no = None
    keys = {r.key for r in derive(header, entries, ec_id=7).runs if r.rule_id == "R9"}
    assert "R9:ec:7/sr:2/doc_no" in keys
    assert not any("None" in k for k in keys)


def test_r4_key_names_the_parent_document_because_that_is_what_an_upload_fixes(ec2):
    dangling = [r for r in derive(*ec2).runs
                if r.rule_id == "R4" and r.outcome == "REVIEW"]
    assert {r.key for r in dangling} == {f"R4:parent={d}" for d in (
        "4451/2005", "4453/2005", "4581/2007", "4582/2007", "4755/2011")}


def test_rules_show_their_working(ec2):
    """'Why did this fire?' must be answerable from the run itself — the rule
    already knew its inputs, it simply never reported them."""
    r3 = derive(*ec2).run("R3:gap=2005-2017")
    labels = {i.label: i.value for i in r3.inputs}
    assert labels["years EC-A covers"] == "01-Jan-2018 → 18-Jun-2023"
    assert (labels["years of the earlier documents"]
            == "2005, 2005, 2007, 2007, 2011, 2019")
    assert labels["what we looked for"] == "anything earlier than 2018 → 5 found"
    assert r3.pages and r3.pages[0].page_num == 1


# ── R2 LIVE_ENCUMBRANCE ───────────────────────────────────────────────────────

def test_r2_is_not_applicable_when_no_entry_is_an_encumbrance(ec2):
    """Pollachi is a lease and a cancellation. 'Not applicable' with its reason —
    never silence, and never a pass that implies we found nothing open."""
    run = next(r for r in derive(*ec2).runs if r.rule_id == "R2")
    assert run.outcome == "NOT_APPLICABLE"
    assert run.reason and "not one of them creates a claim" in run.reason


def test_r2_fires_on_a_mortgage_with_no_discharge(ec2):
    """The real Erumaipatti fact pattern: a 1985 mortgage without possession, in a
    window running to 2024, with no release naming it."""
    header, entries = ec2
    entries[0].nature = "சுவாதீனமில்லாத அடைமானம்"      # mortgage without possession
    entries[0].remarks = "ஈடு ரூ.3300/- வட்டி 10%"
    entries[1].nature = "விற்பனை"                       # a sale, not a discharge
    entries[1].remarks = None
    run = next(r for r in derive(header, entries).runs if r.rule_id == "R2")
    assert run.outcome == "FAIL"
    assert run.severity == "blocking"
    assert run.key == "R2:enc=2520/2019"
    assert "still open" in run.message


def test_r2_recognises_the_english_form_of_the_same_instrument(ec2):
    """ec3 says "Mortgage without possession deed" for what ec4 writes in Tamil.
    One taxonomy, both spellings, or the rule fires on one certificate and not the
    other for no reason the advocate can see."""
    header, entries = ec2
    entries[0].nature = "Mortgage without possession deed"
    entries[1].nature = "Gift deed"
    entries[1].remarks = None
    assert next(r for r in derive(header, entries).runs
                if r.rule_id == "R2").outcome == "FAIL"


def test_r2_will_not_call_an_unnamed_release_a_discharge(ec2):
    """A release deed that names nothing may be a family release of an interest,
    not a redemption. Treating it as one asserts 'not a live charge' about a live
    charge — wrong in the dangerous direction."""
    header, entries = ec2
    entries[0].nature = "Mortgage deed"
    entries[1].nature = "Release deed"
    entries[1].remarks = None
    entries[1].pr_numbers = []
    assert next(r for r in derive(header, entries).runs
                if r.rule_id == "R2").outcome == "FAIL"


def test_r2_clears_when_a_discharge_names_the_mortgage(ec2):
    header, entries = ec2
    entries[0].nature = "Mortgage deed"
    entries[1].nature = "Release deed"
    entries[1].remarks = None
    entries[1].pr_numbers = [PRNumber(doc_no="2520/2019", year=2019)]
    run = next(r for r in derive(header, entries).runs if r.rule_id == "R2")
    assert run.outcome == "PASS"
    assert run.severity == "confirmation"
    assert "discharged" in run.message


def test_r2_reports_a_cancelled_mortgage_as_cancelled_not_open(ec2):
    """Pollachi's own grammar: 8756/2020 cancels 2520/2019. If that had been a
    mortgage, it is not an open charge — and R1 already proved the cancellation."""
    header, entries = ec2
    entries[0].nature = "Mortgage deed"
    run = next(r for r in derive(header, entries).runs if r.rule_id == "R2")
    assert run.outcome == "PASS"
    assert "cancelled" in run.message


def test_r2_cannot_be_evaluated_when_a_nature_was_not_read(ec2):
    """Saying "no encumbrance on this case" while a nature cell is blank is the
    false reassurance the rulebook exists to prevent."""
    header, entries = ec2
    entries[1].nature = None
    runs = [r for r in derive(header, entries, ec_id=4).runs if r.rule_id == "R2"]
    ne = [r for r in runs if r.outcome == "NOT_EVALUABLE"]
    assert ne and ne[0].key == "R2:unread-nature=ec:4/sr:2"
    assert not any(r.outcome == "NOT_APPLICABLE" for r in runs)


def test_r2_flags_a_nature_it_does_not_recognise(ec2):
    """An unrecognised nature must fall through to "could not check", never to
    "no encumbrance found"."""
    header, entries = ec2
    entries[0].nature = "Deed of some kind we have never seen"
    entries[1].nature = "Another unfamiliar instrument"
    entries[1].remarks = None
    run = next(r for r in derive(header, entries).runs if r.rule_id == "R2")
    assert run.outcome == "NOT_EVALUABLE"
    assert "Types we did not recognise" in run.reason


def test_release_is_a_discharge_and_not_a_lease(ec2):
    """'Release deed' contains the substring 'lease'. Unanchored, the taxonomy
    classified a mortgage release AS a lease — which is how a discharged charge
    gets reported as still open. Latin terms are anchored; this is the guard."""
    from app.derive import nature_kind
    assert nature_kind("Release deed") == "discharge"
    assert nature_kind("Lease deed") == "lease"
    assert nature_kind("Deed of release of mortgage") == "discharge"
    assert nature_kind("Mortgage without possession deed") == "encumbrance"
    assert nature_kind("சுவாதீனமில்லாத அடைமானம்") == "encumbrance"
    assert nature_kind("விற்பனை") == "transfer"
    assert nature_kind(None) is None
    assert nature_kind("Some instrument we have never seen") is None
