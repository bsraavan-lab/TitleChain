"""Ingest → digitise → type. The stage-①/② seam — now wired to the real thing.

`digitise.py` (sarvamai SDK) and `extract.py` (raw httpx → sarvam-105b, strict
json_schema) replace the fixture replay this file shipped with. The status
transitions, the polling UI and everything downstream are unchanged — which was
the entire point of the seam.

The status walk is not decoration, and it is no longer simulated. Every state it
sets is user-visible and true: READING moves as digitisation jobs finish, the
case page renders as soon as the header is typed — so the coverage ruler is drawn
while the entries are still being typed — and TYPING counts blocks as 105B
actually returns them.

Extraction results are cached on disk next to the stage-① output
(`extraction.json`). Two reasons, same as the digitisation cache: a re-upload of
a certificate we have read is free and instant, and the three staged demo ECs
keep working through a total Sarvam outage.
"""

from __future__ import annotations

import json
import shutil
import time
from dataclasses import asdict
from pathlib import Path

from . import crops, db, store
from . import digitise as digitise_mod
from . import extract as extract_mod
from .digitise import Digitised, UnreadChunk
from .extract import Extraction, Refusal
from .fixtures import SAMPLES
from .models import ECHeader, Entry

ROOT = Path(__file__).resolve().parent.parent
UPLOADS = ROOT / "uploads"
UPLOADS.mkdir(exist_ok=True)


def property_key(header: ECHeader) -> str:
    surveys = header.survey_details
    tail = f" +{len(surveys) - 1}" if len(surveys) > 1 else ""
    first = surveys[0] if surveys else "—"
    return f"{header.village or 'Unknown village'} · S.No {first}{tail}"


# ── stage-② disk cache ───────────────────────────────────────────────────────

def _cached_extraction(dig: Digitised) -> Extraction | Refusal | None:
    f = dig.source_dir / "extraction.json"
    if not f.is_file():
        return None
    try:
        raw = json.loads(f.read_text(encoding="utf-8"))
        if raw.get("version") != extract_mod.EXTRACT_VERSION:
            return None
        if raw.get("refusal"):
            return Refusal(**raw["refusal"])
        return Extraction(
            header=ECHeader.model_validate(raw["header"]),
            entries=[Entry.model_validate(e) for e in raw["entries"]],
            unread=[UnreadChunk(**u) for u in raw.get("unread", [])],
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None                       # a corrupt cache is a miss, not a crash


def _save_extraction(dig: Digitised, result: Extraction | Refusal) -> None:
    payload: dict = {"version": extract_mod.EXTRACT_VERSION}
    if isinstance(result, Refusal):
        payload["refusal"] = asdict(result)
    else:
        payload["header"] = result.header.model_dump()
        payload["entries"] = [e.model_dump(exclude={"db_id"}) for e in result.entries]
        payload["unread"] = [asdict(u) for u in result.unread]
    (dig.source_dir / "extraction.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


# ── the walk ─────────────────────────────────────────────────────────────────

def run(case_id: int, pdf_path: Path) -> None:
    """Runs in a background thread. Every state it sets is user-visible and true."""
    try:
        pages = crops.page_count(pdf_path)
    except Exception as exc:                                    # unreadable file
        db.set_status(case_id, "FAILED", f"Could not open this file: {exc}")
        return

    db.set_status(case_id, "READING", f"Reading page 1 of {pages}",
                  pages_total=pages, pages_done=0)

    # ── stage ① ──────────────────────────────────────────────────────────────
    try:
        dig = digitise_mod.digitise(
            pdf_path, pages_total=pages,
            on_progress=lambda done, detail: db.set_status(
                case_id, "READING", detail, pages_done=min(done, pages)))
    except Exception as exc:
        db.set_status(case_id, "FAILED",
                      f"Digitisation failed: {str(exc)[:200]}")
        return

    db.set_status(case_id, "READING", f"Read {len(dig.pages)} pages",
                  pages_done=pages)

    # ── stage ② ──────────────────────────────────────────────────────────────
    # The header lands first (on_header), so the case page — ruler included —
    # renders while the entry blocks are still being typed. ec_id is created
    # then; entries attach to it when they arrive.
    ec_id: int | None = None

    def save_header(header: ECHeader) -> int:
        nonlocal ec_id
        if ec_id is None:
            ec_id = store.save_header(case_id, header, filename=pdf_path.name,
                                      file_path=str(pdf_path), page_count=pages)
            db.execute("UPDATE cases SET property_key = ? WHERE id = ?",
                       (property_key(header), case_id))
        else:
            # The early header (on_header) carried no declared_entry_count — it is
            # read separately, by regex, as the R10 checksum. Without this update
            # R10 never runs, and R10 not running looks exactly like R10 passing.
            db.execute("UPDATE ec_documents SET declared_entry_count = ? WHERE id = ?",
                       (header.declared_entry_count, ec_id))
        return ec_id

    result = _cached_extraction(dig)
    if result is None:
        db.set_status(case_id, "TYPING", "Typing entries into the schema")
        try:
            result = extract_mod.extract(
                dig, filename=pdf_path.name,
                on_progress=lambda detail: db.set_status(case_id, "TYPING", detail),
                on_header=lambda h: save_header(h))
        except Exception as exc:
            db.set_status(case_id, "FAILED",
                          f"Entry typing failed: {str(exc)[:200]}")
            return
        _save_extraction(dig, result)

    if isinstance(result, Refusal):
        db.set_status(case_id, "REFUSED", result.detail,
                      refusal_checks=json.dumps(result.checks))
        return

    save_header(result.header)
    store.save_entries(ec_id, result.entries)
    for u in [*dig.unread, *result.unread]:
        db.insert("unread_chunks", ec_id=ec_id, page_from=u.page_from,
                  page_to=u.page_to, reason=u.reason)

    db.set_status(case_id, "DERIVING", "Building the chain and running the rulebook")
    time.sleep(0.2)     # derive() is fast; let the state be seen, not subliminal
    db.set_status(case_id, "READY", "")


def accept_upload(filename: str, data: bytes) -> tuple[Path | None, str | None]:
    """FR-1. Reject at the door, with the specific reason and the limit."""
    if len(data) > 50 * 1024 * 1024:
        return None, f"{len(data) / 1_048_576:.0f} MB — the limit is 50 MB."
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".jpg", ".jpeg", ".png"}:
        return None, f"{suffix or 'this file type'} is not supported. PDF, JPEG or PNG."
    dest = UPLOADS / f"{int(time.time())}_{Path(filename).name}"
    dest.write_bytes(data)
    return dest, None


def stage_sample(key: str) -> Path:
    spec = SAMPLES[key]
    src = ROOT / spec["pdf"]
    dest = UPLOADS / src.name
    if not dest.exists():
        shutil.copy(src, dest)
    return dest
