"""The checklist collapses a family of runs into one row without losing any.

R4 fires once per unresolved parent, so a certificate naming five of them
produced five checklist rows differing only in the number inside them. Five rows
that say the same sentence teach the eye to skim exactly where it should stop.

The grouping is presentational and must stay that way: every run still exists,
still carries its own key, and is still individually addressable — because each
one can be expanded, cited and signed off on its own.
"""

from __future__ import annotations

import copy

import pytest

from app.derive import derive
from app.fixtures import EC2_ENTRIES, EC2_HEADER
from app.models import Entry


def numbered(entries: list[Entry]) -> list[Entry]:
    out = copy.deepcopy(entries)
    for i, e in enumerate(out, 1):
        e.db_id = i
    return out


@pytest.fixture
def view():
    return derive(copy.deepcopy(EC2_HEADER), numbered(EC2_ENTRIES))


def test_the_five_unread_parents_become_one_row(view):
    groups = [i for i in view.runs_grouped if i.grouped]
    assert len(groups) == 1

    group = groups[0]
    assert group.lead.rule_id == "R4"
    assert group.family == "R4:parent"
    assert len(group.members) == 5
    assert group.subjects == ["4451/2005", "4453/2005", "4581/2007",
                              "4582/2007", "4755/2011"]


def test_grouping_loses_no_run(view):
    """The row count drops; the run count must not."""
    flattened = [m for item in view.runs_grouped for m in item.members]
    assert len(flattened) == len(view.runs_ranked)
    assert {r.key for r in flattened} == {r.key for r in view.runs_ranked}
    assert len(view.runs_grouped) < len(view.runs_ranked)


def test_every_run_is_still_addressable_by_key(view):
    """Each member keeps its own key, which is what the expand, the evidence
    link and the sign-off are all keyed on."""
    for item in view.runs_grouped:
        for member in item.members:
            assert view.run(member.key) is member


def test_a_group_states_its_case_over_the_whole_set(view):
    """The lead member's own sentence names one document. A title that has just
    counted five of them must not be followed by a sentence about one."""
    group = next(i for i in view.runs_grouped if i.grouped)
    assert group.title == "5 earlier documents are named that nobody has read"
    assert "4451/2005" not in group.message
    assert group.message != group.lead.message


def test_a_lone_run_keeps_its_own_words(view):
    """Only a family is rewritten. Everything else reads as derive() wrote it."""
    for item in view.runs_grouped:
        if not item.grouped:
            assert item.title == item.lead.title
            assert item.message == item.lead.message


def test_runs_that_differ_in_outcome_do_not_merge(view):
    """R4 also emits a PASS for the parent that WAS resolved. A passed check and
    a failed one are never the same row, whatever rule they came from."""
    r4_rows = [i for i in view.runs_grouped if i.lead.rule_id == "R4"]
    assert len(r4_rows) == 2
    assert {i.lead.outcome for i in r4_rows} == {"REVIEW", "PASS"}
