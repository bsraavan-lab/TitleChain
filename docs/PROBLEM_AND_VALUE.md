# The Problem, Explained From Zero — and What It's Worth

**TitleChain · Sarvam Epoch Buildathon**
Companion to [PRD.md](PRD.md) §3 (Problem) and §4 (Business Value), and to
[CUSTOMER_JOURNEY.md](CUSTOMER_JOURNEY.md).
Assume the reader has never heard of an Encumbrance Certificate. Version 1.0 · 26 Jul 2026.

---

# Part 1 — The problem, for someone with no background

## 1.1 What is actually happening today

Someone is buying a property. Before a bank lends against it — or before a careful buyer
pays — somebody has to answer one question:

> **Does the seller actually own this, cleanly, and has anyone else got a claim on it?**

India has no register that answers that question directly. There is no file you can open
that says "this land belongs to X, free of claims." What exists instead is a **register of
transactions**: every time a property is sold, mortgaged, gifted, leased, partitioned or
released, that deed is registered at a Sub-Registrar's Office and gets a number and a date.

So the only way to answer "who owns this" is to **reconstruct it** — read the transactions in
order and work out where the property ended up.

To do that you buy a document called an **Encumbrance Certificate (EC)**.

> **The intuition: an EC is a bank statement for a piece of land.**
> You name a date range and a survey number, you pay, and the state prints every registered
> transaction on that plot between those two dates. One numbered row per transaction: who
> gave, who received, what kind of deed, dates, values.

Now the three details that make this hard, and none of them are obvious:

**One — you must choose the date range before you know anything.**
Not the bank's choice, not the state's. The advocate picks it, up front, blind. The law says
go back 13 years; careful practice says 30. Whatever they pick, that's what they get, and
everything downstream inherits that guess.

**Two — the rows point at each other, and at rows you didn't buy.**
Each entry carries a field called the **PR Number** — literally *"previous document number."*
It is the row saying: *"the property came to me through document 1464 of 1961."* That is a
pointer to a different transaction, and often to a **year outside the range you paid for**.

**Three — nothing tells you when a pointer leads off the edge of the page.**
The certificate is not wrong. It answered exactly the question it was asked. It simply has no
way of saying *"by the way, the story starts before the window you chose."*

So a real advocate reads a dense 3-to-40 page Tamil table, on paper, with a highlighter,
sketches the chain of ownership on the file cover, and eventually stops — because she has
read the last row — and signs her name to an opinion the bank will lend crores against.

**This is what today looks like. A human doing a database join, from memory, on paper,
under a deadline, once per file, and throwing the result away afterwards.**

## 1.2 Why this is frustrating

Not because it's slow. Tedium is annoying, not frightening. It's frustrating for a sharper
reason:

> **You cannot tell whether the answer you got is complete.**

Think of searching your email for a receipt, but the search box only accepts a date range you
have to guess, charges you each time, and takes three days to return. Now: **"no results" and
"you searched the wrong years" look identical.** That's the situation. A clean certificate and
a useless certificate are the same object to the naked eye.

Three consequences follow, and they compound:

| | |
|---|---|
| **The finish line is fake** | She stops when she's read every row. But *reading every row* and *verifying the chain* are different achievements, and nothing in the workflow distinguishes them. |
| **Attention is the safety system** | Row 5 gets sharp attention. Row 40 gets tired attention. The cancelled mortgage is in row 40. The failure mode is human, predictable, and unmanaged. |
| **The feedback loop is 5–10 years long** | Nothing comes back after signing. If she was wrong, it surfaces at resale or foreclosure — by legal notice. She never learns which files were fine and which were luck. |

And she knows all of this. The anxiety at the signature isn't *"did I misread a row."* It's:

> **"Was the document I was given even capable of answering the question I was asked?"**

That question is asked on every file and answered on none, because **nothing in existence
computes it.**

## 1.3 "Why not just use Google Translate, or OCR it?"

This is the correct instinct and it fails at five distinct layers. Each one alone would sink
it; they stack.

**Layer 1 — There is no text to translate.**
The certificate arrives as a scan. A picture of a table. Translation tools need text; there
isn't any. So you need OCR first, which brings you to layer 2.

**Layer 2 — In a table, the grid *is* the meaning.**
Generic OCR reads a page as a stream of words. But "1464/1961" is only meaningful because it
sits in the *PR Number column* of *entry 7*. Drop it one row and you've asserted a false fact
about a different transaction. Indic-script table OCR — where column boundaries, reading order
and Tamil glyphs must all survive together — is genuinely hard, and it's the specific thing
that was not reliably available until recently. (This is the capability Sarvam's Document
Digitization now provides, and the reason this product is buildable in 2026 and wasn't in
2020 — measured, not assumed: [PRD §0.2](PRD.md), 69/70 ground-truth anchors intact across
real certificates.)

**Layer 3 — Legal Tamil is not conversational Tamil.**
A general translator will happily render *கிரய பத்திரம்* (sale deed), *விடுதலை பத்திரம்*
(release deed) and *அடமானம்* (mortgage) into overlapping English mush — "deed," "transfer,"
"document." Those distinctions *are* the legal effect. A tool that collapses "mortgage
discharged" and "sale cancelled" into one English phrase hasn't helped; it has manufactured a
confident error where there was previously an honest gap.

**Layer 4 — Perfect translation still hands you an unread table.**
Suppose all of the above works flawlessly. You now have the same 40-row table, in English.
The advocate's job was never *reading*. It was **cross-referencing** — row 31 cancels row 12;
rows 7, 19 and 26 are the same person spelled three ways; row 4 points at a document you don't
have. Translation is a per-row operation. The work is a whole-document operation.

**Layer 5 — the decisive one. The answer she needs is not written anywhere in the document.**

> "Does this certificate cover the chain?" is not a sentence on any page.
> It is a **computation**: the date range in the header, compared against every
> parent-document pointer in the body.

You cannot translate your way to it, summarise your way to it, or OCR your way to it — because
**it is a property of what the document omits**, and omissions have no text. This is also
precisely why a general-purpose LLM is the wrong tool and a dangerous one: asked "is this title
clear," it will produce a fluent answer, with no rulebook, no provenance, and no ability to say
*"this certificate is structurally incapable of telling you."* A confident wrong answer about an
encumbrance is worse than no answer.

## 1.4 The underlying bottleneck

Strip away the language, the scanning and the tedium, and one sentence is left:

> **The state records the edges of a graph, and publishes only disconnected slices of it.**

The PR Number is a foreign key. It has been sitting in every certificate for decades. The
registry writes it faithfully and **never once follows it.** There is no traversal, no join, no
index of "which documents point to which." The graph exists in the data and nowhere else.

So every traversal in Tamil Nadu is performed:

- **by hand**, by the most expensive person in the chain;
- **from scratch**, per file, with no reuse of anyone's previous traversal;
- **without a completeness check**, because a human reading rows has no way to compute coverage;
- **and then discarded.** The chain she sketched on the file cover dies with the file.

That is the bottleneck. Not access — Landeed and others solved *access* years ago, and it
didn't help, because they hand you the same unread table faster. Not translation. Not OCR.
**The bottleneck is that nobody follows the pointers, and nobody checks whether the evidence
in hand can reach them.**

Which reframes the whole product in one line:

> **The link was always in the document. The product is the traversal, and the verdict on
> whether the evidence reaches far enough.**

## 1.5 Why users are effectively "locked in"

This is the part people from a software background get wrong. Nobody *chose* this ecosystem,
so nobody can leave it. The lock-in is **statutory, not commercial** — five layers deep:

| Lock | What it means | Can a user route around it? |
|---|---|---|
| **The record is a state monopoly** | Registration is a sovereign function. The Sub-Registrar's record is the only record with legal standing. | **No.** There is no competing title dataset in India that a court or bank will accept. You cannot buy better data; better data does not exist. |
| **The output format is fixed** | The state sells *certificates for a window*. There is no query interface, no chain view, no bulk feed, no "show me every document referencing 1464/1961." | **No.** You get the artifact the state prints, in the state's layout. |
| **The window must be pre-purchased** | Each certificate costs money and days. You can't just fetch everything and filter later. | **No.** Guessing the range is structurally forced. |
| **The language is the record** | The authoritative certificate is in Tamil. An English rendering has no legal standing — it is a convenience, not a document. | **No.** The Tamil artifact must remain the source of truth, which is why fidelity and provenance-to-source matter more than fluency. |
| **The workflow is mandated downstream** | Banks require an advocate's title opinion, written on these certificates, before disbursing. Courts weigh the same artifacts. | **No.** Even a superior private process must terminate in this artifact. |

Two conclusions fall out of that table, and they are the two most important strategic facts
about this product:

**For the user:** there is no exit. Not a slow migration or an expensive switch — *no exit
exists.* Every property advocate in Tamil Nadu will read certificates in this format, in this
language, bought in this way, for the foreseeable future. Their pain is not a preference to be
churned out of.

**For the builder:** nobody can bypass the format either. There is no clever startup that
replaces the EC — the state would have to. So the entire competitive game is played on
**interpretation**, not on access or replacement. That is the durable ground, and it is where
the moat is deliberately placed ([PRD §4.5](PRD.md)): the rulebook, the correction memory, the
name graph. Not model quality, which anyone can buy tomorrow.

---

# Part 2 — Business value

*Same discipline as [PRD §4](PRD.md): claims are graded. **Measured** = observed in our own
runs on real documents. **Assumed** = stated as an assumption with a verification route.
**Context** = order-of-magnitude only, not to be defended.*

## 2.1 Why solving this matters

Three reasons, in ascending order of importance.

**1. It returns expensive hours.** ~2 hours per file, ~40% of the scrutiny effort *(Assumed:
A1/A2/A6 — verification route is a timed A/B with practising advocates).* Real, defensible,
and the least interesting thing here.

**2. It moves the moment of discovery.** Today a title defect surfaces 5–10 years later, at
resale or foreclosure — the most expensive possible moment, when the property is illiquid, the
loan is impaired and the remedy is litigation. TitleChain surfaces the *evidence gap* **before
the signature**, when the fix costs one more certificate and a few days. The operational metric
isn't hours saved. It's **time-to-defect-discovery, moving from years to minutes.**

**3. It creates a number that does not currently exist.**

> **Evidence-sufficiency rate** — the share of title opinions written on a certificate that
> actually covers the chain it was ordered to verify.

Nobody knows this number, for any bank, in any district, because nothing computes it. Across
our real sample *(Measured — five certificates, four SROs, three districts, all obtainable
from public filings)*:

| Certificate | SRO | Window | Sufficient? |
|---|---|---|---|
| `ec2_pacollege` | Pollachi | 2018–2023 | **No** — 5 parents 2005–2011 |
| `ec3_rera` | Pollachi | — | **No** — parents outside |
| `ec4_erumaipatti` | Erumaipatti | 1975–2024 | **Yes** — all 3 PR edges resolve inside |
| `ec5_adyar` | Adyar | 7 months | **No** — ~10 parents back to 1961 |
| `ec6_thiruchengode` | Thiruchengode | blank | Not evaluable |

**Three of four evaluable certificates could not support the search they were ordered for.**

Stated precisely, because the precision is the credibility: this means those chains were
**unverified**, not that those titles are **bad**. Four is not a base rate. But it is checkable
by anyone who opens the PDFs, it needs no assumption about fees or hours, and the clean case
matters as much as the three — a detector that fires on everything is a broken detector.

## 2.2 Who benefits

Ordered by how directly the value lands.

### Lawyers — the primary beneficiary and the buyer

*Advocate Meena, property advocate, Coimbatore. 8–15 scrutiny files a month.*

- **Operational:** ~2 h/file back → **16–30 hours a month, roughly 2–4 working days** *(Assumed)*.
- **Professional:** the thing she cannot buy today — a defensible record of what was checked,
  what was verified, what could not be, and what she did about it. Her name is on the opinion;
  this is the first tool that protects it.
- **Commercial:** capacity to take more files without hiring, and a differentiator when a bank
  panel compares empanelled advocates.

The value that closes the sale is not the time. It is that the **"what this search does not
cover"** section converts her largest unmanaged liability into documented diligence.

### Banks and lenders — the scale beneficiary and the second payer

*Credit Manager Ravi, nationalised bank, Salem.*

Today he **cannot evaluate a scrutiny report at all.** He trusts the empanelled advocate
completely and finds out about defects at foreclosure. He receives:

- a structured, evidence-linked chain instead of a prose opinion;
- an explicit statement of what the search did not cover;
- for the first time, a **portfolio-level quality metric** — evidence-sufficiency rate by
  advocate, by district, by SRO.

Banks already fund this work through empanelment fees and hold the residual risk. That
combination — pays already, bears the loss, can mandate — makes them the natural second payer
and the fastest route to scale: **one bank mandating this across its panel puts it on every
file in a district.**

### Property buyers — bear the entire downside, see none of the tool

*Buyer Karthik.* He pays for the scrutiny, inherits 100% of the risk, and has no ability to
evaluate what he received. He benefits **through** his advocate, not directly. Deliberately out
of scope for v1 — buying property is a once-a-decade event, so there's no habit to build, no
trust to trade on, and no repeat purchase. He is the reason the product matters and the wrong
person to sell it to.

### Citizens more broadly — real, but do not lead with it

Beyond individual buyers, the diffuse benefit is that title uncertainty is a tax on everyone
who owns land: it depresses collateral value, blocks small-holder credit, and feeds a large
share of civil litigation. The commonly cited figures here (land disputes as a majority of
Indian civil cases; large capital sums locked in land conflict) are *Context only* — widely
repeated, not verified by us, and **not to be defended in a demo.** The honest citizen-level
claim is narrower and stronger: *fewer opinions written on evidence that doesn't reach.*

### Government agencies — a beneficiary, not a v1 customer

The Registration Department and IGRS get something they currently have no way to produce: a
measurement of how well their own certificates serve the purpose they're bought for. A
district-level distribution of window-insufficiency is a policy input — it argues for changing
the default search window, or for surfacing parent-document reachability on the certificate
itself. Genuine value; procurement cycles measured in years. **Not the wedge.**

### Digitization initiatives — the strategic fit

Programmes like DILRMP and the state registration portals have spent a decade converting paper
into **images and PDFs**. That work is largely done, and it produced exactly what we consumed:
scanned, native-script, structured-but-unstructured certificates.

> **Scanning was the first half. Nobody did the second half.**
> A scanned table is still not data. The semantic layer — typed entries, resolved parties,
> followed pointers — was never built, and it is the layer every "conclusive titling" ambition
> silently depends on.

TitleChain runs *on the output those programmes already produced*, and emits a machine-readable
title graph with provenance back to the source crop of the source certificate. It doesn't
compete with digitisation; it is the missing layer on top of it, built bottom-up from documents
transactions already generate.

## 2.3 Who would pay

| Payer | Willingness | Why | Timing |
|---|---|---|---|
| **Advocates / property law firms** | **High** | Direct time return, direct liability reduction, price is a rounding error against the fee | **Day 1** |
| **Banks (legal vetting / retail credit)** | **High** | Already funds this; holds the residual risk; can mandate across a panel | Wedge is the advocate; bank is the multiplier |
| **Bank legal-vetting vendors** | Medium | Labour-arbitrage businesses whose margin is exactly the hours we remove | Follows the bank |
| **Buyers (direct D2C)** | Low | Once-a-decade purchase, no trust, no repeat | Not a market |
| **Government / IGRS** | Medium value, **very slow** | Real policy value, multi-year procurement | Not v1 |

**Unit economics** *(Measured on real runs)*: processing cost per certificate is **under ₹5**
— ₹0.5/page over 3–6 pages, plus negligible LLM tokens; a 12-page certificate runs ~60 s for
about ₹6. At a per-file price of **₹200–500** that is ~98% gross margin, against a professional
fee of ₹3,000–15,000 per scrutiny *(Assumed: A3)*. The customer's ROI needs no spreadsheet: one
file pays for itself in the first twenty minutes it saves.

## 2.4 Economic and operational impact

**Per file** — *Assumed (A1/A2/A6), pessimistic case stated*
EC reading and chain assembly: 2.5–3 h → 30–60 min of *review*. ~2 h saved, ~40% of total
scrutiny effort. Even at the pessimistic end of A6 (60% reduction) it's ~1.5 h, ~30% — which
still clears the rubric's L5 bar for movement on an operating metric.

**Per advocate** — *Assumed*
8–15 files/month → 16–30 h/month → **2–4 working days a month returned**, or the same headcount
absorbing ~40% more files.

**Per certificate, machine side** — *Measured*
≤90 s for a ≤10-page certificate, under ₹5. Versus 2.5–3 h and a highlighter.

**Time-to-defect-discovery** — *Measured mechanism, unmeasured base rate*
5–10 years (foreclosure/resale) → **before signature**. The mechanism is deterministic: header
window versus every PR pointer. What we don't know is how often it fires in the wild — 3 of 4
in our sample, which is a signal, not a rate. *(Verification: A7 — sufficiency audit over a
bank's existing scrutiny file archive. This is also the highest-value first pilot, because it
produces the number and sells the product with the same run.)*

**Rework avoided** — *Design claim*
A discovered gap is only useful if it comes with an action. The pre-filled replacement-EC order
(SRO, village, every survey number, computed date range — all reassembled from the certificate
in front of her) converts "your evidence is short" from a blown SLA into a same-day order.
Without it, the product ends on bad news with no next step.

**Market size** — *Context only, stated last and deliberately*
Under A4/A5 (TN registrations order 10⁶–10⁷/yr; 30–50% loan- or diligence-backed), at ₹200–500
per file, Tamil Nadu alone is plausibly ₹10²–10³ crore. **This is the least reliable number in
this document and the least important.** Defend §2.1 and §2.4; TAM is context.

## 2.5 What this does not claim

Stated because the boundary is what makes the rest credible.

- **It does not detect what the registry never wrote.** An unregistered claim, or an entry the
  SRO omitted, is invisible to every reader including us. *R. Ravichandran* was a certificate
  **wrong about its contents**; TitleChain catches the adjacent and more common defect — a
  certificate **right about what it contains and silent about what it omits by design.**
- **It does not establish title, and it never opines.** Every finding is deterministic and
  cites its source crop. Human sign-off is mandatory. It is an evidence tool.
- **Window insufficiency means the chain is *unverified*, not that the title is *bad*.**
- **v1 is Tamil Nadu, post-1987 computerised registration.** Handwritten pre-computerisation
  records are out of scope — and out of scope by the workflow's own rules, since the bank's
  13–30-year search window sits inside the computerised era.
- **The hour-based numbers are assumptions, not findings.** They are labelled A1–A6 in
  [PRD §4.1](PRD.md) precisely so they can be attacked; the evidence-sufficiency argument is
  the one that stands without them.
