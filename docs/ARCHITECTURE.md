# The Architecture — How It Runs

**TitleChain · Sarvam Epoch Buildathon**
Companion to [PRD.md](PRD.md) §11. [PIPELINE.md](PIPELINE.md) explains the four stages,
[STACK.md](STACK.md) explains what each layer is built out of, PRD §11 is the shape of the
system — **this is the wiring**: routes, job states, module contracts, and the exact call
sequence behind every action the advocate takes.
Version 1.0 · 26 Jul 2026.

> **Compliance note (PRD §14.0):** this is a decision record, like STACK.md. No product code
> exists. Every signature, route and table below is written on the floor tomorrow.

---

## The organising rule

PIPELINE has one: *models read, code decides.* This document has the second one:

> **Recorded state is append-only. Derived state is disposable.**

`entries`, `parties`, `corrections`, the original PDF, the raw Sarvam JSON — facts. Written
once, never mutated, never deleted.
`edges`, `findings`, `name_clusters` — opinions. Deleted and rebuilt in full every time
`derive()` runs.

Everything difficult in this system falls out of that line. Correction propagation is not a
diff algorithm — it is an append to `corrections` followed by a full rebuild of the disposable
half. Re-running the pipeline on a half-finished case is safe because every step is idempotent
against recorded state. A stale finding is impossible because findings never survive a
re-derivation; only their `rulebook_version` stamp tells you which run produced the set you're
looking at.

The whole system is one process, one writer, no queue, no scheduler.

---

## Runtime shape

```
browser ──HTML/HTMX──► FastAPI (uvicorn, single process, single worker)
                            │
                    ┌───────┴────────┐
                    │                │
              request path      background task
              (< 200 ms)        (60–120 s per EC)
                    │                │
                    │        run_pipeline(ec_id)
                    │           ingest → digitise → extract → derive
                    │                │
                    └────────┬───────┘
                             ▼
                  SQLite (titlechain.db)  +  filesystem (data/)
```

**No worker process, no Celery, no websockets.** FastAPI `BackgroundTasks` runs the pipeline;
the browser polls a status fragment every 2 s with `hx-trigger="every 2s"`. Two reasons: a
second process is a second thing that can be down at 16:10, and polling is the failure mode
you can *see* — a stuck job shows a stuck progress line, where a dropped websocket shows a
page that looks fine and is lying.

The cost is that a 40-page EC occupies the single worker's background slot for two minutes.
Acceptable: one advocate, one case at a time, and the demo is a 12-page certificate.

---

## Job state machine

One `status` column on `ec_documents`, one on `chunks`. The pipeline is a walk through these,
and **every transition is committed before the next step starts** — which is what makes
`run_pipeline()` resumable rather than restartable.

```
ec_documents.status

  UPLOADED ──► CHUNKED ──► DIGITISING ──► DIGITISED ──► EXTRACTING ──► EXTRACTED ──► DERIVED
                               │                            │                           │
                               ▼                            ▼                           │
                           (partial)                     FAILED_TYPING ─────────────────┘
                        ≥1 chunk UNREAD                  manual typing        (derive runs on
                        → continue, degraded              still enters         whatever entries
                                                          DERIVED              exist — always)

chunks.status   PENDING ──► RUNNING ──► DONE
                                └─────► RETRY ──► UNREAD     (retry once, then surface it)
```

Three properties worth stating because they are decisions, not accidents:

**`DERIVED` is reachable from every failure state.** A certificate with an unread chunk still
gets a chain, still gets findings, and gets an extra one saying pages 11–20 were never read.
Partial evidence honestly labelled is the product; withheld output is not.

**`UNREAD` is a terminal state that renders.** It appears in the UI as a page-sized gap with
the raw page image next to it. PIPELINE's rule — *degrade visibly* — is enforced here, in the
state machine, rather than being remembered at each call site.

**Re-entry is idempotent.** `run_pipeline(ec_id)` called on a `DIGITISED` document skips
straight to extraction, because it dispatches on the stored status, not on a position in a
function. That is the recovery story for every "it died halfway" scenario: call it again.

---

## Routes

Full pages are rare. Almost everything is a fragment, because HTMX swapping fragments *is* the
interaction model (STACK, "Frontend: why HTMX").

| Method | Path | Returns | Notes |
|---|---|---|---|
| `GET` | `/` | page | upload form |
| `POST` | `/cases` | 303 → `/cases/{id}` | multipart upload; hashes, dedupes, spawns `run_pipeline` |
| `GET` | `/cases/{id}` | page | shell + four fragment slots |
| `GET` | `/cases/{id}/status` | fragment | `hx-trigger="every 2s"`; self-cancels on `DERIVED` |
| `GET` | `/cases/{id}/entries` | fragment | typed table |
| `GET` | `/cases/{id}/chain` | fragment | graph (CSS grid; nested list if cut) |
| `GET` | `/cases/{id}/findings` | fragment | ranked blocking → material → informational |
| `GET` | `/cases/{id}/order-block` | fragment | pre-filled replacement EC |
| `GET` | `/crop/{entry_id}` | `image/png` | lazy render + disk cache |
| `POST` | `/entries/{id}/correct` | fragment (+2 OOB) | the memory proof — sequence below |
| `GET` | `/cases/{id}/report` | page | print stylesheet, no PDF library |

**The status fragment cancels its own polling.** When the pipeline reaches `DERIVED` it renders
the finished panels with `hx-swap-oob="true"` and omits the `hx-trigger` attribute — the
element that was polling replaces itself with one that doesn't. No JavaScript, no timer to
clear, and the "is it done" logic lives in exactly one template.

**`/crop/{entry_id}` takes an entry, not a bbox.** Coordinates never travel through the URL.
The endpoint looks up `page_num` + `block_id`, reads the coordinates out of the stored raw
Sarvam JSON, and renders. So a crop cannot be requested for a rectangle nobody extracted, and
the provenance thread stays a server-side lookup from finding → entry → block → pixels.

---

## Module contracts

The column that matters is **network**. Only three modules touch it, and none of them is
allowed to make a judgment.

| Module | In → Out | Network | Pure |
|---|---|---|---|
| `ingest.py` | `UploadFile` → `ec_id`, chunk rows, stored original | — | no (disk) |
| `digitise.py` | chunk → `document.md` + per-page JSON on disk | Sarvam DI | no |
| `extract.py` | table HTML → `list[Entry]` (Pydantic-validated) | 105B | no |
| `names.py` | `list[Party]` → cluster ids | Transliteration | no |
| `graph.py` | `list[Entry]` → `list[Edge]` | **no** | **yes** |
| `rulebook.py` | `(entries, edges, header)` → `list[Finding]` | **no** | **yes** |
| `crops.py` | `(pdf_path, page, bbox)` → PNG bytes | **no** | **yes** |
| `report.py` | `(entries, edges, findings)` → HTML | **no** | **yes** |
| `db.py` | SQL ↔ dicts | — | no |

`graph.py` and `rulebook.py` are pure functions over Pydantic objects. They never see a
database handle, never see a request, and never see an API key. That is the precondition for
`tests/test_rulebook.py` running against hand-built fixtures with no network — which is what
makes the PRD's "unit-tested" claim true rather than aspirational.

### `derive()` — the one recompute path

```
derive(case_id):
    entries  = db.entries_for(case_id)          # recorded, with corrections applied
    parties  = names.cluster(db.parties_for(case_id))
    edges    = graph.build(entries, parties)    # PR · cancel · succession
    findings = rulebook.run(entries, edges, header)
    db.replace_derived(case_id, edges, findings, RULEBOOK_VERSION)
    return Bundle(entries, edges, findings)
```

Five lines, and everything routes through them. The pipeline's last step calls it. The
correction endpoint calls it. A rulebook version bump calls it. **There is no second path that
produces a finding**, which is why a finding's provenance is always the same shape and why
`replace_derived` can be a blunt `DELETE ... WHERE case_id = ?` inside one transaction.

`names.cluster()` is called inside `derive()`, not at extraction time, deliberately: a
corrected name must re-cluster, and re-clustering must re-run the graph, because a chain break
and a spelling variant are the same shape until names are resolved (PIPELINE §3a). Putting
clustering upstream of `derive()` would make that correction a no-op — the exact bug the memory
proof would fail on.

---

## The correction loop, step by step

This is F11, the Memory parameter, and the sequence is worth pinning because it is the demo
beat that must not be improvised.

```
① advocate edits a name / date / doc-no in the entries table
② hx-post → POST /entries/{id}/correct   {field, new_value}
③ INSERT INTO corrections (entry_id, field, old_value, new_value, actor, created_at)
       ← append-only; the original extraction is never overwritten
④ UPDATE entries SET {field} = new_value        ← the working value
⑤ derive(case_id)                                ← re-cluster, rebuild graph, re-run R1..R10
⑥ response: findings fragment  →  hx-target="#findings"
       + entries row           →  hx-swap-oob
       + chain panel           →  hx-swap-oob
```

One POST, three panels updated, no client state. Steps ③ and ④ together are why the correction
is *memory* and not an edit: `corrections` is the durable record of what this advocate knew
that the model didn't, it survives restart, and it is the table that "prior corrections by this
advocate" (PRD §10.7) reads from in the production version.

The visible proof on stage is step ⑤ doing real work: fix one Tamil name and a `CHAIN_BREAK`
finding disappears while a `DANGLING_PARENT` resolves — because the cluster changed, so an edge
changed, so two rules changed their minds. Nothing about that is a UI animation.

---

## Storage split

| Where | What | Why |
|---|---|---|
| SQLite | the nine tables (PRD §11) | queried, joined, corrected |
| `data/uploads/{sha256}.pdf` | original certificate | content-addressed → re-upload is a dedupe, not a re-run |
| `data/digitised/{ec_id}/` | `document.md`, per-page JSON | the raw Sarvam response, immutable, the audit record |
| `data/crops/{entry_id}.png` | rendered crop | write-through cache; deletable, regenerable |

**Raw Sarvam JSON is never parsed into the database and then discarded.** Coordinates,
`layout_tag`, `reading_order` and block confidence stay on disk in the form Sarvam returned
them, and `entries.block_id` is the join key back into that file. Auditability (PRD §9) means
the response that produced a finding is still recoverable byte-for-byte a year later, not
summarised into columns we chose in a hurry.

Content-addressing the upload also gives the demo a free safety net: re-uploading the same
certificate returns the existing case instantly instead of spending ₹6 and 60 s. Combined with
`digitise.py`'s cache check against the three files already in `output/`, the demo path can run
with the Sarvam calls never leaving the building.

---

## `schema.sql`

Nine tables, executed at startup with `CREATE TABLE IF NOT EXISTS`. Recorded-vs-derived is
marked, because it dictates who may delete what.

| Table | Kind | Key columns |
|---|---|---|
| `cases` | recorded | `id, advocate_id, property_key, created_at` |
| `ec_documents` | recorded | `id, case_id, status, sha256, sro, village, survey_nos, search_start, search_end, issue_date, declared_entry_count, page_count, file_path` |
| `chunks` | recorded | `id, ec_id, page_from, page_to, status, attempts, output_dir` |
| `entries` | recorded | `id, ec_id, sr_no, doc_no, doc_year, date_*, nature, volume_page, consideration_value, market_value, remarks, page_num, block_id, block_confidence` |
| `parties` | recorded | `id, entry_id, role, name_native, name_roman, role_marker` |
| `corrections` | recorded | `id, entry_id, field, old_value, new_value, actor, created_at` |
| `name_clusters` | **derived** | `id, case_id, party_id, cluster_key` |
| `edges` | **derived** | `id, case_id, from_entry, to_doc_no, to_doc_year, edge_type, resolved_entry_id NULL` |
| `findings` | **derived** | `id, case_id, rule_id, severity, message, evidence_entry_ids, rulebook_version, status` |

Two departures from PRD §11 worth naming: `chunks` is new (the 10-page cap needs a state
machine of its own, and PRD §11 had nowhere to put chunk status), and `cluster_id` moved off
`parties` into a `name_clusters` table — because clustering is derived and must be deletable,
and a derived column sitting on a recorded table is exactly how the two halves get confused at
15:40.

`edges.resolved_entry_id IS NULL` is R4. `findings.rulebook_version` is F12. Neither needs
code beyond the column.

---

## Failure surface, by route

PIPELINE lists what breaks; this is where the handling lives, so it isn't written twice.

| Failure | Handled in | What the advocate sees |
|---|---|---|
| DI job fails twice | `run_pipeline`, chunk → `UNREAD` | gap in the entries table + raw page image |
| Rate limit (10/min) | `digitise.py`, backoff | status fragment shows real queue position |
| 105B rejects schema | `extract.py` → retry → 30B → `FAILED_TYPING` | entry flagged for manual typing, case still derives |
| Field unreadable | Pydantic `Optional`, no default | `null` → R9 fires → review against crop |
| Background task dies | status stuck; `POST /cases/{id}/retry` | one button, resumes from stored status |
| SQLite corrupted | `rm titlechain.db`, restart re-execs `schema.sql` | full reset in one command |
| Sarvam outage in demo | cache check in `digitise.py` | nothing — cached path is the same path |

The retry button is the whole recovery story, and it works because of the state machine: it
calls `run_pipeline(ec_id)` again, and the function resumes wherever the committed status says
it stopped.

---

## Build order, and where the seams are

The order below is chosen so that the two files that *are* the product get built against real
data as early as possible, and so that the STACK cut list can be executed without unpicking
anything.

1. `models.py` + `schema.sql` + `db.py` — the schema is the contract; nothing else can be
   written honestly before it exists.
2. `extract.py` against the **cached** `output/ec2_pacollege-ta-IN/document.md`. No upload
   path, no UI. This is the last load-bearing unknown (STACK) and it is resolved with a file
   already on disk.
3. `graph.py` + `rulebook.py` + `tests/` — pure, offline, fixture-driven. Buildable with the
   wifi off.
4. `derive()` — five lines wiring 3 to the database.
5. Routes + templates, entries → findings → crops → chain → order block.
6. `ingest.py` + `digitise.py` — the live upload path, built **last**, because the cached
   outputs mean nothing downstream is blocked on it.

Building the ingest path last is the non-obvious call and the important one. It is the only
part that is slow, rate-limited, and dependent on conference wifi — and it is the part the
product's argument does not live in. Cached inputs make steps 2–5 an offline exercise.

The cut list from STACK maps onto seams, not surgery:

| Cut | Touches | Leaves intact |
|---|---|---|
| F12 staleness UI | one template block | the `rulebook_version` column |
| F11 login | `advocate_id` becomes a constant | case scoping, corrections |
| Chain visualisation | `chain.html` → nested `<ul>` | every line of `graph.py` |
| F13 two-seed pass | one call in `extract.py` | everything |

None of them touches `derive()`, `rulebook.py`, `crops.py` or the correction endpoint — which
is the test of whether the cut order was chosen honestly.

---

## Still open

1. **105B strict `json_schema` via raw httpx** — untested, blocks step 2 above. Fifteen minutes
   against the cached `document.md` (STACK says resolve it tonight; it is the only genuine
   unknown left).
2. **Sub-row attachment across a chunk boundary.** A parent entry starting on page 10 and
   continuing on page 11 spans two digitisation chunks. Mitigation: overlap chunks by one page
   and dedupe on `sr_no`. Untested; only bites on ECs longer than ten pages, which the demo
   certificate is not.
3. **Background task and SQLite write contention.** Single writer in practice, but a
   correction POST arriving mid-pipeline shares the connection. `PRAGMA journal_mode=WAL` at
   startup, and don't hold a transaction open across a network call.
