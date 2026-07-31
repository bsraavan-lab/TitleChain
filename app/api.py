"""The JSON contract the React front end reads.

Additive on purpose. The Jinja screens keep working untouched while this exists
beside them, so the demo never depends on a half-finished migration — and both
render from the SAME `derive_case()` output, which is the only way the two can
agree about what a certificate proves.

What is deliberately NOT here: the crops. `/crop/{entry_id}.png`,
`/page/{ec_id}/{page_num}.png` and `/pageview/{entry_id}.png` already return
images, so the front end points an `<img>` at them. Provenance does not need a
JSON envelope.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from . import cost as cost_mod
from . import db, derive as derive_mod, layout, store
from .models import DerivedView

router = APIRouter(prefix="/api", tags=["api"])

# The same set main.py uses. Kept in one literal here rather than imported,
# because importing main would be circular; if these ever disagree the working
# screen and the JSON status would report different things about one case.
PROCESSING = {"QUEUED", "READING", "TYPING", "DERIVING"}


def _header(doc) -> dict[str, Any] | None:
    return doc.header.model_dump(mode="json") if doc and doc.header else None


@router.get("/cases")
def cases() -> dict[str, Any]:
    """The home screen's list. Carries the verdict, not the filename — the same
    reason the Jinja list does: `ec2_pacollege.pdf` means nothing to the reader,
    *Puliyampatti, survey 95/2* is how the file sits in her head."""
    out = []
    for case in store.case_list():
        row: dict[str, Any] = {
            "id": case["id"],
            "property_key": case["property_key"],
            "status": case["status"],
            "status_detail": case["status_detail"],
            "processing": case["status"] in PROCESSING,
            "header": None,
            "coverage": None,
            "open_count": None,
        }
        try:
            docs = store.load_case(case["id"])
            row["header"] = _header(docs[0] if docs else None)
            if docs and any(d.entries for d in docs):
                view = derive_mod.derive_case(
                    docs, reviewed=store.reviewed_keys(case["id"]))
                row["coverage"] = view.coverage.model_dump(mode="json")
                row["open_count"] = len(view.open_runs)
        except Exception:
            # A row written by an older extractor must not 500 the list. Same
            # guard the Jinja summary carries, for the same reason.
            pass
        out.append(row)
    return {"cases": out}


@router.get("/case/{case_id}")
def case(case_id: int) -> dict[str, Any]:
    """Everything one workspace screen needs, in one request.

    One call rather than five because every tab is a view of the same
    derivation: splitting it would let the checklist and the chain disagree
    about the same certificate, which is the one failure this product cannot
    have.
    """
    row = db.one("SELECT * FROM cases WHERE id = ?", (case_id,))
    if row is None:
        return {"error": "not_found", "case_id": case_id}

    docs = store.load_case(case_id)
    reviewed = store.reviewed_keys(case_id)
    corrections = store.corrections_for_case(case_id)
    unread = store.unread_for_case(case_id)
    entries = [e for d in docs for e in d.entries]

    # Mid-processing a certificate has a header but no entries yet. Deriving an
    # entry-less case would report "no parent document is named", which is a
    # statement about the certificate rather than about our progress.
    typed = any(d.entries for d in docs)
    view = (derive_mod.derive_case(
                docs, reviewed=reviewed, corrections=len(corrections),
                unread_pages=sum(
                    max((r["page_to"] or 0) - (r["page_from"] or 0) + 1, 1)
                    for r in unread))
            if typed else DerivedView(docs=docs))

    reviews = store.review_state(case_id)
    log = store.review_history(case_id)
    by_key: dict[str, list[dict]] = {}
    for entry in log:
        by_key.setdefault(entry["finding_key"], []).append(entry)

    return {
        "case": {
            "id": row["id"],
            "property_key": row["property_key"],
            "status": row["status"],
            "status_detail": row["status_detail"],
            "processing": row["status"] in PROCESSING,
            "pages_total": row["pages_total"],
        },
        "view": view.model_dump(mode="json"),
        "reviews": reviews,
        "review_by_key": by_key,
        "corrections": corrections,
        "unread": unread,
        "graph": layout.build_layout(
            docs, entries, view.edges,
            corrected_entry_ids={c["entry_id"] for c in corrections},
            open_encumbrance_docs={
                r.key.removeprefix("R2:enc=") for r in view.runs
                if r.rule_id == "R2" and r.outcome == "FAIL"}),
        "cost": {
            "estimate": cost_mod.estimate(row["pages_total"] or 1),
            "actual": cost_mod.actual(case_id),
            "ledger": [dict(r) for r in db.q(
                "SELECT * FROM api_calls WHERE case_id = ? ORDER BY id", (case_id,))],
        },
    }


@router.get("/case/{case_id}/status")
def case_status(case_id: int) -> dict[str, Any]:
    """What the working screen polls. Deliberately small: the pipeline runs in a
    background thread that outlives the request which started it, so this is hit
    on a timer and must stay cheap."""
    row = db.one("SELECT * FROM cases WHERE id = ?", (case_id,))
    if row is None:
        return {"error": "not_found", "case_id": case_id}
    return {
        "id": row["id"],
        "status": row["status"],
        "status_detail": row["status_detail"],
        "processing": row["status"] in PROCESSING,
        "pages_total": row["pages_total"],
    }
