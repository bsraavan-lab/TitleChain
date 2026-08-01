"""The two write paths answer, and answer with every region they promise.

Both were returning 500 at HEAD. `_review_swap.html` and `_correction_swap.html`
each included `_rail_oob.html`, which has never existed — the verdict strip was
renamed to "the verdict rail" and the include followed the new name while the
file kept the old one (`_verdict_oob.html`, which nothing then included). The
correction form compounded it by targeting `#derived`, an id removed in 01afd7c.

Nothing caught it because every existing test renders GET screens. These are the
POSTs: recording a review and correcting a cell are the two things the advocate
actually DOES here, and they were the two things that could not be done.

The region assertions are the point. A correction that returns only the cell is
worse than one that 500s — the value changes on screen while the meters, the
readiness gate and the checklist keep showing conclusions drawn from the old
value, and the product's whole claim is that findings are recomputed rather than
written.
"""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

# The four regions every write must bring back, because one edit changes all of
# them. Ids, not classes: these are hx-swap-oob targets.
REGIONS = ('id="verdict-rail"', 'id="tabs"', 'id="ruler-strip"', 'id="tab-body"')


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TITLECHAIN_DATA_DIR", str(tmp_path))
    import config as config_mod
    from app import paths as paths_mod, db as db_mod, main as main_mod
    for m in (config_mod, paths_mod, db_mod, main_mod):
        importlib.reload(m)
    main_mod.paths.ensure()
    main_mod.db.init()
    c = TestClient(main_mod.app)
    c.store = main_mod.store
    return c


@pytest.fixture
def seeded(client):
    """A case with a real certificate and real entries on disk.

    `create_case` alone gives a row with nothing in it, and `/correct` needs an
    entry that actually exists — the correction is applied to a database row, not
    to a view model."""
    import copy
    from app.fixtures import EC2_ENTRIES, EC2_HEADER

    from app import db

    case_id = client.store.create_case("ec2_pacollege.pdf")
    ec_id = client.store.save_header(
        case_id, EC2_HEADER.model_copy(deep=True),
        filename="ec2_pacollege.pdf", file_path="", page_count=3)
    client.store.save_entries(ec_id, copy.deepcopy(EC2_ENTRIES))

    entry_id = db.one(
        "SELECT id FROM entries WHERE ec_id = ? ORDER BY id LIMIT 1", (ec_id,))["id"]
    return case_id, entry_id


def test_recording_a_review_answers(client):
    case_id = client.store.create_case("ec_test_01.pdf")
    r = client.post("/review", data={
        "case_id": case_id, "key": "R3:gap=2005-2017",
        "state": "reviewed", "note": "checked against the parent", "tab": "review"})
    assert r.status_code == 200


def test_a_review_brings_back_every_region_it_changes(client):
    """Marking an item reviewed moves the checklist, the counts, the readiness
    gate and the meters. All four arrive in one response so they cannot disagree
    on screen."""
    case_id = client.store.create_case("ec_test_01.pdf")
    body = client.post("/review", data={
        "case_id": case_id, "key": "R3:gap=2005-2017",
        "state": "reviewed", "note": "", "tab": "review"}).text

    for region in REGIONS:
        assert region in body, f"the review response dropped {region}"


def test_correcting_a_cell_answers(client, seeded):
    case_id, entry_id = seeded
    r = client.post("/correct", data={
        "entry_id": entry_id, "field": "date_registration",
        "value": "05-Aug-2020", "case_id": case_id, "tab": "entries"})
    assert r.status_code == 200


def test_a_correction_brings_back_every_region_it_changes(client, seeded):
    case_id, entry_id = seeded
    body = client.post("/correct", data={
        "entry_id": entry_id, "field": "date_registration",
        "value": "05-Aug-2020", "case_id": case_id, "tab": "entries"}).text

    for region in REGIONS:
        assert region in body, f"the correction response dropped {region}"


def test_the_edit_form_targets_something_that_exists(client, seeded):
    """The form posted to `#derived`, an id no template emits any more, so the
    answer had nowhere to land. It targets the cell, which is what the response
    leads with and what Escape restores."""
    case_id, entry_id = seeded
    body = client.get(f"/entry/{entry_id}/edit/date_registration",
                      params={"case_id": case_id}).text

    assert 'hx-target="closest td"' in body
    assert "#derived" not in body


def test_every_template_a_write_includes_actually_exists(client):
    """The regression was an include naming a file that was never added. Jinja
    only raises when the branch renders, so a swap template can be broken for
    weeks while every GET test passes."""
    from app import main as main_mod
    env = main_mod.templates.env
    for name in ("_review_swap.html", "_correction_swap.html",
                 "_verdict_poll.html", "_tab_swap.html"):
        env.get_template(name)          # raises TemplateNotFound on a bad include
