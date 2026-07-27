# The Review Workspace — UX Redesign

**TitleChain · v2 of the frontend**
Supersedes [FRONTEND_MVP.md](FRONTEND_MVP.md) Parts 3–6 where they disagree. Everything in
FRONTEND_MVP Part 7 (the decision log) is either **kept**, or **overturned with a reason
stated below** — nothing is silently dropped.
Version 1.1 · 26 Jul 2026. **Built** — see Part 11 for what shipped, what changed
during the build, and what is still open.

> **What changes in one line.** The case page stops being a report you read top-to-bottom and
> becomes a **workspace you work down to zero** — a checklist with a completion state, a graph
> you can click into, and a hole-filling loop that turns "this certificate is insufficient"
> into "upload the one I just ordered."

---

# Part 0 · What exists today, and what each new surface needs

Half of what was requested is renderable from data already in the database. The other half
needs `derive()` to emit something it currently does not. Separating those two piles is the
first job, because the second pile is where all the risk lives.

| Requested surface | Data today | What is actually missing |
|---|---|---|
| Interactive ownership graph | ✅ `Edge`, `ChainNode` complete | Geometry (x/y layout) + SVG. Logic is done. |
| Timeline of transactions | ✅ `date_registration`, `doc_year` | Nothing. Pure render. Needs an "undated" lane for R9 nulls. |
| Search-window visualisation | ✅ `Coverage`, ruler already built | Multi-EC union. Today's ruler assumes **one** certificate. |
| Property lineage / dangling parents | ✅ `Edge.resolved_entry_id is None` | Per-parent findings. R4 currently emits **one aggregate** finding for all 5 dangling parents — unusable as actionable items. |
| Encumbrance status cards | ⚠️ `nature` only | **R2 `LIVE_ENCUMBRANCE` is not implemented.** Without it, "Active" is an unbacked legal assertion. |
| Confidence / review heatmap | ⚠️ `block_confidence` | Block confidence is **layout detection, not cell fidelity** — `_evidence.html` already says so in print. See §1.4: this becomes a *review-need* grid, not a confidence grid. |
| Survey-number evolution | ✅ `entries.survey_nos` | Nothing to render. But R6 `SURVEY_DRIFT` is not implemented, so the matrix is descriptive and must say so. |
| Rule execution dashboard | ❌ | **The big one.** Rules that don't fire emit nothing, so "passed" and "never ran" are indistinguishable. Needs `RuleRun` for all ten. §6.1. |
| Click node/finding → source crop | ✅ `/crop/{entry_id}.png`, `/pageview/…` | A page-level route (`/page/{ec}/{n}.png`) for "jump to page 7" where no entry anchors it. |
| Cost calculator | ❌ | No usage is recorded anywhere. `extract.py` throws away the `usage` block in every response. Needs an `api_calls` ledger. §6.5. |
| Mark reviewed / notes | ❌ | New `reviews` table **and** a stable finding identity — §6.2 is the crux of the whole redesign. |
| Missing-document upload & merge | ⚠️ schema allows it | `ec_documents.case_id` already permits N certificates per case, but `store.load_header()` returns `LIMIT 1` and `derive()` takes one header. §7. |

**Read that table as the plan's spine.** Rows with ✅ are an afternoon of Jinja and CSS. Rows
with ❌ are backend contracts that must be designed before a single template is touched, or the
UI will end up asserting things the data cannot support — which is the one failure mode this
product exists to prevent.

---

# Part 1 · Five places the request fights the existing design, and how each resolves

I am not going to quietly break decisions this project already made deliberately. Each tension
below is real; each resolution keeps the original principle intact.

## 1.1 "Title Chain Completeness: 82%" vs. *"Excluded: any numeric score, ever"*

FRONTEND_MVP Part 7 #1 rejected a sufficiency percentage on the grounds that it invites
*"how did you compute 82%?"* and can only be answered with a methodology page nobody reads.
That reasoning is still correct — **for an opinion score**. It does not apply to a **count
ratio**.

**Resolution.** The number ships, and it is arithmetic the advocate can verify in two seconds,
printed next to itself:

```
Chain completeness   9 of 11 parent documents examined              82%
                     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░
```

Three hard constraints on it, which are what keep it from becoming the thing that was rejected:

1. **No weights.** It is `examined ÷ named`. Nothing is multiplied by a coefficient anybody
   chose. §6.3 gives the full definition, and the tooltip *is* the numerator and denominator.
2. **It never renders alone.** It always sits beside the readiness gate line (§6.4), because
   82% next to two unexamined 2005 deeds must not read as "82% good." A case at 82% with one
   blocking finding is `Not ready to opine`, full stop.
3. **Readiness itself is never a percentage.** It is a gate list — pass/fail, first failure
   named. A file is signable or it is not; there is no 82% of a signature.

## 1.2 A dashboard vs. *"Dashboard / analytics — never. Nothing to aggregate."*

That exclusion was aimed at cross-case vanity metrics: how many ECs this month, average
processing time, a chart of nothing. Still deleted. **Never coming back.**

What was asked for is a *per-case completion state* — a worklist, not analytics. It aggregates
one case's open obligations, every one of which is clickable and actionable. That is the
opposite of a vanity metric, so it ships, and it ships **as the case header rail** (§2.2)
rather than as a separate screen, because a completion state you have to navigate to is a
completion state you forget.

## 1.3 The cost calculator serves the judge, not Meena — say so and place it accordingly

Meena does not care that her certificate cost ₹6.40 and 31 model calls. She is not paying
per case and it is not her decision. Pretending otherwise would put engineering telemetry in a
lawyer's primary workflow.

The panel is still worth building, for two real audiences: **the buildathon judge** (API-cost
awareness against the Sarvam rubric) and **whoever prices this product later** (per-case unit
economics are the whole margin question). So:

- It gets its own tab, positioned **last**, labelled `Processing`.
- The advocate-facing surfaces never mention money.
- **Estimated** shows before processing, from page count. **Actual** replaces it after. A cache
  hit shows `₹0 · cached (would have been ₹4.10)` — which is honest *and* is the most
  interesting number on the panel.
- **If the rate card is not configured, no rupee figure is rendered at all.** Units only:
  `14 pages · 31 model calls · 214k tokens`. Inventing a per-token rate to fill a card is
  exactly the class of fabrication this codebase refuses everywhere else. See §6.5.

## 1.4 "Confidence heatmap" must not become a per-cell confidence claim

`_evidence.html` already carries this warning in the UI: *a 0.96-confidence block dropped three
date cells in this very document.* Sarvam's number scores **whether a layout region was
detected**, not whether each cell inside it was transcribed correctly. Painting a heatmap from
it would tell the advocate that a green row is trustworthy, which is precisely the false
reassurance that motivated R9.

**Resolution: it becomes a review-need grid, and the inputs are ours, not the model's.** One
row per entry, one column per checked property, cell state deterministic:

| Column | Cell is flagged when |
|---|---|
| Fields read | any required field is `null` (R9) |
| Parents resolved | any PR pointer on this entry is dangling (R4) |
| Inside window | any parent year predates the covering window (R3) |
| Corrected | a `corrections` row exists → renders as a ✎, never as a warning |
| Reviewed | a `reviews` row in state `reviewed` exists |
| Layout conf. | shown as a **number in the last column**, unstyled, captioned |

Block confidence appears as a sortable figure, not as a colour. Colour is reserved for facts
our own code established.

## 1.5 Tabs hide things, and this product's rule is *"never hide uncertainty"*

Nine visualisations cannot stack as bands — that is a 6000px scroll tower where the verdict
scrolls off and the missing-document workflow is below the fold. Tabs are the right structure.
The principle is preserved by two rules, not by avoiding tabs:

1. **The rail is above the tabs and always visible** — verdict sentence, the completeness
   meter, the gate line, and the coverage ruler. Every tab inherits the 30-second answer.
2. **Every tab label carries its own live count.** `Review ⑤` · `Documents ②`. A tab can be
   closed but its contents can never be silent. Zero counts render as nothing, not as `0`.

**Kept unchanged from the original decision log:** ruler-not-badge (§2.2), evidence as a
persistent pane and never a modal, findings before entries with entries collapsed, confirmations
rendered alongside failures, severity as glyph + word + colour, append-only corrections, no CDN
/ no icon font / no webfont, Tamil verbatim with no transform.

---

# Part 2 · The new information architecture

## 2.1 Routes

Two full pages become three. Everything else is still a fragment.

| Method | Route | Returns | Note |
|---|---|---|---|
| `GET` | `/` | page | dropzone + case list (now with readiness state per case) |
| `POST` | `/upload` | 303 | unchanged |
| `POST` | `/sample/{key}` | 303 | unchanged |
| `GET` | `/case/{id}` | page | **the workspace.** `?tab=review\|chain\|documents\|entries\|processing` |
| `GET` | `/case/{id}/rail` | frag | polled while processing; carries verdict + meter + ruler |
| `GET` | `/case/{id}/tab/{name}` | frag | tab body; the only thing that swaps on tab change |
| `GET` | `/case/{id}/graph.svg` | frag | inline SVG (not an `<img>` — nodes must be clickable) |
| `POST` | `/case/{id}/documents` | frag | **the merge loop.** multipart + `request_key` |
| `POST` | `/review` | frag | `finding_key`, `state`, `note` → append-only |
| `GET` | `/finding/{key}/detail` | frag | expanded checklist row: inputs, evidence, working |
| `GET` | `/evidence/{entry_id}` | frag | unchanged |
| `GET` | `/crop/{entry_id}.png` | png | unchanged |
| `GET` | `/pageview/{entry_id}.png` | png | unchanged |
| `GET` | `/page/{ec_id}/{n}.png` | png | **new** — "jump to page 7" with no entry to anchor on |
| `GET` | `/case/{id}/cost` | frag | estimated → actual; polled during processing |
| `GET` | `/report/{id}` | page | unchanged shape, new sections (§5.3) |

Still one route change in the product for the core journey: `/` → `/case/{id}`. Tab switches are
`hx-get` + `hx-push-url`, so the URL is shareable and the back button works, but no page reloads.

## 2.2 The case workspace, structurally

```
┌─ topbar ─────────────────────────────────────────── Pollachi SRO · Puliyampatti ──┐
├───────────────────────────────────────────────────────────────────────────────────┤
│ ▲ This certificate cannot support a 13-year search.              [export] [⇩ PDF] │  ← rail
│                                                                                   │    (sticky,
│ Chain 1 of 6 parents examined  17%  ▓▓▓░░░░░░░░░░░░░░░░░  Coverage 6 of 34 yrs 18%│     polls
│ Not ready to opine — 5 parent documents unexamined, 28 years uncovered            │     while
│                                                                                   │     working)
│ ▾ 1993 ─┬───────────────────────────────────────────────────────┬─ 2026           │
│    ╷ ╷  ╷      ╷                              ▓▓▓▓▓▓▓             ← EC-A           │
│   2005 2007  2011                            2018  2023                           │
├───────────────────────────────────────────────────────────────────────────────────┤
│  Review ⑦ │ Chain │ Documents ② │ Entries │ Processing                            │  ← tabs
├──────────────────────────────────────────┬────────────────────────────────────────┤
│                                          │                                        │
│           tab body (fragment)            │        SOURCE (persistent pane)        │
│                                          │        survives every tab switch       │
│                                          │                                        │
└──────────────────────────────────────────┴────────────────────────────────────────┘
```

Three structural facts:

**The rail replaces the old `.verdict` strip** and absorbs the coverage ruler. It is the same
element in PROCESSING and READY states — the merge that FRONTEND_MVP got right is preserved and
extended. During processing the meters render as skeletons with honest labels
(`counting parents…`), never as `0%`.

**The evidence pane is outside the tab fragment**, so clicking a graph node on `Chain`, then
switching to `Review`, leaves the crop on screen. That is what makes the pane worth half the
viewport.

**The ruler is collapsible (`<details open>`) and nothing else is.** On a 900px laptop the rail
must be able to shrink to two lines.

## 2.3 The five tabs, and the question each answers

| Tab | Her question | Primary action |
|---|---|---|
| **Review** | "What do I have to check before I sign?" | Work the checklist to zero |
| **Chain** | "How do these documents connect?" | Click a node → its crop; click a hole → order it |
| **Documents** | "What am I missing, and can I add it now?" | Upload the EC that fills a gap |
| **Entries** | "Is the extraction right?" | Correct a cell → everything re-derives |
| **Processing** | "What did this cost / how did it run?" | Nothing. It is a record. |

`Review` is the default tab, replacing today's coverage-first band order. Coverage did not lose
its primacy — it moved *up*, into the always-visible rail.

---

# Part 3 · Screen layouts

## 3.1 `/` — home (returning user)

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│  TitleChain                                                       rulebook v1.0   │
├───────────────────────────────────────────────────────────────────────────────────┤
│        [ Drop an Encumbrance Certificate here · or choose file ]                   │
│        or open a sample:  [ Pollachi · 2018–23 ]  [ Uthukuli · 2024–25 ]           │
│                                                                                   │
│  YOUR CASES                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ ▲ Puliyampatti · S.No 95/2 +4      1 EC   17% chain   5 to resolve   2d ago │  │
│  │ ✓ Erumaipatti · S.No 128/1B        2 ECs  100% chain  ready to opine  5d ago│  │
│  │ ● Kotturpuram · S.No 11/1          2 ECs  71% chain   3 in review    1w ago │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────────┘
```

Changes from today: the EC count (a case is now plural by design), the completeness figure, and
the readiness state. Rows still lead with property identity, never filenames. This row is still
the restart proof.

## 3.2 `Review` — the checklist (the new money screen)

```
│  Review ⑦ │ Chain │ Documents ② │ Entries │ Processing                            │
├──────────────────────────────────────────┬────────────────────────────────────────┤
│  ❌ 1 failed   ⚠ 6 need review   ✅ 3 passed   — 1 not applicable                 │
│  [ all ] [ open ] [ reviewed ]                              3 of 7 reviewed       │
│                                                                                   │
│  ❌  R3  Search window insufficient                              ▸  [ review ]    │
│      5 parent documents predate 01-Jan-2018. Earliest 4451/2005.                  │
│      ── expanded ─────────────────────────────────────────────────────────────    │
│      │ WHAT THIS RULE CHECKED                                                 │   │
│      │   search_period_start   01-Jan-2018      ← EC-A header, p1  [source]   │   │
│      │   parent years found    2005, 2005, 2007, 2007, 2011                   │   │
│      │   condition             any parent year < 2018        → 5 matched      │   │
│      │   rulebook              R3 · v1.0                                      │   │
│      │ EVIDENCE                                                               │   │
│      │   entry 1 · p1 · block …4652c_1_003    [crop] [full page] [go to p1]   │   │
│      │ WHAT CLOSES THIS                                                       │   │
│      │   An EC for Pollachi / Puliyampatti, 01-Jan-1993 → 31-Dec-2017         │   │
│      │   [ copy order text ]        [ upload it now → Documents ]             │   │
│      │ REVIEW                                                                 │   │
│      │   ( ) reviewed  ( ) accepted risk  ( ) needs a second EC               │   │
│      │   [ note ................................................. ] [ save ] │   │
│      └────────────────────────────────────────────────────────────────────────┘   │
│                                                                                   │
│  ⚠  R4  Parent 4451/2005 not present in any certificate on this case   ▸ [review] │
│  ⚠  R4  Parent 4453/2005 not present in any certificate on this case   ▸ [review] │
│  ⚠  R9  Entry 2 · date of registration could not be read     ✎ fixed   ▸          │
│  ⚠  R1  8756/2020 cancels 2520/2019 — not a live encumbrance            ▸ [review]│
│  ⚠  R8  Certificate issued 19-Jun-2023 — 1133 days ago                  ▸ [review]│
│  ✅  R10 Entry count matches the certificate's own declaration (2)       ▸         │
│  ✅  R4  Parent link 2520/2019 resolves inside this certificate          ▸         │
│  ✅  R1  Cancellation of 2520/2019 confirmed in-document by 8756/2020    ▸         │
│  —   R2  Live encumbrance — not evaluated: no mortgage, charge or lien   ▸         │
│         found among 2 entries.                                                    │
└───────────────────────────────────────────────────────────────────────────────────┘
```

Four things this layout is doing on purpose:

**Every one of the ten rules appears, always.** `— not applicable` is a first-class row with its
reason spelled out. A checklist that shows 9 items on one case and 4 on another teaches the
advocate that absence means "fine", which is the exact inversion the refusal screen already
refuses to make (*"never claim a check it did not make"*). This is that principle applied to the
rulebook.

**R4 and R9 split into one row per subject.** Today R4 emits `"5 parent documents are named
but not present: 4451/2005, 4453/2005, …"` — a single row you cannot mark reviewed
individually, cannot resolve individually, and cannot attribute an upload to. One dangling
parent = one checklist item = one document request. Same for R9: one missing field, one row,
one correction that clears it.

**"What this rule checked" is the trust surface.** FRONTEND_MVP's own critique lists *"show the
rule's working"* as improvement #2 after launch. It is cheap here because the rulebook is
already pure and deterministic — the rule knows its inputs; it just never reported them. Each
input carries its own `[source]` link back to the pixel it was read from.

**"What closes this" is on the finding, not only in a separate band.** The order block is no
longer one panel at the top of the page for one rule (R3); every finding that a document would
resolve carries its own closing action. The old `_order.html` becomes a component reused in
three places.

## 3.3 `Chain` — graph, timeline, survey drift

```
│  OWNERSHIP GRAPH                          [ graph ] [ timeline ] [ survey nos ]   │
│                                                                                   │
│   1961      1981        2005  2007  2011        2019      2020                    │
│  ───┼─────────┼───────────┼─────┼─────┼───────────┼─────────┼──────────────────    │
│     ○         ○           ○ ○   ○ ○   ○           ■━━━━━━━━━⊘                     │
│  1464/61   4148/81    4451 4453 4581 4582 4755  2520/2019   8756/2020             │
│     ╲         ╲          ╲   ╲    ╲    ╲   ╲        │ cancels  ╱                  │
│      ╲_________╲__________╲___╲____╲____╲___╲_______┘         ╱                   │
│                        (parent-of edges)                     ╱                    │
│                                                   ●━━━━━━━━━━                     │
│                                                                                   │
│   ● examined   ○ named but not in any certificate   ⊘ cancelled   ■ lease         │
│   ▭ transfer  ◆ mortgage/charge  ⊙ cancellation   ✎ corrected                    │
│                                                                                   │
│   ○ open circles are the holes in this title. Click one to order the document      │
│     that fills it.                                                                │
│                                                                                   │
│   ▸ read as a nested list  (accessible equivalent — the SVG is aria-hidden)        │
```

- **Server-rendered inline SVG.** No D3, no CDN, no client-side layout — the constraint from
  FRONTEND_MVP #8 holds. Layout is a pure function in a new `app/layout.py`, returning a
  `GraphLayout` of `{node_id, x, y, glyph, state}` and edge paths. Deterministic, unit-testable,
  and it does not touch `derive()`'s existing contract.
- **X is the year, always.** Not a force-directed blob. The year axis is the whole reason the
  gap is visible, and it makes the graph and the ruler in the rail read as the same picture.
- **Y is lane assignment**, greedy by first-free-lane, ties broken by `doc_no` so the drawing is
  byte-identical across runs.
- **Click a node** → `hx-get /evidence/{entry_id}` into the pane. **Click an open circle** →
  jumps to `Documents` with that request card focused. The hole is the call to action.
- **Accessible equivalent is the existing nested list**, kept verbatim, in a `<details>`. Same
  pattern the ruler already uses (`aria-hidden` + a sentence). Nothing regresses.

**Timeline sub-view** — one row per registered transaction, chronological, with a separate
`UNDATED` lane at the bottom for entries whose `date_registration` is null. Those entries are
*not* placed at a guessed position; a guessed date on a timeline is an invented fact.

```
│  2019 ─ 12-Mar  ■ 2520/2019  Lease deed      Trust → College        ⊘ cancelled   │
│  2020 ─ ——      ⊙ 8756/2020  Cancellation    Trust → College        ✎ date fixed  │
│  UNDATED (1)    the certificate's date cells for this entry could not be read      │
```

**Survey-numbers sub-view** — a presence matrix, rows = survey numbers, columns = entries in
chronological order. Explicitly captioned: *"Descriptive. R6 SURVEY_DRIFT is not implemented in
rulebook v1.0, so no drift verdict is asserted here."*

```
│              2520/2019   8756/2020                                                │
│   95/2           ●           ●                                                    │
│   100/3A         ●           ●                                                    │
│   116/B1         ●           ●                                                    │
│   116/B3         ·           ·      ← in the header's search list, in no entry     │
```

That last row is the interesting one and it falls out of the data for free.

## 3.4 `Documents` — the missing-document workflow

This is the tab that changes what the product *is*, so it gets the most detail.

```
│  Review ⑦ │ Chain │ Documents ② │ Entries │ Processing                            │
├───────────────────────────────────────────────────────────────────────────────────┤
│  ON THIS CASE                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ EC-A  ec2_pacollege.pdf   Pollachi · Puliyampatti                           │  │
│  │       01-Jan-2018 → 18-Jun-2023 · 2 entries · 2 pages · issued 19-Jun-2023   │  │
│  │       ▓▓▓▓▓▓▓ covered                                        [ pages ▾ ]     │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                   │
│  STILL REQUIRED — 2 items                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ ① Encumbrance Certificate · Pollachi SRO · Puliyampatti                     │  │
│  │    01-Jan-1993 → 31-Dec-2017                                                │  │
│  │    S.No 95/2, 100/3A, 101/3, 113/1B, 116/A1, 116/B3                         │  │
│  │    Why: R3 — 5 parent documents (2005–2011) fall outside every window on     │  │
│  │         this case.        Closes: R3, and R4 for 4451/2005 +4  [see rules]   │  │
│  │                                                                             │  │
│  │    [ copy order text ]     ┌───────────────────────────────────────────┐    │  │
│  │                            │  drop the certificate here when it arrives │    │  │
│  │                            └───────────────────────────────────────────┘    │  │
│  ├─────────────────────────────────────────────────────────────────────────────┤  │
│  │ ② Certified copy · document 4451/2005                                       │  │
│  │    Named as a parent by entry 1. Not present in any certificate on this case.│  │
│  │    Alternative: the EC in ① also covers 2005 and would examine it.           │  │
│  │    Why: R4 · Closes: R4 for 4451/2005          [ copy ]  [ drop file ]       │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                   │
│  RESOLVED BY LATER UPLOADS                                                        │
│    (empty until the first merge — then it is the most persuasive panel in the app) │
└───────────────────────────────────────────────────────────────────────────────────┘
```

**Requests are derived, never stored.** A `DocumentRequest` is a pure function of the current
findings, exactly like `OrderBlock` is today. Nothing to keep in sync, nothing to garbage-collect
when a correction makes a request unnecessary. The only thing persisted is `request_key` on the
uploaded `ec_documents` row — so the app can say *which hole this certificate was fetched to
fill*, and check whether it actually filled it.

**Two request kinds, and the distinction is legally real.** A dangling parent is a *document*
(you order a certified copy from the SRO); a window gap is a *date range* (you order another EC).
Where one EC would resolve several parents, the card says so, and the parent cards point at it
rather than duplicating the order. Never tell an advocate to order six things when one covers
five of them.

## 3.5 `Entries` and `Processing`

`Entries` is today's `_entries.html`, kept nearly as-is — the audit surface, the correctable
cells, the append-only correction log, the unread-page rows. Three additions: it groups by
certificate once a case has more than one; a doc_no present in two certificates renders a
`corroborated ×2` marker (with both crops reachable); and the review-need grid from §1.4 sits
above the table as a compact overview.

`Processing`:

```
│  PROCESSING COST                                     estimated → actual           │
│                                                                                   │
│                              estimated        actual      Δ                       │
│  Document Intelligence       2 pages          2 pages     —      cached  ₹0       │
│  Entry typing (105B)         ~14k tok         31.2k tok   +123%          ₹—       │
│    ├ 105b                    4 calls          9 calls                             │
│    └ 30b (fallback)          0 calls          2 calls     ← truncation ladder      │
│  Header typing (105B)        ~3k tok          2.9k tok    −3%            ₹—       │
│  Transliteration             not run          not run     —              ₹0       │
│                              ─────────────────────────────────────────────        │
│  Total                                                                  ₹—        │
│  Wall clock                  ~50 s            41 s                                │
│  Model calls                 4                11        (retries included)         │
│                                                                                   │
│  Rate card not configured — rupee figures are withheld rather than estimated.      │
│  Add rates from dashboard.sarvam.ai → Billing to config/rates.yml.                 │
│                                                                                   │
│  ▸ per-call ledger (11 rows)                                                      │
```

`11 model calls for 4 blocks` is the most honest number in the product and I want it visible:
it is the truncation ladder in `extract.py` doing its job, and it is the real per-case cost
driver. A cost panel that hid retries would be marketing.

## 3.6 Mobile (≤ 900px)

Unchanged in philosophy: the phone is for capture. The rail stacks and the ruler collapses
closed by default. Tabs become a horizontally scrollable strip. The evidence pane moves below
the tab body. `Chain`'s SVG becomes horizontally scrollable at a fixed height, and the nested
list opens by default instead of the graph. No attempt is made to make graph review comfortable
on a phone.

---

# Part 4 · Interaction flows

## 4.1 The core loop, extended

```
/ ──drop EC──► /case/{id}?tab=review
                   │  rail fills in as the pipeline runs (unchanged)
                   ├─ expand a rule ─────► inputs + evidence + working
                   │        └─ [source] ──► crop in the pane (unchanged, 1 click)
                   ├─ mark reviewed ─────► counter drops, tab badge drops
                   ├─ correct a cell ────► derive() re-runs ► rail + review + chain all swap
                   ├─ click a hole in ───► Documents, that request focused
                   │  the graph
                   └─ upload the EC ─────► THE MERGE LOOP (§4.2)
```

## 4.2 The merge loop — the flow that matters most

```
 advocate drops EC-B on request card ①
        │
        ▼
 POST /case/{id}/documents  (file + request_key="R3:gap=1993-2017")
        │
        ├─ accept_upload()            same 50MB / type gate as today
        ├─ INSERT ec_documents        second row on the SAME case, fulfils_request_key set
        ├─ background pipeline.run()  identical code path — digitise, type, persist
        │       rail shows "Reading EC-B, page 3 of 9" while EC-A's findings stay on screen
        │       ← nothing is cleared. The case does not go blank. This is the whole point.
        ▼
 derive_case(all ECs on the case)     graph rebuilt over doc_no across both certificates
        │
        ├─ corrections survive        automatic: they live on entry rows, which are never deleted
        ├─ review state survives      because finding_key is subject-scoped, not id-scoped (§6.2)
        ▼
 INSERT derivations(finding_keys)     append-only snapshot of what the rulebook said, when
        │
        ▼
 diff(previous, current) ────────────► the resolution report
        │
        ▼
 ┌────────────────────────────────────────────────────────────────────────────┐
 │ ✓ EC-B merged · Pollachi · 01-Jan-1993 → 31-Dec-2017 · 9 entries · 9 pages │
 │                                                                            │
 │   RESOLVED (4)                                                             │
 │     R3  the 1993–2017 gap is now covered                                   │
 │     R4  4451/2005 is present in EC-B, entry 3   [source]                   │
 │     R4  4453/2005 is present in EC-B, entry 4   [source]                   │
 │     R4  4581/2007 is present in EC-B, entry 6   [source]                   │
 │   NEW (2)                                                                  │
 │     R4  1464/1961 named by EC-B entry 3, not present     [ order it ]      │
 │     R9  EC-B entry 7 · nature could not be read          [ fix it ]        │
 │   UNCHANGED (5)   your 3 reviewed items stayed reviewed                    │
 │                                                                            │
 │   Chain completeness  1 of 6 → 5 of 11   17% ▓░░ → 45% ▓▓▓▓░░              │
 └────────────────────────────────────────────────────────────────────────────┘
```

**Progressive, not restarted** — the promise in the request — is delivered by three specific
mechanics, not by wording: findings stay on screen during the second ingest; review state is
keyed on the subject rather than a row id; and the derivation log makes "what did this document
fix?" a diff rather than a guess. `NEW (2)` is not a failure of the workflow. Finding a 1961
parent behind a 2005 one is what a title chain *does*, and showing the count going 17% → 45% →
next hole is the loop that makes this a tool rather than a one-shot novelty.

## 4.3 Correction, re-derivation, and what flashes

Today a correction swaps `#derived`. Now four regions can change: rail (meters), review
(the R9 row clears), chain (a node gains a date), entries (the cell). HTMX out-of-band swaps
handle it in one response:

```
POST /correct  →  200 with:
   the cell fragment                       (targeted)
   <div id="rail"          hx-swap-oob="true">   …
   <div id="tab-body"      hx-swap-oob="true">   …   (only the active tab)
```

The single one-shot flash stays on the region that changed meaning — not on all four, which
would read as a page reload and lose the causal link between her edit and its consequence.

## 4.4 Review state transitions

```
open ──[ reviewed ]──────► reviewed          counts down, row collapses, stays visible
     ├─[ accepted risk ]─► accepted          stays counted separately; never silently closed
     └─[ needs a doc ]───► awaiting document  links to its Documents card
```

Append-only, like corrections. `reviews` rows are never updated or deleted; the current state is
the latest row for that `finding_key`, and the history is shown in the report. An advocate who
marks something reviewed, then unmarks it, has that sequence in the record — in a file
supporting a legal opinion, a destructive edit is a defect. Same rule as `corrections`, same
reason.

---

# Part 5 · Component hierarchy

## 5.1 Template tree

```
base.html
├── home.html
│   ├── _dropzone.html                    (reused by Documents request cards)
│   └── _case_list.html                   + readiness column
└── case.html                             shell: rail + tabs + panes
    ├── _rail.html                        ← polls while processing
    │   ├── _verdict.html                 the sentence + export
    │   ├── _meters.html                  completeness · coverage · gate line
    │   └── _ruler.html                   TODAY'S _coverage.html, multi-EC
    │       └── _ruler_band.html          one band per certificate
    ├── _tabs.html                        labels + live counts
    ├── tab_review.html
    │   ├── _rule_summary.html            ❌ ⚠ ✅ — counts + filter
    │   └── _rule_row.html                collapsed row (one per RuleRun)
    │       └── _rule_detail.html         hx-get on expand
    │           ├── _rule_inputs.html     "what this rule checked"
    │           ├── _evidence_links.html  crop · full page · go to page
    │           ├── _closing_action.html  ← was _order.html
    │           └── _review_form.html     state radios + note
    ├── tab_chain.html
    │   ├── _graph_svg.html               inline SVG from GraphLayout
    │   ├── _chain_list.html              TODAY'S _chain.html (a11y equivalent)
    │   ├── _timeline.html                + UNDATED lane
    │   └── _survey_matrix.html
    ├── tab_documents.html
    │   ├── _ec_card.html                 one per certificate on the case
    │   ├── _request_card.html            one per DocumentRequest + _dropzone
    │   └── _merge_result.html            the §4.2 resolution report
    ├── tab_entries.html
    │   ├── _review_grid.html             the §1.4 grid
    │   ├── _entries.html                 TODAY'S, grouped by EC
    │   │   ├── _cell.html                unchanged
    │   │   └── _edit_field.html          unchanged
    │   └── _corrections.html             extracted from _entries.html
    ├── tab_processing.html
    │   ├── _cost_table.html              estimated → actual
    │   └── _call_ledger.html             collapsed
    ├── _evidence.html                    unchanged
    ├── _refusal.html                     unchanged
    └── report.html                       + rules table, review log, documents list
```

Reused today, unchanged: `_cell.html`, `_edit_field.html`, `_evidence.html`, `_refusal.html`.
Renamed and extended: `_coverage.html` → `_ruler.html`, `_order.html` → `_closing_action.html`,
`_findings.html` → `_rule_row.html`. `_derived.html` and `_body.html` disappear — the rail plus
addressable tabs replace them.

## 5.2 CSS additions

One stylesheet, still hand-written, still no framework. New sections: `meters`, `tabs`,
`checklist`, `graph` (SVG classes only — geometry comes from Python), `matrix`, `request-card`,
`cost-table`. Existing custom properties are sufficient; the only new tokens are two neutral
fills for the graph's unexamined nodes and the matrix's absent cells. **No new colours with
meaning** — the four severity colours already carry all the semantics, and every new state gets
glyph + word + colour like everything else.

## 5.3 The report gains three sections

The exported report is Ravi's entire UI and the only artifact that leaves the building, so
everything above must survive the print stylesheet:

- **Rules executed** — all ten, with outcome and, for `not applicable` / `not evaluable`, the
  reason. This is the single most valuable addition to the report: it converts *"I checked what
  I could"* from a claim into a table.
- **Review log** — who marked what reviewed, when, and their notes. Append-only history.
- **Documents on this case, and documents still required** — with the order text, so the report
  is also the shopping list.

The graph prints as the nested list, not the SVG. A 2000px-wide SVG on A4 is unreadable, and the
list is the same information.

---

# Part 6 · The deterministic contracts

These are the pieces that must exist before templates are written. All of them are pure
functions over recorded state — `derive()` stays free of model calls, forever.

## 6.1 `RuleRun` — every rule reports, including the ones that did not fire

```python
RuleOutcome = Literal["FAIL", "REVIEW", "PASS", "NOT_APPLICABLE", "NOT_EVALUABLE"]

class RuleRun(BaseModel):
    rule_id: str                    # R1 … R10
    subject_key: str                # "" for case-level rules; see §6.2
    outcome: RuleOutcome
    message: str                    # her language, not ours
    reason: Optional[str]           # REQUIRED when NOT_APPLICABLE / NOT_EVALUABLE
    inputs: list[RuleInput]         # what the rule read → "show your working"
    evidence_entry_ids: list[int]
    pages: list[tuple[int, int]]    # (ec_id, page_num) — for "jump to page"
    closes_with: Optional[DocumentRequest]
    rulebook_version: str

class RuleInput(BaseModel):
    label: str                      # "search_period_start"
    value: str                      # "01-Jan-2018"
    source_entry_id: Optional[int]  # where the pixel is
```

The five outcomes map to the requested three, plus the two the request did not ask for and the
product cannot go without:

| UI | Outcomes | Meaning |
|---|---|---|
| ❌ Failed | `FAIL` | fired at blocking severity — do not sign across this |
| ⚠ Needs review | `REVIEW`, `NOT_EVALUABLE` | fired at material/informational, **or** could not run for lack of inputs. Sub-labelled, never merged. |
| ✅ Passed | `PASS` | ran, condition not met, and that is good news |
| — Not applicable | `NOT_APPLICABLE` | ran; the case has no inputs of the kind it checks |

`reason` being mandatory on the last two outcomes is enforced by a validator, not by discipline.
`NOT_EVALUABLE` rendered as ⚠ rather than as its own glyph is deliberate: "we could not check
this" is an unresolved item for the advocate, which is exactly what ⚠ means.

`Finding` is not deleted — `RuleRun` with a failing outcome *is* the finding, and
`DerivedView.findings` remains as a computed property over the runs so the existing report
template and all 20 tests keep passing unchanged.

## 6.2 `finding_key` — the crux

Review notes must survive re-derivation and must survive a second certificate arriving. Finding
objects do not survive either (derived state is disposable, by design). So review state keys on
the **subject** of the finding — the thing in the world the rule is about:

| Rule | `finding_key` | Why that subject |
|---|---|---|
| R1 | `R1:cancelled=2520/2019` | the cancelled instrument |
| R2 | `R2:enc=1234/2011` | the encumbrance |
| R3 | `R3:gap=1993-2017` | the uncovered span; a different span is a different obligation |
| R4 | `R4:parent=4451/2005` | **the dangling parent — this is what an upload resolves** |
| R5 | `R5:break=8756/2020` | the transfer whose predecessor is missing |
| R6 | `R6:survey=116/B3` | the drifting survey number |
| R7 | `R7:extent=8756/2020` | the entry whose extent changed |
| R8 | `R8:stale=ec:3` | the certificate |
| R9 | `R9:ec:3/sr:2/date_registration` | **`ec_id` + the certificate's own `sr_no`**, never the db id |
| R10 | `R10:count=ec:3` | the certificate |

R9's key deserves the note: keying on `doc_no` would break precisely when `doc_no` is the field
that could not be read. `ec_id` + `sr_no` is the certificate's own numbering, stable under every
correction.

Keys are computed by the rule that emits them, in `derive.py`, and unit-tested for stability:
*correct a field, re-derive, and every unrelated key must be byte-identical.*

## 6.3 Completeness — the arithmetic, in full

```python
class Completeness(BaseModel):
    links_named: int        # distinct parent doc_nos named anywhere on the case
    links_examined: int     # of those, present as an entry on this case
    span_required: tuple[int, int]
    years_required: int
    years_covered: int      # union of EC windows ∩ required span
    review_total: int       # RuleRuns in FAIL | REVIEW | NOT_EVALUABLE
    review_done: int
    corrections: int
    unread_pages: int

    chain_pct  = links_examined / links_named           # 100% + "no parents named" if 0
    coverage_pct = years_covered / years_required
```

`span_required = (min(earliest_parent_year, today.year - 13), today.year)` — 13 years is the TN
search convention; if the certificate names a parent older than that, the obligation reaches
back to it. Both terms are printed next to the meter.

On the Pollachi sample this evaluates to `1 of 6 links = 17%` and `6 of 34 years = 18%`. On
Erumaipatti (the clean sample) it is 100% / 100%. That contrast is real, not staged — and it is
why the clean sample stays in the demo.

## 6.4 Readiness — gates, not a score

```
G1  no rule outcome is FAIL
G2  links_examined == links_named
G3  years_covered == years_required
G4  review_done == review_total
G5  unread_pages == 0
```

All pass → `Ready to opine`. Otherwise the label names the **first** unmet gate in that order,
with its count: `Not ready to opine — 5 parent documents unexamined, 28 years uncovered`. The
gate list is the readiness indicator. There is no 82% of a signature.

## 6.5 Cost — a ledger, and the honesty rule

```python
class ApiCall(BaseModel):     # one row per real HTTP request, recorded fact
    case_id: int; ec_id: Optional[int]
    stage: Literal["digitise", "header", "entries", "transliterate"]
    model: Optional[str]                       # sarvam-105b | sarvam-30b | DI | mayura
    ladder_rung: Optional[str]                 # "105b/low+s1" — retries are visible
    pages: int; tokens_in: int; tokens_out: int; chars: int
    cached: bool; ms: int; created_at: str
```

`extract.py::_post` already receives `usage` in every response body and discards it — capturing
it is a few lines. `digitise.py` knows its page count and its cache-hit status. That is the whole
ledger.

**Rates live in `config/rates.yml`, with a `source:` and a `retrieved:` date.** The Sarvam
pricing surface reports billing *units* per model (DI per page, 105B/30B per 1M tokens, mayura
per character) but says exact per-unit rates depend on the plan — so:

> If `rates.yml` is absent or a rate is unset, the panel renders **units only** and says the
> rate card is not configured. No rupee figure is ever computed from a number I guessed.

**Estimated** comes from `pages` (known at upload) × medians over this machine's own `api_calls`
history, falling back to the three staged samples, and is labelled with which basis it used.
**Actual** replaces it in place. Cache hits show `₹0 · cached` alongside what a cold run would
have cost, because that comparison is the strongest thing on the panel.

## 6.6 `DocumentRequest`

```python
class DocumentRequest(BaseModel):
    key: str                          # == the finding_key that generated it
    kind: Literal["EC_FOR_RANGE", "CERTIFIED_COPY"]
    sro: Optional[str]; village: Optional[str]; survey_nos: list[str]
    date_from: Optional[str]; date_to: Optional[str]
    doc_no: Optional[str]                 # CERTIFIED_COPY only
    because: str                          # "R3 — 5 parents fall outside every window"
    closes: list[str]                     # finding_keys this would resolve
    superseded_by: Optional[str]          # a parent request that already covers this
    as_text: str                          # the copyable order block
```

`superseded_by` is what stops the app telling her to order six documents when one EC covers five
of them. Derived, never stored — today's `build_order()` generalised from one rule to all of
them.

## 6.7 Encumbrance cards need R2, or they must say they are not evaluated

`Active / Cancelled / Released` cannot be rendered from `nature` alone. Labelling a 2011
mortgage "Active" because nothing said otherwise is an unbacked legal assertion about a live
charge — wrong in the dangerous direction, which is the same reasoning `build_graph()` already
uses to require an explicit cancellation keyword before it will call a remark a cancellation.

Two honest options:

- **Implement R2** — a nature taxonomy (mortgage · simple mortgage · deposit of title deeds ·
  charge · lien · release · discharge) plus discharge matching by party and survey. Then the
  cards are real, with a fourth status: `Not evaluated · nature not recognised`.
- **Ship the cards descriptive** — group entries by nature with an explicit caption that no
  live/discharged verdict is asserted in rulebook v1.0.

**Implement it.** `ec_samples/README.md` already identifies the firing case: `ec4_erumaipatti`
entry 1 is a 1985 `சுவாதீனமில்லாத அடைமானம்` (mortgage without possession) to a cooperative
society, with **no discharge or release anywhere in a window that runs to 2024**. That is a live
encumbrance on the face of the record, in a real certificate we hold — the corpus notes it as
R2's first real firing, and PRD §10.5 currently lists no real data for R2. So the rule is ~40
lines of pure function with a genuine positive case *and* a genuine negative control (the same
certificate's 3→2, 4→3, 5→3 edges must not fire R4). If R2 is cut, the cards must be cut with
it — a status card whose status is always "not evaluated" is worse than no card.

---

# Part 7 · Backend changes this requires

Stated plainly, because none of the UI above is reachable without them.

**Schema (all additive, `schema.sql` stays idempotent):**

```sql
ALTER ec_documents  ADD label TEXT;                  -- "EC-A"
                    ADD uploaded_at TEXT;
                    ADD fulfils_request_key TEXT;    -- attribution for the merge loop
                    ADD status TEXT;                 -- per-certificate processing state

CREATE TABLE reviews (                               -- append-only, like corrections
  id, case_id, finding_key, state, note, actor, created_at);

CREATE TABLE derivations (                           -- append-only log of what the rulebook said
  id, case_id, at, rulebook_version, finding_keys TEXT);   -- JSON array

CREATE TABLE api_calls (                             -- the cost ledger, recorded fact
  id, case_id, ec_id, stage, model, ladder_rung,
  pages, tokens_in, tokens_out, chars, cached, ms, created_at);
```

`derivations` deserves a note against the architecture's own rule (*derived state is
disposable*). It does not violate it: the table stores no derived state for reading, it stores
the **fact that at time T the rulebook said X**. That is a recorded event, and it is the only
way "which findings did this upload resolve?" can be answered by a diff rather than a guess.
Findings themselves are still rebuilt from scratch every derivation.

**Module changes:**

| File | Change |
|---|---|
| `derive.py` | rules return `RuleRun` (not just failures); R4 and R9 split per subject; `subject_key` per rule; new `derive_case(list[ECDoc])` merging by `doc_no`; `Coverage` grows to N bands; `build_order` generalises to `build_requests` |
| `models.py` | `RuleRun`, `RuleInput`, `RuleOutcome`, `Completeness`, `Readiness`, `DocumentRequest`, `GraphLayout`, `TimelineRow`, `SurveyMatrix`, `CostLine`, `ApiCall`. `DerivedView.findings` becomes a property over runs → templates and tests unchanged |
| `layout.py` | **new.** Pure graph geometry → `GraphLayout`. Deterministic, unit-tested |
| `cost.py` | **new.** Ledger reads, rate-card loading, estimate/actual |
| `store.py` | `load_case()` returns all ECs; `reviews` read/write; `api_calls` writes; corrections unchanged |
| `extract.py` | record `usage` and the ladder rung per call. Otherwise untouched |
| `digitise.py` | record pages + cache-hit per job |
| `pipeline.py` | accept an existing `case_id` with a second certificate; per-EC status |
| `main.py` | the routes in §2.1 |

**Tests.** The existing 20 pass unchanged (that is a constraint on the refactor, not a hope —
`DerivedView.findings` keeps its shape). New tests, minimum: outcome for all ten rules on both
samples; `finding_key` stability across a correction; review state surviving a merge; the merge
diff on `ec5`; `Completeness` arithmetic on both samples; graph layout determinism.

## 7.1 Multi-EC is not only a feature — it fixes a live correctness bug

`ec5_adyar_chennai_bundle.pdf` is **two certificates for the same property in one PDF**: pages
1–3 are an EC for `11-Sep-2023 → 04-Apr-2024`, and pages 4–5 are a **Nil EC** for
`01-Apr-2024 → 09-May-2024`. The corpus README calls it the strongest demo input we have, and
the reason matters here.

Today's pipeline maps **one uploaded file to one `ec_documents` row**, and `extract.py`'s header
pass reads *page 1 only*. Feed it `ec5` and it produces a single header carrying the first
certificate's window, then attaches **both certificates' entries to it**. The Nil EC's pages are
silently absorbed under a window that does not describe them — the coverage ruler draws one band
where there are two, and R3 evaluates parent years against the wrong span. That is the product's
own central failure mode (*a certificate that is right about what it contains and silent about
what it omits*) reproduced inside our own data model.

The multi-EC work in phase 4 is what fixes it, and the fix is small once `derive_case()` exists:
detect a second header block mid-document (a page carrying its own `தேடுதல் காலம்` /
`Number of Entries` header table), split the pages into two `ec_documents` rows on one case, and
let the merge path do the rest. Then `ec5` renders as it actually is — two windows on the rail,
a five-week Nil EC visibly covering five weeks of a chain that runs to 1961, and roughly a dozen
dangling parents as individual, orderable checklist items.

Two consequences for the plan:

- **The merge demo needs no synthetic certificate.** `ec5` is the material, and `ec4` (clean
  chain, live 1985 mortgage) remains the negative control.
- **Detecting the split is deterministic and ours** — the same regex family `extract.py`
  already uses for `declared_count()` and `is_entry_table()`. No model call decides where one
  certificate ends and the next begins.

---

# Part 8 · Build order, and where to stop

Phases are independently shippable. Each one leaves the app working.

| # | Phase | Contains | Est. |
|---|---|---|---|
| **1** | **The contract** | `RuleRun` + all ten rules reporting + `finding_key` + R4/R9 split + tests | 2.0 h |
| **2** | **Rail + tabs** | shell, meters, `Completeness`, readiness gates, multi-EC ruler, tab routing, OOB swaps | 1.5 h |
| **3** | **Review checklist** | rows, expand, inputs/working, evidence links, `reviews` table, notes, counts | 2.0 h |
| **4** | **Missing documents** | `DocumentRequest`, request cards, upload-into-case, `derive_case` merge, `derivations` diff, resolution report | 2.5 h |
| **4b** | **Bundle split** | detect a second certificate header mid-PDF → two `ec_documents` on one case (§7.1) | 0.75 h |
| **5** | **Chain visuals** | `layout.py`, SVG graph, click-through, timeline, survey matrix | 2.0 h |
| **6** | **Cost** | ledger capture, `rates.yml`, estimated/actual, per-call table | 1.0 h |
| **7** | **R2 + encumbrance cards** | nature taxonomy, discharge matching, cards | 1.0 h |
| **8** | **Report + review grid** | rules table, review log, documents section, print pass | 1.0 h |

**Cut order if the clock runs out**, hardest to easiest to lose: 7 → 6 → the survey matrix and
timeline in 5 → the graph in 5 (the nested list already carries the information; this was
already cut once for the same reason) → 8.

**Never cut:** phase 1, phase 4, and phase 4b. Phase 1 is what makes every other surface honest.
Phase 4 is the only phase that changes what the product *is* — and it is the one the request
calls critical, correctly. 4b is not a demo nicety; it closes a correctness bug that exists in
`main` today (§7.1). Phases 1–4b alone are a coherent, shippable redesign; 5–8 are the
visualisation layer on top.

Recommended stopping point if you want one: **finish 1–4b, then 5's graph, and treat 6–8 as
stretch.**

---

# Part 9 · Honest weaknesses in this proposal

**The rail is 140px of permanent chrome.** On a 13" laptop that is real estate taken from the
checklist. Mitigated by the collapsible ruler, but if it feels heavy in use, the ruler should
default closed on `Review` and open on `Documents`, where it is the argument.

**Tabs cost orientation on first use.** A first-time user will not know that `Documents` is
where the fix lives. Mitigated by making the closing action on each finding link *into* that
tab, so the checklist teaches the navigation. Watch for it in testing.

**`NOT_EVALUABLE` may swamp the checklist on a thin certificate.** A nil EC with two entries
could show four rules as "could not be checked", which reads as brokenness rather than honesty.
If that happens, group them under one collapsed row — *"4 rules could not be checked on this
certificate"* — expanded by default only when a blocking rule is among them. Do not hide them.

**The graph is the weakest earner, again.** It was cut in v1 for being nearly decorative on a
2-entry certificate, and that is still true. It earns its place only on a merged multi-EC case —
which is precisely what phase 4 creates, so its value is contingent on phase 4 landing first.
Build it after, not before.

**Cost figures depend on a rate card I cannot supply.** Design it so the panel is useful with
units only; the rupee column is an enhancement, not the feature.

**The review workflow assumes one advocate.** No auth, no reviewer identity beyond `'meena'`, no
concurrent-edit handling. Correct for v1; the `actor` column is already there for when it isn't.

---

# Part 10 · Decisions needed before phase 1

1. **Scope to build now** — all eight phases, or 1–4 plus the graph, or 1–4 only?
2. **Rate card** — do you have real per-unit Sarvam rates to put in `rates.yml`, or should the
   cost panel ship units-only with the rupee column withheld?
3. **R2** — implement it (encumbrance cards become real), or ship the cards descriptive with an
   explicit "no verdict asserted" caption, or cut the cards?
4. **How the merge demo runs** — see §7.1. `ec5_adyar_chennai_bundle.pdf` is already two
   certificates for one property in one file, so the material exists. The question is whether
   phase 4 also handles the **bundle split** (one upload → two `ec_documents`) or only the
   **second upload** path (drop file → merge). The split is the stronger demo and fixes a real
   correctness bug; it is also ~45 min more work.

---

## The one-line summary

> One rail, five tabs, one pane. Every rule reports whether it ran, every hole in the chain is a
> button that orders the document that fills it, and the case has a completion state you can
> work down to zero.


---

# Part 11 · As built

Phases 1 → 8 are implemented. 61 tests pass (`.venv/bin/pytest -q`). What follows is
only the places where the build disagreed with the plan, plus the two things it
cannot verify.

## What changed during the build, and why

**The ruler left the sticky header.** The plan put verdict, meters, gate line and
ruler in one pinned rail. Built that way, the rail was 236px of permanent chrome
with the ruler open, and it fought the sticky tab strip for `top: 0`. The rail and
the tabs now stick together as one compact unit (`.case-head`) and the ruler is a
collapsible strip directly beneath them — visible on every tab, but it scrolls. The
pinned part is the 30-second answer; the argument for it scrolls.

**The verdict is no longer always coverage.** Coverage-as-verdict produced a
contradiction the moment a second certificate closed the window gap: the rail read
*"every parent document falls inside a window it covers"* while the gate line below
said one blocking finding remained. `DerivedView.verdict` now leads with the
worst-ranked FAIL and falls back to coverage. Regression-tested.

**One test changed, not zero.** The plan claimed all 20 existing tests would pass
untouched. Nineteen did. `test_r4_dangling_parents_are_counted_not_dropped`
asserted the old aggregate message (*"5 parent documents are named but not
present: …"*), which the per-subject split deliberately removes. It now asserts five
separate findings with five stable keys, which is a better test of the same
property.

**R2 found a real bug in its own taxonomy.** "Release deed" contains the substring
"lease", so the first unanchored pattern set classified a mortgage *release* as a
*lease* — which is precisely how a discharged charge gets reported as still open.
Latin terms are now `\b`-anchored, Tamil terms are not (no word boundary to anchor
against, and the terms are long enough not to collide). Guarded by
`test_release_is_a_discharge_and_not_a_lease`.

**Document requests re-shape themselves as the case fills in.** Not designed, but
correct: while R3 is failing, one EC request supersedes all five certified-copy
requests. Once a merged certificate closes R3, the EC request disappears and the
five parents surface as individual errands again — because `superseded_by` is
derived from the live findings, not stored.

## Verified against real data

| Claim | Evidence |
|---|---|
| Every rule reports on every derivation | 10 of 10 rule ids present on three different inputs, including an empty case |
| A check that did not run says why | validator-enforced; asserted end to end |
| R4 splits per parent | five keys, `R4:parent=4451/2005` … |
| Keys survive a correction | correcting entry 2's date changes exactly two keys and leaves the rest byte-identical |
| R2 fires on a real mortgage | `ec4` entry 1 — the 1985 `சுவாதீனமில்லாத அடைமானம்` with no release through 2024 → FAIL, and `ec3`'s English "Mortgage without possession deed" → FAIL |
| The merge loop resolves findings | uploading `ec4` onto a `ec2` case resolved R3, surfaced 2 new findings, carried 12 unchanged; chain 17% → 38%, coverage 27% → 96% |
| Multi-EC ruler | two bands, EC-A 2018–2023 and EC-B 1975–2024 |
| Cost ledger | cached digitisation recorded as 6 pages, 1 call, ₹0; rupee columns withheld with the rate card unset |
| Graph layout is deterministic | identical `model_dump()` across runs; x ordered by year |

## The two things this build cannot verify

**The bundle split has no end-to-end run.** `certificate_ranges()` and
`slice_pages()` are implemented and unit-tested on synthetic pages in the exact
`ec5` shape (headers on pages 1 and 4 → `[(1,3), (4,5)]`). But **`ec5` is not
digitised** — there is no cached Document Intelligence output for it, and it is the
one file in the corpus with no text layer, so proving the split on the real document
means spending real API calls on 5 pages. That is a spend decision, not a code
decision. Everything downstream of the split is already exercised by the upload
path, which produces the same two-certificate case.

**No rupee figure has ever been rendered.** By design — `config/rates.yml` ships
empty and the panel withholds money until it is filled in. The pricing arithmetic
is implemented but has only been exercised with the card unset, i.e. on the path
that prints units.

## Still open

- **R5, R6, R7** remain unimplemented and now say so, out loud, in the checklist and
  in the report. R6's descriptive survey matrix is built; the verdict is not.
- **Print pass is inherited, not tuned.** The report prints and the graph prints as
  the nested list, but the new tables have had no A4 proofing.
- **Mobile is untuned below 760px.** Rules exist; no device pass was done.
- The evidence pane still has no keyboard path to the graph's SVG nodes — the
  parallel button list (`_graph_nodes.html`) is the accessible route, and it is
  what a keyboard or screen-reader user gets.
