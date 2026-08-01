"""The JSON contract the React front end reads.

These are seam tests. The front end is a separate codebase compiled from typed
fixtures, so the only thing keeping it honest is that these keys keep existing
and keep meaning what they meant. A rename here is a silent blank screen there.

They also pin the property that matters most: the JSON and the server-rendered
screens come from ONE derive_case(), so the two cannot disagree about what a
certificate proves.
"""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TITLECHAIN_DATA_DIR", str(tmp_path))
    import config as config_mod
    from app import (paths as paths_mod, db as db_mod, pipeline as pipeline_mod,
                     main as main_mod)
    # pipeline does `from .paths import UPLOADS`, which binds the value at import
    # time — so reloading paths alone leaves it writing to the previous test's
    # data dir. It has to be reloaded between paths and main.
    for m in (config_mod, paths_mod, db_mod, pipeline_mod, main_mod):
        importlib.reload(m)
    main_mod.paths.ensure()
    main_mod.db.init()
    c = TestClient(main_mod.app)
    c.store = main_mod.store
    return c


def test_the_case_list_is_json_and_empty_before_anything_is_uploaded(client):
    r = client.get("/api/cases")
    assert r.status_code == 200
    assert r.json() == {"cases": []}


def test_a_case_appears_in_the_list_carrying_its_state(client):
    client.store.create_case("ec_test_01.pdf")
    body = client.get("/api/cases").json()

    assert len(body["cases"]) == 1
    row = body["cases"][0]
    # The keys the home screen binds to. Renaming any of them blanks a column.
    for key in ("id", "property_key", "status", "processing", "header",
                "coverage", "open_count"):
        assert key in row


def test_a_missing_case_answers_instead_of_500ing(client):
    """A bookmarked case id that no longer resolves is an ordinary Tuesday on a
    host with an ephemeral disk — the same reason the HTML routes redirect
    rather than error."""
    for path in ("/api/case/999", "/api/case/999/status"):
        r = client.get(path)
        assert r.status_code == 200
        assert r.json()["error"] == "not_found"


def test_the_case_payload_carries_every_section_a_screen_needs(client):
    """One request, because every tab is a view of the same derivation. Split
    into five and the checklist could disagree with the chain about one
    certificate, which is the failure this product cannot have."""
    case_id = client.store.create_case("ec_test_01.pdf")
    body = client.get(f"/api/case/{case_id}").json()

    assert set(body) >= {"case", "view", "reviews", "review_by_key",
                         "corrections", "unread", "graph", "cost"}
    assert set(body["view"]) >= {"coverage", "completeness", "readiness", "runs",
                                 "edges", "chain", "docs", "requests",
                                 "rulebook_version"}
    assert set(body["cost"]) == {"estimate", "actual", "ledger"}


def test_status_stays_small_because_it_is_polled(client):
    """The working screen hits this on a timer while a background thread runs.
    If it ever grows a derivation it becomes a per-second re-derive."""
    case_id = client.store.create_case("ec_test_01.pdf")
    body = client.get(f"/api/case/{case_id}/status").json()

    assert set(body) == {"id", "status", "status_detail", "processing",
                         "pages_total"}


def test_mounting_the_api_left_the_rendered_screens_alone(client):
    """The migration proceeds one screen at a time, so the Jinja app has to keep
    answering for exactly as long as it takes."""
    assert client.get("/").status_code == 200
    case_id = client.store.create_case("ec_test_01.pdf")
    assert client.get(f"/case/{case_id}").status_code == 200


# ── writes ───────────────────────────────────────────────────────────────────

def test_a_rejected_upload_answers_with_the_reason_not_a_status_code(client):
    """The reason is rendered where the file was dropped, because the fix is to
    pick a different file and that control is right there. A bare 4xx would make
    the front end invent the sentence, and it would invent a worse one."""
    r = client.post("/api/upload",
                    files={"file": ("notes.txt", b"not a certificate", "text/plain")})
    assert r.status_code == 200
    body = r.json()
    assert body["error"] == "rejected"
    assert body["detail"]                       # a sentence, not a code


def test_an_unknown_sample_is_refused_by_name(client):
    body = client.post("/api/sample/not-a-sample").json()
    assert body["error"] == "rejected"


def test_a_note_against_a_finding_persists_and_reads_back(client):
    case_id = client.store.create_case("ec_test_01.pdf")
    key = "R3:gap=2005-2017"

    assert client.post("/api/review", json={
        "case_id": case_id, "key": key,
        "state": "reviewed", "note": "checked against the parent"}).json() == {"ok": True}

    assert key in client.get(f"/api/case/{case_id}").json()["reviews"]


def test_writing_against_a_case_that_is_gone_answers_instead_of_500ing(client):
    body = client.post("/api/review", json={
        "case_id": 999, "key": "R1:x", "state": "reviewed"}).json()
    assert body["error"] == "not_found"


def test_correcting_an_entry_that_is_gone_answers_instead_of_500ing(client):
    body = client.post("/api/correct", json={
        "entry_id": 999, "field": "date_registration", "value": "05-Aug-2020"}).json()
    assert body["error"] == "not_found"


def test_the_samples_are_offered_by_key_and_label(client):
    """The home screen renders these as buttons, so it needs both the key it
    posts back and the words it prints."""
    samples = client.get("/api/samples").json()["samples"]
    assert samples and all({"key", "label"} == set(s) for s in samples)


# ── adding a document to an existing case ────────────────────────────────────
# The product's differentiating loop, and the reason a case is a case rather than
# a document: the certificate that closes a gap is read into the same chain
# instead of starting a second analysis.

def test_a_document_can_join_a_case_that_already_exists(client):
    case_id = client.store.create_case("ec_test_01.pdf")
    r = client.post(f"/api/case/{case_id}/documents",
                    files={"file": ("second.pdf", b"%PDF-1.4 fake", "application/pdf")},
                    data={"request_key": "R3:gap=2005-2017"})
    assert r.status_code == 200
    # Either it was accepted onto this case, or it was refused with a reason —
    # never a 500, and never a silent nothing.
    body = r.json()
    assert body.get("case_id") == case_id or body.get("error") == "rejected"


def test_a_rejected_second_document_says_why(client):
    """The Jinja route redirects with `?rejected=` to a screen that renders no
    such message, so an oversized or wrong-type file added to an existing case
    fails silently there. The JSON path answers with the sentence."""
    case_id = client.store.create_case("ec_test_01.pdf")
    body = client.post(f"/api/case/{case_id}/documents",
                       files={"file": ("notes.txt", b"not a certificate", "text/plain")},
                       data={"request_key": ""}).json()

    assert body["error"] == "rejected"
    assert body["detail"]


def test_adding_to_a_case_that_is_gone_answers_instead_of_500ing(client):
    body = client.post("/api/case/999/documents",
                       files={"file": ("x.pdf", b"%PDF-1.4", "application/pdf")},
                       data={"request_key": ""}).json()
    assert body["error"] == "not_found"
