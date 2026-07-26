# Customer Journey — Before and After

**TitleChain · Sarvam Epoch Buildathon**
Companion to [PRD.md](PRD.md) §5 (Personas), §6 (User Journey), §4 (Business Value).
Worked against real certificates in [`ec_samples/`](ec_samples/README.md). Version 1.0 · 26 Jul 2026.

**Persona anchor:** *Advocate Meena* — property advocate, Coimbatore. 15 years' practice,
empanelled with two nationalised banks, 8–15 scrutiny files a month. She is the buyer, the
user, and the person whose name goes on the opinion.

---

## The short version

| | Today | With TitleChain |
|---|---|---|
| What she does | Reads every row | Reviews flagged findings against source |
| Time on EC reading + chain assembly | 2.5–3 h of a 5 h scrutiny | 30–60 min |
| How she knows she's finished | She has read the last row | The certificate's coverage has been computed |
| Can she tell if the EC covers the chain? | **No — nothing computes this** | Yes, deterministically |
| What she does when evidence is short | Usually doesn't know it is | Orders the exact replacement certificate, pre-filled |
| When she learns she was wrong | 5–10 years later, by legal notice | Before she signs |

The headline is not the time. It is row 4: **a question that cannot be answered today becomes
answerable.**

---

## BEFORE — the journey today

Nine stages. The middle is tedious; the end is where the risk actually sits.

### 1 · Instruction
Bank or client sends the file. SLA clock starts (typically 3–7 days). One of 8–15 this month.

### 2 · She chooses the search period
The first hidden decision, and nobody audits it. 13 years statutory, 30 if she is careful.
**She is deciding how much history to buy before she knows anything about the property.**
Everything downstream inherits this choice, and nothing later revisits it.

### 3 · The wait
Dead time. Order placed on TNREGINET or at the SRO.

### 4 · The certificate arrives
A dense Tamil table. Could be 3 pages, could be 40. One numbered entry per registered
transaction: document number and year, three dates, nature of deed, executants, claimants,
volume/page, consideration, market value, **PR Number**, remarks, and property schedules.

### 5 · The read — 2.5 to 3 hours
Printout, highlighter, chain sketched on the file cover. Linear, row by row.
Attention is sharp at entry 5 and dull at entry 40 — and entry 40 is where the cancelled
mortgage sits.

### 6 · Scattered doubt moments
Not one big moment, but dozens of small ones:
- *Is this the same person, spelled differently?* (`(முத.)` / `(முக.)` markers, initials, honorifics)
- *Was this mortgage ever discharged?*
- *What is document 1085/1992 that this row points to — do I even have it?*
- *Did the survey number change legitimately, or is that drift?*

Each is resolvable with effort. Collectively they are unresolvable with attention alone.

### 7 · She decides she is finished
**No signal tells her this.** She stops when she has read every row.
Reading every row and verifying the chain are not the same thing, and nothing in the
workflow distinguishes them.

### 8 · She signs
The opinion goes out with her name on it.

### 9 · Silence
Nothing comes back. If she was wrong, it surfaces in 5–10 years — at resale or foreclosure,
by legal notice. The most expensive possible moment, and far too late to fix.

### The emotional arc

```
  mild dread ──► fading attention ──► scattered doubt ──► ANXIETY AT SIGNATURE ──► unresolved residue
   (stage 1)        (stage 5)            (stage 6)             (stage 7–8)              (stage 9)
```

The anxiety at signature never resolves. It gets buried, and it accumulates across
8–15 files a month for fifteen years.

---

## The friction moment

Not the reading. Tedium is not fear.

The friction is the transition from **stage 7 to stage 8** — the moment she converts

> "I have read everything in this document"

into

> "this title is clear."

**Those are different statements and she knows it.** The gap between them is exactly the size
of what the certificate did not cover. Nothing in her workflow measures that gap, so she
signs across it.

Stated precisely, the fear is **not** *"did I misread a row."* It is:

> **"Was the document I was given even capable of answering the question I was asked?"**

**What a trusted human does here.** A senior partner glances at a junior's file and asks two
questions: *"What's the parent document?"* and *"Does your EC period reach it?"* That instinct
is the entire expertise being encoded. It is not reading skill — it is **sufficiency skill**.

---

## AFTER — the journey with TitleChain

### 1 · Instruction
Unchanged.

### 2 · She chooses the search period
Unchanged in v1 — but now auditable after the fact, and the product will tell her if the
choice was wrong.

### 3 · The wait
Unchanged.

### 4 · Upload
She drops the PDF into the case file. Sarvam Vision digitises: tables, coordinates, reading
order preserved. ≤90 s for a ≤10-page certificate.

### 5 · Typed rows, not a table
`sarvam-105b` types each entry into a strict schema; transliteration clusters party names
across scripts. Tamil preserved verbatim. **She is no longer the parser.**

### 6 · The rulebook runs — deterministic, ours
Ten checks over the assembled graph. No model decides an encumbrance. Findings ranked
blocking → material → informational, each citing its evidence entries and source crops.

### 7 · The verdict she could not compute
This replaces "she decides she is finished." The product states the certificate's coverage:

> This certificate covers **11-Sep-2023 → 04-Apr-2024**.
> Entry 2 declares **ten parent documents**; the earliest is **1464/1961**.
> **None fall inside this window. This EC cannot support a 13-year search.**

And — equally important — it confirms what *is* verified:

> Three parent links resolve to entries inside this certificate. **Verified.**
> One instrument (2520/2019 Lease) was **cancelled** by 8756/2020 — not a live encumbrance.

### 8 · The next action, pre-filled
The moment she learns the window is short, her next thought is *"so what do I order?"* —
which needs SRO, village, every survey number, and a computed date range, reassembled by
hand from the certificate in front of her. It arrives filled in:

> **Order EC** · Pollachi SRO · Puliyampatti · survey 95/2, 100/3A, 113/1B, 116/A1, 116/B1
> · **01-Jan-1993 → 31-Dec-2017**

### 9 · Continuity
She corrects a party name → clustering, graph and every rule re-derive → the correction
persists, attributed, across restart. Weeks later the earlier certificate arrives; she drops
it into the same case and the chain extends. The report exports with an explicit
**"what this search does not cover"** section.

### 10 · She signs — on a measured basis
Her file now records what was checked, what was verified, what could not be, and what she
did about it.

---

## Worked example — a real document

`ec5_adyar_chennai_bundle.pdf`, obtained from a TN RERA promoter filing. Kotturpuram
(Adyar SRO, Chennai), survey 11/1 and 11/PART. This is not a constructed example.

**What the buyer's side actually received — two certificates:**

| | Coverage | What it shows |
|---|---|---|
| EC (pp. 1–3) | 11-Sep-2023 → 04-Apr-2024 | 2 GPA entries; entry 2 is a **₹2,71,42,000** property declaring ~10 parent documents back to **1464/1961** and **4148/1981** |
| Nil EC (pp. 4–5) | 01-Apr-2024 → 09-May-2024 | Certifies **no encumbrance found** |

**Read today:** the Nil EC says clean. The first certificate is a dense Tamil table with no
extractable text layer. Nothing on either page announces a problem.

**Read with TitleChain:** the two certificates together cover about seven months of a chain
that is sixty-plus years deep. Every declared parent sits outside both windows. The Nil EC is
accurate *and* uninformative — it is true about five weeks and silent about six decades.

This is the *R. Ravichandran* fact pattern in a live document: a purchaser induced by a clean
certificate, where the Madras High Court held the resulting omission **negligence per se**
(see [`ec_samples/README.md`](ec_samples/README.md)).

**Note what the product does not claim.** *Ravichandran* was a certificate that was *wrong
about its contents* — no reader can detect an entry the registry never wrote. TitleChain
catches the adjacent and more common defect: a certificate **right about what it contains and
silent about what it omits by design.**

---

## What changes, and where the value lands

### Delight — the friction moment, answered

Per the rubric, extraction quality scores under Document Intelligence and **cannot be reused
as Delight**; polish and reassuring copy score L2 at best. Delight is earned only at stage 7–8.

| Level | What earns it | Where in the journey |
|---|---|---|
| L4 | Tells the truth without alarming; **reassures only where evidence supports it** | Stage 7 — the coverage verdict *and* the "three links verified" confirmation |
| L5 | Anticipates the next concern; preserves continuity; makes follow-up effortless | Stages 8–9 — pre-filled order, then the case that stays open until the chain closes |

**The reassurance half matters as much as the flag.** A tool that only ever reports problems
becomes noise she learns to skim. `ec4_erumaipatti` is the material for this: three PR edges
resolve cleanly, and the product should say so out loud. The contrast is what makes the
warnings credible.

### Impact — the metric that actually moves

The time saving (~2 h/file, ~40% of scrutiny effort) is the defensible floor, but it rests on
assumptions A1/A2/A6, none yet verified by interview.

The stronger claim, and the one the ladder's *"previously inaccessible outcome"* language
supports:

> **Evidence-sufficiency rate** — the share of title opinions written on a certificate that
> actually covers the chain.

Today that number is unknown and unknowable, because nothing computes it. Across the sample:

| Certificate | SRO | Window | Sufficient? |
|---|---|---|---|
| `ec2_pacollege` | Pollachi | 2018–2023 | **No** — 5 parents 2005–2011 |
| `ec3_rera` | Pollachi | — | **No** — parents outside |
| `ec4_erumaipatti` | Erumaipatti | 1975–2024 | **Yes** — all 3 PR edges resolve inside |
| `ec5_adyar` | Adyar | 7 months | **No** — ~10 parents back to 1961 |
| `ec6_thiruchengode` | Thiruchengode | **blank** | Not evaluable |

**Three of four evaluable certificates could not support the search they were ordered for**,
across four SROs in three districts.

The clean case is what makes this credible — a detector firing 2 of 2 looks like selection
bias; one firing 3 of 4 and staying silent on the fourth looks like measurement.

**State it precisely:** window insufficiency means the chain is *unverified*, not that the
title is *bad*. The defensible claim is about evidence quality — in three of four real
certificates, the advocate would have been opining on a chain the certificate does not cover.
That requires no assumption about fees or hours and is checkable by anyone who opens the PDFs.

### The second beneficiary

**Credit Manager Ravi** (nationalised bank, Salem) today cannot evaluate a scrutiny report at
all — he trusts the empanelled advocate entirely and discovers defects at foreclosure. He
receives a structured, evidence-linked chain report with an explicit statement of what the
search did not cover. Banks already fund this work through empanelment and hold the residual
risk, which makes them the natural second payer and the route to adoption at scale: one bank
mandating it across its panel puts it on every file in a district.

### The beneficiary who never sees it

**Buyer Karthik** bears the entire downside and has no ability to verify. Out of scope for
v1, and the reason the product matters.

---

## Two honest notes

**1. "Aren't you just creating work?"** Expect this question. The verdict tells her the file
needs another certificate, another wait, and a blown SLA. The answer: she is not choosing
between a gap and no gap — **the gap exists either way; she is choosing between knowing and
not knowing.** This is exactly why the pre-filled order is not a nicety. Without it the
product ends without a usable next step, which the rubric scores L1. The pre-fill is what
converts bad news into an action.

**2. Frame the "what this search does not cover" section as hers, not ours.** The same words
can read as the product protecting itself or as the advocate documenting her diligence.
Written as her record — *I checked what I checked, and I flagged what I could not* — it
becomes the thing that protects her name on the opinion, and the thing that makes the report
valuable to Ravi.

---

## Status

Stages 4–10 are **not built** as of this document. PRD §0.3 rates Delight at L2 for exactly
this reason. This document describes the target journey and the evidence supporting it; the
build plan is [PRD.md](PRD.md) §14.
