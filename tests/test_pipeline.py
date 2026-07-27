"""The status a failed read produces. No API calls, no database — db.set_status
and stage ① are both stubbed, which is the whole surface pipeline.run() touches
before it decides.

Run: .venv/bin/pytest -q
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app import pipeline
from app.digitise import Digitised, UnreadChunk

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
    assert "Could not read this document" in detail
    assert "state 'Failed'" in detail          # the digitiser's own reason, kept
    assert not any(s == "REFUSED" for s, _ in statuses)


def test_a_readable_document_is_not_short_circuited(statuses, monkeypatch):
    """The guard is about zero pages, not about unread chunks. A document that
    lost one chunk of many still goes to stage ②, with the loss recorded."""
    partial = Digitised(pages=[object()], markdown="", source_dir=Path("."),
                        from_cache=False,
                        unread=[UnreadChunk(11, 20, "chunk 2 timed out")])
    monkeypatch.setattr(pipeline.digitise_mod, "digitise", lambda *a, **k: partial)
    monkeypatch.setattr(pipeline, "_cached_extraction", lambda dig: None)

    def boom(*a, **k):
        raise RuntimeError("stage ② reached")
    monkeypatch.setattr(pipeline.extract_mod, "extract", boom)

    pipeline.run(1, SAMPLE)

    assert any(s == "TYPING" for s, _ in statuses)
    assert statuses[-1][0] == "FAILED"
    assert "stage ② reached" in statuses[-1][1]
