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

from . import crops, db, derive as derive_mod, store
from . import digitise as digitise_mod
from . import extract as extract_mod
from .digitise import Digitised, UnreadChunk
from .extract import Extraction, Refusal
from .fixtures import SAMPLES
from .models import ECHeader, Entry

from .paths import ROOT, UPLOADS    # UPLOADS follows TITLECHAIN_DATA_DIR;
                                    # created by paths.ensure() at startup


def property_key(header: ECHeader) -> str:
    surveys = header.survey_details
    tail = f" +{len(surveys) - 1}" if len(surveys) > 1 else ""
    first = surveys[0] if surveys else "—"
    return f"{header.village or 'Unknown village'} · S.No {first}{tail}"


# ── stage-② disk cache ───────────────────────────────────────────────────────

def _cached_extraction(dig: Digitised, suffix: str = "") -> Extraction | Refusal | None:
    """`suffix` names one certificate inside a bundle ("_p4-5"), so the two halves
    of ec5 cache separately instead of overwriting each other."""
    f = dig.source_dir / f"extraction{suffix}.json"
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


def _save_extraction(dig: Digitised, result: Extraction | Refusal,
                     suffix: str = "") -> None:
    payload: dict = {"version": extract_mod.EXTRACT_VERSION}
    if isinstance(result, Refusal):
        payload["refusal"] = asdict(result)
    else:
        payload["header"] = result.header.model_dump()
        payload["entries"] = [e.model_dump(exclude={"db_id"}) for e in result.entries]
        payload["unread"] = [asdict(u) for u in result.unread]
    (dig.source_dir / f"extraction{suffix}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


# ── the walk ─────────────────────────────────────────────────────────────────

def run(case_id: int, pdf_path: Path,
        fulfils_request_key: str | None = None) -> None:
    """Runs in a background thread. Every state it sets is user-visible and true.

    Called with an existing `case_id` that already holds a certificate, this
    APPENDS: a second `ec_documents` row on the same case, whose entries join the
    same graph. Nothing is cleared and nothing is re-read — corrections live on the
    entries already stored, and review state keys on the finding's subject rather
    than on a row id, so both survive by construction.
    """
    try:
        pages = crops.page_count(pdf_path)
    except Exception as exc:                                    # unreadable file
        db.set_status(case_id, "FAILED", f"Could not open this file: {exc}")
        return

    # The cost ledger. digitise() and extract() do not know what a case is, so they
    # are handed a recorder and every real HTTP request lands in one row — retries
    # included, because the truncation ladder is the actual per-case cost driver.
    ec_box: dict[str, int | None] = {"ec_id": None}

    def record(row: dict) -> None:
        db.insert("api_calls", case_id=case_id, ec_id=ec_box["ec_id"],
                  created_at=db.now(), **row)

    digitise_mod.set_recorder(record)
    extract_mod.set_recorder(record)

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

    # digitise() reports a chunk that would not read as an UnreadChunk rather than
    # raising — visible degradation, which is right when SOME of the document came
    # back. When NONE of it did, that same non-raising path hands stage ② a
    # zero-page document, and stage ②'s first check ("no table on any page") then
    # refuses: it tells the advocate their certificate is not a certificate. That
    # is a statement about the document we have no evidence for — the fault is
    # ours, and the status has to say so. Same rule extract() already applies when
    # every entry block fails to type.
    if not dig.pages:
        why = "; ".join(u.reason for u in dig.unread[:3]) or "no pages were returned"
        db.set_status(case_id, "FAILED", f"Could not read this document: {why}"[:300])
        return

    db.set_status(case_id, "READING", f"Read {len(dig.pages)} pages",
                  pages_done=pages)

    # ── stage ② ──────────────────────────────────────────────────────────────
    # A file may hold MORE THAN ONE certificate (ec5 holds two for the same
    # property). Each range becomes its own ec_documents row on this one case, and
    # the merge path downstream is the same one an uploaded second certificate
    # takes — so the ruler draws two bands, and R3 evaluates against both windows
    # instead of silently filing the second certificate's entries under the first
    # one's search period.
    ranges = extract_mod.certificate_ranges(dig)
    split = len(ranges) > 1
    if split:
        db.set_status(case_id, "TYPING",
                      f"This file holds {len(ranges)} certificates — reading each "
                      f"separately")

    last_ec_id: int | None = None
    for n, (page_from, page_to) in enumerate(ranges, start=1):
        part = digitise_mod.slice_pages(dig, page_from, page_to) if split else dig
        label = f" ({n} of {len(ranges)}, pages {page_from}–{page_to})" if split else ""
        ec_id: int | None = None

        def save_header(header: ECHeader, _pf=page_from, _pt=page_to) -> int:
            nonlocal ec_id
            if ec_id is None:
                ec_id = store.save_header(
                    case_id, header, filename=pdf_path.name,
                    file_path=str(pdf_path), page_count=_pt - _pf + 1,
                    fulfils_request_key=fulfils_request_key,
                    page_from=_pf, page_to=_pt)
                ec_box["ec_id"] = ec_id
                # The property key names the case, and the FIRST certificate names
                # the property. A later certificate must not rename it.
                if len(store.ec_rows(case_id)) == 1:
                    db.execute("UPDATE cases SET property_key = ? WHERE id = ?",
                               (property_key(header), case_id))
            else:
                # The early header (on_header) carried no declared_entry_count — it
                # is read separately, by regex, as the R10 checksum. Without this
                # update R10 never runs, and R10 not running looks exactly like R10
                # passing.
                db.execute(
                    "UPDATE ec_documents SET declared_entry_count = ? WHERE id = ?",
                    (header.declared_entry_count, ec_id))
            return ec_id

        suffix = f"_p{page_from}-{page_to}" if split else ""
        result = _cached_extraction(dig, suffix)
        if result is None:
            db.set_status(case_id, "TYPING",
                          f"Typing entries into the schema{label}")
            try:
                result = extract_mod.extract(
                    part, filename=pdf_path.name,
                    on_progress=lambda detail, _l=label: db.set_status(
                        case_id, "TYPING", f"{detail}{_l}"),
                    on_header=save_header)
            except Exception as exc:
                db.set_status(case_id, "FAILED",
                              f"Entry typing failed{label}: {str(exc)[:200]}")
                return
            try:
                _save_extraction(dig, result, suffix)
            except OSError:
                # output/ is read-only on a serverless host. Losing the cache write
                # costs a slower next run; failing the case here would throw away an
                # extraction we have already paid Sarvam for.
                pass

        if isinstance(result, Refusal):
            if not split:
                db.set_status(case_id, "REFUSED", result.detail,
                              refusal_checks=json.dumps(result.checks))
                return
            continue        # one certificate in a bundle may be unreadable

        save_header(result.header)
        store.save_entries(ec_id, result.entries)
        for u in [*part.unread, *result.unread]:
            db.insert("unread_chunks", ec_id=ec_id, page_from=u.page_from,
                      page_to=u.page_to, reason=u.reason)
        last_ec_id = ec_id

    if last_ec_id is None:
        db.set_status(case_id, "REFUSED",
                      "No certificate in this file could be read.",
                      refusal_checks=json.dumps(
                          ["a registration-entry table",
                           "at least one numbered entry"]))
        return
    ec_id = last_ec_id

    db.set_status(case_id, "DERIVING", "Building the chain and running the rulebook")
    time.sleep(0.2)     # derive() is fast; let the state be seen, not subliminal

    # Log what the rulebook said. Two of these are what let the Documents tab
    # report "this certificate resolved these four findings" as a diff of recorded
    # facts rather than as a guess.
    docs = store.load_case(case_id)
    view = derive_mod.derive_case(docs, reviewed=store.reviewed_keys(case_id))
    store.record_derivation(case_id, view,
                            trigger="merge" if len(docs) > 1 else "upload",
                            ec_id=ec_id)

    digitise_mod.set_recorder(None)
    extract_mod.set_recorder(None)
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
