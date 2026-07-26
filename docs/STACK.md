# The Stack — Decided

**TitleChain · Sarvam Epoch Buildathon**
Companion to [PRD.md](PRD.md) §11 (system architecture) and §14 (build plan). **PRD §11, §14 and
Appendix B have been reconciled to this document** — the spec and the stack now agree, and the
"changed from" notes below are kept as decision history, not as live conflicts. This document
explains *why* each layer is what it is; §11 is the shape of the system, and
[ARCHITECTURE.md](ARCHITECTURE.md) is how it runs — routes, job states, module contracts and
the correction loop.
Version 1.1 · 26 Jul 2026.

> **Compliance note (PRD §14.0):** this document is a decision record. No product code exists.
> Everything in the file layout below is written on the floor tomorrow.

---

## The decision in one table

| Layer | Pick | Status |
|---|---|---|
| Environment | `uv`, Python **3.14.3** | verified — full dep set resolves and installs |
| Backend | **FastAPI + uvicorn**, single process | as PRD §11 |
| Frontend | **Jinja2 + HTMX + hand-written CSS**, served by FastAPI | changed from PRD §11 (was React + Vite) — **§11 now updated to match** |
| Typed schema | **Pydantic v2**, one definition, three uses | new decision |
| Sarvam — digitise | **`sarvamai` SDK** | proven working (`run_di.py`, 3 real ECs) |
| Sarvam — extract | **raw `httpx`** → `/v1/chat/completions` | SDK's strict-`json_schema` path untested |
| Crops | **pypdfium2 + Pillow** | **verified end to end on a real EC** (below) |
| Storage | **stdlib `sqlite3`**, no ORM | as PRD §11, minus SQLAlchemy |
| Graph | **plain dicts**, no networkx | new decision |
| Rulebook | pure functions + **pytest** | makes PRD's "unit-tested" claim true |
| Public link | **Cloudflare quick tunnel** over localhost | not a deploy |

Total third-party surface: **eight packages.** Every one of them installed and imported on this
machine before the event started.

---

## The one thing that was still an assumption, now verified

PRD §11 lists `crops.py — OURS — bbox → cropped PNG from page raster` as if it were free. It was
the last unproven mechanical dependency, and the entire provenance argument rests on it. So it
was tested against a real certificate rather than reasoned about.

`pypdfium2` renders `ec_samples/ec2_pacollege.pdf` page 2 at **3509 × 2480** — byte-for-byte the
raster geometry Sarvam digitised against. Therefore stage-① `coordinates` land on the page render
with **no transform at all**:

```python
scale = 3509 / max(page.get_size())      # 3509 / 842.0
img   = page.render(scale=scale).to_pil()
crop  = img.crop((x1, y1, x2, y2))       # straight from the block JSON
```

Cropping `[308, 114, 3208, 1342]` returns exactly the block traced in
[PIPELINE.md](PIPELINE.md) — `8756/2020`, `Cancellation Deed`, `PR Number: 2520/2019`, and the
remarks sentence `This document cancels the document R/பொள்ளாச்சி/புத்தகம் 1/2520/2019`.

**What this buys:** `crops.py` is about fifteen lines, has no system dependencies (no poppler, no
ImageMagick), ships as a wheel on Python 3.14, and the "every finding is falsifiable in one
click" claim is now a mechanical certainty rather than a hope. The R1 demo beat is safe.

---

## Frontend: why HTMX and not React

PRD §11 committed to React + Vite. That was written before the team size was fixed at **one**.

Solo, React costs a second process, a CORS config, a build step, a JSON contract negotiated
between two halves of the same brain, and roughly **45–60 minutes of scaffolding before the first
pixel appears** — paid out of the 11:30–14:00 MVP window, which is the same window that has to
produce `graph.py` and `rulebook.py`. Those two files are the product. Nothing may compete with
them for attention.

HTMX removes the tax without lowering the ceiling that matters here:

| Surface (PIPELINE §④) | Implementation | Cost |
|---|---|---|
| Entries table | Jinja loop over typed rows | trivial |
| Source crop | `<img src="/crop/{entry_id}">` — endpoint returns PNG bytes | trivial |
| Chain graph | CSS grid, one column per generation depth; resolved edges solid, dangling edges dashed and open | ~40 min |
| Findings list | Jinja loop, ranked, each linking its evidence entries | trivial |
| Inline correction | `hx-post="/correct"` with `hx-target="#findings"` | ~20 min |
| Order block | Jinja template + a copy button | trivial |

The correction row is the argument. **`hx-target` makes correction propagation nearly free** — the
POST re-runs `derive()` server-side and swaps the findings panel with the re-derived HTML. That
is not a UI trick standing in for the F11 memory proof; it *is* the memory proof, rendered. In
React the same behaviour is state management you have to write, debug, and keep in sync.

The genuine loss is visual ceiling. It is bought back with hand-written CSS on a single page —
which is affordable precisely because there is no framework underneath it.

---

## Pydantic as the single schema source

Write the PRD §10.4 extraction schema **once**, as Pydantic models. It then serves three jobs:

1. `Entry.model_json_schema()` → the `response_format` payload sent to `sarvam-105b`
2. `Entry.model_validate(...)` → validation of what comes back
3. the same models type `derive()`, the rules, and the template context

The failure this prevents is specific and common: the prompt's schema and the code's expectations
drift apart during a rushed afternoon, and the symptom is a `KeyError` at 15:40 that looks like a
model failure and is not. One definition means drift is impossible by construction.

It also makes the `null` discipline enforceable. Every field is `Optional` with **no default** —
so a model that quietly omits a field fails validation loudly instead of silently producing a
half-entry. Honest nulls are load-bearing (PIPELINE §②); the type system should be what enforces
them, not the prompt.

---

## Sarvam access: SDK for one call, httpx for the other

Split deliberately, not out of inconsistency.

**Digitisation → `sarvamai` SDK.** Already proven against three real certificates. The async
job/upload/poll/download dance is genuinely fiddly and the SDK handles it. Do not rewrite it.

**Extraction → raw `httpx`.** Whether the SDK's chat surface passes a strict `json_schema`
`response_format` through cleanly is **untested**, and this is the last load-bearing unknown in
the whole system (PRD §14.0 flags it too). A direct POST is eight lines, makes the exact request
body visible, and means a schema rejection is debuggable in seconds rather than through a wrapper.
Under time pressure, transparency beats ergonomics.

**Resolve this tonight.** It is the only stack question still genuinely open, and it is fifteen
minutes of work against a cached `document.md` that already exists in `output/`.

---

## SQLite without an ORM

Nine tables (PRD §11), every write authored by us, single process, single writer, no migrations,
no concurrent access. SQLAlchemy or SQLModel would cost 30–45 minutes of model definition and buy
connection pooling, migrations, and relationship lazy-loading — three things not needed once.

Instead: one `schema.sql`, executed at startup, plus a `db.py` of maybe sixty lines with a row
factory returning dicts.

What Memory is actually scored on (rubric L4/L5) is that **state survives restart**, that
**corrections propagate**, and that **stale findings are distinguishable from current** — the last
of which is the `rulebook_version` column, not an ORM feature. Plain SQL delivers all three.

The rule to hold: **SQLite is a persistence layer, never a computation layer.** No business logic
in SQL. `derive()` reads typed Python objects and returns typed Python objects, which is what
makes it unit-testable — and stage ③ being testable is the product (PIPELINE §③).

---

## No graph library

Fewer than fifty nodes, one traversal, three edge types. `networkx` would mean reading its docs
during the MVP window to save code that is shorter than the import statement's documentation.

```python
nodes = {entry.doc_key: entry for entry in entries}
edges = [...]                                  # PR · cancel · succession
for e in edges:
    e.resolved_entry_id = nodes.get(e.target_key)   # ← the entire product
```

That `.get()` returning `None` is `R4 DANGLING_PARENT`. The traversal nobody performs is a
dictionary lookup. Keeping it that visible is a feature — it is also the line to point at on stage.

---

## File layout

Mapping PRD §11's module names onto real files. Written tomorrow, from zero.

```
app/
  main.py          FastAPI, routes, startup schema exec
  models.py        Pydantic — the §10.4 schema, single source
  ingest.py        chunk >10p, validate, store original
  digitise.py      → sarvamai SDK
  extract.py       → httpx, 105b, strict json_schema
  names.py         → transliteration ta-IN→en-IN, role-marker normalisation
  graph.py         OURS — nodes, PR/cancel/succession edges
  rulebook.py      OURS — R1..R10, pure functions
  crops.py         OURS — pypdfium2 → PNG  (verified)
  report.py        OURS — scrutiny report
  db.py            sqlite3, row factory
  schema.sql       9 tables
  templates/       Jinja — index · entries · chain · findings · order_block
  static/          one stylesheet, htmx.min.js vendored locally
tests/
  test_rulebook.py one test per rule
  fixtures.py      hand-built entries[] — no API calls in tests
```

**`htmx.min.js` is vendored, not CDN-linked.** ~14 KB in `static/`. A CDN is a third-party network
dependency at demo time, and PRD §11 says *"Sarvam APIs only. No third-party services."* A demo
that needs conference wifi to render its own buttons is a demo that can fail for reasons that have
nothing to do with the product.

---

## Bootstrap (run on the floor, 10:30)

```bash
uv venv && uv pip install fastapi "uvicorn[standard]" sarvamai pypdfium2 pillow jinja2 python-multipart pytest httpx
```

```bash
uv run uvicorn app.main:app --reload
```

**Tonight, permitted as environment prep:** pre-warm the wheel cache with `uv pip download` of the
same list. Installing from a warm cache is offline and instant; installing over conference wifi at
10:31 is a gamble taken at the worst possible moment. Downloading wheels is not writing code.

---

## Public link

The rubric's final block expects public-link verification. **Cloudflare quick tunnel over
localhost** — one command, real HTTPS, no account, roughly thirty seconds.

Not Render, not Fly, not Vercel. A real deploy means a build environment that differs from the
laptop, secret management, a cold-start, an ephemeral filesystem that eats the SQLite file, and a
first-deploy failure mode discovered at 16:10. The tunnel keeps the database on disk where the
demo state already lives, and the thing behind the link is the exact process that was just
rehearsed.

Bring it up during 15:30–16:30 (PRD §14.4, the reserved block), never earlier.

---

## Where this stack breaks, and the answer

| Failure | Response |
|---|---|
| 105B rejects the strict schema | already the reason for raw `httpx` — the request body is visible and editable in one file |
| DI rate limit (10/min) | `output/` already holds three cached digitisations; `digitise.py` checks cache before calling |
| HTMX swap targets the wrong element | it is HTML in a template — view source, fix, reload. No build, no source map |
| SQLite file corrupted mid-demo | delete it; startup re-execs `schema.sql`. The reset script from §14.4 is `rm titlechain.db` |
| pypdfium2 render is slow on a 40-page EC | render lazily, per crop request, and cache the PNG. Never render the whole document up front |
| Conference wifi dies | everything except the two Sarvam calls is local; cached outputs cover the demo path (PRD §15.5) |

---

## Solo: the honest cut order

PRD §14 was drafted without a fixed team size; **it now opens with this same cut order.** At one
person, §14.2 and §14.3 together are more than the clock allows. Cut in this order, decided
**now** rather than at 14:45:

1. **F12 staleness clock** — the `rulebook_version` column earns the point; the UI for it does not.
2. **F11 advocate login** — case scoping without auth still demonstrates memory. Auth is pure cost.
3. **Chain graph visualisation → nested list.** Keep every line of graph *logic*. This is the
   PRD's own stated fallback and it remains the right one.
4. **F13 two-seed disagreement pass** — a beautiful idea and the first genuine luxury on the list.

**Never cut:** `rulebook.py`, `crops.py`, correction propagation, the order block. Those four are
the four rubric parameters, one each. Everything else is decoration on top of them.
