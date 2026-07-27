"""The one-entry, one-month certificate — the shape the samples never had.

`ec_samples/ec_test_02.pdf` (Periyanayakkan Palayam, 01-Jan-2025 → 30-Jan-2025,
one entry, one parent) is the smallest real certificate in the corpus, and every
count in the UI is 1 on it. That is the case the plural-only sentences, the
two-ended ruler label and the case-sensitive survey merge were all written
against a two-entry document and never met.

No API calls, no database: derive() takes and returns typed Python objects.

Run: .venv/bin/pytest -q
"""

from __future__ import annotations

import pytest

from app.derive import build_coverage, build_order, derive
from app.models import ECHeader, Entry, PRNumber, Schedule, Source


@pytest.fixture
def ec_test_02() -> tuple[ECHeader, list[Entry]]:
    """Transcribed from ec_samples/ec_test_02.pdf. Header spells the survey
    numbers "94/3b"; the schedule spells the same two "94/3B". Both verbatim."""
    header = ECHeader(
        sro="Periyanayakkan Palayam",
        village="Kurudampalayam",
        survey_details=["94/3b", "94/6"],
        search_period_start="01-Jan-2025",
        search_period_end="30-Jan-2025",
        issue_date="31-Jan-2025",
        declared_entry_count=1,
    )
    entry = Entry(
        sr_no=1, doc_no="845/2025", doc_year=2025,
        date_execution="20-Jan-2025", date_presentation="20-Jan-2025",
        date_registration="20-Jan-2025", nature="Gift deed",
        executants=[], claimants=[],
        volume_page="-", consideration_value="-", market_value="ரூ. 200/-",
        pr_numbers=[PRNumber(doc_no="19803/2024", year=2024)],
        remarks=None,
        schedules=[Schedule(property_type=None, extent=None, village_street=None,
                            survey_nos=["94/3B", "94/6"], door_no=None,
                            boundaries_native=None)],
        source=Source(page_num=1, block_id="block_003",
                      bbox=[326.0, 1047.0, 3216.0, 2329.0], confidence=0.9481),
        db_id=1,
    )
    return header, [entry]


def find(view, rule_id: str, severity: str):
    return [f for f in view.findings
            if f.rule_id == rule_id and f.severity == severity]


# ── sentences an advocate signs ──────────────────────────────────────────────

def test_r3_reads_as_english_when_exactly_one_parent_predates(ec_test_02):
    view = derive(*ec_test_02)
    msg = find(view, "R3", "blocking")[0].message
    assert "1 parent document predates" in msg
    assert "parent documents" not in msg
    assert "19803/2024" in msg


def test_r4_reads_as_english_when_exactly_one_parent_dangles(ec_test_02):
    view = derive(*ec_test_02)
    msg = find(view, "R4", "material")[0].message
    assert "1 parent document is named but not present" in msg
    assert "It has not been examined" in msg


def test_coverage_detail_reads_as_english_for_one_parent(ec_test_02):
    header, entries = ec_test_02
    detail = build_coverage(header, entries).detail
    assert "1 parent document is named, from 2024" in detail
    assert "It does not fall inside this window" in detail


def test_plurals_are_untouched_above_one(ec_test_02):
    """The singular path must not have been bought by breaking the plural one."""
    header, entries = ec_test_02
    entries[0].pr_numbers = [PRNumber(doc_no="19803/2024", year=2024),
                             PRNumber(doc_no="4148/1981", year=1981)]
    view = derive(header, entries)
    assert "2 parent documents predate" in find(view, "R3", "blocking")[0].message
    assert "The earliest is 4148/1981" in find(view, "R3", "blocking")[0].message
    assert "They have not been examined" in find(view, "R4", "material")[0].message


# ── the order block, which she copies into a request ─────────────────────────

def test_one_survey_number_spelled_two_ways_is_ordered_once(ec_test_02):
    """"94/3b" and "94/3B" are the same plot. Ordering both asks the SRO for a
    survey number that does not exist."""
    header, entries = ec_test_02
    order = build_order(header, entries, build_coverage(header, entries))
    assert order.survey_nos == ["94/3b", "94/6"]
    assert order.as_text.count("94/3") == 1


def test_a_genuinely_new_schedule_survey_still_joins_the_order(ec_test_02):
    header, entries = ec_test_02
    entries[0].schedules[0].survey_nos = ["94/3B", "94/6", "101/2A"]
    order = build_order(header, entries, build_coverage(header, entries))
    assert order.survey_nos == ["94/3b", "94/6", "101/2A"]


# ── the ruler, on a window too short to label at both ends ───────────────────

def test_a_one_month_window_gets_one_label_not_two_on_top_of_each_other(ec_test_02):
    """band_width clamps to 1.5%, and two translateX(-50%) labels at 75% and
    76.5% drew "2025" over "2025". One centred label instead."""
    header, entries = ec_test_02
    c = build_coverage(header, entries)
    assert c.start_year == c.end_year == 2025
    assert c.band_is_narrow
    assert c.band_label == "2025"
    assert c.band_left <= c.band_centre <= c.band_left + c.band_width


def test_a_window_wide_enough_still_gets_both_ends(ec_test_02):
    header, entries = ec_test_02
    header.search_period_start, header.search_period_end = "01-Jan-1975", "26-Apr-2024"
    c = build_coverage(header, entries)
    assert not c.band_is_narrow
    assert (c.start_year, c.end_year) == (1975, 2024)


def test_a_narrow_window_spanning_two_years_names_both_in_one_label(ec_test_02):
    header, entries = ec_test_02
    header.search_period_start, header.search_period_end = "01-Dec-2024", "31-Jan-2025"
    entries[0].pr_numbers = [PRNumber(doc_no="4148/1981", year=1981)]
    c = build_coverage(header, entries)
    assert c.band_is_narrow
    assert c.band_label == "2024–2025"
