"""Persistence ↔ typed objects. The only place SQL and Pydantic meet."""

from __future__ import annotations

import json
from pathlib import Path

from . import db
from .models import ECHeader, Entry, Party, PRNumber, Schedule, Source

ROOT = Path(__file__).resolve().parent.parent


def create_case(property_key: str) -> int:
    return db.insert("cases", property_key=property_key, status="QUEUED",
                     status_detail="Queued", created_at=db.now())


def save_header(case_id: int, header: ECHeader, *, filename: str,
                file_path: str, page_count: int) -> int:
    return db.insert(
        "ec_documents", case_id=case_id, filename=filename, file_path=file_path,
        sro=header.sro, village=header.village,
        survey_nos=",".join(header.survey_details),
        search_start=header.search_period_start, search_end=header.search_period_end,
        issue_date=header.issue_date,
        declared_entry_count=header.declared_entry_count, page_count=page_count,
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
