"""TitleChain — FastAPI serving Jinja + HTMX from one process.

Two routes the user can see (/ and /case/{id}). Everything else is a fragment
swap or an image. No build step, no npm, no CORS, no CDN.
"""

from __future__ import annotations

import json
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import crops, db, derive as derive_mod, paths, pipeline, store
from .fixtures import SAMPLES
from .models import DerivedView

ROOT = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(_: FastAPI):
    paths.ensure()     # creates uploads/ and output/ under the data dir
    paths.seed_cache() # bundled digitisations, so the samples never wait on Sarvam
    db.init()          # idempotent; if the file is ever corrupted: rm titlechain.db
    yield


app = FastAPI(title="TitleChain", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.globals["SAMPLES"] = SAMPLES
templates.env.globals["EDITABLE"] = store.EDITABLE
templates.env.globals["RULEBOOK_VERSION"] = derive_mod.RULEBOOK_VERSION

PROCESSING = {"QUEUED", "READING", "TYPING", "DERIVING"}


# ── shared page assembly ─────────────────────────────────────────────────────

def case_context(request: Request, case_id: int) -> dict:
    case = db.one("SELECT * FROM cases WHERE id = ?", (case_id,))
    if not case:
        return {"request": request, "case": None}
    header, ec_row = store.load_header(case_id)
    entries = store.load_entries(ec_row["id"]) if ec_row else []
    view = derive_mod.derive(header, entries) if (header and entries) else DerivedView()
    return {
        "request": request,
        "case": case,
        "header": header,
        "ec": ec_row,
        "entries": entries,
        "view": view,
        "processing": case["status"] in PROCESSING,
        "corrections": store.corrections_for(ec_row["id"]) if ec_row else [],
        "unread": store.unread_chunks(ec_row["id"]) if ec_row else [],
        "refusal_checks": json.loads(case["refusal_checks"] or "null"),
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
            header, ec_row = store.load_header(case["id"])
            entries = store.load_entries(ec_row["id"]) if ec_row else []
            summary["header"] = header
            if header and entries:
                summary["view"] = derive_mod.derive(header, entries)
                summary["entry_count"] = len(entries)
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
            "label": c["property_key"] or "Untitled case",
            "sub": f"{header.sro} SRO" if header and header.sro else c["status"].lower(),
        })
    return {
        "cases": cases,
        "commands": [{"label": "All cases", "kind": "Go", "href": "/"}],
    }


@app.post("/upload")
async def upload(file: UploadFile):
    data = await file.read()
    path, error = pipeline.accept_upload(file.filename or "upload", data)
    if error:
        return RedirectResponse(f"/?rejected={error}", status_code=303)
    case_id = store.create_case(file.filename or "New case")
    threading.Thread(target=pipeline.run, args=(case_id, path), daemon=True).start()
    return RedirectResponse(f"/case/{case_id}", status_code=303)


@app.post("/sample/{key}")
def open_sample(key: str):
    if key not in SAMPLES:
        return RedirectResponse("/?rejected=Unknown sample", status_code=303)
    path = pipeline.stage_sample(key)
    case_id = store.create_case(SAMPLES[key]["label"])
    threading.Thread(target=pipeline.run, args=(case_id, path), daemon=True).start()
    return RedirectResponse(f"/case/{case_id}", status_code=303)


@app.get("/case/{case_id}", response_class=HTMLResponse)
def case_page(request: Request, case_id: int):
    ctx = case_context(request, case_id)
    if ctx["case"] is None:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "case.html", ctx)


@app.get("/case/{case_id}/body", response_class=HTMLResponse)
def case_body(request: Request, case_id: int):
    """Polled while processing. When the returned fragment is READY it carries no
    hx-trigger, so polling stops by itself — no client-side state to unwind."""
    return templates.TemplateResponse(request, "_body.html", case_context(request, case_id))


# ── correction: the memory proof, rendered ───────────────────────────────────

@app.get("/entry/{entry_id}/edit/{field}", response_class=HTMLResponse)
def edit_field(request: Request, entry_id: int, field: str):
    row = _entry(entry_id)
    return templates.TemplateResponse(request, "_edit_field.html", {
        "request": request, "entry_id": entry_id, "field": field,
        "label": store.EDITABLE.get(field, field), "value": row[field] if row else "",
        "case_id": db.one("SELECT case_id FROM ec_documents WHERE id = ?",
                          (row["ec_id"],))["case_id"] if row else None,
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
            value: str = Form(""), case_id: int = Form(...)):
    store.apply_correction(entry_id, field, value)
    ctx = case_context(request, case_id)
    ctx["just_corrected"] = True          # drives the one-shot flash
    return templates.TemplateResponse(request, "_derived.html", ctx)


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
        return HTMLResponse("<p class='rail-empty'>That entry is no longer available.</p>")
    return _rail(request, mode="evidence", case_id=row["case_id"],
                 page=row["page_num"], row=row, view=view)


@app.get("/page/{case_id}/{page_num}.png")
def document_page(case_id: int, page_num: int):
    """The certificate itself, unmarked. Rendered lazily, one page at a time."""
    doc = _document(case_id)
    if not doc or not doc["file_path"]:
        return Response(status_code=404)
    png = crops.page_rect(doc["file_path"], page_num, None)
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


# ── the artifact that leaves the building ────────────────────────────────────

@app.get("/report/{case_id}", response_class=HTMLResponse)
def report(request: Request, case_id: int):
    return templates.TemplateResponse(request, "report.html", case_context(request, case_id))
