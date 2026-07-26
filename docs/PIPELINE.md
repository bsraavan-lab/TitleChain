# The Pipeline — Four Stages, One Boundary That Matters

**TitleChain · Sarvam Epoch Buildathon**
Companion to [PRD.md](PRD.md) §10 (AI architecture) and §11 (System architecture) — the PRD is
the spec, this is the explanation, [STACK.md](STACK.md) is what each stage is built out of, and
[ARCHITECTURE.md](ARCHITECTURE.md) is how the stages are wired together at runtime.
Traced against real output in [`output/`](output/).
Version 1.1 · 26 Jul 2026.

```
Tamil EC (pdf)
      │
      │  ① Sarvam Vision reads pixels → tables + text + where each block sits
      ▼
markdown tables + per-page JSON (bboxes, layout tags)
      │
      │  ② sarvam-105b transcribes rows → strict typed records
      ▼
entries[] — doc no, dates, nature, parties, PR numbers, remarks, source page+block
      │
      │  ③ derive()  ← OUR CODE, no model touches this
      │      · build the graph from PR pointers and remark cross-references
      │      · run the rules over it
      ▼
findings[] — ranked, each pointing back at the entries that caused it
      │
      │  ④ render
      ▼
one page: entries · chain · findings · source crops · order block
```

**The one-line reading of this diagram:**

> **Models read. Code decides.**
> Stages ① and ② are transcription. Stage ③ is judgment, and no model touches it.
> The arrow between ② and ③ is the most important line in the product.

---

## Stage ① — Pixels → structure

**In:** a scanned Tamil EC. No text layer. Could be 3 pages, could be 40.
**Out:** markdown tables (`document.md`) + one JSON file per page.
**Who does it:** Sarvam Document Digitization, `language=ta-IN`, `output_format=md`.

The certificate is a *picture of a grid*. Generic OCR flattens it into a word stream, and in a
table the grid **is** the meaning — `2520/2019` matters because it sits in the PR Number cell of
entry 2, not entry 3. So this stage has to preserve three things simultaneously: Tamil glyphs,
cell topology, and reading order.

**What we actually get back** — verified, not assumed. Every per-page JSON block carries:

```jsonc
{ "block_id": "…_2_block_000",
  "coordinates": { "x1": 308, "y1": 114, "x2": 3208, "y2": 1342 },
  "layout_tag": "table",
  "confidence": 0.962,
  "reading_order": 1,
  "text": "<table><tbody><tr><td rowspan=\"7\">2</td>…" }
```

That is the whole stage in one object. `coordinates` is what makes **source crops** possible in
stage ④ — every finding can point at the exact rectangle of the exact page it came from. This
was the biggest upgrade in the pre-event audit: bounding boxes and per-block confidence were
undocumented in the API docs and turned out to be *there*, which moved provenance from "stretch
goal" to "verified capability."

**Measured, on real certificates:** 69/70 ground-truth anchors intact across three inputs
(96% / 100% / 100%), including a deliberately degraded 120 dpi scan. ≈₹0.5/page; a 12-page
certificate ≈60 s ≈₹6.

**Constraints designed around:** 10 pages per job (so `ingest.py` chunks), 200 MB, 10 req/min,
async only.

**The failure this stage has, and why it shapes everything downstream:** the single miss was a
dropped date cell **inside a block reporting 0.96 confidence.** So Sarvam's `confidence` is
*layout-detection* confidence, not per-cell fidelity. A high number does not mean the cells are
all there. That fact is why the uncertainty net in stage ③ is ours and not the model's.

---

## Stage ② — Structure → typed records

**In:** the digitised table HTML/markdown.
**Out:** `entries[]` — one strict object per numbered EC entry.
**Who does it:** `sarvam-105b`, `temperature=0`, fixed seed, `response_format=json_schema`
strict. `sarvam-30b` is the fallback if 105B rate-limits.

The model is given exactly one job and told so explicitly: **transcriber, not analyst.**

- Copy values. Do not interpret, summarise, translate, or resolve contradictions.
- Tamil stays verbatim in `*_native` fields. Never translate a name.
- Unreadable or absent → `null`. **Never infer a plausible value.**
- Copy PR numbers and remark text exactly — *they are the graph edges.*

The `null` rule is load-bearing. A model that helpfully guesses a missing date destroys the only
signal that would have caught the stage-① cell drop. Honest nulls are what make the completeness
validator meaningful.

Every entry carries `source: {page_num, block_id}`, which is the thread back to a bounding box,
and therefore back to a crop. **Nothing in this system is ever asserted without a way back to
the pixel it came from.**

128K context holds a full certificate's table HTML, so entries are typed in document context
rather than page-by-page — which matters because sub-rows (consideration, market value, PR
number, remarks, schedules) attach to a parent entry that may have started on the previous page.

Temperature 0 plus a fixed seed means a re-run is reproducible — and therefore that a
*disagreement* between two runs is real signal, not noise. That is what the optional two-seed
pass (F13) exploits: fields that differ get shown side by side as **competing readings** against
the source crop, rather than one being silently chosen.

---

## Stage ③ — `derive()` · the boundary

**In:** `entries[]`.
**Out:** `findings[]`, ranked blocking → material → informational, each citing the entries that
caused it.
**Who does it:** us. Pure Python. Unit-tested. **No model call happens inside this function.**

This is the stage that separates the product from "upload the PDF to a chatbot," and it does two
things.

### 3a · Build the graph

The certificate is a table. The truth is a graph. Nodes are entries; edges come from two places:

| Edge type | Source | Meaning |
|---|---|---|
| **PR edge** | `pr_numbers[]` | *"this property came to me through document 1464/1961"* — an explicit parent pointer |
| **Cancel edge** | remarks cross-reference | entry X's remarks name document Y that extinguishes it |
| **Succession edge** | party-name clusters | claimant of entry *n* reappears as executant of entry *n+k* |

Party names are clustered first — via the transliteration API (`ta-IN→en-IN`) plus role-marker
normalisation (`(முத.)` / `(முக.)`, initials, honorifics) — because a chain break and a spelling
variant look identical until names are resolved.

Then each edge is **resolved or not**: does the pointed-at document exist as an entry inside this
certificate? That single boolean is the product.

> The PR Number has been printed on every EC for decades. The registry writes it faithfully and
> **never follows it.** Stage 3a is the traversal nobody performs.

### 3b · Run the rulebook

Ten deterministic rules over the assembled graph ([PRD §10.5](PRD.md)). Six of them fire on
documents we already hold — the demo is not staged, it's what the data does. The three that
carry the argument:

- **R1 `CANCELLED_INSTRUMENT`** — a deed and the deed cancelling it are separate entries, pages
  apart, linked only by a sentence in a remarks cell. In `ec2_pacollege`, entry 2 contains
  `8756/2020 · Cancellation Deed` against `PR 2520/2019` — read linearly, a dead lease looks
  like a live encumbrance.
- **R3 `WINDOW_INSUFFICIENT`** — any PR year earlier than the search-period start. The chain
  continues outside the certificate in hand. **This is the finding that cannot be produced by
  reading**, because it is a property of what the document *omits*.
- **R4 `DANGLING_PARENT`** — a PR pointer with no matching entry here. The parent document was
  never examined.

Plus the uncertainty net, which is deliberately **not** the model's confidence score:

1. block confidence (triages regions — useful, blind to cell loss),
2. **R9 schema completeness** — a required field is `null`; this is the signal that catches the
   real stage-① failure,
3. **R10 entry-count checksum** — the EC declares its own entry count
   (`பதிவுகளின் எண்ணிக்கை: 2`); ours must match. A free ground-truth check on whole-entry loss.

### Why this stage is code, and will stay code

Every judgment an advocate is *liable* for — is this encumbrance live, is the chain broken, is
this search sufficient — is executed by deterministic Python over typed data. Which means each
one is unit-testable, reproducible, explainable by citing the rule and its evidence, and
**versioned**: every finding records the rulebook version that produced it, so a stale finding is
distinguishable from a current one.

A generative model asked "is this title clear" will always answer. That is the problem. It cannot
say *"this certificate is structurally incapable of telling you"* — and that sentence is the
entire product. A confident wrong answer about an encumbrance is worse than no answer.

It is also where the moat sits ([PRD §4.5](PRD.md)): the rulebook encodes TN registration
practice — discharge semantics, cancellation grammar, role markers, subdivision conventions —
acquired from practitioners, not derivable from the document, and not something a competitor
gets by buying a better model.

---

## Stage ④ — Render

**In:** `entries[]`, the graph, `findings[]`.
**Out:** one page.

Four surfaces, in the order she needs them:

| Surface | What it answers |
|---|---|
| **Entries** | the typed table — she is no longer the parser |
| **Chain** | the graph, with resolved edges solid and dangling ones open |
| **Findings** | ranked, each linked to its evidence entries **and its source crop** |
| **Order block** | pre-filled replacement EC: SRO, village, every survey number, computed date range |

Two design rules govern this stage.

**Every finding must be falsifiable in one click.** A finding without its crop is an assertion;
a finding with its crop is evidence. The `coordinates` from stage ① make this a rectangle on a
page raster, not a citation she has to go find.

That claim is now mechanical rather than architectural. `pypdfium2` renders our own page at
**3509 × 2480** — byte-for-byte the raster geometry Sarvam digitised against — so a stage-①
bounding box lands on it with **no transform**, at `scale = 3509 / max(page.get_size())`.
Cropping `[308,114,3208,1342]` on page 2 of `ec2_pacollege.pdf` returns exactly the entry traced
below, cancellation sentence and all. The provenance thread from finding back to pixel is a
dictionary lookup and an `img.crop()`.

**Say what is verified, out loud.** `ec4_erumaipatti` has three PR edges that resolve cleanly
inside the window, and the product should say so. A tool that only ever reports problems becomes
noise she learns to skim; the clean confirmations are what make the warnings credible.

And the order block is not a nicety. The moment she learns her evidence is short, her next
thought is *"so what do I order?"* — which today means reassembling SRO, village, every survey
number and a date range by hand from the certificate in front of her. Pre-filling it is what
converts bad news into an action instead of a blown SLA.

---

## One entry, traced end to end

`ec2_pacollege.pdf`, page 2, entry 2 — real document, real output in [`output/`](output/).

| Stage | State |
|---|---|
| **input** | pixels — a Tamil table cell, no text layer |
| **①** | block `…_2_block_000`, `layout_tag: table`, `confidence: 0.962`, `coordinates: [308,114,3208,1342]`, HTML with `<td rowspan="7">2</td>` |
| **②** | `{sr_no: 2, doc_no: "8756/2020", nature: "Cancellation Deed", pr_numbers: [{doc_no:"2520", year:2019}], executants:[{name_native:"அருள்ஜோதி சாரிடபிள் டிரஸ்ட்", role_marker:"முத."}], market_value:"ரூ. 12,000/-", source:{page_num:2, block_id:"…block_000"}}` |
| **③** | cancel edge 8756/2020 → 2520/2019, **resolved inside this EC** → **R1 fires** (Material): the 2019 lease is extinguished, not a live encumbrance. PR years vs. search window → **R3** fires on this certificate's earlier parents. |
| **④** | finding card: *"Entry 2 cancels 2520/2019 (Lease). Not a live encumbrance."* + crop of `[308,114,3208,1342]` on page 2 |

The row that a tired reader at entry 40 misreads in the dangerous direction, resolved
deterministically, with the pixel that proves it.

---

## When it breaks

| Failure | Response | Never |
|---|---|---|
| Digitisation job fails | retry once → mark chunk `UNREAD`, show the raw page | silently drop pages |
| 105B returns unparseable JSON | strict schema makes it unlikely → retry → fall back to 30B → flag for manual typing | emit a partial entry as complete |
| Field unreadable | `null` → **R9** fires → advocate reviews against the crop | infer a plausible value |
| Rate limit (10/min) | queue with backoff, honest queue position in the UI | pretend it's processing |
| Total Sarvam outage in demo | pre-cached outputs for the three demo ECs | improvise |

The pattern is the same in every row: **degrade visibly.** An unread page marked `UNREAD` is
recoverable; an unread page silently omitted becomes a title opinion written on evidence that
was never there.

---

## What this pipeline does not do

- It cannot see what the registry never wrote. An unregistered claim or an omitted entry is
  invisible to every reader including us.
- It never opines. It evidences, and a human signs.
- Stage ③ is where the value is, and stage ③ is not AI. That is the design, not a limitation.
