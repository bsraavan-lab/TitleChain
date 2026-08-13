"""The explain-aloud feature: scripts, synthesis, and the two API surfaces.

The property these tests defend is the one the module docstrings promise: the
spoken explanation is a pure function of the derivation. Nothing here checks
what bulbul sounds like — synthesis is faked at the seam — but everything
checks that the words are the right words, said once, in the asked-for
language, and that the audio path caches, ledgers and refuses honestly.
"""

from __future__ import annotations

import copy
import importlib
import io
import wave

import pytest
from fastapi.testclient import TestClient

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
def seeded(client):
    from app import db

    case_id = client.store.create_case("ec2_pacollege.pdf")
    ec_id = client.store.save_header(
        case_id, EC2_HEADER.model_copy(deep=True),
        filename="ec2_pacollege.pdf", file_path="", page_count=3)
    client.store.save_entries(ec_id, copy.deepcopy(EC2_ENTRIES))
    entry_id = db.one(
        "SELECT id FROM entries WHERE ec_id = ? ORDER BY id LIMIT 1", (ec_id,))["id"]
    return case_id, entry_id


def _tiny_wav(frames: int = 240) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(b"\x00\x00" * frames)
    return buf.getvalue()


# ── the scripts ───────────────────────────────────────────────────────────────


def test_a_lease_entry_is_explained_in_both_languages(view):
    from app import explain

    entry = view.entries[0]
    en = explain.entry_script(entry, view, "en")
    assert "Entry 1" in en and "2520/2019" in en
    assert "lease" in en
    assert "அருள்ஜோதி" in en          # names keep their one true form

    ta = explain.entry_script(entry, view, "ta")
    assert "குத்தகை" in ta and "2520/2019" in ta


def test_the_same_entry_is_explained_in_hindi(view):
    from app import explain

    hi = explain.entry_script(view.entries[0], view, "hi")
    assert "प्रविष्टि 1" in hi and "2520/2019" in hi
    assert "पट्टे" in hi                # lease, in the Hindi register
    assert "அருள்ஜோதி" in hi          # names keep their one true form here too


def test_the_parents_sentence_counts_the_missing(view):
    from app import explain

    en = explain.entry_script(view.entries[0], view, "en")
    assert "5 earlier documents" in en
    assert "None of them is in this case" in en


def test_r4_never_reaches_the_flags_section(view):
    """R4's content IS the parents sentence, composed from the same edges. A
    different rule about the same document (R3's window gap) may still speak —
    that is a different statement — but R4 itself must never say it twice."""
    from app import explain

    entry = view.entries[0]
    assert all(r.rule_id != "R4" for r in explain._open_runs_for(entry, view))
    en = explain.entry_script(entry, view, "en")
    # The R4 phrasing appears once, from the parents sentence, never a second
    # time from a quoted run message.
    assert en.count("read what is inside") == 1


def test_the_blank_date_entry_carries_its_flag(view):
    """Entry 2's dropped date cells are the real R9 case the fixtures preserve
    deliberately — the script must surface it, not read past it."""
    from app import explain

    en = explain.entry_script(view.entries[1], view, "en")
    assert "Worth your attention:" in en


def test_scripts_are_deterministic(view):
    from app import explain

    for lang in ("en", "ta", "hi"):
        first = explain.entry_script(view.entries[0], view, lang)
        second = explain.entry_script(view.entries[0], view, lang)
        assert first == second


def test_the_case_script_states_verdict_and_readiness(view):
    from app import explain

    en = explain.case_script(view, "en")
    assert "sign off" in en
    ta = explain.case_script(view, "ta")
    assert "கையெழுத்" in ta
    hi = explain.case_script(view, "hi")
    assert "दस्तख़त" in hi


# ── chunking and stitching ────────────────────────────────────────────────────


def test_chunks_respect_the_cap_and_never_split_a_sentence():
    from app import speak

    text = " ".join(f"Sentence number {i} says something useful." for i in range(40))
    parts = speak.chunks(text)
    assert all(len(p) <= speak.CHUNK_CHARS for p in parts)
    assert all(p.endswith(".") for p in parts)
    assert " ".join(parts) == text


def test_concatenated_wavs_carry_every_frame():
    from app.speak import _concat_wavs

    merged = _concat_wavs([_tiny_wav(100), _tiny_wav(150)])
    with wave.open(io.BytesIO(merged)) as w:
        assert w.getnframes() == 250
        assert w.getframerate() == 24000


def test_synthesise_buys_once_and_caches_after(client, monkeypatch):
    from app import speak

    calls = []

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            import base64
            return {"audios": [base64.b64encode(_tiny_wav()).decode()]}

    def fake_post(url, **kwargs):
        calls.append(url)
        return FakeResponse()

    monkeypatch.setattr(speak.httpx, "post", fake_post)
    monkeypatch.setenv("SARVAM_API_KEY", "test-key")

    first = speak.synthesise("One sentence.", "en")
    second = speak.synthesise("One sentence.", "en")
    assert len(calls) == 1
    assert first.cached is False and second.cached is True
    assert second.audio == first.audio


# ── the API surfaces ──────────────────────────────────────────────────────────


def test_the_explain_json_carries_script_and_a_versioned_audio_url(seeded, client):
    _, entry_id = seeded
    body = client.get(f"/api/entry/{entry_id}/explain").json()
    for key in ("entry_id", "sr_no", "lang", "text", "audio_url"):
        assert key in body
    assert body["lang"] == "en"
    assert "lease" in body["text"]
    assert f"/api/entry/{entry_id}/explain.wav" in body["audio_url"]
    assert "v=" in body["audio_url"]


def test_tamil_is_one_query_param_away(seeded, client):
    _, entry_id = seeded
    body = client.get(f"/api/entry/{entry_id}/explain?lang=ta").json()
    assert body["lang"] == "ta"
    assert "குத்தகை" in body["text"]


def test_hindi_is_one_query_param_away(seeded, client):
    _, entry_id = seeded
    body = client.get(f"/api/entry/{entry_id}/explain?lang=hi").json()
    assert body["lang"] == "hi"
    assert "पट्टे" in body["text"]


def test_an_unknown_lang_clamps_to_english(seeded, client):
    _, entry_id = seeded
    body = client.get(f"/api/entry/{entry_id}/explain?lang=fr").json()
    assert body["lang"] == "en"
    assert "lease" in body["text"]


def test_a_correction_changes_the_audio_url(seeded, client):
    """The URL is content-addressed. If it survives a correction unchanged, a
    browser cache will replay yesterday's sentence over today's data."""
    _, entry_id = seeded
    before = client.get(f"/api/entry/{entry_id}/explain").json()["audio_url"]
    client.post("/api/correct", json={
        "entry_id": entry_id, "field": "nature", "value": "Sale deed"})
    after = client.get(f"/api/entry/{entry_id}/explain").json()["audio_url"]
    assert before != after


def test_the_audio_endpoint_serves_wav_and_ledgers_the_spend(seeded, client, monkeypatch):
    from app import db, speak

    def fake_synthesise(text, lang):
        return speak.Spoken(audio=_tiny_wav(), cached=False, ms=5, chars=len(text))

    monkeypatch.setattr(speak, "synthesise", fake_synthesise)

    case_id, entry_id = seeded
    r = client.get(f"/api/entry/{entry_id}/explain.wav")
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/wav"

    row = db.one("SELECT * FROM api_calls WHERE case_id = ? AND stage = 'speak'",
                 (case_id,))
    assert row is not None
    assert row["model"] == speak.MODEL
    assert row["chars"] > 0


def test_a_dead_voice_is_a_502_not_a_broken_wav(seeded, client, monkeypatch):
    from app import speak

    def refuse(text, lang):
        raise RuntimeError("no network")

    monkeypatch.setattr(speak, "synthesise", refuse)
    _, entry_id = seeded
    assert client.get(f"/api/entry/{entry_id}/explain.wav").status_code == 502


def test_missing_subjects_answer_instead_of_500ing(seeded, client):
    body = client.get("/api/entry/99999/explain").json()
    assert body["error"] == "not_found"
    assert client.get("/api/entry/99999/explain.wav").status_code == 404

    body = client.get("/api/case/99999/explain").json()
    assert body["error"] == "not_found"


def test_the_case_explanation_exists_at_case_level(seeded, client):
    case_id, _ = seeded
    body = client.get(f"/api/case/{case_id}/explain").json()
    assert body["entry_id"] is None
    assert "sign off" in body["text"]
    assert f"/api/case/{case_id}/explain.wav" in body["audio_url"]


def test_an_unread_case_is_rejected_with_a_sentence(client):
    case_id = client.store.create_case("fresh.pdf")
    body = client.get(f"/api/case/{case_id}/explain").json()
    assert body["error"] == "rejected"
