"""TitleChain — FastAPI serving Jinja + HTMX from one process.

Two full pages the user can see (/ and /case/{id}) plus the printable report.
Everything else is a fragment swap or an image. No build step, no npm, no CDN,
and no CORS unless TITLECHAIN_CORS_ORIGINS names a host that needs it.

The case page is one shell: a sticky rail that always carries the verdict and the
completion state, a tab strip, and a persistent evidence pane that survives tab
switches. Tabs are `hx-get` + `hx-push-url`, so the URL stays shareable and the
back button works without a page reload.
"""

from __future__ import annotations

import json
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import (cost as cost_mod, crops, db, derive as derive_mod, layout, paths,
               pipeline, store)
from .fixtures import SAMPLES
from .models import OUTCOME_ORDER, OUTCOME_UI, DerivedView

ROOT = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(_: FastAPI):
    paths.ensure()     # creates uploads/ and output/ under the data dir
    paths.seed_cache() # bundled digitisations, so the samples never wait on Sarvam
    db.init()          # idempotent; if the file is ever corrupted: rm titlechain.db
    yield


app = FastAPI(title="TitleChain", lifespan=lifespan)

# The JSON contract the React front end reads. Mounted beside the Jinja screens
# rather than replacing them: both render from the same derive_case(), so the
# migration can proceed one screen at a time without the demo ever depending on
# a half-finished one.
from .api import router as api_router          # noqa: E402  (after `app` exists)
app.include_router(api_router)

# Off unless asked for, and the deployed app never asks: Vercel and Render are
# one origin to the browser, so no preflight is ever sent there. It exists for a
# host that serves the bundle without the rewrite — Lovable's preview — where the
# front end is told the backend's address outright and the request becomes
# cross-origin. Comma-separated exact origins; no wildcard, because credentials
# would then be refused by the browser anyway.
_cors = [o.strip() for o in os.environ.get("TITLECHAIN_CORS_ORIGINS", "").split(",") if o.strip()]
if _cors:
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(CORSMiddleware, allow_origins=_cors,
                       allow_methods=["GET", "POST"], allow_headers=["*"])

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.globals["SAMPLES"] = SAMPLES
templates.env.globals["EDITABLE"] = store.EDITABLE
templates.env.globals["RULEBOOK_VERSION"] = derive_mod.RULEBOOK_VERSION
templates.env.globals["RULEBOOK"] = derive_mod.RULEBOOK
templates.env.globals["OUTCOME_ORDER"] = OUTCOME_ORDER
templates.env.globals["OUTCOME_UI"] = OUTCOME_UI
templates.env.globals["REVIEW_STATES"] = store.REVIEW_STATES

PROCESSING = {"QUEUED", "READING", "TYPING", "DERIVING"}


# Order is her question order, and each label is that question in her words:
# what must I check → how does it connect → what am I missing → did you read it
# right → what did this cost. No label needs the domain explained to it first.
TABS = [
    ("review", "What to check"),
    ("chain", "How it connects"),
    ("documents", "What's missing"),
    ("entries", "What we read"),
    ("processing", "What it cost"),
]
TAB_NAMES = {name for name, _ in TABS}


# ── shared page assembly ─────────────────────────────────────────────────────

def _unread_pages(rows: list[dict]) -> int:
    return sum(max((r["page_to"] or 0) - (r["page_from"] or 0) + 1, 1) for r in rows)


def _review_grid(view, entries, corrections, reviewed) -> dict[int, dict]:
    """Where review is needed, per entry — from OUR checks, not from the model's
    confidence. Sarvam's block score is blind to a dropped cell, so it is reported
    as a bare number in its own column and never as a colour."""
    counted = {"R9": "fields", "R4": "parents", "R3": "window"}
    grid: dict[int, dict] = {
        e.db_id: {"fields": 0, "parents": 0, "window": 0, "corrected": 0,
                  "reviewed": False, "open": 0}
        for e in entries
    }
    for r in view.runs:
        col = counted.get(r.rule_id)
        if not (col and r.is_open):
            continue
        for eid in r.evidence_entry_ids:
            if eid in grid:
                grid[eid][col] += 1
                grid[eid]["open"] += 1
                if r.key in reviewed:
                    grid[eid]["open"] -= 1
    for c in corrections:
        if c["entry_id"] in grid:
            grid[c["entry_id"]]["corrected"] += 1
    for eid, flags in grid.items():
        flags["reviewed"] = flags["open"] == 0
    return grid


ENC_STATUS = {
    # R2 outcome → (label, glyph, css class). "Couldn't tell" is a first-class
    # status: an entry whose nature could not be read must never be shown as
    # settled, and must never be shown as open either.
    "FAIL":           ("Still open", "▲", "active"),
    "PASS":           ("Closed", "✓", "closed"),
    "NOT_EVALUABLE":  ("Couldn't tell", "⚠", "unknown"),
}


def _encumbrance_cards(view) -> list[dict]:
    """One card per R2 run that is about an instrument. The rule already decided;
    this only chooses the words."""
    cards = []
    for r in view.runs:
        if r.rule_id != "R2" or r.key in ("R2:none", "R2:unclassified"):
            continue
        label, glyph, cls = ENC_STATUS.get(r.outcome, ("Couldn't tell", "⚠", "unknown"))
        if r.outcome == "PASS":
            label = "Cancelled" if "cancelled" in r.message else "Released"
        nature = next((i.value for i in r.inputs if i.label == "nature"), None)
        cards.append({
            "key": r.key, "status": label, "glyph": glyph, "status_class": cls,
            "doc_no": r.key.split("=", 1)[-1].split("/sr:")[0]
                      if "enc=" in r.key else r.title,
            "nature": None if nature in (None, "not read", "null") else nature,
            "detail": r.message if r.outcome != "NOT_EVALUABLE" else r.reason,
            "entry_id": r.evidence_entry_ids[0] if r.evidence_entry_ids else None,
        })
    return cards


def _gone(case_id: int) -> RedirectResponse:
    """A case id that no longer resolves. Not an error page: on a host with an
    ephemeral disk the instance restarts and takes the case store with it, so a
    bookmarked /report/7 is an ordinary Tuesday. Send her to the case list, which
    is the honest answer to "that file is not here"."""
    return RedirectResponse("/", status_code=303)


def case_context(request: Request, case_id: int, tab: str = "review") -> dict:
    case = db.one("SELECT * FROM cases WHERE id = ?", (case_id,))
    if not case:
        return {"request": request, "case": None}

    docs = store.load_case(case_id)
    reviews = store.review_state(case_id)
    reviewed = {k for k, r in reviews.items() if r["state"] in ("reviewed", "accepted")}
    corrections = store.corrections_for_case(case_id)
    unread = store.unread_for_case(case_id)

    # Mid-processing a certificate has a header but no entries yet. derive_case on
    # an entry-less case would report "no parent document is named", which is a
    # statement about the certificate rather than about our progress — so the
    # rail renders the windows it already knows and says nothing else.
    typed = any(d.entries for d in docs)
    view = (derive_mod.derive_case(docs, reviewed=reviewed,
                                  corrections=len(corrections),
                                  unread_pages=_unread_pages(unread))
            if typed else DerivedView(docs=docs))

    tab = tab if tab in TAB_NAMES else "review"
    first = docs[0] if docs else None

    log = store.review_history(case_id)
    by_key: dict[str, list[dict]] = {}
    for row in log:
        by_key.setdefault(row["finding_key"], []).append(row)
    return {
        "request": request,
        "case": case,
        "docs": docs,
        "header": first.header if first else None,
        "ec": db.one("SELECT * FROM ec_documents WHERE case_id = ? ORDER BY id LIMIT 1",
                     (case_id,)),
        "entries": [e for d in docs for e in d.entries],
        "view": view,
        "processing": case["status"] in PROCESSING,
        "corrections": corrections,
        "unread": unread,
        "reviews": reviews,
        "refusal_checks": json.loads(case["refusal_checks"] or "null"),
        "tab": tab,
        "tabs": TABS,
        "tab_counts": {
            "review": len(view.open_runs),
            "documents": len(view.requests_live),
            "entries": len(unread),
        },
        "review_log": log,
        "review_by_key": by_key,
        "grid": _review_grid(view, [e for d in docs for e in d.entries],
                             corrections, reviewed),
        "merge": store.merge_summary(case_id, view) if typed else None,
        "graph": layout.build_layout(
            docs, [e for d in docs for e in d.entries], view.edges,
            corrected_entry_ids={c["entry_id"] for c in corrections},
            open_encumbrance_docs={
                r.key.removeprefix("R2:enc=") for r in view.runs
                if r.rule_id == "R2" and r.outcome == "FAIL"}),
        "encumbrances": _encumbrance_cards(view),
        "cost_estimate": cost_mod.estimate(case["pages_total"] or 1),
        "cost_actual": cost_mod.actual(case_id),
        "ledger": db.q("SELECT * FROM api_calls WHERE case_id = ? ORDER BY id",
                       (case_id,)),
        # Recognition over recall: the switcher lists the other open properties
        # by name, so moving between files never routes through the home screen.
        "other_cases": [c for c in store.case_list() if c["id"] != case_id],
    }


def _entry(entry_id: int):
    row = db.one("SELECT e.*, d.file_path, d.case_id, d.page_count FROM entries e "
                 "JOIN ec_documents d ON d.id = e.ec_id WHERE e.id = ?", (entry_id,))
    return row


def _document(case_id: int):
    return db.one("SELECT * FROM ec_documents WHERE case_id = ? ORDER BY id LIMIT 1",
                  (case_id,))


def case_summaries() -> list[dict]:
    """The case list is the returning user's landing screen, so it carries the
    answer, not the filename: chain state, what is still open, and the same
    search-window rule the case page draws — at 1/8 the size.

    Deriving per row is cheap (entries are already typed and in memory) and it
    keeps ONE source of truth for the verdict. A denormalised `cases.verdict`
    column would be a second one, and the two would disagree the first time the
    rulebook version changed.
    """
    out: list[dict] = []
    for case in store.case_list():
        summary = {"case": case, "header": None, "view": None,
                   "processing": case["status"] in PROCESSING}
        try:
            docs = store.load_case(case["id"])
            summary["header"] = docs[0].header if docs else None
            summary["docs"] = len(docs)
            if docs and any(d.entries for d in docs):
                view = derive_mod.derive_case(
                    docs, reviewed=store.reviewed_keys(case["id"]))
                summary["view"] = view
                summary["entry_count"] = sum(len(d.entries) for d in docs)
                summary["chain_pct"] = view.completeness.chain_pct
                summary["open_count"] = len(view.open_runs)
                summary["ready"] = view.readiness.ready
        except Exception:                       # a row written by an older
            pass                                # extractor must not 500 the list
        out.append(summary)
    return out


# ── screens ──────────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
def home(request: Request, rejected: str | None = None):
    return templates.TemplateResponse(request, "home.html", {
        "request": request, "summaries": case_summaries(), "rejected": rejected,
    })


@app.get("/palette.json")
def palette():
    """Feeds the command palette. Recognition over recall: she picks a property
    by name instead of remembering where it sat in a list."""
    cases = []
    for c in store.case_list():
        header, _ = store.load_header(c["id"])
        cases.append({
            "id": c["id"],
            "label": c["property_key"] or "New case",
            "sub": f"{header.sro} SRO" if header and header.sro else c["status"].lower(),
        })
    return {
        "cases": cases,
        "commands": [{"label": "See all your cases", "kind": "Go", "href": "/"}],
    }


@app.post("/upload")
async def upload(file: UploadFile):
    data = await file.read()
    path, error = pipeline.accept_upload(file.filename or "upload", data)
    if error:
        return RedirectResponse(f"/?rejected={error}", status_code=303)
    case_id = store.create_case(file.filename or "New case")
    threading.Thread(target=pipeline.run, args=(case_id, path),
                     daemon=True).start()
    return RedirectResponse(f"/case/{case_id}", status_code=303)


@app.post("/sample/{key}")
def open_sample(key: str):
    if key not in SAMPLES:
        return RedirectResponse(
            "/?rejected=We could not find that example. Pick one of the others below.",
            status_code=303)
    path = pipeline.stage_sample(key)
    case_id = store.create_case(SAMPLES[key]["label"])
    threading.Thread(target=pipeline.run, args=(case_id, path),
                     daemon=True).start()
    return RedirectResponse(f"/case/{case_id}", status_code=303)


@app.get("/case/{case_id}", response_class=HTMLResponse)
def case_page(request: Request, case_id: int, tab: str = "review"):
    ctx = case_context(request, case_id, tab)
    if ctx["case"] is None:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "case.html", ctx)


@app.get("/case/{case_id}/status", response_class=HTMLResponse)
def case_status(request: Request, case_id: int, tab: str = "review"):
    """Polled while processing. The READY fragment carries no hx-trigger, so
    polling stops by itself — no client-side state to unwind. The response also
    carries the ruler, the active tab body and the tab counts out-of-band, so the
    whole page keeps up with one request rather than one poller per region.

    Named `status`, not `rail`: `/case/{id}/rail` is the document pane, which is a
    different component that happens to have wanted the same word."""
    ctx = case_context(request, case_id, tab)
    if ctx["case"] is None:
        return _gone(case_id)
    return templates.TemplateResponse(request, "_verdict_poll.html", ctx)


@app.get("/case/{case_id}/tab/{name}", response_class=HTMLResponse)
def case_tab(request: Request, case_id: int, name: str):
    ctx = case_context(request, case_id, name)
    if ctx["case"] is None:
        return _gone(case_id)
    return templates.TemplateResponse(request, "_tab_swap.html", ctx)


# ── the missing-document loop ────────────────────────────────────────────────

@app.post("/case/{case_id}/documents")
async def add_document(case_id: int, file: UploadFile,
                       request_key: str = Form("")):
    """Drop a certificate on a request card and it joins THIS case.

    Same pipeline, same code path, one extra `ec_documents` row. The findings
    already on screen are not cleared while it reads — the case does not go blank,
    which is the difference between completing a title history and restarting an
    analysis.
    """
    if not db.one("SELECT id FROM cases WHERE id = ?", (case_id,)):
        return RedirectResponse("/", status_code=303)
    data = await file.read()
    path, error = pipeline.accept_upload(file.filename or "upload", data)
    if error:
        return RedirectResponse(f"/case/{case_id}?tab=documents&rejected={error}",
                                status_code=303)
    threading.Thread(target=pipeline.run,
                     args=(case_id, path, request_key or None),
                     daemon=True).start()
    return RedirectResponse(f"/case/{case_id}?tab=documents", status_code=303)


# ── correction: the memory proof, rendered ───────────────────────────────────

@app.get("/entry/{entry_id}/edit/{field}", response_class=HTMLResponse)
def edit_field(request: Request, entry_id: int, field: str,
               tab: str = "entries"):
    row = _entry(entry_id)
    return templates.TemplateResponse(request, "_edit_field.html", {
        "request": request, "entry_id": entry_id, "field": field,
        "label": store.EDITABLE.get(field, field), "value": row[field] if row else "",
        "case_id": row["case_id"] if row else None, "tab": tab,
    })


@app.get("/entry/{entry_id}/cell/{field}", response_class=HTMLResponse)
def cell(request: Request, entry_id: int, field: str):
    """Escape out of an edit without committing."""
    row = _entry(entry_id)
    return templates.TemplateResponse(request, "_cell.html", {
        "request": request, "entry_id": entry_id, "field": field,
        "value": row[field] if row else None,
    })


@app.post("/correct", response_class=HTMLResponse)
def correct(request: Request, entry_id: int = Form(...), field: str = Form(...),
            value: str = Form(""), case_id: int = Form(...),
            tab: str = Form("entries")):
    """One POST, four regions. The cell is the target; the rail and the active tab
    come back out-of-band, because a correction changes the meters and the
    checklist as well as the value — and seeing all three move is the memory
    proof, not a stand-in for it."""
    if not db.one("SELECT id FROM cases WHERE id = ?", (case_id,)):
        return _gone(case_id)
    store.apply_correction(entry_id, field, value)
    row = _entry(entry_id)
    ctx = case_context(request, case_id, tab)
    ctx["just_corrected"] = True          # drives the one-shot flash
    ctx["entry_id"] = entry_id
    ctx["field"] = field
    ctx["value"] = row[field] if row else None
    return templates.TemplateResponse(request, "_correction_swap.html", ctx)


# ── review: the advocate's own record ────────────────────────────────────────

@app.post("/review", response_class=HTMLResponse)
def review(request: Request, case_id: int = Form(...), key: str = Form(...),
           state: str = Form(...), note: str = Form(""),
           tab: str = Form("review")):
    if not db.one("SELECT id FROM cases WHERE id = ?", (case_id,)):
        return _gone(case_id)
    store.set_review(case_id, key, state, note)
    ctx = case_context(request, case_id, tab)
    ctx["focus_key"] = key
    return templates.TemplateResponse(request, "_review_swap.html", ctx)


@app.get("/finding/{case_id}/detail", response_class=HTMLResponse)
def finding_detail(request: Request, case_id: int, key: str, tab: str = "review"):
    ctx = case_context(request, case_id, tab)
    if ctx["case"] is None:
        return _gone(case_id)
    ctx["run"] = ctx["view"].run(key)
    ctx["expanded"] = True
    return templates.TemplateResponse(request, "_rule_row.html", ctx)


@app.get("/finding/{case_id}/collapse", response_class=HTMLResponse)
def finding_collapse(request: Request, case_id: int, key: str, tab: str = "review"):
    ctx = case_context(request, case_id, tab)
    if ctx["case"] is None:
        return _gone(case_id)
    ctx["run"] = ctx["view"].run(key)
    ctx["expanded"] = False
    return templates.TemplateResponse(request, "_rule_row.html", ctx)


# ── the document rail ────────────────────────────────────────────────────────
# One component, two modes. `document` browses the certificate itself and is
# what the rail shows on arrival — the old build left this half of the screen
# empty until the first click, which is the largest piece of dead space in the
# product. `evidence` pins one entry's region. Both are the same HTML shell, so
# switching between them never moves the controls.

def _rail(request: Request, *, mode: str, case_id: int, page: int = 1,
          row=None, view: str = "crop"):
    doc = _document(case_id)
    return templates.TemplateResponse(request, "_rail.html", {
        "request": request, "mode": mode, "doc": doc, "case_id": case_id,
        "page": max(1, min(page, (doc["page_count"] if doc else 1) or 1)),
        "page_count": (doc["page_count"] if doc else 1) or 1,
        "row": row, "view": view,
    })


@app.get("/case/{case_id}/rail", response_class=HTMLResponse)
def rail(request: Request, case_id: int, page: int = 1):
    return _rail(request, mode="document", case_id=case_id, page=page)


@app.get("/evidence/{entry_id}", response_class=HTMLResponse)
def evidence(request: Request, entry_id: int, view: str = "crop"):
    row = _entry(entry_id)
    if not row:
        return HTMLResponse("<p class='rail-empty'>We cannot find that entry any "
                            "more. Reload the case and it will come back.</p>")
    return _rail(request, mode="evidence", case_id=row["case_id"],
                 page=row["page_num"], row=row, view=view)


@app.get("/page/{ec_id}/{page_num}.png")
def document_page(ec_id: int, page_num: int):
    """One page of one certificate, unmarked. Rendered lazily.

    The path id is the EC DOCUMENT, not the case. This route was declared twice
    — once reading the id as a case_id and once as an ec_id — and FastAPI keeps
    whichever it saw first, so the case_id reading won and every caller that
    passed an ec_id got `ec_documents ORDER BY id LIMIT 1`: the first
    certificate on that case. On a single-certificate case the two ids collide
    often enough to look correct. On a case with two, which is the whole point
    of the product, the rail showed the wrong document's page.

    Resolving by ec_id is what the React rail, `_evidence_page.html` and
    `tab_documents.html` all already asked for; `_rail.html` was the only
    caller passing a case_id and now passes `ec_id` too.
    """
    row = db.one("SELECT file_path FROM ec_documents WHERE id = ?", (ec_id,))
    if not row or not row["file_path"]:
        return Response(status_code=404)
    try:
        png = crops.page_rect(row["file_path"], page_num, None)
    except Exception:
        # A page number outside this certificate is a 404, not a 500 — the rail
        # pages through a count that a bundle split can disagree with.
        return Response(status_code=404)
    return Response(png, media_type="image/png",
                    headers={"Cache-Control": "max-age=3600"})


@app.get("/crop/{entry_id}.png")
def crop_png(entry_id: int):
    row = _entry(entry_id)
    if not row or not row["bbox"]:
        return Response(status_code=404)
    png = crops.crop(row["file_path"], row["page_num"], tuple(json.loads(row["bbox"])))
    return Response(png, media_type="image/png",
                    headers={"Cache-Control": "max-age=3600"})


@app.get("/pageview/{entry_id}.png")
def page_png(entry_id: int):
    """The same rectangle, drawn on the whole page. A crop with no context is as
    unfalsifiable as no crop."""
    row = _entry(entry_id)
    if not row:
        return Response(status_code=404)
    bbox = tuple(json.loads(row["bbox"])) if row["bbox"] else None
    png = crops.page_rect(row["file_path"], row["page_num"], bbox)
    return Response(png, media_type="image/png",
                    headers={"Cache-Control": "max-age=3600"})


@app.get("/evidence/page/{ec_id}/{page_num}", response_class=HTMLResponse)
def evidence_page(request: Request, ec_id: int, page_num: int):
    row = db.one("SELECT * FROM ec_documents WHERE id = ?", (ec_id,))
    return templates.TemplateResponse(request, "_evidence_page.html", {
        "request": request, "ec": row, "page_num": page_num,
    })


# ── the artifact that leaves the building ────────────────────────────────────

@app.get("/report/{case_id}", response_class=HTMLResponse)
def report(request: Request, case_id: int):
    ctx = case_context(request, case_id)
    if ctx["case"] is None:
        return _gone(case_id)
    return templates.TemplateResponse(request, "report.html", ctx)
