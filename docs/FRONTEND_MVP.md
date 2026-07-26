# The Frontend — Bare-Bones MVP

**TitleChain · Sarvam Epoch Buildathon**
Companion to [PRD.md](PRD.md) §7 (Core MVP), [PIPELINE.md](PIPELINE.md) §④ (Render) and
[STACK.md](STACK.md) (HTMX/Jinja, solo cut order). Where this document and PRD §11's UI sketch
disagree, this one wins — it is the later decision, made against a fixed team size of one and a
fixed clock. Version 1.0 · 26 Jul 2026.

> **The constraint that governs every choice below:** the build window is 11:30–14:00 for the
> product and 14:00–15:30 for the scoring surface. `graph.py` and `rulebook.py` are the product.
> **No frontend decision in this document is allowed to cost them a minute.** Everything here is
> either a Jinja loop, a CSS grid, or an `hx-target` — the three things that are already free.

---

# Part 1 · First principles

## The single most important user problem

Not "Tamil ECs are hard to read." Reading is tedious, and tedium is not the hypothesis.

> **Meena cannot tell whether the certificate she was given is capable of answering the question
> she was asked.** She converts *"I have read every row"* into *"this title is clear"* — two
> different statements — and signs across the gap.

Extraction is the *cost of entry* to solving that. It is not the value. If the frontend spends its
budget making the extracted table beautiful, it will have optimised the part of the product that is
already table stakes ([CUSTOMER_JOURNEY.md](CUSTOMER_JOURNEY.md), Delight section: extraction
quality scores under Document Intelligence and **cannot be reused** as Delight).

## The one workflow that must complete successfully

```
upload one EC  →  see a computed statement of what it covers and what it misses
               →  check one finding against the pixel that proves it
               →  leave with the exact next certificate to order
```

Four steps. Everything else in the PRD is a variation on, or an accessory to, this line. If a user
completes this once and believes the result, the hypothesis is validated. If they complete it and
shrug, no amount of polish elsewhere saves it.

## The smallest feature set that delivers it

| Keep | Why it is irreducible |
|---|---|
| **Upload → processing → case page** | There is no product without an input |
| **Coverage verdict** (window vs. PR years) | This *is* the hypothesis. R3 rendered. |
| **Findings list, ranked, with confirmations** | The verdict is not believable alone; it needs the rest of the rulebook around it |
| **Source crop on click** | A finding without its crop is an assertion. Falsifiability is the trust mechanic. |
| **Pre-filled order block** | Without it the product ends on bad news and no action — PRD's own L1 trap |
| **Inline correction that re-derives** | The Memory proof, and ~20 min via `hx-target` |
| **Case list that survives restart** | The only evidence that state persisted |

Seven surfaces. Six of them are Jinja loops.

## Deliberately deferred

| Deferred | To | Because |
|---|---|---|
| Login / accounts | V2 | Case scoping demonstrates memory without auth. Auth is pure cost (STACK.md cut #2). |
| Chain **visualisation** | V2 | Nested list carries the same information. Keep every line of graph *logic*. (cut #3) |
| Staleness clock UI | V2 | The `rulebook_version` column earns the point; a countdown does not. (cut #1) |
| Two-seed disagreement UI | V2 | First genuine luxury. (cut #4) |
| Dark mode | V2 | The document raster is a white page. A dark chrome around a white crop is *worse* for comparison, and the report is printed. |
| Settings screen | never | v1 has exactly one setting (staleness threshold). A setting used in one place lives in that place. |
| Dashboard / analytics | never | Nothing to count yet, and counting is not the job |
| Mobile review | V2 | Mobile is for *capture*, not for evidence work. Responsive down to upload + verdict only. |
| Sort / filter / search on entries | V2 | At 2–15 entries it is decoration. At 40 it becomes real — that is a V2 signal, not a V1 feature. |
| Undo/redo, multi-user, notifications, onboarding tour | V2+ | None of them touch the hypothesis |

---

# Part 2 · Define the MVP

**Primary persona.** Advocate Meena — property advocate, Coimbatore, 8–15 scrutiny files/month,
her name on the opinion. Single user. Ravi (bank credit manager) is a *reader of the exported
report*, never a logged-in user — so **the report is Ravi's entire UI**, and it costs one Jinja
template.

**A fourth persona the PRD does not name, and the frontend must serve:** the judge. 90 seconds, over
a shoulder, on a projector, from three metres. This is not vanity — it means the verdict must be
legible at 3 m, which forces large type and high contrast, which is *also* right for a 45-year-old
advocate reading a dense document at the end of a long day. The two constraints agree. Design for
the projector and the real user gets it too.

**Core journey (the only one built):**

```
/ (home)  ──drop PDF──►  /case/{id}  ──polls──►  same page fills in
                              │
                              ├─ click finding ──► crop appears in right pane
                              ├─ click a "—" ────► correct it ──► findings re-derive in place
                              ├─ copy order block
                              └─ export report
```

One route change in the entire product. `/` → `/case/{id}`. Everything else is a fragment swap.

**Success criteria for the MVP** — measurable on the day:

1. A person who has never seen the product opens a case and states, unprompted, what the
   certificate fails to cover. *(the comprehension test — binary, testable on a neighbour at the venue)*
2. Upload → verdict visible in ≤90 s on a ≤10-page EC.
3. Every finding reaches its source crop in one click, <5 s.
4. Correct a name → findings visibly change → restart the server → correction and findings intact.
5. The order block is copyable and correct without editing.

**Assumptions being tested** (and what each result teaches):

| Assumption | If it holds | If it fails |
|---|---|---|
| A coverage verdict changes her behaviour before signing | The insight is the product; sell the verdict, not the OCR | We built a faster reader, not a new answer — reposition to time-saved and compete on extraction, which is a worse business |
| She trusts a computed verdict | Provenance-on-click was sufficient | Trust needs more than a crop — likely a rule-explanation surface, i.e. V2 is "show your working" |
| The pre-filled order converts bad news into action | Order block becomes the monetisable surface (per-order fee, TNREGINET integration) | The product creates work and gets uninstalled — the honest failure mode flagged in CUSTOMER_JOURNEY |
| She will correct errors rather than abandon | Corrections compound into the name-cluster asset (the moat) | Extraction must be near-perfect before launch; the human-in-loop model is wrong |

---

# Part 3 · The simplest possible UX

## Two routes. One pane. That's the whole app.

| Route | Purpose |
|---|---|
| `/` | Upload + case list. Also the empty state, also the "history", also the landing page. |
| `/case/{id}` | Everything else, in five bands, plus a persistent evidence pane. |

**Screens deliberately not built, and what happened to them instead:**

| The screen a SaaS reflex would add | Where it went |
|---|---|
| Landing page | `/` — the dropzone *is* the pitch |
| Dashboard | Deleted. There is nothing to aggregate. |
| Project / workflow creation | Deleted. Uploading a certificate creates the case. There is no workflow to configure — there is one pipeline and it always runs. |
| Processing screen | Merged into `/case/{id}`. It is the same screen in a different state, which means the user never watches a page they will have to leave. |
| Results view | Same. |
| History | The case list on `/`. |
| Settings | One threshold, rendered inline next to the staleness finding that uses it. |
| Team management | Not applicable in v1 (single advocate, no login). |
| Onboarding | Replaced by a sample case. See below. |
| Help & docs | Replaced by the finding text itself, which states the rule in her language. |

**The merge that matters most:** *processing* and *results* are one page. The bands fill in as data
arrives, top-down, in the order she cares about. This is not a nicety — it removes a navigation
step, removes a "your job is ready" notification, removes the possibility of losing a job by closing
a tab, and turns 60 seconds of dead time into visible work. One decision, five problems deleted.

## The 30-second job

Above the fold, without a click:

> **▲ This certificate cannot support a 13-year search.**
> It covers 01-Jan-2018 → 31-Dec-2023. Entry 2 names five parent documents, the earliest from
> 2005. None fall inside this window.

Rendered as a **ruler**, not a badge. See the decision log.

**Revised during the build:** parent documents sit *above* the axis, the certificate's own
window sits *below* it, and both carry their years. The first version put them on one row, where
a parent-year label landed on top of the window band and the band's own years (2018–2023) were
never labelled at all — so the ruler could not be read without the sentence underneath it. Split
across the axis, the gap between the red cluster and the blue band is the argument, and it lands
before any prose is read.

## Onboarding under one minute

There is none. There is a **sample case** on `/`: two buttons that open pre-digitised certificates
from `output/` — one insufficient (Pollachi), one clean (Erumaipatti). Cost: two rows in the
database and a seed script. Value: a first-time user, and a judge, reaches the verdict in three
seconds without owning a Tamil EC; and it is the offline demo fallback (PRD §15.5) reusing the same
code path. One artifact, three jobs.

**The clean sample is not optional.** A detector that fires on 2 of 2 inputs looks like a rigged
demo. Shipping `ec4_erumaipatti` — where the product says *"three parent links resolve inside this
window. Verified."* — is what makes the warnings credible.

---

# Part 4 · The edge cases that would break the core experience

Only these. Everything else is deferred with a shrug.

| # | Case | The pattern — explicit |
|---|---|---|
| 1 | **Empty state (no cases)** | Not "No cases yet." The dropzone is the primary element, with the two sample buttons beneath it. Nothing else on the page. |
| 2 | **Loading (60–90 s)** | The case page renders immediately with the bands present and empty. A status line polls (`hx-trigger="every 2s"`). Header fields (SRO, village, search window) land first, from page 1 — **so the coverage ruler is drawn before the entries finish**, and the PR-year ticks land on it one at a time. The wait becomes the demo. |
| 3 | **Nil EC — no encumbrances found** | The most dangerous "empty state" in the product, because it looks like success. Never render "No findings." Render: *"This certificate reports no encumbrances between 01-Apr-2024 and 09-May-2024. That is a statement about five weeks."* The ruler makes the point visually without a word of alarm. |
| 4 | **Zero findings on a genuinely clean EC** | Show the confirmations band (`✓ 3 parent links resolve inside this window`). A product that only ever reports problems becomes noise she learns to skim. |
| 5 | **Not an EC** (the nil-EC portal screenshot in `ec_samples/`) | Refuse with the reason and the evidence: *"No registration-entry table found, and no declared entry count (`பதிவுகளின் எண்ணிக்கை`). This does not look like an Encumbrance Certificate."* Never hallucinate entries. The refusal is a scored moment, not a failure. |
| 6 | **Invalid input** (>50 MB, wrong type, password-protected PDF) | Reject at the dropzone before the upload, naming the specific reason and the limit. No server round trip. |
| 7 | **Partial results** — a chunk fails, pages unread | The gap is rendered **in the place where the evidence would have been**: a row in the entries table reading `pages 11–20 unread — retry`, not a toast. A toast is dismissible; an unread page must not be. |
| 8 | **A field could not be read** | The cell renders `—` and the `—` is a **button**. Clicking it opens the crop of the block it should have come from, with the field editable. Absence becomes a task, not a blank. |
| 9 | **Processing failure / retry** | The status line becomes `Failed at page 7 · [retry this page]`. Retry is per-chunk, not per-document — re-running 12 pages to fix 1 is a 60-second punishment for our bug. |
| 10 | **Rate limit (10/min)** | Honest queue position: `Queued — 2 jobs ahead, ~40 s.` Never a spinner pretending it is working. |
| 11 | **Tab closed / network drops mid-job** | The job is server-side and persisted; the page only polls. Reopening `/case/{id}` resumes the same view. Nothing lives in browser state, which is a property of HTMX we get for free. |
| 12 | **Correction saved** | No save button, therefore no unsaved state. Commit on Enter/blur, `hx-post` swaps the findings band, changed findings flash once. |

**The principle these share, stated once:**

> **Any absence of evidence is rendered in the place where the evidence would have been.**
> A missing date is a `—` in its cell. An unread page is a row in the table. An unexamined parent
> is an open circle in the chain. Nothing is ever silently omitted, and nothing that matters is
> ever put in dismissible chrome.

That principle is the entire error-handling design, and it costs nothing to implement because it is
mostly *not* building toasts, modals, and banners.

---

# Part 5 · Screen flow

```
        ┌──────────────────────────────────────────────────┐
        │  /   home                                        │
        │  purpose: start a case, or resume one            │
        │  primary: drop a PDF                             │
        │  secondary: open a sample · open an existing case│
        └───────────────────┬──────────────────────────────┘
                            │ POST /upload  → creates case, redirects
                            ▼
        ┌──────────────────────────────────────────────────┐
        │  /case/{id}   state: PROCESSING                  │
        │  purpose: keep her oriented while the pipeline   │
        │           runs; start answering before it ends   │
        │  primary: none — she waits, and watches it fill  │
        └───────────────────┬──────────────────────────────┘
                            │ polling fragment flips to READY
                            ▼
        ┌──────────────────────────────────────────────────┐
        │  /case/{id}   state: READY                       │
        │  purpose: the verdict, its evidence, the action  │
        │  primary: copy the order block                   │
        │  secondary: click a finding → crop               │
        │             correct a field → re-derive          │
        │             export report                        │
        └───────────────────┬──────────────────────────────┘
                            │
                            ▼  GET /report/{id}  (new tab, printable)
        ┌──────────────────────────────────────────────────┐
        │  the scrutiny report — Ravi's only surface        │
        └──────────────────────────────────────────────────┘
```

Fragments (not screens — HTMX swaps, no route change): `#status`, `#findings`, `#entries`,
`#evidence`, `#order`.

---

# Part 6 · Wireframes

## 6.1 `/` — home · empty (first run)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  TitleChain                                              rulebook v1.0       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│      ┌────────────────────────────────────────────────────────────────┐      │
│      │                                                                │      │
│      │        Drop an Encumbrance Certificate here                    │      │
│      │                    [ choose file ]                             │      │
│      │        PDF, JPEG or PNG · up to 50 MB                          │      │
│      │                                                                │      │
│      └────────────────────────────────────────────────────────────────┘      │
│                                                                              │
│      or open a sample:   [ Pollachi · 2018–23 ]   [ Erumaipatti · 1975–24 ]  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

*No hero copy, no feature grid, no sign-up.* The dropzone is the pitch. States: idle · dragover
(border solid) · rejected (`⚠ 62 MB — the limit is 50 MB` under the box, no modal) · uploading
(progress line, then redirect).

## 6.2 `/` — home · returning

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  TitleChain                                              rulebook v1.0       │
├──────────────────────────────────────────────────────────────────────────────┤
│      [ Drop an EC here · or choose file ]                                    │
│                                                                              │
│  YOUR CASES                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ ▲  Puliyampatti · S.No 95/2 +4      2 ECs   3 to resolve      2 d ago  │  │
│  │ ✓  Erumaipatti · S.No 128/1B        1 EC    chain verified    5 d ago  │  │
│  │ ●  Kotturpuram · S.No 11/1          2 ECs   1 to resolve      1 w ago  │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

Rows lead with **property identity and chain state**, never filenames. `ec2_pacollege.pdf` means
nothing to her; *Puliyampatti, survey 95/2* is how the file sits in her head. This row is also the
restart proof: it is rendered from SQLite, so its mere presence after `^C` and relaunch is the
Memory demonstration.

## 6.3 `/case/{id}` — PROCESSING

```
┌─ TitleChain ────────────────────────────── Pollachi SRO · Puliyampatti ──────┐
│  Reading page 3 of 12 · about 45 s remaining                        [cancel] │
├────────────────────────────────────────┬─────────────────────────────────────┤
│ COVERAGE                               │  SOURCE                             │
│                                        │                                     │
│  1961 ───────────────────────── 2024   │   p1 ▓  p2 ▓  p3 ░  p4 ·  p5 ·      │
│    ╷                    ▓▓▓▓▓▓▓▓▓▓▓    │   p6 ·  p7 ·  p8 ·  …               │
│   1961                   2018────2023  │                                     │
│   ↑ found in entry 2     ↑ this EC     │   ▓ read   ░ reading   · queued     │
│                                        │                                     │
│ FINDINGS                               │                                     │
│   ░░░░░░░░░░░  waiting for entries     │                                     │
│                                        │                                     │
│ ENTRIES                                │                                     │
│   2 of 2 declared · 1 typed so far     │                                     │
└────────────────────────────────────────┴─────────────────────────────────────┘
```

**The design decision inside this screen:** the ruler is drawn from the EC header, which lands with
page 1 — so the frame of the answer exists at ~8 seconds, and each PR year *lands on it* as entries
type. The user is not waiting for a result; she is watching the result assemble. Same code path as
READY, one Jinja conditional. Zero extra build cost, and it is the 0:10–0:25 beat of the 90-second
demo script.

## 6.4 `/case/{id}` — READY (the money screen)

```
┌─ TitleChain ────────────────────────────── Pollachi SRO · Puliyampatti ──────┐
│ ▲ This certificate cannot support a 13-year search.   [export] [copy order]  │ ← sticky
├────────────────────────────────────────┬─────────────────────────────────────┤
│ COVERAGE                               │  SOURCE                             │
│                                        │  ┌───────────────────────────────┐  │
│  2005  2007    2011        2019        │  │                               │  │
│   ╷     ╷       ╷            ╷         │  │  [ crop · page 2 block 000 ]  │  │
│  ─┴─────┴───────┴────────────┴──────   │  │                               │  │
│                        ▓▓▓▓▓▓▓▓▓▓▓     │  └───────────────────────────────┘  │
│                       2018      2023   │                                     │
│                                        │  page 2 · block 000 · conf 0.96     │
│  Entry 2 names five parent documents.  │  [ crop ] [ show on full page ]     │
│  The earliest is 1464/1961. None fall  │                                     │
│  inside 01-Jan-2018 → 31-Dec-2023.     │                                     │
│                                        │                                     │
│ NEXT ────────────────────────────────  │                                     │
│  Order EC                              │                                     │
│  Pollachi SRO · Puliyampatti           │                                     │
│  S.No 95/2, 100/3A, 113/1B, 116/A1,    │                                     │
│       116/B1                           │                                     │
│  01-Jan-1993 → 31-Dec-2017     [copy]  │                                     │
│                                        │                                     │
│ FINDINGS  1 resolve · 3 check · 1 note │                                     │
│  ▲ Window insufficient        entry 2 ▸│                                     │
│  ● Lease 2520/2019 was cancelled by   ▸│                                     │
│    8756/2020 — not a live encumbrance  │                                     │
│  ● 5 parent documents unexamined      ▸│                                     │
│  ● Entry 2 registration date missing  ▸│                                     │
│  ⚑ Certificate issued 2023 · 400 days ▸│                                     │
│  ✓ Cancellation confirmed in-document ▸│                                     │
│                                        │                                     │
│ CHAIN ───────────────────────────────  │                                     │
│  ○ 1464/1961   unexamined              │                                     │
│  ○ 4148/1981   unexamined              │                                     │
│  ● 2520/2019   Lease        ⊘cancelled │                                     │
│    └ ● 8756/2020  Cancellation Deed    │                                     │
│                                        │                                     │
│ ▸ ENTRIES (2)                collapsed │                                     │
└────────────────────────────────────────┴─────────────────────────────────────┘
```

**Band order is her question order**, not the pipeline's order: *can this answer my question →
what do I do about it → what did you find → how does it connect → show me the rows*. The pipeline
runs extract→graph→rules→render; the page runs the exact reverse. Entries are last and collapsed
because they are the **audit surface, not the reading surface** — she must be able to reach them,
and she must not have to start there.

## 6.5 The evidence pane — the only "app-like" component

```
crop view                             full-page view
┌──────────────────────────────┐      ┌──────────────────────────────┐
│ ┌──────────────────────────┐ │      │ ┌──────────────────────────┐ │
│ │ 8756/2020 ரத்து ஆவணம்   │ │      │ │  ░░░░░░░░░░░░░░░░░░░░░░  │ │
│ │ PR: 2520/2019  ...       │ │      │ │  ┏━━━━━━━━━━━━━━━━━━━━┓  │ │
│ └──────────────────────────┘ │      │ │  ┃ the same rectangle ┃  │ │
│                              │      │ │  ┗━━━━━━━━━━━━━━━━━━━━┛  │ │
│ page 2 · block 000 · 0.96    │      │ │  ░░░░░░░░░░░░░░░░░░░░░░  │ │
│ [crop] [show on full page]   │      │ └──────────────────────────┘ │
└──────────────────────────────┘      └──────────────────────────────┘
```

Two levels, and the second is not decoration: **a crop with no context is as unfalsifiable as no
crop at all.** She has to see that the rectangle sits inside entry 2 and not entry 3. One extra
endpoint (`/page/{n}?rect=…` renders the full raster with a drawn box); `crops.py` already has the
renderer and the coordinates.

## 6.6 Correction

```
before                                    after (one hx-post)
  date_registration  [ — ]                  date_registration  14-08-2020
     ↑ click                                FINDINGS  ✓ updated
  ┌───────────────────────────┐             ● Entry 2 registration date  ← removed
  │ [ 14-08-2020        ] ⏎   │             (band flashes once, 400 ms)
  │ crop shown at right       │
  └───────────────────────────┘
```

`hx-post="/correct" hx-target="#findings"`. The POST re-runs `derive()` server-side and swaps the
band. **This is not a UI trick standing in for the Memory proof — it is the Memory proof, rendered**
(STACK.md). ~20 minutes.

## 6.7 Refusal / failure

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  This does not look like an Encumbrance Certificate.                         │
│                                                                              │
│  We looked for: a registration-entry table  ✗ not found                      │
│                 a declared entry count (பதிவுகளின் எண்ணிக்கை)  ✗ not found  │
│                                                                              │
│  [ show what we read ]        [ upload a different file ]                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

Refusing with its reasons is on-message: the product's thesis is that it exposes what it cannot
establish. `[show what we read]` reveals the raw digitised markdown — never hide the evidence for
the refusal.

## 6.8 Mobile (≤768 px) — capture only

Bands stack; the evidence pane becomes a full-width block below the finding it was opened from.
The entries table is horizontally scrollable and stays collapsed. **No attempt is made to make
evidence review comfortable on a phone** — the phone's job is dropping a photographed certificate
in and seeing the verdict sentence. Everything else is desk work, and pretending otherwise costs
CSS time for a use case that does not exist.

---

# Part 7 · Decisions — what was excluded and why

**1 · Coverage as a ruler, not a badge or a score.**
Alternatives: a red/amber/green pill; a "sufficiency score" percentage; a sentence alone.
Rejected because she will not trust a machine verdict on a question she is liable for — she will
trust **arithmetic she can check in two seconds**. A ruler shows the certificate's window and the
parent years on one axis, and the conclusion becomes self-evident before she reads the sentence. A
score would invite the question *"how did you compute 62%?"* which we would have to answer with a
methodology page nobody reads. Cost: ~30 lines of CSS (absolutely positioned ticks on a flex bar).
Excluded: any numeric score, ever.

**2 · Evidence as a persistent pane, not a modal.**
Alternatives: lightbox modal; crop inlined under each finding; hover preview.
Modal rejected — she compares several findings against the page in sequence, and a modal forces
open/close/lose-place on every one. Inline rejected — the crops are wide table strips (2900×1230 px)
that turn the page into a tower of images. Hover rejected — no keyboard path, no touch, nothing
persists. Tradeoff: the pane costs half the viewport on ≥1280 px and forces the left column narrow.
Accepted, because the narrow column also forces the findings to stay short, which is a discipline
we want.

**3 · One page in two states, not a processing screen and a results screen.**
Deletes a navigation step, a "ready" notification, and the whole class of "user closed the tab
during the job" bugs. Extensibility: any future stage (multi-EC merge, sale-deed cross-check) adds
a band and inherits the streaming behaviour for free. Cost: one Jinja conditional.

**4 · Findings before entries; entries collapsed.**
The reflex is to lead with the extracted table because it is the impressive part. Rejected: leading
with the table restores her as the parser, which is exactly the job we removed. Novice impact: she
sees conclusions first, which is what she wants and what she can act on. Expert impact: one click
to the audit surface, and that click is the trust ritual — she will use it for the first several
cases and then stop. **Design for the click to become unnecessary, not for it to disappear.**

**5 · Confirmations rendered alongside findings.**
`derive()` currently emits problems only. It should also emit `✓` records for resolved PR edges and
confirmed cancellations — the data already exists (a resolved edge is `nodes.get(key)` returning
non-`None`). Cost: a handful of lines in `graph.py`. Value: a tool that only reports problems
becomes noise she skims. *The reassurance is what makes the warnings credible.* Flagged here because
it is a small **backend** ask arising from a frontend requirement — worth deciding before 11:30.

**6 · Severity words, not engineering words.**
`blocking / material / informational` are our vocabulary and mean nothing to her. Render as
**Resolve ▲ · Check ● · Note ⚑ · Verified ✓**. Colour is never the only carrier — always glyph +
word + colour, which also settles colour-blindness without a separate accessibility pass.

**7 · Corrections are append-only; there is no undo.**
An edit writes a `corrections` row and never mutates history. "Undo" in V2 is a *new* correction
that reverts, so the log stays honest. In a document that supports a legal opinion, a destructive
edit is a defect, not a convenience. Cost of getting this right on day one: zero. Cost of retrofitting
it: the entire audit story.

**8 · No icon library, no CDN, no fonts over the network.**
PRD §11: *Sarvam APIs only, no third-party services.* So the icon set is four typographic glyphs
(`▲ ● ⚑ ✓ ○ ⊘`) and CSS shapes. A demo that needs conference wifi to render its own buttons can fail
for reasons that have nothing to do with the product. Same reason `htmx.min.js` is vendored.

**9 · Tamil is content, English is chrome. No language toggle.**
Every `*_native` field renders verbatim in a Tamil font stack; the romanised form appears
*beside* it, never *instead of* it. No `text-transform`, no `letter-spacing` on Tamil. There is no
locale switcher because the app is not bilingual — the **data** is bilingual and the UI is one
language. This is the entire i18n design, and it is a CSS class.

---

# Part 8 · Build cost, mapped to the clock

| Piece | Where | Estimate |
|---|---|---|
| `base.html`, one stylesheet, two-pane grid | §14.2 | 25 min |
| Home: dropzone + case list | §14.2 | 15 min |
| Case page shell + polling status fragment | §14.2 | 20 min |
| Entries table (Jinja loop) | §14.2 | 10 min |
| Crop endpoint + evidence pane | §14.2 | 20 min |
| Findings band + confirmations | §14.2 | 15 min |
| **Coverage ruler** | §14.3 | 30 min |
| Order block + copy | §14.3 | 15 min |
| Inline correction + `hx-target` re-derive | §14.3 | 20 min |
| Chain as nested list | §14.3 | 15 min |
| Report template (printable) | §14.3 | 20 min |
| **Total** | | **≈3 h 25 m across both windows** |

That fits only because nothing above requires a build step, a state library, or a JSON contract.
If it slips, cut in STACK.md's order — staleness UI, then login, then chain visualisation, then the
two-seed pass. **Never cut:** the ruler, the crops, correction propagation, the order block. Those
four are one rubric parameter each.

---

# Part 9 · Critique

**Is anything here unnecessary?** Two candidates. The **chain band** is arguably redundant with the
findings band on a 2-entry certificate — it earns its place only at 15+ entries, and on demo inputs
it is nearly decorative. Keep it as a nested list (15 min), cut it before the ruler. The
**full-page-with-rectangle view** is a second endpoint for a trust concern that may be theoretical
— but it is the cheapest possible answer to *"how do I know that crop is from entry 2?"*, and that
question will be asked on stage.

**Could this ship in 2–4 weeks with a small team?** It has to ship in one afternoon with one person,
which is the harder version of the question, and the estimate above says yes with ~1 h of slack
inside a 4 h frontend budget. The reason it fits is that the design contains almost no *application*
— one persistent pane, one polling fragment, one POST that swaps a band. Everything else is a loop
over typed data. That is a deliberate consequence of Pydantic being the single schema source: the
template context is already the right shape.

**Does it validate the core hypothesis?** Yes, and this is the one thing to keep checking. The
hypothesis is not "we can read Tamil ECs" — that is already measured at 98.6%. It is *"a computed
coverage verdict plus a pre-filled order changes what an advocate does before signing."* The ruler
and the order block are the experiment; everything else is the apparatus that makes the experiment
believable. **If the frontend budget is under pressure, protect those two and let the rest degrade
visibly.**

**Honest weaknesses.**
- *First-time user:* nobody has seen a "coverage ruler" before. It needs its sentence directly
  beneath it, permanently — not as a tooltip. Mitigated in the wireframe; watch for it in testing.
- *Power user at month three:* no case-to-case comparison, no keyboard triage, no filtering at 40
  entries. All correctly deferred, all will be the first complaints.
- *Accessibility:* the entire evidence layer is images of text. A screen-reader user is wholly
  dependent on `alt`. Fix that for free — **set `alt` to the typed field values from that block**;
  we have them, which makes this the rare a11y win that falls out of the data model. The ruler gets
  `aria-hidden`, and its sentence is the accessible equivalent.
- *Conversion (PM view):* the exported report is the only artifact that leaves the building and
  reaches Ravi. It is currently designed as a document, not a channel. That is correct for v1 and is
  the obvious growth loop for v2.
- *Linear's view:* too much prose on screen; they would compress to one line and a keyboard-driven
  list. Rejected for this user — she is not a keyboard-native engineer, and the prose *is* the
  product's argument.
- *Notion's view:* the real deliverable is her opinion file, not our dashboard. Long-term, the case
  page should become a view onto an editable document she owns. That is the strongest v2 direction
  in this critique, and it is a re-founding, not a feature.

**First three improvements after initial feedback**, in the order I would expect to need them:

1. **Multi-EC merge into one chain (F14).** The moment the replacement certificate she ordered
   arrives, the product either extends the chain or is a one-shot novelty. This is the retention
   feature, and the order block manufactures demand for it.
2. **Show the rule's working.** If trust is the blocker, add a per-finding "why this fired" panel
   naming the rule, its inputs, and the rulebook version. Cheap, because the rulebook is already
   deterministic and versioned.
3. **Entries at scale** — sort, filter, jump-to-entry, and keyboard triage (`j/k/Enter/c`). This
   only becomes real on 30–40 entry certificates, which is precisely when the product stops being a
   demo and starts being a tool.

---

## The one-line summary

> Two routes, five bands, one pane. The frontend's only job is to make a computed sentence
> believable in under thirty seconds — and to hand her the next certificate to order.
