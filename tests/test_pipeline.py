"""The status a failed read produces. No API calls, no database — db.set_status
and stage ① are both stubbed, which is the whole surface pipeline.run() touches
before it decides.

Run: .venv/bin/pytest -q
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app import pipeline
from app.digitise import Block, Digitised, Page, UnreadChunk

SAMPLE = Path(__file__).resolve().parent.parent / "ec_samples" / "ec_test_01.pdf"


@pytest.fixture
def statuses(monkeypatch) -> list[tuple[str, str]]:
    """Every db.set_status call pipeline.run makes, in order."""
    seen: list[tuple[str, str]] = []
    monkeypatch.setattr(pipeline.db, "set_status",
                        lambda case_id, status, detail="", **kw: seen.append(
                            (status, detail)))
    return seen


def test_total_digitisation_failure_fails_it_does_not_refuse(statuses, monkeypatch):
    """A document nothing could be read from is OUR failure, not a bad EC.

    digitise() reports a dead chunk instead of raising, so without a guard here
    stage ② sees zero pages, finds no table, and REFUSES — telling the advocate a
    perfectly good certificate is not a certificate.
    """
    dead = Digitised(pages=[], markdown="", source_dir=Path("."), from_cache=False,
                     unread=[UnreadChunk(1, 3, "digitisation job ended in state 'Failed'")])
    monkeypatch.setattr(pipeline.digitise_mod, "digitise", lambda *a, **k: dead)

    pipeline.run(1, SAMPLE)

    status, detail = statuses[-1]
    assert status == "FAILED"
    assert "We could not read this document" in detail
    assert "state 'Failed'" in detail          # the digitiser's own reason, kept
    assert not any(s == "REFUSED" for s, _ in statuses)


def test_a_readable_document_is_not_short_circuited(statuses, monkeypatch):
    """The guard is about zero pages, not about unread chunks. A document that
    lost one chunk of many still goes to stage ②, with the loss recorded."""
    # A REAL Page, not a bare object(): stage ② is now entered through
    # certificate_ranges(), which reads page numbers to find where one certificate
    # ends and the next begins. A stub thin enough to pass through the old
    # straight-line path raises AttributeError on the new one, and that would be
    # the stub failing rather than the guard.
    page = Page(page_num=1, width=100, height=100, blocks=[
        Block(block_id="b", page_num=1, bbox=None, layout_tag="table",
              confidence=0.9, reading_order=0, text="<table></table>")])
    partial = Digitised(pages=[page], markdown="", source_dir=Path("."),
                        from_cache=False,
                        unread=[UnreadChunk(11, 20, "chunk 2 timed out")])
    monkeypatch.setattr(pipeline.digitise_mod, "digitise", lambda *a, **k: partial)
    monkeypatch.setattr(pipeline, "_cached_extraction", lambda dig, suffix="": None)

    def boom(*a, **k):
        raise RuntimeError("stage ② reached")
    monkeypatch.setattr(pipeline.extract_mod, "extract", boom)

    pipeline.run(1, SAMPLE)

    assert any(s == "TYPING" for s, _ in statuses)
    assert statuses[-1][0] == "FAILED"
    assert "stage ② reached" in statuses[-1][1]


# ── a case id that no longer resolves ────────────────────────────────────────

def test_no_route_500s_on_a_case_that_is_gone(tmp_path, monkeypatch):
    """Render's free plan has an ephemeral disk: the instance restarts and takes
    the case store with it, so a bookmarked /report/7 is an ordinary Tuesday.
    Every route that takes a case id has to survive it — /report/ did not, and
    returned a 500 in production the first time the instance recycled.
    """
    monkeypatch.setenv("TITLECHAIN_DATA_DIR", str(tmp_path))
    import importlib
    from fastapi.testclient import TestClient
    import config as config_mod
    from app import paths as paths_mod, db as db_mod, main as main_mod
    for m in (config_mod, paths_mod, db_mod, main_mod):
        importlib.reload(m)
    main_mod.db.init()

    client = TestClient(main_mod.app, follow_redirects=False)
    for path in ("/case/999", "/case/999/status", "/case/999/tab/review",
                 "/report/999", "/finding/999/detail?key=R3:gap=1-2"):
        r = client.get(path)
        assert r.status_code < 500, f"{path} returned {r.status_code}"
