"""Persistence ↔ typed objects. The only place SQL and Pydantic meet."""

from __future__ import annotations

import json
from pathlib import Path

from . import db
from .models import ECDoc, ECHeader, Entry, Party, PRNumber, Schedule, Source

ROOT = Path(__file__).resolve().parent.parent


def create_case(property_key: str) -> int:
    return db.insert("cases", property_key=property_key, status="QUEUED",
                     status_detail="Queued", created_at=db.now())


def save_header(case_id: int, header: ECHeader, *, filename: str,
                file_path: str, page_count: int,
                fulfils_request_key: str | None = None,
                page_from: int | None = None, page_to: int | None = None) -> int:
    return db.insert(
        "ec_documents", case_id=case_id, filename=filename, file_path=file_path,
        sro=header.sro, village=header.village,
        survey_nos=",".join(header.survey_details),
        search_start=header.search_period_start, search_end=header.search_period_end,
        issue_date=header.issue_date,
        declared_entry_count=header.declared_entry_count, page_count=page_count,
        uploaded_at=db.now(), fulfils_request_key=fulfils_request_key,
        page_from=page_from, page_to=page_to,
    )


def save_entries(ec_id: int, entries: list[Entry]) -> None:
    for e in entries:
        sch = e.schedules[0] if e.schedules else None
        e.db_id = db.insert(
            "entries", ec_id=ec_id, sr_no=e.sr_no, doc_no=e.doc_no,
            doc_year=e.doc_year, date_execution=e.date_execution,
            date_presentation=e.date_presentation,
            date_registration=e.date_registration, nature=e.nature,
            volume_page=e.volume_page, consideration_value=e.consideration_value,
            market_value=e.market_value, remarks=e.remarks,
            pr_numbers=",".join(p.doc_no for p in e.pr_numbers),
            survey_nos=",".join(sch.survey_nos) if sch else "",
            page_num=e.source.page_num, block_id=e.source.block_id,
            block_confidence=e.source.confidence,
            bbox=json.dumps(e.source.bbox) if e.source.bbox else None,
        )
        for role, people in (("executant", e.executants), ("claimant", e.claimants)):
            for p in people:
                db.insert("parties", entry_id=e.db_id, role=role,
                          name_native=p.name_native, name_roman=p.name_roman,
                          role_marker=p.role_marker)


def load_header(case_id: int) -> tuple[ECHeader | None, dict | None]:
    row = db.one("SELECT * FROM ec_documents WHERE case_id = ? ORDER BY id LIMIT 1",
                 (case_id,))
    if not row:
        return None, None
    return ECHeader(
        sro=row["sro"], village=row["village"],
        survey_details=[s for s in (row["survey_nos"] or "").split(",") if s],
        search_period_start=row["search_start"], search_period_end=row["search_end"],
        issue_date=row["issue_date"],
        declared_entry_count=row["declared_entry_count"],
    ), row


def load_entries(ec_id: int) -> list[Entry]:
    out: list[Entry] = []
    for r in db.q("SELECT * FROM entries WHERE ec_id = ? ORDER BY sr_no", (ec_id,)):
        people = db.q("SELECT * FROM parties WHERE entry_id = ? ORDER BY id", (r["id"],))
        # Defensive on purpose: this row may have been written by an older
        # extractor, and a record that outlives its writer must not 500 the page.
        prs = [PRNumber(doc_no=d, year=int(d.split("/")[-1]))
               for d in (r["pr_numbers"] or "").split(",")
               if "/" in d and d.split("/")[-1].isdigit()]
        surveys = [s for s in (r["survey_nos"] or "").split(",") if s]
        out.append(Entry(
            sr_no=r["sr_no"], doc_no=r["doc_no"], doc_year=r["doc_year"],
            date_execution=r["date_execution"],
            date_presentation=r["date_presentation"],
            date_registration=r["date_registration"], nature=r["nature"],
            executants=[Party(name_native=p["name_native"], role_marker=p["role_marker"],
                              name_roman=p["name_roman"])
                        for p in people if p["role"] == "executant"],
            claimants=[Party(name_native=p["name_native"], role_marker=p["role_marker"],
                             name_roman=p["name_roman"])
                       for p in people if p["role"] == "claimant"],
            volume_page=r["volume_page"], consideration_value=r["consideration_value"],
            market_value=r["market_value"], pr_numbers=prs, remarks=r["remarks"],
            schedules=[Schedule(property_type=None, extent=None, village_street=None,
                                survey_nos=surveys, door_no=None,
                                boundaries_native=None)] if surveys else [],
            source=Source(page_num=r["page_num"], block_id=r["block_id"],
                          bbox=json.loads(r["bbox"]) if r["bbox"] else None,
                          confidence=r["block_confidence"]),
            db_id=r["id"],
        ))
    return out


# Editable fields. Deliberately short: correction is for what the pipeline
# misread, not a general-purpose document editor.
EDITABLE = {
    "doc_no": "Document no.",
    "date_registration": "Date of registration",
    "date_execution": "Date of execution",
    "nature": "Nature",
    "market_value": "Market value",
    "remarks": "Remarks",
}


def apply_correction(entry_id: int, field: str, new_value: str, actor: str = "meena") -> None:
    """Append-only. The entries row is updated, and the change is logged forever.
    An 'undo' is a NEW correction that reverts — never a delete."""
    if field not in EDITABLE:
        raise ValueError(f"field not editable: {field}")
    row = db.one("SELECT * FROM entries WHERE id = ?", (entry_id,))
    if not row:
        raise ValueError("no such entry")
    old = row[field]
    new = new_value.strip() or None
    db.execute(f"UPDATE entries SET {field} = ? WHERE id = ?", (new, entry_id))
    db.insert("corrections", entry_id=entry_id, field=field, old_value=old,
              new_value=new, actor=actor, created_at=db.now())


def corrections_for(ec_id: int) -> list[dict]:
    return db.q(
        "SELECT c.*, e.sr_no FROM corrections c JOIN entries e ON e.id = c.entry_id "
        "WHERE e.ec_id = ? ORDER BY c.created_at DESC", (ec_id,))


def unread_chunks(ec_id: int) -> list[dict]:
    return db.q("SELECT * FROM unread_chunks WHERE ec_id = ?", (ec_id,))


def case_list() -> list[dict]:
    return db.q("SELECT * FROM cases ORDER BY id DESC")


# ── the case: every certificate on it, in upload order ───────────────────────

def _label(n: int) -> str:
    """EC-A, EC-B, … The advocate's handle for a certificate; a filename is not."""
    return f"EC-{chr(ord('A') + n)}" if n < 26 else f"EC-{n + 1}"


def ec_rows(case_id: int) -> list[dict]:
    return db.q("SELECT * FROM ec_documents WHERE case_id = ? ORDER BY id", (case_id,))


def _header_of(row: dict) -> ECHeader:
    return ECHeader(
        sro=row["sro"], village=row["village"],
        survey_details=[s for s in (row["survey_nos"] or "").split(",") if s],
        search_period_start=row["search_start"], search_period_end=row["search_end"],
        issue_date=row["issue_date"],
        declared_entry_count=row["declared_entry_count"],
    )


def load_case(case_id: int) -> list[ECDoc]:
    """Every certificate on the case, each with its own entries. This is what
    `derive_case` consumes; the graph is built over their union."""
    return [
        ECDoc(ec_id=row["id"], label=_label(i), filename=row["filename"],
              header=_header_of(row), entries=load_entries(row["id"]),
              page_count=row["page_count"] or 0,
              fulfils_request_key=row["fulfils_request_key"])
        for i, row in enumerate(ec_rows(case_id))
    ]


def corrections_for_case(case_id: int) -> list[dict]:
    return db.q(
        "SELECT c.*, e.sr_no, e.ec_id FROM corrections c "
        "JOIN entries e ON e.id = c.entry_id "
        "JOIN ec_documents d ON d.id = e.ec_id "
        "WHERE d.case_id = ? ORDER BY c.created_at DESC", (case_id,))


def unread_for_case(case_id: int) -> list[dict]:
    return db.q(
        "SELECT u.* FROM unread_chunks u JOIN ec_documents d ON d.id = u.ec_id "
        "WHERE d.case_id = ?", (case_id,))


def case_of_entry(entry_id: int) -> int | None:
    row = db.one(
        "SELECT d.case_id FROM entries e JOIN ec_documents d ON d.id = e.ec_id "
        "WHERE e.id = ?", (entry_id,))
    return row["case_id"] if row else None


# ── review state: append-only, keyed on the finding's subject ─────────────────

REVIEW_STATES = {
    "reviewed": "Reviewed",
    "accepted": "Accepted risk",
    "awaiting_document": "Awaiting a document",
    "open": "Reopened",
}


def set_review(case_id: int, finding_key: str, state: str, note: str = "",
               actor: str = "meena") -> None:
    if state not in REVIEW_STATES:
        raise ValueError(f"unknown review state: {state}")
    db.insert("reviews", case_id=case_id, finding_key=finding_key, state=state,
              note=note.strip() or None, actor=actor, created_at=db.now())


def review_history(case_id: int) -> list[dict]:
    return db.q("SELECT * FROM reviews WHERE case_id = ? ORDER BY id DESC",
                (case_id,))


def review_state(case_id: int) -> dict[str, dict]:
    """finding_key → the latest review row. Latest wins; nothing is overwritten."""
    latest: dict[str, dict] = {}
    for row in db.q("SELECT * FROM reviews WHERE case_id = ? ORDER BY id",
                    (case_id,)):
        latest[row["finding_key"]] = row
    return latest


def record_derivation(case_id: int, view, *, trigger: str,
                      ec_id: int | None = None) -> None:
    """Log what the rulebook said, and when.

    This does not violate "derived state is disposable" — findings are still
    rebuilt from scratch on every derivation. What is recorded is the EVENT, and it
    is the only way "which findings did this upload resolve?" can be answered by a
    diff instead of a guess. The title is stored alongside the key because a
    resolved finding no longer exists to be asked for its own sentence.
    """
    db.insert("derivations", case_id=case_id, at=db.now(),
              rulebook_version=view.rulebook_version, trigger=trigger, ec_id=ec_id,
              open_keys=json.dumps({r.key: r.title for r in view.open_runs},
                                   ensure_ascii=False),
              all_keys=json.dumps([r.key for r in view.runs], ensure_ascii=False))


def derivations(case_id: int) -> list[dict]:
    return db.q("SELECT * FROM derivations WHERE case_id = ? ORDER BY id", (case_id,))


def merge_summary(case_id: int, view) -> dict | None:
    """What the most recently added certificate changed on this case.

    A diff between the last recorded derivation and the one before it. Nothing is
    inferred: both sides are logged facts.
    """
    docs = load_case(case_id)
    if len(docs) < 2:
        return None
    rows = derivations(case_id)
    if len(rows) < 2:
        return None

    prev = json.loads(rows[-2]["open_keys"] or "{}")
    cur = {r.key: r.title for r in view.open_runs}
    latest = docs[-1]
    return {
        "label": latest.label,
        "window": latest.window,
        "entries": len(latest.entries),
        "pages": latest.page_count,
        "resolved": [t for k, t in prev.items() if k not in cur],
        "appeared": [t for k, t in cur.items() if k not in prev],
        "unchanged": len(set(prev) & set(cur)),
        "reviews_kept": len([k for k in reviewed_keys(case_id)
                             if k in {r.key for r in view.runs}]),
        "corrections_kept": len(corrections_for_case(case_id)),
    }


def reviewed_keys(case_id: int) -> set[str]:
    """Keys whose latest state closes them. 'accepted risk' closes an item for
    readiness purposes — she looked at it and decided — but it stays counted
    separately in the report, never silently."""
    return {k for k, r in review_state(case_id).items()
            if r["state"] in ("reviewed", "accepted")}
