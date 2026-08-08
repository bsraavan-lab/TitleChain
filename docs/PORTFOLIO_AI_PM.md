# TitleChain

**An AI-native title-scrutiny workspace that turns a dense Tamil government certificate into a verified ownership graph — and tells a property lawyer, for the first time, whether the evidence in her hand can support the opinion she is about to sign.**

## Product

TitleChain ingests a Tamil Nadu **Encumbrance Certificate** (EC) — a multi-page, Tamil-script government table listing every registered transaction on a property — and returns a title-scrutiny workspace: typed transaction records, an ownership/encumbrance graph, a ranked findings list, per-finding source crops, a readiness gate, and, when the certificate falls short, a **pre-filled order for the exact replacement certificate to buy**.

Built for property advocates and bank-empanelled lawyers who perform pre-sale and pre-mortgage title scrutiny — the people banks rely on before lending crores against a plot. AI does the reading; deterministic code does the deciding. That boundary is the product.

## Problem

Title scrutiny is a 13-to-30-year search performed by the most expensive person in the transaction, with a highlighter, at the end of a long day. Three failure modes recur, and all three are *mechanical* rather than intellectual: a cancelled instrument read as a live encumbrance; a party name spelled two ways hiding a real break in the chain; and — the expensive one — **parent-document pointers that lead to years the certificate never covered, with nothing on the page announcing it**.

That third failure has no text to read. It is a computation over what the document *omits*. Faster document retrieval doesn't touch it; you receive the same unread table, sooner. Generic LLM summarisation makes it worse, because a confident narrated conclusion about an encumbrance is more dangerous than no answer. The cost lands on the buyer, five to ten years later, at foreclosure.

## AI Solution

The core reframe: **an EC is not a document to read, it is a partially-observed graph to reconstruct.** Every entry carries an explicit parent pointer (*PR Number* / முந்தைய ஆவண எண்) that nobody assembles. Following those pointers makes a previously uncomputable question computable — *does this certificate's window actually reach the chain it claims to verify?*

- **Multimodal document intelligence** — Sarvam Vision reads Tamil-script tables as structure, not text, returning per-block bounding boxes, layout tags and reading order. Verified at **98.6% field fidelity (69/70 ground-truth anchors)** across 12 pages of real certificates *before* a line of product code was written.
- **Constrained LLM extraction** — `sarvam-105b` at `temperature=0`, fixed seed, strict `json_schema`, prompted explicitly as **"transcriber, not analyst."** Unreadable cell → honest `null`, never a plausible guess.
- **Deterministic decision layer** — a 10-rule title rulebook runs as pure, unit-tested Python. **No model call happens inside it.** Every legally sensitive verdict is explainable by citing a rule and its evidence.
- **Evaluation-driven uncertainty net** — the vendor's confidence score was *measured* to be layout confidence, not cell fidelity: a **0.96-confidence block silently dropped three date cells**. So the safety net is ours — schema completeness, plus the certificate's own declared entry count as a free checksum.
- **Human-in-the-loop by design** — every finding clicks through to a pixel crop of the source cell; corrections persist, stay attributed, and **re-derive the graph**; the product evidences and never opines. The signature stays human.

## Product Architecture

```
Advocate ─► Upload EC ─► ① Sarvam Vision (ta-IN)      pixels → tables + bboxes + reading order
                         ② sarvam-105b, strict JSON    structure → typed records  (30b fallback)
                         ▼ ─────── the boundary that matters ───────
                         ③ derive()  OUR CODE, NO MODEL   graph · 10-rule rulebook · gates
                         ▼
   Workspace ◄── ranked findings · ownership graph · coverage ruler · source crops
        │                                                    ▲
        └── correction / review ──► re-derive ──► persist ────┘   (SQLite, attributed)
                         ▼
   Insufficient window ─► pre-filled next-EC order ─► merge new certificate into the same case
```

Three design rules hold the system together: **the model is never asked for its own provenance** (source is attached from the block that was sent, so a hallucinated block id isn't a value the model may write); **five-valued rule outcomes** — FAIL / REVIEW / PASS / NOT_APPLICABLE / NOT_EVALUABLE — so "passed" and "never ran" can never be confused; and **the product refuses rather than fabricates**, both for non-certificates and for cost figures it lacks a real rate card to compute.

## Impact

**Measured**

| | |
|---|---|
| Field-anchor fidelity on real Tamil certificates | **98.6%** (69/70 anchors, 12 pages, 3 inputs: 96% / 100% / 100%) |
| Cost to process a certificate | **≈ ₹0.5/page — under ₹5 per EC**; a 12-page run ≈ ₹6 |
| Turnaround | **≈ 60 s for 12 pages**, against a 2.5–3 h manual read |
| Rules shipped | **7 of 10** implemented; the other 3 ship as explicit `NOT_EVALUABLE` with a stated reason rather than a silent pass |
| Regression coverage | **117 tests**, CI-gated on every PR (pytest + typecheck + build + deploy-route assertion) |

**The number that did not previously exist.** TitleChain computes an *evidence-sufficiency rate* — the share of title opinions written on a certificate that actually covers the chain it was ordered to verify. Nobody knows this figure for any bank in any district, because nothing computes it. Across the real corpus, **3 of 4 evaluable certificates could not support the search they were ordered for.** Stated precisely, because the precision is the credibility: those chains were *unverified*, not those titles *bad* — and the one clean certificate matters as much as the three, because a detector that fires on everything is a broken detector.

**Modelled (assumption-based, with the register published in the repo).** Under stated assumptions on advocate time and reduction rate, EC reading and chain assembly drop from ~2.5–3 h to 30–60 min of *review* — ~2 h/file, ~40% of total scrutiny effort, holding at ~30% at the pessimistic end. Unit economics are the strong half of this: **~98% gross margin at a ₹200–500 per-file price against a ₹3,000–15,000 professional fee.** These are labelled assumptions in `PROBLEM_AND_VALUE.md`, not measurements, and are presented as such.

## Scale

**5 real Encumbrance Certificates · 4 sub-registrar offices · 3 districts · 2 TNREGINET layout generations** — a corpus deliberately sourced from public regulatory filings to kill a formatting-overfit risk the PRD itself had flagged. It includes a **certificate with no extractable text layer at all** (`pdftotext` returns zero characters — any pipeline that shortcuts to text extraction fails outright), a certificate whose **search period field is blank**, a **two-certificate bundle** where a "Nil EC" reads clean while covering five weeks of a chain running back to 1961, and a **negative case** the product must refuse rather than hallucinate entries from. Deepest chain in the corpus spans **1964 → 2023**.

The build: **~5,300 lines of production Python**, a React/TanStack front end, **93 commits across 33 reviewed PRs in under two weeks**, deployed to Render behind Vercel with health checks, CORS, and CI that fails the build if the deployment routes stop pointing at the backend.

## AI / Technology Stack

**AI / ML** — Sarvam **Document Intelligence** (Vision) for Tamil-script layout-aware digitisation with bounding-box provenance · **`sarvam-105b`** for schema-constrained extraction (strict `json_schema`, `temperature=0`, fixed seed), **`sarvam-30b`** as fallback rung · **Transliteration API** (`ta-IN→en-IN`) for cross-script party-name normalisation · a **six-rung escalation ladder** (reasoning-effort → seed variants → model downgrade → prompt shedding) engineered against *measured stochastic truncation*.

**Product / Application** — FastAPI (single process, background pipeline with live status polling) · Pydantic v2 as the **single schema source** — one definition generates the LLM's `response_format`, validates the reply, and types the rules and the UI, making prompt/code drift structurally impossible · React + TanStack Start + Vite + shadcn/ui (v2 front end; v1 shipped as Jinja + HTMX).

**Data / Infrastructure** — SQLite (cases, entries, parties, edges, findings, corrections, reviews, API-call ledger) · `pypdfium2` + Pillow for pixel-exact source crops at the same 3509×2480 raster Sarvam digitised, so coordinates land **with no transform** · disk-cached digitisation and extraction so a re-upload is free and the demo survives a total API outage · Render + Vercel.

**Observability / Operations** — per-API-call ledger (model, ladder rung, tokens in/out, latency, cache hit) feeding a per-case unit-economics panel that reports **units only until a real rate card is configured** · explicit `finish_reason` and truncation detection · GitHub Actions CI: pytest, TypeScript typecheck, production build, deployment-route assertion.

**Product & Delivery** — PRD with a published assumption register and evidence map · stack decision record · pipeline and architecture docs · customer-journey and problem/value analyses · UX redesign spec with a decision log · 90-second and 3-minute demo scripts.

## Product Decisions

- **Models read, code decides.** Every judgment a lawyer carries liability for is deterministic Python, not model output. This costs automation coverage and buys explainability, unit-testability, and the ability to say *"this evidence is insufficient"* — a sentence a summariser structurally cannot produce, because it does not know what it was not given.
- **Build the uncertainty net rather than buy it.** The vendor ships a confidence score; measurement proved it cannot catch a dropped cell inside a high-confidence block. Trusting it would have been the cheap decision and the wrong one.
- **Ship 7 rules honestly instead of 10 vaguely.** R5–R7 return `NOT_EVALUABLE` with a written reason. A checklist that cannot distinguish "passed" from "never ran" is worse than a shorter checklist.
- **Readiness is a gate list, never a percentage.** Chain completeness ships as unweighted arithmetic (`examined ÷ named`) precisely because a weighted score invites *"how did you compute 82%?"* — and there is no 82% of a signature.
- **Refuse rather than fabricate — including about ourselves.** The cost panel reports pages, calls and tokens and renders no rupee figure at all until an operator supplies real rates. A fabricated unit cost would be the one invented number in a codebase that refuses them everywhere else.
- **Optimise for the moat, not the model.** Model quality is purchasable by any competitor tomorrow. The rulebook, the correction memory and the party-name graph compound with every file — so build time went there, and the front end was deliberately cut to HTMX in v1 to protect it.
- **Answer bad news with a next action.** "This certificate is insufficient" is a dead end; the pre-filled replacement order with computed SRO, village, survey numbers and date range — and a merge path that folds the new certificate into the same case — turns a blown deadline into a same-day fix.

## My Role

Sole product owner and builder: problem discovery through shipped, deployed product.

I chose the domain and the wedge, wrote the PRD and the assumption register, and **de-risked the hardest technical dependency with an empirical kill test on real certificates before committing to the idea** — which is what surfaced the finding that reshaped the whole architecture (vendor confidence ≠ cell fidelity). I defined the AI/deterministic boundary as a product-integrity rule, specified the 10-rule rulebook and its five-valued outcome model, designed the human-in-the-loop review workspace and correction-propagation loop, and sourced the certificate corpus specifically to attack a formatting-overfit risk my own PRD had named as a weakest link.

I made the prioritisation calls under a hard clock — a written cut order fixed in advance, with `rulebook.py`, source crops, correction propagation and the order block declared uncuttable — resolved five documented conflicts between a redesign request and prior product principles without silently dropping either, and drove delivery through 33 reviewed PRs to a deployed application with CI gates and a demo narrative.

## Resume Bullets

- **Defined and shipped an AI-native title-scrutiny product** that converts multi-page Tamil-script government certificates into a verified ownership graph with per-finding pixel-level provenance — validating the core capability at **98.6% field fidelity (69/70 anchors)** on real documents *before* committing to the roadmap, and shipping **117 CI-gated tests** across ~5,300 lines of production Python in under two weeks.

- **Architected a hybrid AI system on the principle "models read, code decides"** — vision-based document intelligence and schema-constrained LLM extraction (`temperature=0`, strict `json_schema`, fixed seed) feeding a **deterministic 10-rule decision layer that no model touches** — making every legally consequential verdict explainable, unit-testable, and defensible to a professional carrying liability for it.

- **Identified a product opportunity invisible to the market**: certificates routinely fail to cover the ownership chains they are ordered to verify, and nothing computes it. Productized the check into an evidence-sufficiency verdict with a pre-filled replacement order — finding that **3 of 4 evaluable certificates could not support their own search**.

- **Engineered AI reliability as a product surface, not a hidden implementation detail** — designing a three-signal uncertainty net after measuring that the vendor's confidence score silently missed dropped cells inside a 0.96-confidence block, a **six-rung model escalation ladder** against stochastic truncation, and a **five-valued rule-outcome model** so users can never confuse "passed" with "never ran."

- **Designed the human-in-the-loop review workflow** where every AI-derived finding clicks through to a pixel-exact crop of its source cell and every advocate correction persists, stays attributed, and re-derives the graph — converting reviewer effort into compounding system memory while keeping professional sign-off with the human.

- **Drove unit economics and delivery end to end**: **sub-₹5 per-certificate processing at ~60-second turnaround** (~98% modelled gross margin at a ₹200–500 price point), instrumented with a per-call token/latency/cache ledger that reports units rather than fabricating a rupee figure without a configured rate card.

## Why This Demonstrates AI PM Capability

- **AI product thinking, not AI feature thinking.** The differentiated value isn't extraction — it's a question AI made computable for the first time (*is this evidence sufficient?*) and a next action attached to the answer. Extraction is table stakes and is treated that way.
- **Technical fluency deep enough to make the hard calls.** Structured-output constraints, reasoning-token budgets, seed/temperature determinism, model fallback ladders, provenance binding and eval design were product decisions I specified — including deliberately drawing the automation boundary *short* of where the model could have reached.
- **Evaluation-first instinct.** The capability was measured against human-read ground truth before the roadmap existed, and the single measured failure — not the vendor's marketing — determined the safety architecture.
- **Judgment about what not to automate.** Legally consequential verdicts stay deterministic; three rules ship as honest abstentions; the signature stays human. The product evidences and never opines.
- **Commercial literacy with intellectual honesty.** Measured unit economics and a real defensibility thesis (rulebook, correction memory, name graph — none of it the model), with every soft assumption labelled as an assumption in a published register rather than dressed up as a measurement.

## Project Link

**https://github.com/bsraavan-lab/TitleChain** — full PRD, stack decision record, pipeline and architecture docs, assumption register, real certificate corpus, and demo scripts included. Built for the Sarvam Epoch Buildathon, Document Intelligence track.
