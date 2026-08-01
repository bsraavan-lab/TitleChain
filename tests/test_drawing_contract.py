"""The keys the two drawings bind to.

The coverage ruler read `from_year` / `to_year` off each band for as long as the
React front end has existed. `CoverageBand` has always serialised `start_year` /
`end_year`. Every band therefore positioned itself at `NaN%`, the browser
dropped the declaration, and the bands simply never drew — silently, with no
error anywhere, on the one picture the product is built to show.

Nothing caught it because both halves were internally consistent: the Python was
right, the TypeScript compiled, and the interface between them was two hand-
written files that agreed with nothing. These tests are that interface. They
assert the exact field names `TabHowItConnects.tsx` and `ChainGraph.tsx` read,
so the next rename fails here instead of on a screen nobody is looking at.

Deliberately shaped as string comparisons rather than `assert "x" in body`
loops over a list built from the model — a test that derives its expectations
from the code under test cannot detect a rename.
"""

from __future__ import annotations

import copy
import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TITLECHAIN_DATA_DIR", str(tmp_path))
    import config as config_mod
    from app import (paths as paths_mod, db as db_mod, pipeline as pipeline_mod,
                     main as main_mod)
    for m in (config_mod, paths_mod, db_mod, pipeline_mod, main_mod):
        importlib.reload(m)
    main_mod.paths.ensure()
    main_mod.db.init()
    c = TestClient(main_mod.app)
    c.store = main_mod.store
    return c


@pytest.fixture
def drawn(client):
    """A case with a header and entries, so coverage and the graph both exist."""
    from app.fixtures import EC2_ENTRIES, EC2_HEADER

    case_id = client.store.create_case("ec2_pacollege.pdf")
    ec_id = client.store.save_header(
        case_id, EC2_HEADER.model_copy(deep=True),
        filename="ec2_pacollege.pdf", file_path="", page_count=3)
    client.store.save_entries(ec_id, copy.deepcopy(EC2_ENTRIES))
    return client.get(f"/api/case/{case_id}").json()


# ── the ruler ────────────────────────────────────────────────────────────────

def test_coverage_carries_the_axis_the_ruler_is_drawn_on(drawn):
    c = drawn["view"]["coverage"]
    for key in ("axis_min", "axis_max", "start_year", "end_year",
                "required_from", "required_to", "ticks", "bands",
                "sufficient", "headline", "detail"):
        assert key in c, f"the ruler reads coverage.{key}"


def test_a_band_names_its_years_start_and_end_not_from_and_to(drawn):
    """The exact regression. `from_year`/`to_year` is what the front end used to
    ask for, and asking for a key that is not there is `undefined` — which
    becomes NaN the moment it is used as a number, and NaN in a CSS length is
    dropped without complaint."""
    bands = drawn["view"]["coverage"]["bands"]
    assert bands, "a case with a readable search period has at least one band"

    band = bands[0]
    assert set(band) == {"label", "start_year", "end_year", "ec_id"}
    assert "from_year" not in band
    assert "to_year" not in band
    # And they are numbers, because `left: NaN%` is what a string year would
    # have produced just as quietly.
    assert isinstance(band["start_year"], int)
    assert isinstance(band["end_year"], int)


def test_a_tick_carries_the_year_and_whether_it_is_inside(drawn):
    ticks = drawn["view"]["coverage"]["ticks"]
    assert ticks, "EC2 names five earlier documents, so there are ticks to draw"
    assert set(ticks[0]) == {"year", "label", "inside"}


def test_the_axis_spans_every_band_and_every_tick(drawn):
    """`pos()` divides by `axis_max - axis_min` and clamps into it. A tick
    outside the axis is a mark drawn on the frame instead of the rule."""
    c = drawn["view"]["coverage"]
    assert c["axis_max"] > c["axis_min"], "a zero-width axis divides by zero"
    for t in c["ticks"]:
        assert c["axis_min"] <= t["year"] <= c["axis_max"]
    for b in c["bands"]:
        assert c["axis_min"] <= b["start_year"] <= c["axis_max"]
        assert c["axis_min"] <= b["end_year"] <= c["axis_max"]


# ── the chain drawing ────────────────────────────────────────────────────────

def test_the_graph_is_returned_with_its_geometry(drawn):
    g = drawn["graph"]
    assert set(g) == {"width", "height", "nodes", "edges", "ticks", "undated"}
    assert g["nodes"], "EC2 has entries, so it has documents to draw"


def test_a_node_carries_everything_needed_to_draw_it(drawn):
    node = drawn["graph"]["nodes"][0]
    for key in ("doc_no", "year", "nature", "kind", "shape", "entry_id",
                "ec_id", "ec_label", "x", "y", "examined", "cancelled",
                "corrected", "open_encumbrance"):
        assert key in node, f"ChainGraph reads node.{key}"
    assert node["shape"] in {"square", "diamond", "bar", "slash", "ring", "circle"}


def test_an_edge_carries_four_endpoints_and_not_a_path(drawn):
    """`GraphEdge.path` is a Python @property, and @property does not survive
    model_dump — so the front end has to rebuild the curve from the endpoints.
    If `path` ever starts arriving, the duplicated maths should go."""
    edges = drawn["graph"]["edges"]
    assert edges, "EC2 entry 1 names five parents, so there are edges"
    edge = edges[0]
    assert set(edge) == {"kind", "resolved", "x1", "y1", "x2", "y2"}
    assert "path" not in edge


def test_a_node_carries_no_label_or_title_either(drawn):
    """Same trap, same reason: both are @property. ChainGraph derives them."""
    node = drawn["graph"]["nodes"][0]
    assert "label" not in node
    assert "title" not in node


# ── the row-shaped payloads ──────────────────────────────────────────────────
#
# These carry database column names rather than the shape of the request that
# wrote them, and the front end had guessed the latter for all three. Nothing
# broke only because no screen reads them yet.

def test_reviews_is_keyed_by_finding_not_a_list(client, drawn):
    case_id = drawn["case"]["id"]
    key = drawn["view"]["runs"][0]["key"]
    client.post("/api/review", json={
        "case_id": case_id, "key": key, "state": "reviewed", "note": "checked"})

    body = client.get(f"/api/case/{case_id}").json()
    assert isinstance(body["reviews"], dict)
    assert key in body["reviews"]
    assert set(body["reviews"][key]) == {
        "id", "case_id", "finding_key", "state", "note", "actor", "created_at"}
    # The column is finding_key. It is not `key`.
    assert "key" not in body["reviews"][key]

    # And the history under the same key is a list, because reviews append.
    assert isinstance(body["review_by_key"][key], list)


def test_a_correction_carries_both_values_not_one(client, drawn):
    case_id = drawn["case"]["id"]
    entry_id = drawn["view"]["docs"][0]["entries"][0]["db_id"]
    client.post("/api/correct",
                json={"entry_id": entry_id, "field": "nature", "value": "Sale deed"})

    row = client.get(f"/api/case/{case_id}").json()["corrections"][0]
    assert set(row) == {"id", "entry_id", "field", "old_value", "new_value",
                        "actor", "created_at", "sr_no", "ec_id"}
    # `value` is what you POST. What comes back is the before and the after —
    # an undo is a new correction that reverts, so both have to survive.
    assert "value" not in row


def test_an_unexamined_parent_is_still_drawn(drawn):
    """The hole is the product. A document named by an entry but held by nobody
    gets a node like any other, drawn hollow — omitting it would hide exactly
    the thing the reader is being warned about."""
    nodes = drawn["graph"]["nodes"]
    assert any(n["examined"] is False for n in nodes)
    assert any(n["examined"] is True for n in nodes)
