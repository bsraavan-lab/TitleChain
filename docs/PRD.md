# TitleChain — Product Requirements Document

**Sarvam Epoch Buildathon · Document Intelligence track**
Version 1.0 · 26 Jul 2026 · Owner: bsraavan@gmail.com
Status: **Idea locked. Hardest dependency empirically de-risked (see §0.2).**

---

# 0. Pre-PRD: Rubric Validation

This section exists because the rubric — not a generic product standard — is the objective function. Everything downstream is designed against it.

## 0.1 Declared job (fixed, do not drift)

> **Given a Tamil Nadu Encumbrance Certificate, produce a title-scrutiny-ready chain report: the property's ownership/encumbrance graph, with every live encumbrance, chain break, and search-window gap identified deterministically and traceable to its source region on the page.**

## 0.2 Evidence already in hand (run 26 Jul 2026, pre-event validation)

| Input | Provenance | Pages | Anchors intact |
|---|---|---|---|
| EC-A | Pollachi SRO EC, public AICTE filing | 3 | **23/24 = 96%** |
| EC-A′ | same, re-rasterised 120 dpi grayscale JPEG | 3 | **24/24 = 100%** |
| EC-B | Pollachi SRO EC, public RERA filing | 6 | **22/22 = 100%** |
| **Total** | real documents, not hand-authored | 12 | **69/70 = 98.6%** |

Ground truth was read directly from the source PDFs by a human/model reading the original, *not* from pipeline output. Checker: `check_ec_integrity.py`. Runtime 12 pages ≈ 60 s. Cost ≈ ₹6.

**Two findings that change the design:**

1. **The undocumented per-page JSON contains provenance.** Every block carries `block_id`, `coordinates{x1,y1,x2,y2}`, `layout_tag`, `confidence`, `reading_order`, and `text` (tables as HTML). Bounding-box provenance and confidence-ranked review move from "stretch goal" to **verified Explicit capability**. Image space is 3509×2480 (300 dpi).

   **Verified further (26 Jul, second pass):** `pypdfium2` renders `ec2_pacollege.pdf` page 2 at exactly 3509×2480 — the same raster geometry Sarvam digitised — so block coordinates land on our own page render with **no transform**, at `scale = 3509 / max(page.get_size())`. Cropping `[308,114,3208,1342]` returns precisely the traced entry-2 block (`8756/2020`, Cancellation Deed, `PR 2520/2019`, and the cancellation sentence in remarks). F6 is therefore ~15 lines with no system dependencies, and "every finding is falsifiable in one click" is mechanical rather than hoped-for.

2. **`confidence` is layout confidence, not transcription confidence.** The single lost anchor (entry 2's three dates) was dropped from a table block scoring **0.96**. Thresholding on the API's confidence would *not* have caught it. Therefore the uncertainty net must be **our own schema-completeness validator** (§10.6). This is proven necessary by real data, not assumed — and it is a moat component, not a vendor feature.

Observed confidence distribution across 48 blocks / 12 pages:

| layout_tag | n | min | median | max |
|---|---|---|---|---|
| table | 15 | 0.64 | **0.95** | 0.98 |
| paragraph | 14 | 0.29 | 0.65 | 0.86 |
| page-number | 11 | 0.26 | 0.34 | 0.70 |
| header | 3 | 0.38 | 0.41 | 0.46 |
| footer | 3 | 0.28 | 0.38 | 0.60 |
| footnote | 2 | 0.75 | 0.80 | 0.80 |

Tables — the only blocks we care about — are reliably high-confidence. Decorative regions are low. The signal is discriminative for *region triage*, useless for *cell omission*.

## 0.3 Honest level assessment

| Parameter | Today | Target | Why not L5 yet | Concrete fix before/during build |
|---|---|---|---|---|
| **Job-to-be-done** | L3 | **L5** | Stage 1 verified on 3 inputs; stage 2 (HTML→typed rows) **untested**. L5 needs 85%+ on ≥3 repeated cases, no builder rescue. | Run stage-2 dry run tonight (§14.0). Source 3 more ECs from different SROs. Demo on 3 unseen ECs live. |
| **Memory & Context** | L2 | **L4→L5** | Nothing persists yet. L5 demands current task + case history + business rules across sessions/handoffs, with corrections propagating, staleness visible, permissions intact. | SQLite case store from hour 2. Correction table that re-derives the graph. Rulebook versioning. EC staleness clock. Advocate-scoped case ownership. |
| **Creativity** | L4 | **L5** | The graph reframing + PR-pointer edges + window-insufficiency detection are several reinforcing choices. L5 needs the "I didn't know you could solve it that way" beat. | Lead the demo with **search-window insufficiency → pre-filled next EC order**. That is the non-obvious unlock. |
| **Impact** | L3 | **L4→L5** | Numbers are currently order-of-magnitude assumptions, not defended baselines. Rubric: market size alone is not impact. | Build the arithmetic explicitly with stated assumptions and sensitivity (§4). Anchor on one defensible number: hours per scrutiny. |
| **Delight** | L2 | **L4→L5** | Not built. The friction moment is "did I miss something, and is this EC even sufficient?" | Answer it: the insufficiency verdict + exact next action (SRO, village, survey, date range) pre-filled. Stay with the user past the immediate result. |
| **Document Intelligence** | **L4** | **L5** | Real Tamil ECs with dense multi-page tables pass at 98.6%, and uncertain regions are inspectable against source. L5 wants the hardest material + competing readings visible. | Add: true phone-photo input class (§14.0), structural-gap flags rendered as competing/missing readings with source crops. |

**Weakest links, ranked:** (1) stage-2 extraction unverified, (2) both real ECs are from the *same SRO* (Pollachi) — formatting luck is untested, (3) the "degraded scan" was synthetic re-rasterisation, not a real phone photo with skew/shadow/glare, (4) Memory is entirely unbuilt, (5) Impact baseline is assumption-heavy.

## 0.4 Sarvam capability selection

**Chosen: Document Intelligence.** Scored deeply, and it is the only capability the declared job actually requires.

*Why it is the strongest choice.* The job's hard input is a dense, multi-page, Tamil-script government table where names, deed types, survey numbers and previous-document pointers must survive **as structured rows with source coordinates**. That is precisely what Sarvam Vision returns and precisely where frontier VLMs degrade. Swap-out test: replace Sarvam with a GPT/Gemini-class VLM and the Tamil table flattens, reading order scrambles, and — decisively — you lose the per-block coordinates that make every finding traceable. The degradation is severe and visible on the hardest case. This is a genuine structural advantage, not a preference.

*Why Voice is unnecessary and harmful.* This is a desk workflow. A lawyer reviewing title does not want to talk; they want a document they can attach to an opinion. Adding voice would (a) score zero — additional capabilities add no points, (b) land us on the most crowded ground at the event (the Sarvam cookbook ships collections, government-scheme, tutor and loan-advisory voice agents; reproducing that shape is an explicit creativity handicap), and (c) consume hours on turn-taking and barge-in quality that the rubric would score under a parameter we did not declare.

*Why Dubbing is unnecessary and impossible.* There is no dubbing API — it is a Sarvam Studio dashboard workflow. It cannot be a programmatic dependency, and nothing about title scrutiny involves media adaptation.

*Additional capabilities used, and only because the product needs them:* `sarvam-105b` (row typing into strict JSON — the alternative is brittle regex over Tamil HTML) and the Transliteration API (cross-script party-name clustering — genuinely load-bearing for chain-break detection). Neither is decorative. No TTS, no STT, no dubbing.

---

# 1. Executive Summary

**One sentence.** TitleChain turns a Tamil Nadu Encumbrance Certificate into a verified ownership-and-encumbrance graph, flagging every live encumbrance, chain break, and — critically — whether the certificate even covers enough history to support the title search it was ordered for.

**Why it should exist.** Every property sale and home loan in Tamil Nadu requires a title search over 13–30 years. The EC is the primary instrument for that search: a dense Tamil table, one row per registered transaction. Today an advocate reads it row by row with a highlighter and assembles the ownership chain in their head or on paper. Three failure modes recur, and all three are mechanical rather than intellectual: a cancelled instrument is read as a live encumbrance (or worse, a live one is missed); a parent-document pointer leads outside the certificate's search window and nobody notices the chain is unverified; and a name spelled two ways across entries hides a break in the chain. The cost of each miss is borne by the buyer, years later, in litigation.

**Why now.** The EC already contains explicit machine-readable chain edges — the *PR Number* (முந்தைய ஆவண எண், "previous document number") field — that nobody assembles into a graph. Until now nothing could read the Tamil table reliably enough to trust those pointers. As of this month, Sarvam Vision does, at 98.6% field fidelity on real certificates, with coordinates for every block. The raw material for the graph has existed for years; the reader arrived this year.

**Why this is an ideal Buildathon project.** The hardest dependency is already empirically de-risked on real, publicly obtained documents. The demo input is genuinely hard (dense Tamil government table) and genuinely real. The output is a usable artifact a professional would attach to a file. The winning insight — an EC can be *insufficient for its own purpose*, and we can prove it and pre-fill the fix — is invisible from the idea card and unlikely to occur to another team.

---

# 2. Idea Lock

*Fixed for the duration of the build. Changes require deleting a feature, not adding one.*

| Field | Locked answer |
|---|---|
| **One-sentence product** | Upload a TN Encumbrance Certificate; get the property's ownership chain as a verified graph — every link traceable to its source region, every live encumbrance, chain break and search-window gap flagged deterministically. |
| **Target user** | Property advocate / bank-empanelled lawyer performing pre-sale or pre-mortgage title scrutiny in Tamil Nadu. |
| **Job completed** | A title-scrutiny-ready chain report, produced end to end from a raw EC, with findings a lawyer can sign off on or contest against the source. |
| **Hard input** | Multi-page Tamil-script government EC with dense nested tables, mixed Tamil/English, bilingual column headers, Tamil party names, and cross-referencing remarks. Scanned or digital. |
| **Final artifact / state change** | A persisted **case file** containing: typed transaction entries, the ownership graph, a ranked findings list, and an exportable scrutiny report. Corrections persist and re-derive the graph. |
| **Sarvam capability (declared, scored)** | **Document Intelligence** |
| **Exact Sarvam APIs** | `document_intelligence` create/upload/start/status/download (Sarvam Vision, `output_format=md`, `language=ta-IN`) · `chat.completions` `sarvam-105b` with `response_format=json_schema` strict · `text.transliterate` `ta-IN→en-IN` |
| **Additional capability justification** | 105B: converts digitised Tamil table HTML into typed rows — regex over Tamil HTML is brittle and unmaintainable. Transliteration: normalises party names across scripts so chain-break detection works. Nothing else. |
| **Supported language / input subset** | Tamil + English TN ECs, post-1987 computerised registration era, ≤10 pages per job (chunked beyond). |
| **Team advantage** | We already ran the kill test on real certificates before the event and know exactly what the API returns — including that its confidence score cannot catch cell omissions, which most teams will discover too late or never. |
| **Creativity thesis** | An EC is not a document to read — it is a graph to reconstruct. The PR Number field is an explicit parent pointer that nobody follows; following it reveals that most ECs **cannot support the title search they were ordered for**, and we can compute the exact replacement certificate to order. |
| **Delight thesis** | The lawyer's real fear is not "what does this say" but "what did I miss." We answer with a deterministic, evidence-cited verdict — including honest admissions of what this certificate *cannot* tell them — and a pre-filled next action instead of a shrug. |
| **Demo proof** | On a real, unmodified EC: a Lease deed that looks like a live encumbrance is shown to have been cancelled by a later deed; simultaneously, five parent documents from 2005–2011 are shown to fall outside the certificate's 2018–2023 window, so the chain is unverified — with the exact earlier EC to order, pre-filled. |
| **Non-goals** | Handwritten pre-1987 records · Modi/Kaithi/Grantha scripts · other states · voice/TTS/dubbing · patta/chitta/FMB integration · legal opinions (we produce evidence and flags; the advocate signs) · TNREGINET scraping/automation |

---

# 3. Problem Statement

## 3.1 The current workflow

1. Buyer/bank instructs an advocate to conduct title scrutiny, statutorily over 13 years, in practice often 30.
2. The advocate obtains an EC from TNREGINET or the sub-registrar's office for a stated search period and survey number(s).
3. The EC arrives as a PDF: a header block (SRO, village, survey details, search period) and then a table, one numbered entry per registered transaction. Each entry carries: document number & year, three dates (execution / presentation / registration), nature of deed, executant(s), claimant(s), volume & page, consideration value, market value, **PR Number (previous document numbers)**, document remarks, and one or more property schedules with type, extent, survey numbers, door number and boundaries.
4. The advocate reads every entry, mentally assembles who transferred what to whom in what order, notes mortgages and whether they were discharged, and cross-checks survey numbers and extents for drift.
5. They write a scrutiny report / title opinion.

## 3.2 Why the current process fails

These are mechanical failure modes, which is exactly why software should own them:

- **The cancellation trap.** A deed and the instrument cancelling it appear as separate numbered entries, often pages apart, linked only by a sentence in a remarks cell. Read linearly, a cancelled lease looks like a live encumbrance. Read carelessly in the other direction, a live mortgage looks resolved.
- **The silent window gap.** PR Numbers routinely point to documents registered *before* the EC's search period. The chain therefore continues outside the certificate in hand. Nothing on the document announces this. The advocate must notice, unprompted, that the evidence is insufficient — and it is easy not to.
- **Name-variance breaks.** Tamil party names appear with differing transliterations, honorifics, initials and parenthetical role markers (e.g. `(முத.)`, `(முக.)`) across entries. A break between claimant *n* and executant *n+1* can be real or an artefact of spelling; distinguishing the two by eye is unreliable.
- **Survey and extent drift.** Subdivisions renumber survey plots. Extents change across entries for legitimate (partition) and illegitimate reasons. Tracking this across a 30-year EC by hand is drudgery with high stakes.
- **It does not scale.** The work is linear in the number of entries and is performed by the most expensive person in the chain.

## 3.3 Who, how often, what it costs

- **Who:** property advocates and bank-empanelled lawyers in TN; secondarily the buyer and the lending bank who inherit the risk.
- **How often:** every property transaction requiring a loan or diligence — a continuous, non-seasonal workload for the profession.
- **Cost today:** hours of senior professional time per file (assumption, §4.1), and on failure, a title defect discovered years later during resale or foreclosure — the most expensive possible moment.
- **Why now:** the reading problem is newly solved (§0.2), and the chain edges were always in the data.

## 3.4 Existing alternatives and why they fail

| Alternative | What it does | Why it fails this job |
|---|---|---|
| Manual reading (status quo) | Advocate reads EC | Slow, linear, and the three failure modes above are attention failures under time pressure |
| Record-retrieval platforms (e.g. Landeed and similar) | Fetch land records/ECs quickly across states | Solves *access*, not *interpretation*. You still receive an unread table. |
| Generic LLM (upload the PDF to ChatGPT/Gemini) | Summarises the document | Tamil table fidelity degrades; more importantly it will *narrate* a conclusion with no deterministic rulebook, no provenance, and no ability to say "this certificate is insufficient." A confident wrong answer on an encumbrance is worse than no answer. |
| Generic OCR / IDP suites | Extract text and fields | Produce a text dump or flat fields. No chain, no graph, no domain rules, no Indic-script table fidelity. |
| Bank legal-vetting vendors | Human-powered scrutiny at scale | Labour arbitrage, not tooling. Same failure modes, outsourced. |

---

# 4. Business Value

*Constructed as a defensible argument, with assumptions labelled. Per the rubric: market size alone is not impact.*

## 4.1 Assumption register

Every number below is an assumption to be verified before external use. They are stated so they can be attacked.

| # | Assumption | Value used | Confidence | How to verify |
|---|---|---|---|---|
| A1 | Advocate time per title scrutiny (EC reading + chain assembly) | 3–8 h, midpoint **5 h** | Medium | Interview 5 TN property advocates |
| A2 | Share of that time that is EC reading/chain assembly (vs. drafting, client comms) | **50–60%** | Medium | Same interviews |
| A3 | Professional fee per scrutiny | **₹3,000–15,000** | Medium | Published empanelment schedules; practitioner interviews |
| A4 | TN document registrations per year | **order 10⁶–10⁷** | Low — order of magnitude only | IGRS TN annual administration report |
| A5 | Share of transactions requiring formal scrutiny (loan/diligence-backed) | **30–50%** | Low | Bank empanelment data |
| A6 | Reduction in EC-reading time with TitleChain | **60–80%** | Medium — grounded in 98.6% field fidelity + deterministic rules | Timed A/B with practising advocates |

## 4.2 The value calculation

Take one advocate, one file. Under A1/A2, EC reading and chain assembly consume ≈ **2.5–3 h** of a 5 h scrutiny. Under A6, TitleChain reduces this to ≈ **30–60 min** of *review* — the advocate is checking flagged findings against source crops rather than reading a table.

**Time saved per file: ~2 h, i.e. ~40% of total scrutiny effort.** That clears the rubric's L5 bar (>30% movement on an operating metric) on the metric that matters to the payer, and it survives challenge even at the pessimistic end of A6 (60% reduction → ~1.5 h → ~30%).

Second-order value, harder to quantify but larger: **the window-insufficiency check converts an invisible risk into a caught defect.** An advocate who unknowingly opines on a chain whose parents lie outside the search window has produced an unsound opinion. We do not know the base rate of this (verify: A7), but its cost is not the ₹5,000 fee — it is the litigated value of the property. Both ECs we tested exhibit PR pointers outside their search window. Two out of two is not a base rate, but it is a signal that the pattern is common rather than exotic.

## 4.3 Why customers pay

The buyer is the advocate or the firm, and the purchase is straightforward: a tool that returns ~2 hours per file and reduces professional-liability exposure, priced far below the fee for a single file. Per-EC processing cost is **under ₹5** (₹0.5/page × 3–6 pages, plus negligible LLM tokens). Even at a per-file price of ₹200–500 the gross margin is ~98% and the customer's ROI is immediate and obvious. Banks are the second payer: they already fund this work through empanelment and bear the residual risk.

## 4.4 TAM — stated last, deliberately

Under A4/A5, the annual volume of TN transactions requiring scrutiny is plausibly in the low millions; at ₹200–500 per file that is a market in the ₹10²–10³ crore range for Tamil Nadu alone, before expansion. **This number is the least reliable thing in this document and the least important.** The urgency argument in §4.2 is what should be defended; TAM is context.

## 4.5 Defensibility

The moat is deliberately placed in our layer, never in Sarvam's model quality — which any competitor can buy tomorrow.

1. **The rulebook.** Encoded TN registration practice: deed-nature taxonomy, discharge semantics, cancellation cross-reference grammar, the meaning of `(முத.)` / `(முக.)` role markers, subdivision conventions. This is institutional knowledge, acquired from practitioners, not derivable from the document.
2. **Correction memory.** Every advocate correction (a merged name cluster, a re-typed deed nature, a rejected finding) is stored, attributed and replayed. The system's accuracy on *this firm's* districts and vocabulary compounds with use. A competitor starts at zero corrections.
3. **The name graph.** Accumulated party-name clusters across cases become a proprietary entity graph — the same trust, the same builder, the same family appearing across files. This is a genuine network effect *within a firm* and, if pooled with consent, across firms.
4. **Workflow lock-in.** Once the case file is the working surface for scrutiny, the report, the corrections and the audit trail live here.

## 4.6 Network effects

Weak-to-moderate and honestly bounded: the name graph and rulebook improve with volume, and improvements are shared across all users of the same district profile. This is a data network effect, not a marketplace one — it compounds but does not create winner-take-all dynamics.

## 4.7 Expansion path

EC chain reconstruction (TN) → sale-deed cross-verification against the EC → patta/chitta reconciliation → other computerised states with equivalent instruments (KA, TS, AP each have analogous certificates and the same PR-pointer logic) → bank-side portfolio scanning (re-scrutinise an existing loan book for defective titles). Each step reuses the graph and the rulebook.

## 4.8 Long-term vision

A verified, machine-readable title graph for Indian property, assembled bottom-up from the documents transactions already generate — with provenance to the source region of the source certificate for every edge. The registry that the registry does not provide.

## 4.9 Biggest risks and assumptions

| Risk | Severity | Mitigation |
|---|---|---|
| A1/A3 wrong — advocates value their time differently than assumed | High for pricing, low for product | Interviews before pricing; the time-saving claim holds even at pessimistic A6 |
| Formatting varies materially across SROs/districts | **High — currently untested** | Source ECs from ≥3 districts tonight (§14.0) |
| Advocates distrust automated findings | Medium | Every finding is deterministic and cites a source crop; the product never opines, it evidences |
| Regulatory/liability exposure for a wrong flag | Medium | Positioned as an evidence tool with mandatory human sign-off; no legal opinion is generated |
| TNREGINET changes EC layout | Low-medium | Layout-agnostic extraction (LLM over digitised HTML, not fixed coordinates) |

---

# 5. User Personas

## Primary — "Advocate Meena", property advocate, Coimbatore

- **Practice:** 15 years; bank empanelment with two nationalised banks; 8–15 scrutiny files a month.
- **Goals:** clear the file accurately, protect her name on the opinion, keep turnaround inside the bank's SLA.
- **Pain points:** the tedium is the risk — attention fades on entry 40 of a 30-year EC, and that is exactly where the cancelled-mortgage entry sits. She has no systematic way to know whether an EC's window actually covers the chain.
- **Current workaround:** printouts, highlighters, a handwritten chain on the file cover, and re-reading when something feels off.
- **Why she switches:** two hours back per file, and a written record showing she checked what she checked.

## Secondary — "Credit Manager Ravi", nationalised bank branch, Salem

- **Goals:** disburse fast without booking a bad title; defensible file if the loan sours.
- **Pain points:** cannot evaluate the quality of a scrutiny report he receives; discovers defects only at foreclosure.
- **Current workaround:** trusts the empanelled advocate entirely.
- **Why he adopts:** a structured, evidence-linked chain report attached to the loan file — and an explicit statement of what the search did *not* cover.

## Tertiary — "Buyer Karthik" (beneficiary, not a user in v1)

Bears the entire downside of a missed encumbrance and has no ability to verify. Out of scope for the build; the reason the product matters.

---

# 6. User Journey

```
TODAY
  Order EC ──► receive dense Tamil PDF ──► read 40 entries linearly
                                              │
                                              ├─ miss the cancellation cross-reference
                                              ├─ never notice PR pointers precede the search window
                                              ├─ mis-read name variance as a chain break (or miss a real one)
                                              └─ track survey/extent drift by memory
                                              ▼
                                    write opinion under time pressure
                                              ▼
                              residual risk transfers silently to the buyer

WITH TITLECHAIN
  Upload EC ──► Sarvam Vision digitises (tables + coordinates + reading order)
            ──► 105B types each entry into a strict schema
            ──► transliteration clusters party names across scripts
            ──► OUR deterministic rulebook builds the graph and runs 10 checks
                                              ▼
        ┌─────────────────────────────────────────────────────────┐
        │  CHAIN GRAPH          FINDINGS (ranked, evidence-cited) │
        │  ○ 2520/2019 Lease    ⚠ WINDOW INSUFFICIENT             │
        │    └ cancelled by ──► 5 parent docs (2005–2011) outside │
        │  ○ 8756/2020 Cancel     the 2018–2023 search period     │
        │                       ✓ Lease extinguished — not a live │
        │                         encumbrance                      │
        │                       ⚑ Entry 2: registration date      │
        │                         missing → review source          │
        └─────────────────────────────────────────────────────────┘
                                              ▼
      every finding clicks to its bounding-box crop on the source page
                                              ▼
        advocate corrects one name → graph re-derives → correction persists
                                              ▼
     NEXT ACTION, PRE-FILLED: order EC · Pollachi SRO · Puliyampatti ·
     survey 95/2, 100/3A, 113/1B, 116/A1, 116/B1 · 01-Jan-1993 → 31-Dec-2017
                                              ▼
                    export scrutiny report → attach to file
```

**Where value is created:** not at extraction (that is table stakes), but at the two moments a human reliably fails — the cross-referenced cancellation, and the unannounced insufficiency of the evidence itself.

---

# 7. Core MVP

Ruthlessly scoped. Every feature names the rubric parameter it serves and its status. **If we are behind, cut from the bottom.**

| # | Feature | Why it exists | Rubric parameter | Status |
|---|---|---|---|---|
| F1 | EC upload → Sarvam Vision digitisation (chunked >10 pages) | The hard input must be read | Document Intelligence | **Mandatory** |
| F2 | Entry typing into strict JSON schema (105B) | Rows must become records before they can become a graph | JTBD | **Mandatory** |
| F3 | Graph assembly from PR pointers + remark cross-references | The core reframing | Creativity | **Mandatory** |
| F4 | Deterministic rulebook — 10 checks (§10.5) | The findings a lawyer acts on; legally sensitive logic must not be model output | JTBD | **Mandatory** |
| F5 | Window-insufficiency detection + pre-filled next EC order | The non-obvious unlock and the delight beat | Delight | **Mandatory** |
| F6 | Source-crop provenance (bbox → cropped image per finding) | Traceability; makes review precise | Document Intelligence | **Mandatory** |
| F7 | Schema-completeness validator → uncertainty flags | Catches cell omissions that confidence cannot (§0.2) | Document Intelligence | **Mandatory** |
| F8 | Persisted case file (SQLite) + correction propagation | Memory L4; corrections re-derive the graph | Memory & Context | **Mandatory** |
| F9 | Party-name clustering via transliteration | Chain-break detection is unreliable without it | JTBD | **Mandatory** |
| F10 | Exportable scrutiny report | The final usable artifact | JTBD | **Mandatory** |
| F11 | Advocate login + case ownership scoping | Memory L5 requires permissions intact | Memory & Context | High-value optional |
| F12 | EC staleness clock (issue date vs today) | Stale vs current information distinguishable — explicit L5 wording | Memory & Context | High-value optional |
| F13 | Double-pass extraction disagreement flags | Second uncertainty signal | Document Intelligence | Optional — cut first |
| F14 | Multi-EC merge into one property chain | Expansion demo | — | **Parking lot** |
| F15 | Sale-deed cross-verification | Expansion demo | — | **Parking lot** |

**Explicitly cut:** any voice interface, any dashboard analytics, any avatar/animation, multi-state support, TNREGINET integration, mobile app, real-time collaboration.

---

# 8. Functional Requirements

**FR-1 Ingest.** Accept PDF/JPEG/PNG ≤50 MB. Split >10-page PDFs into ≤10-page jobs client-side; stitch results preserving global page numbering. Reject unsupported types with a specific message.

**FR-2 Digitise.** For each chunk: `create_job(language="ta-IN", output_format="md")` → `upload_file` → `start` → poll → `download_output`. Persist both `document.md` and every `metadata/page_NNN.json` verbatim. Never discard the raw response — it is the provenance record.

**FR-3 Table isolation.** From page metadata, select blocks with `layout_tag == "table"`, ordered by `reading_order`. Retain `block_id`, `coordinates`, `confidence`, `page_num` alongside the HTML.

**FR-4 Entry typing.** For each EC (or page group), call `sarvam-105b` with `response_format={"type":"json_schema", ...}` strict, supplying the table HTML and the schema in §10.4. The model transcribes and structures; it must not infer, summarise, or resolve conflicts. Unreadable field → explicit `null`, never a guess.

**FR-5 Provenance binding.** Every typed entry stores the `page_num` and `block_id` it came from, so any field can be rendered as a cropped region of the source page image.

**FR-6 Name normalisation.** For each party name, call `text.transliterate` `ta-IN→en-IN`; store native and roman forms; strip honorifics and parenthetical role markers into a separate `role_marker` field; cluster by normalised-token similarity within a case.

**FR-7 Graph assembly.** Nodes = entries. Edges: `PR_PARENT` (from PR Number), `CANCELS` / `CANCELLED_BY` (parsed from remarks), `SUCCESSION` (claimant of entry *n* clusters with executant of entry *m*, *m* later). Edges to documents absent from this EC become **dangling nodes**, explicitly typed as unexamined.

**FR-8 Rulebook execution.** Run all ten checks (§10.5) as pure deterministic functions over the typed graph. Each emits `{rule_id, severity, message, evidence:[entry_ids], source_crops:[...]}`. **No rule may call a model.**

**FR-9 Findings presentation.** Rank by severity (blocking → material → informational). Each finding shows its evidence entries and their source crops.

**FR-10 Insufficiency action.** When R3 fires, compute the required earlier search window (from the earliest PR year, minus a configurable buffer, to the day before the current window opens) and render a pre-filled EC order block: SRO, village, survey numbers, date range.

**FR-11 Correction.** Any typed field is editable. On save: persist `{entry_id, field, old, new, actor, timestamp}`, re-run FR-6 → FR-9, and visibly update affected findings. Corrections survive restart and are attributed.

**FR-12 Case persistence.** Cases, EC documents, entries, parties, edges, findings, corrections persist in SQLite. Reopening a case restores full state including which findings were reviewed.

**FR-13 Export.** Generate a scrutiny report (HTML/PDF) containing property identifiers, search period, the chain, all findings with evidence, an explicit *"what this search does not cover"* section, the rulebook version, and a correction log.

**FR-14 Staleness.** Display EC issue date and days elapsed; flag beyond a configurable threshold.

---

# 9. Non-Functional Requirements

| Dimension | Requirement | Basis |
|---|---|---|
| **Performance** | ≤90 s from upload to findings for a ≤10-page EC | Measured: 12 pages ≈ 60 s |
| **Throughput** | Respect 10 req/min on Document Digitization; queue and back off | Documented hard limit, all plans |
| **Reliability** | Any Sarvam call retries with exponential backoff; a failed chunk degrades that page, never the case | Async job API can fail mid-poll |
| **Correctness** | 100% of legally sensitive verdicts produced by deterministic code, 0% by model output | Non-negotiable design rule |
| **Scalability** | Stateless workers, job queue; per-case data isolated | Post-hackathon |
| **Security** | API key server-side only, never in the browser; uploads scoped to the owning advocate | `.env` already gitignored; server-rendered HTML means no client bundle ever holds a secret |
| **Privacy** | ECs are public records but name real parties; no third-party analytics, no sending documents anywhere but Sarvam; deletable case files | Professional obligation; `htmx.min.js` vendored locally, so the demo makes **zero** non-Sarvam network calls |
| **Cost** | <₹5 per EC (₹0.5/page + negligible tokens) | Measured: ₹6 for 12 pages |
| **Auditability** | Raw Sarvam responses retained immutably alongside every derived record | Provenance is the product |

---

# 10. AI Architecture

## 10.1 Division of labour (the central design rule)

> **Models read. Code decides.**

Sarvam Vision converts pixels to structured text. 105B converts structured text to typed records. Both are *transcription* roles. Every judgment a lawyer would be liable for — is this encumbrance live, is the chain broken, is this search sufficient — is executed by deterministic Python over typed data, is unit-testable, and is explainable by citing the rule and its evidence. This is a product-integrity decision first and a rubric decision second, and it is what separates TitleChain from "upload the PDF to a chatbot."

## 10.2 Models

| Stage | Model | Why | Config |
|---|---|---|---|
| Digitisation | Sarvam Vision (Document Digitization) | Only model verified at 98.6% on real Tamil EC tables with coordinates | `language=ta-IN`, `output_format=md` |
| Entry typing | `sarvam-105b` | 128K context holds a full EC's table HTML; strict `json_schema` guarantees parseable output | `temperature=0`, `seed` fixed, `response_format=json_schema` strict |
| Name normalisation | Transliteration API | Deterministic, purpose-built for Indic↔Roman | `ta-IN→en-IN` |

`sarvam-30b` is the fallback for typing if 105B rate-limits (40 req/min Starter on both).

## 10.3 Prompting strategy

A single system prompt for typing, with these constraints:

- Role: **transcriber, not analyst.** Copy values; do not interpret, summarise, translate, or resolve contradictions.
- Preserve Tamil text verbatim in `*_native` fields; never translate names.
- Unreadable or absent → `null`. **Never infer a plausible value.** (This is what makes the completeness validator meaningful.)
- Emit one object per numbered EC entry; sub-rows (consideration, market value, PR, remarks, schedules) attach to their parent entry.
- Copy PR numbers and remark text exactly — they are the graph edges.

Temperature 0 and a fixed seed, so a re-run is reproducible and a disagreement between two runs is a real signal.

## 10.4 Extraction schema (strict)

```jsonc
{
  "ec_header": {
    "sro": "string", "village": "string",
    "survey_details": ["string"],
    "search_period_start": "string|null", "search_period_end": "string|null",
    "issue_date": "string|null", "declared_entry_count": "integer|null"
  },
  "entries": [{
    "sr_no": "integer",
    "doc_no": "string|null", "doc_year": "integer|null",
    "date_execution": "string|null", "date_presentation": "string|null",
    "date_registration": "string|null",
    "nature": "string|null",
    "executants": [{"name_native": "string", "role_marker": "string|null"}],
    "claimants":  [{"name_native": "string", "role_marker": "string|null"}],
    "volume_page": "string|null",
    "consideration_value": "string|null", "market_value": "string|null",
    "pr_numbers": [{"doc_no": "string", "year": "integer"}],
    "remarks": "string|null",
    "schedules": [{
      "property_type": "string|null", "extent": "string|null",
      "village_street": "string|null", "survey_nos": ["string"],
      "door_no": "string|null", "boundaries_native": "string|null"
    }],
    "source": {"page_num": "integer", "block_id": "string"}
  }]
}
```

`declared_entry_count` is captured deliberately: the EC states its own entry count (`பதிவுகளின் எண்ணிக்கை: 2`), giving us a **free ground-truth checksum** against the number of entries we extracted. Cheap, deterministic, and catches whole-entry loss.

## 10.5 The rulebook (deterministic, ours)

| ID | Rule | Severity | Fires on our real data |
|---|---|---|---|
| R1 | `CANCELLED_INSTRUMENT` — entry X's remarks name a cancelling document Y present in this EC → X extinguished; must not be reported as a live encumbrance | Material | **Yes — EC-A** |
| R2 | `LIVE_ENCUMBRANCE` — nature ∈ {mortgage, simple mortgage, deposit of title deeds, charge, lien} with no matching discharge/release → OPEN | Blocking | — |
| R3 | `WINDOW_INSUFFICIENT` — any PR year < search-period start year → chain continues outside this certificate | Blocking | **Yes — both ECs** |
| R4 | `DANGLING_PARENT` — PR pointer with no corresponding entry in this EC → parent document unexamined | Material | **Yes — both ECs** |
| R5 | `CHAIN_BREAK` — claimant cluster of entry *n* never appears as executant in a later transfer | Blocking | — |
| R6 | `SURVEY_DRIFT` — survey numbers vary across entries without a subdivision/partition deed | Material | — |
| R7 | `EXTENT_MISMATCH` — schedule extent changes without a partition instrument | Material | — |
| R8 | `STALE_EC` — issue date older than threshold | Informational | **Yes — EC-A issued 2023** |
| R9 | `STRUCTURAL_GAP` — a required field is `null` (completeness validator) | Material | **Yes — EC-A entry 2 dates** |
| R10 | `ENTRY_COUNT_MISMATCH` — extracted entries ≠ `declared_entry_count` | Blocking | — |

Six of ten rules fire on documents we already hold. The demo is not staged; it is what the data does.

## 10.6 The uncertainty net

Three independent signals, because §0.2 proved one is insufficient:

1. **Block confidence** (from Sarvam) — triages whole regions. Useful, but blind to cell omissions.
2. **Schema completeness (R9)** — a required field is `null`. This is the signal that would have caught our one real failure inside a 0.96-confidence block.
3. **Entry-count checksum (R10)** — the document's own declared count vs. ours.

Optional fourth (F13): two extractions at different seeds; fields that disagree are surfaced as **competing readings** shown side by side against the source crop — the rubric's L5 wording, achieved literally.

## 10.7 Memory and context strategy

Three layers, matching the L5 definition:

- **Current task** — the open case: which EC, which entries, which findings reviewed, which corrections pending.
- **Relevant history** — prior corrections by this advocate, the party-name clusters accumulated across their cases, previously processed ECs for the same property.
- **Business rules** — the versioned rulebook. Every finding records the rulebook version that produced it, so a stale finding is distinguishable from a current one.

Corrections propagate: editing a name re-runs clustering, graph assembly and every rule, and visibly updates findings. Access is scoped to the owning advocate (F11).

## 10.8 Failure handling

| Failure | Response |
|---|---|
| Digitisation job fails | Retry once; then mark that chunk `UNREAD` and show the raw page — never silently drop pages |
| 105B returns unparseable JSON | Strict schema makes this unlikely; on failure retry once, then fall back to 30B, then flag the entry for manual typing |
| Field unreadable | `null` → R9 fires → advocate reviews against the source crop |
| Rate limit (10/min) | Queue with backoff; UI shows honest queue position |
| Total Sarvam outage during demo | Pre-cached outputs for the three demo ECs (§15.5) |

---

# 11. System Architecture

> Stack decisions, their alternatives, and the evidence behind them live in **[STACK.md](STACK.md)**.
> This section is the shape of the system; that document is why each layer is what it is.
> **[ARCHITECTURE.md](ARCHITECTURE.md)** is how it runs — routes, job states, module contracts,
> `schema.sql`, and the correction loop step by step.

```
┌──────────────────────────────────────────────────────────────────┐
│ FRONTEND — Jinja2 + HTMX, served by the same FastAPI process     │
│  Upload · Chain graph · Findings list · Source-crop viewer ·     │
│  Inline correction · Report export                               │
│  No build step · no npm · no CORS · htmx.min.js vendored local   │
└───────────────────────────┬──────────────────────────────────────┘
                            │ same process — HTML over the wire
┌───────────────────────────▼──────────────────────────────────────┐
│ BACKEND — Python 3.14 · FastAPI · uv                             │
│                                                                  │
│  models.py    Pydantic v2 — §10.4 schema, single source          │
│  ingest.py    chunk >10p, validate, store original               │
│  digitise.py  ── Sarvam Document Digitization (sarvamai SDK) ──► │
│  extract.py   ── sarvam-105b, json_schema strict (raw httpx) ──► │
│  names.py     ── Transliteration ta-IN→en-IN ──────────────────► │
│  graph.py     OURS — nodes, PR/cancel/succession edges           │
│  rulebook.py  OURS — R1..R10, pure functions, unit-tested        │
│  crops.py     OURS — bbox → cropped PNG (pypdfium2 + Pillow)     │
│  report.py    OURS — scrutiny report generation                  │
└───────────────────────────┬──────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│ STORAGE — SQLite via stdlib sqlite3, no ORM (survives restart)   │
│  cases · ec_documents · entries · parties · name_clusters ·      │
│  edges · findings · corrections · rulebook_versions              │
│  + filesystem: original uploads, raw Sarvam JSON, page rasters   │
└──────────────────────────────────────────────────────────────────┘

EXTERNAL: Sarvam APIs only. No third-party services, no CDN. Key server-side.
```

**Why HTMX and not React (changed 26 Jul, after team size was fixed at one).** Solo, a separate SPA costs a second process, a CORS config, a build step, and a JSON contract negotiated between two halves of the same brain — roughly 45–60 minutes paid out of the same §14.2 window that must produce `graph.py` and `rulebook.py`. Those two files are the product; nothing may compete with them for attention. HTMX also makes FR-11 nearly free: the correction POST re-runs `derive()` server-side and swaps the findings panel via `hx-target`. That is not a stand-in for the Memory proof — it *is* the Memory proof, rendered.

**Why SQLite over Supabase:** zero setup cost, survives restart (which is what Memory is actually scored on), and no network dependency during the demo. Supabase is permitted by the rules but buys us nothing here.

**Why no ORM:** nine tables, single writer, single process, no migrations. SQLAlchemy would cost 30–45 minutes of model definition to buy pooling, migrations and lazy-loading — none of which is needed once. One `schema.sql` executed at startup plus a thin `db.py`. The rule that matters: **SQLite persists, it never computes.** No business logic in SQL, because `derive()` taking and returning typed Python objects is what makes §10.5 unit-testable.

**Why Pydantic v2 is load-bearing:** the §10.4 schema is written once and serves three jobs — `model_json_schema()` becomes the `response_format` sent to 105B, `model_validate()` checks the reply, and the same classes type the graph, the rules and the template context. Prompt/code schema drift becomes structurally impossible rather than a bug discovered at 15:40. Every field is `Optional` with **no default**, so an omitted field fails loudly instead of producing a half-entry — the `null` discipline of §10.3 enforced by the type system rather than by the prompt.

**Why raw `httpx` for one call and the SDK for the other:** digitisation via `sarvamai` is proven working on three real ECs (§0.2) and its async job dance is worth not rewriting. Whether the SDK passes a strict `json_schema` `response_format` through cleanly is **untested** — and that is the last load-bearing unknown in the system (§14.0). A direct POST is eight lines and makes a schema rejection debuggable in seconds instead of through a wrapper.

**Data model (core tables):**

- `cases(id, advocate_id, property_key, created_at, rulebook_version)`
- `ec_documents(id, case_id, sro, village, survey_nos, search_start, search_end, issue_date, declared_entry_count, page_count, file_path)`
- `entries(id, ec_id, sr_no, doc_no, doc_year, date_execution, date_presentation, date_registration, nature, volume_page, consideration_value, market_value, remarks, page_num, block_id, block_confidence)`
- `parties(id, entry_id, role, name_native, name_roman, role_marker, cluster_id)`
- `edges(id, case_id, from_entry, to_doc_no, to_doc_year, edge_type, resolved_entry_id NULL)`
- `findings(id, case_id, rule_id, severity, message, evidence_entry_ids, rulebook_version, status)`
- `corrections(id, entry_id, field, old_value, new_value, actor, created_at)`

---

# 12. Success Metrics

## Product
- Time from upload to findings (target ≤90 s for ≤10 pages)
- % of ECs processed without manual intervention (target ≥85%)
- Findings reviewed per case / corrections per case (falling over time = learning)

## Business
- Advocate hours saved per file (target ≥2 h; A6)
- Cost per EC (target <₹5)
- Files per advocate per month (capacity increase)
- Retention: cases per advocate in month 2 vs month 1

## AI quality
- **Field-anchor fidelity** — the §0.2 metric, re-run on every new EC (current: 98.6%)
- Entry-count checksum pass rate (R10)
- Structural-gap rate (R9 fires per 100 entries)
- Correction rate per field type — identifies which fields the pipeline is weakest on
- Rule precision: % of flagged findings the advocate confirms rather than dismisses

## User experience
- Can a first-time advocate complete a case without help? (binary, tested on the day)
- Time to locate the source evidence for a finding (target <5 s via crop)
- % of findings where the advocate clicks through to source (engagement with provenance = trust)

---

# 13. Competitive Landscape

| | What they do | What we change |
|---|---|---|
| **Manual scrutiny** | Human reads the table | We make the mechanical failures structurally impossible to miss, and leave judgment to the human |
| **Record retrieval platforms** | Get you the EC faster | We start where they stop. Access ≠ interpretation. Complementary, not competitive. |
| **Generic LLM upload** | Narrates a summary | We never let a model decide an encumbrance. Deterministic rules + provenance + an honest "this evidence is insufficient" — which a summariser structurally cannot produce, because it does not know what it was not given. |
| **IDP/OCR suites** | Extract fields | They return fields; we return a graph, a rulebook verdict, and a next action |
| **Human vetting vendors** | Outsource the reading | Same failure modes at lower cost; no accumulating asset |

**The structural difference, stated plainly:** everyone else treats the EC as a document to be read. We treat it as a partially-observed graph, and the most valuable thing we output is not what the document says — it is **what the document cannot tell you, and exactly which document to order next.** No competitor is positioned to say that, because saying it requires modelling the chain rather than the page.

---

# 14. Build Plan

**Team size: one.** §14.2 and §14.3 together are more than a solo clock allows, so the cut order is fixed **now** rather than negotiated at 14:45. Cut in this sequence:

1. **F12 staleness clock** — the `rulebook_version` / issue-date columns earn the L5 wording; the UI for them does not.
2. **F11 advocate login** — case scoping still demonstrates Memory without auth. Auth is pure cost.
3. **Chain graph visualisation → nested list.** Keep every line of graph *logic*.
4. **F13 two-seed disagreement pass** — a genuine luxury, and the first one on the list.

**Never cut:** `rulebook.py`, `crops.py`, correction propagation, the order block. That is one per rubric parameter; everything else is decoration on top of them.

## 14.0 Tonight (pre-event — research and validation only, NOT product code)

> ⚠️ **Compliance:** Buildathon rules disqualify "code written off the floor." Everything below is capability validation and test-data sourcing, which the rules permit as research. **All product code is written on the floor tomorrow.** `run_di.py` and `check_ec_integrity.py` are validation harnesses and will not be carried into the product; the pipeline is rebuilt from zero on the day. This will be declared in the submission notes as a borderline starting point — *hiding origin is auto-disqualification, so we declare it.*

- [ ] **Stage-2 dry run** — feed a digitised EC's table HTML to `sarvam-105b` with the §10.4 schema; confirm typed rows come back clean. **This is the last untested load-bearing dependency**, and it also settles SDK-vs-`httpx` for `extract.py` (§11).
- [ ] **Source 3+ ECs from different SROs/districts** — kills the Pollachi-only formatting risk.
- [ ] **True phone-photo test** — print one EC, photograph it at an angle under room light, run it. This is the honest version of the degraded-input class.
- [ ] **Pre-warm the wheel cache** — `uv pip download` of the eight-package dependency set ([STACK.md](STACK.md)). Installing from a warm cache is instant and offline; installing over conference wifi at 10:31 is a gamble taken at the worst possible moment. Downloading wheels is environment prep, not writing code.
- [ ] Confirm API credit balance.
- [x] ~~**Bbox → crop rendering**~~ — **done.** `pypdfium2` verified at 1:1 against a real EC page (§0.2, finding 1). F6 has no remaining unknown.

## 14.1 Hour 1 (10:30–11:30) — prove the hardest dependency end to end

**Goal: one ugly, hardcoded, complete pass.** EC PDF in → typed entries → one rule firing → printed output. No UI, no database, no styling.

- Tasks: FastAPI skeleton · digitise call · table-block isolation · 105B typing with strict schema · R3 (window insufficiency) hardcoded · print findings to console.
- **Acceptance:** on EC-A, the console prints the two entries and correctly states that five PR documents fall outside the search window.
- **Deliverable:** working `main.py`, committed.
- **Fallback if behind:** run against the pre-cached digitisation output and build stage 2 first — the digitisation stage is already proven, so it is the safe thing to stub.
- **Checkpoint:** idea committed by 11:30 ✓ · running by 12:15 ✓ (we should be ahead of both).

## 14.2 MVP (11:30–14:00) — the product

- Graph assembly (PR + cancellation + succession edges) · full rulebook R1–R10 · SQLite persistence · name clustering via transliteration · bbox crop generation · minimal HTMX/Jinja UI (upload, graph, findings, crop viewer).
- **Acceptance:** EC-A and EC-B both produce correct graphs and findings; state survives a server restart; every finding renders its source crop.
- **Deliverable:** demo-able product on two real ECs.
- **Fallback:** cut the graph *visualisation* to a nested list; keep the graph *logic*. Cut F13.

## 14.3 Beta (14:00–15:30) — the scoring surface

- Correction UI with propagation (F11 memory proof) · pre-filled next-EC-order block (F5 delight beat) · report export (F10 artifact) · advocate login + case scoping · staleness clock.
- **Acceptance:** correcting a party name visibly re-derives the chain and updates findings; correction survives restart and is attributed; report exports with the "what this search does not cover" section.
- **Fallback:** cut login (F11) and staleness (F12) — keep correction propagation, which is the actual Memory evidence.

## 14.4 Final (15:30–16:30) — reserved, do not build

**No new features after 15:30.** This block is: three repeated runs on unseen ECs · state reset script (`rm titlechain.db` — startup re-execs `schema.sql`) · fallback inputs staged · pre-cached demo outputs · **public link brought up and verified** · submission assets · **two timed rehearsals** · borderline-starting-point declaration written.

**Public link = Cloudflare quick tunnel over localhost.** One command, real HTTPS, no account, ~30 s. Not Render/Fly/Vercel: a real deploy means a build environment that differs from the laptop, secret management, a cold start, an ephemeral filesystem that eats the SQLite file, and a first-deploy failure discovered at 16:10. The tunnel keeps the database on the disk where the rehearsed demo state already lives, and the process behind the link is the exact one just rehearsed. Bring it up *in this block*, never earlier.

## 14.5 Production vision (post-event)

Multi-EC merge per property → sale-deed cross-verification → district rulebook profiles → firm-level name graph → bank portfolio scanning → adjacent states.

---

# 15. Demo Strategy

## 15.1 The 90-second script

| t | Action | What it proves |
|---|---|---|
| 0:00–0:10 | "Every property loan in Tamil Nadu needs a 13-year title search. This is the certificate it runs on." *Show the raw Tamil EC.* | Hard, real, India-specific input |
| 0:10–0:25 | Upload EC-A. Processing visible. Entries appear as typed rows with Tamil names intact. | **Document Intelligence** |
| 0:25–0:40 | "Read linearly, this lease looks like a live encumbrance." Show the graph: 2520/2019 —cancelled-by→ 8756/2020. "It was cancelled in 2020. It is not an encumbrance." | **Creativity** — the graph reframing |
| 0:40–1:00 | "But here is what this certificate can't tell you." R3 fires: five parent documents from 2005–2011 sit outside the 2018–2023 window. **"This EC cannot support a 13-year search."** Pre-filled order for the exact replacement certificate appears. | **Delight** — the anticipated pain point + next action |
| 1:00–1:15 | Click a finding → source crop highlights the exact region on the Tamil page. Click the flagged missing date → "we could not read this; here is where it is." | **Document Intelligence** (uncertainty made precise) |
| 1:15–1:30 | Correct a party name → chain re-derives → close the case → reopen → correction and findings intact. Export the report. | **Memory & Context** + **JTBD** (final artifact) |

**Held in reserve if asked:** run EC-B live, unseen — proves repeatability without builder rescue (JTBD L5).

## 15.2 Demo inputs

- **Primary:** EC-A (`ec_samples/ec2_pacollege.pdf`) — the cancellation trap + window insufficiency. Real, public, unmodified.
- **Secondary (live, for repeatability):** EC-B (`ec_samples/ec3_rera.pdf`) — 6 pages, 11 schedules, gift deed to a town panchayat.
- **Third:** an EC from a different SRO, sourced tonight — proves we are not overfit to Pollachi.

## 15.3 Expected outputs

EC-A: 2 entries · 2 graph nodes · 1 `CANCELLED_INSTRUMENT` · 1 `WINDOW_INSUFFICIENT` (5 parents, 2005–2011) · 5 `DANGLING_PARENT` · 1 `STRUCTURAL_GAP` (entry 2 dates) · 1 `STALE_EC` · pre-filled order for 01-Jan-1993 → 31-Dec-2017, Pollachi SRO, Puliyampatti, survey 95/2, 100/3A, 113/1B, 116/A1, 116/B1.

## 15.4 Backup inputs

The degraded-scan variant (`ec_samples/ec2_scan.zip`) — scored 100%, and doubles as a "works on scans too" beat if there is time. The nil-EC portal screenshot (`ec_samples/negative_nil-ec-portal-screenshot.pdf`) is retained as a negative case: the product should say "this is not an EC" rather than hallucinate entries.

## 15.5 Failure recovery

1. **Network/API down:** pre-cached digitisation outputs for all three ECs on disk; a `--offline` flag replays them through the real graph and rulebook. The reasoning layer — which is ours and is the actual product — still runs live.
2. **Slow processing:** start the upload while delivering the opening line; the 60 s measured runtime fits the script.
3. **Unexpected extraction error:** it becomes the demo. Show the structural-gap flag catching it and the source crop letting the advocate fix it in five seconds. *The product's thesis is that it exposes uncertainty rather than hiding it — a visible catch is on-message.*
4. **Laptop/projector failure:** exported PDF report of the EC-A case on a USB stick and in the browser.

---

# 16. Evidence Map

*One piece of evidence per parameter. No evidence is reused — per the anti-double-counting rule.*

| Feature | JTBD | Memory | Creativity | Impact | Delight | Doc Intelligence |
|---|---|---|---|---|---|---|
| F1 Digitisation of Tamil EC tables | | | | | | ✅ **the 98.6% fidelity + source crops** |
| F2 Entry typing | supporting | | | | | |
| F3 Graph assembly from PR pointers | | | ✅ **the reframing: document → graph** | | | |
| F4 Deterministic rulebook | supporting | | supporting | | | |
| F5 Window insufficiency + pre-filled order | | | supporting | | ✅ **anticipates the unasked question, gives the next action** | |
| F6 Source-crop provenance | | | | | | supporting |
| F7 Completeness validator | | | | | | supporting |
| F8 Correction propagation + persistence | | ✅ **correction survives restart, re-derives graph, stays attributed** | | | | |
| F9 Name clustering | supporting | | | | | |
| F10 Exported scrutiny report | ✅ **the final usable artifact, produced end to end unaided** | | | | | |
| F11 Login / case scoping | | supporting | | | | |
| Business case §4.2 | | | | ✅ **~40% of scrutiny effort, defended with stated assumptions** | | |

Every mandatory feature maps to a parameter. Anything that maps to nothing is in the parking lot.

---

# 17. Risks

## Technical

| Risk | Sev | Mitigation |
|---|---|---|
| Stage-2 typing produces malformed/incomplete rows | **High** | Strict `json_schema`; verify tonight (§14.0); 30B fallback; R9/R10 catch what slips |
| EC formats vary across SROs | **High** | Source 3 districts tonight; extraction is layout-agnostic (LLM over HTML, not fixed coordinates) |
| Real phone photos degrade worse than our synthetic scan | Medium | Test tonight; digital PDFs are the dominant real-world case (ECs are downloaded, not photographed) |
| Confidence score can't catch cell omissions | **Confirmed real** | Already mitigated by design: completeness validator + entry-count checksum |
| 10 req/min rate limit | Low | Measured headroom is ample; queue with backoff |

## Product

| Risk | Sev | Mitigation |
|---|---|---|
| Advocates distrust automated findings | Medium | Deterministic rules + source crops + mandatory human sign-off; we evidence, never opine |
| Liability if a flag is wrong | Medium | Explicit scope disclaimer; the report states what was *not* covered |
| Impact assumptions don't survive scrutiny | Medium | Assumptions labelled and sensitivity-tested (§4.1–4.2) |

## Demo

| Risk | Sev | Mitigation |
|---|---|---|
| Live API failure | Medium | `--offline` cached replay; our layer still runs live |
| Demo runs long | Medium | Two timed rehearsals in the reserved block; 90 s script with a hard cut list |
| Judges see "OCR + summary" | **High** | Lead with the insufficiency verdict, not the extraction. Extraction is 15 seconds of a 90-second demo. |

## Sarvam limitations (known, designed around)

10-page/job cap (chunk) · 10 req/min (queue) · async-only, no realtime vision (fits a desk workflow) · block confidence ≠ cell confidence (own validator) · no handwriting guarantee via API (out of scope by design) · no Modi/Kaithi/Grantha (out of scope by design).

## Scope

| Risk | Sev | Mitigation |
|---|---|---|
| Feature creep during build | **High** | Parking lot in §7; no new features after 15:30; every feature must name a rubric parameter |
| Over-investment in graph visualisation | Medium | Nested list is an acceptable fallback; the logic is what scores |
| Borderline starting point | **High** | Rebuild all product code on the floor; declare pre-event validation in submission notes |

---

# 18. Why This Wins

**Judges will remember it because of one sentence they did not expect:** *"This certificate cannot support the search it was ordered for, and here is the exact one to order instead."* Every other document product at the event will extract, summarise, or translate. This one tells the user what their evidence does not cover — a conclusion only reachable by modelling the chain rather than the page, and one that is immediately, obviously correct once shown.

**It scores across every dimension without padding.** Document Intelligence is proven at 98.6% on real Tamil government tables with source-region traceability. JTBD produces a genuine professional artifact end to end. Memory is demonstrated by a correction that survives a restart and re-derives the graph, not by remembering a name. Creativity is structural — a document reframed as a partially-observed graph, which then makes the insufficiency check possible. Impact is a defended ~40% reduction in scrutiny effort with assumptions on the table. Delight is answering the question the user was afraid to ask. Nothing is decorative; the voice and dubbing layers are deliberately absent because the job does not need them.

**It is hard to replicate on the day.** Another team would need to find TN ECs, know that the PR Number field is a parent pointer, recognise that PR years routinely precede the search window, and discover — as we did, empirically — that the API's confidence score cannot catch a cell dropped from a high-confidence table. That last one is a trap most teams will walk into and ship without noticing.

**It has a real path to a company.** The reading problem is solved and commoditising; the *rulebook, the corrections and the name graph are not*, and they compound with every file. The wedge is one narrow certificate in one state, which is exactly how a title-graph company should start — the same logic extends to Karnataka, Telangana and Andhra Pradesh, where equivalent instruments carry the same parent pointers. The endgame is a verified title graph for Indian property, assembled from the documents transactions already produce.

---

## Appendix A — Verified capability reference

| Primitive | Tier | Hard limits | Output granularity |
|---|---|---|---|
| Document Digitization (Sarvam Vision) | **Explicit + empirically verified** | 10 pages/job, 200 MB, 10 req/min, ₹0.5/page, async | MD/HTML + per-page JSON: `block_id`, `coordinates{x1,y1,x2,y2}`, `layout_tag`, `confidence`, `reading_order`, `text` (tables as HTML). 3509×2480 raster. |
| `sarvam-105b` | Explicit | 128K ctx, 40 req/min Starter, ₹4/₹16 per 1M tok | Text; strict `json_schema`; tool calling; **no image input** |
| Transliteration | Explicit | `ta-IN` supported both directions | Text + detected source |

**Assumed capabilities we are NOT depending on:** handwriting via API · dashboard-only field extraction with confidence · "Vision real-time" · voice cloning/dubbing APIs · `wiki_grounding` (discontinued for 30B/105B).

## Appendix B — Repository

```
PRD.md                    this document — the spec
STACK.md                  stack decisions and their evidence (supersedes §11 on conflict)
PIPELINE.md               the four stages explained, traced against real output
PROBLEM_AND_VALUE.md      the problem, the market structure, the value arithmetic
CUSTOMER_JOURNEY.md       the advocate's day, before and after
RUBRIC.md                 event handbook and scoring ladders
IDEA_DISCOVERY_PROMPT.md  capability-first methodology that produced this idea
config.py, check_key.py   API key loading (validation harness)
run_di.py                 digitisation harness (validation only — NOT product code)
check_ec_integrity.py     anchor-fidelity checker (validation only)
ec_samples/               real EC test inputs + degraded variants + negative case
output/                   cached digitisation results (demo fallback)
```

**Written on the floor tomorrow, from zero** (layout in [STACK.md](STACK.md)): `app/` — `main.py`, `models.py`, `ingest.py`, `digitise.py`, `extract.py`, `names.py`, `graph.py`, `rulebook.py`, `crops.py`, `report.py`, `db.py`, `schema.sql`, `templates/`, `static/` — and `tests/`.
