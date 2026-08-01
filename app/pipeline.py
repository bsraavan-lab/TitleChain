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

def _read_failure(exc: Exception) -> str:
    """Why stage ① stopped, in words that point at the right thing.

    A missing API key is not a fact about the certificate, and "we got stuck
    reading the pages" — followed by a server filesystem path, which is what the
    raw RuntimeError carried — told the reader their document was bad and told
    the operator nothing useful either.
    """
    from config import MissingAPIKey     # lazy: the app boots without a key

    if isinstance(exc, MissingAPIKey):
        return ("This document is not one we have already read, and reading a "
                "new one needs the document service to be configured on this "
                "server. Nothing is wrong with your file. An administrator "
                "needs to set SARVAM_API_KEY.")
    return f"We got stuck reading the pages. {str(exc)[:200]}"


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
        db.set_status(case_id, "FAILED",
                      f"We could not open this file at all. {exc}")
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
        db.set_status(case_id, "FAILED", _read_failure(exc))
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
        why = "; ".join(u.reason for u in dig.unread[:3]) or "no pages came back"
        db.set_status(case_id, "FAILED",
                      f"We could not read this document: {why}"[:300])
        return

    db.set_status(case_id, "READING", f"Read all {len(dig.pages)} pages",
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
                      f"There are {len(ranges)} certificates in this file, so we "
                      f"are reading each one separately")

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
                          f"Pulling out the entries{label}")
            try:
                result = extract_mod.extract(
                    part, filename=pdf_path.name,
                    on_progress=lambda detail, _l=label: db.set_status(
                        case_id, "TYPING", f"{detail}{_l}"),
                    on_header=save_header)
            except Exception as exc:
                from config import MissingAPIKey     # lazy, as above
                detail = (_read_failure(exc) if isinstance(exc, MissingAPIKey)
                          else f"We could not get the entries out{label}. "
                               f"{str(exc)[:200]}")
                db.set_status(case_id, "FAILED", detail)
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
                      "We could not read a single certificate out of this file.",
                      refusal_checks=json.dumps(
                          ["a table of registered entries",
                           "at least one numbered entry in it"]))
        return
    ec_id = last_ec_id

    db.set_status(case_id, "DERIVING",
                  "Connecting the documents and running the checks")
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
    """FR-1. Turned away at the door — and told what to do about it.

    Both messages name the real limit and suggest the next move, because "invalid
    file" leaves her guessing at a rule she cannot see.
    """
    if len(data) > 50 * 1024 * 1024:
        return None, (f"That file is {len(data) / 1_048_576:.0f} MB, and we can take "
                      f"up to 50 MB. A lighter scan, or one certificate at a time, "
                      f"should go through.")
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".jpg", ".jpeg", ".png"}:
        return None, (f"We can open PDF, JPEG and PNG files, but not "
                      f"{suffix or 'this kind of file'}. A scan or a clear photo of "
                      f"the certificate will work.")
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
