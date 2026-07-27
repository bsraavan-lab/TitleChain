# The 3-Minute Demo Video — Script and Shot Plan

**TitleChain** · Version 1.0 · 26 Jul 2026
Companion to [PROBLEM_AND_VALUE.md](PROBLEM_AND_VALUE.md), [CUSTOMER_JOURNEY.md](CUSTOMER_JOURNEY.md)
and [FRONTEND_MVP.md](FRONTEND_MVP.md).

Audience: non-technical — prospective customers, investors, business stakeholders.
Tone: modern product launch. Confident, quiet, no hype, no jargon. The product is never
described as clever; it is only ever shown solving something expensive.

Every screen, sentence and number quoted in this script was verified against the running
application on the two seeded sample certificates. Nothing here is aspirational unless it is
in [§6, Gaps](#6-gaps-between-this-script-and-the-built-product), which lists what must be
built before the corresponding scene can be filmed.

---

## 1. Three decisions this script makes, and why

**One — the video never says "AI".** The word appears nowhere in the narration. The product's
credibility rests on the opposite claim: the findings are produced by deterministic code that
cites the pixel it came from, and the app says so on screen (`rulebook v1.0`, "not by a language
model"). Leading with "AI-powered" invites exactly the objection the product is built to survive
— *why would I trust a machine on a question I'm liable for?* We show the arithmetic instead.
Investors read that as defensibility, not modesty.

**Two — there is no traffic-light risk score.** A single red/amber/green badge is the natural
ask, and the product deliberately refuses it: *"A ruler, never a score"*
([FRONTEND_MVP.md](FRONTEND_MVP.md)). A score compresses "this document is silent about six
decades" and "one date cell was blurry" into the same amber dot, and the moment a buyer
disagrees with the score, the product has nothing to fall back on. What we film instead is
stronger and already built — a four-level ladder in plain words (**Resolve · Check · Note ·
Verified**) where every line names its evidence, plus the coverage ruler that makes the risk
visible without asking anyone to trust a number. **If the score is non-negotiable for the
audience, see [§6](#6-gaps-between-this-script-and-the-built-product) — but it costs the film
its best moment.**

**Three — the hero is a buyer; the buyer is not the customer.** The brief asks for language an
average property buyer understands, and that is what this script uses throughout. But the
product is sold to the advocate who signs the title opinion, not to the buyer — buying property
is a once-a-decade event with no repeat purchase ([PROBLEM_AND_VALUE.md §2.2](PROBLEM_AND_VALUE.md)).
So the video is *framed* around the buyer's stake and *demonstrated* on the professional's
screen. Scene 4 makes that turn explicitly in one line. An investor who notices the distinction
should see that we have noticed it too.

---

## 2. The one idea the video has to land

If a viewer remembers one sentence, it must be this:

> **A property document can be completely accurate and still fail to answer the question you
> bought it to answer — and until now, nothing could tell you which one you were holding.**

Everything else in the film is setup or proof for that sentence. Translation is table stakes.
The unlock is that the certificate's own limits become measurable.

---

## 3. Assets to prepare before filming

| # | Asset | Where it comes from | Status |
|---|---|---|---|
| A1 | Pollachi sample — insufficient window, cancelled lease | `POST /sample/pollachi`, runs offline from cache | ✅ ready |
| A2 | Uthukuli sample — insufficient window, **live mortgage** | `POST /sample/uthukuli`, runs offline from cache | ✅ ready |
| A3 | A **clean** certificate that passes | `ec_samples/ec4_erumaipatti_namakkal.pdf` | ⚠️ needs seeding — see [§6](#6-gaps-between-this-script-and-the-built-product) |
| A4 | Raw Tamil EC page for the cold open | Page 1 of `ec2_pacollege.pdf` | ✅ ready |
| A5 | Screen recording at 1440×900, `device_scale_factor=2` | Retina capture; UI is legible at 3 m | ✅ ready |
| A6 | Printed report for the closing shot | `/report/{id}` → print to PDF | ✅ ready |

**Run everything from the seeded samples, not a live upload.** Both cached samples reach the
verdict with no network at all — the demo cannot be broken by a vendor outage, a conference
Wi-Fi drop, or a slow API. Film the real 60-second processing sequence once, separately, and
cut it to length; never gamble on it live.

---

## 4. The script

**Total: 3:00.** Narration is written at ~140 words per minute — an unhurried, confident read.
Each scene carries its word count *and* its slot length, so the timings are real rather than
decorative: **408 words across 177 seconds of scene slots — an average of 138 words per minute,
with the final 3 seconds silent.** No individual scene exceeds 156 wpm, which is the ceiling for a
read that still sounds unhurried. Two holds are load-bearing and must survive the edit: the
three-second pause on the verdict (Scene 6) and the still frame at the close (Scene 13). If the
cut runs long, take the time out of Act I — never out of those two.

---

### ACT I — THE PROBLEM · 0:00–0:30

---

#### Scene 1 · 0:00–0:10 · The question everyone is actually asking

> **Narration** (25 words · 10 s)
> "Before you buy property in Tamil Nadu, one question has to be answered. Does the seller really
> own it? Does anyone else have a claim?"

**On screen.** Black. White text fades up, one line at a time, centred:
`Does the seller really own this?` — hold — then it dissolves into a full-bleed scan of a real
Tamil Encumbrance Certificate (A4), dense with tabular Tamil script.

**Camera / animation.** Slow push-in on the certificate, roughly 4% over the whole shot. No cuts.
The type dissolves *into* the document so the question and the document occupy the same space.

**Key business message.** This is a decision worth crores, and it rests on one document.

**Why this moment matters to the customer.** Nobody wakes up wanting document software. They
want to not be the person who bought a property with a mortgage still attached to it. Opening on
the fear, not the file format, is what earns the next twenty seconds.

---

#### Scene 2 · 0:10–0:20 · Why you can't answer it yourself

> **Narration** (26 words · 10 s)
> "The answer is in here. In Tamil. As a scan. Listing every transaction on the property — but
> only for a date range someone guessed in advance."

**On screen.** The certificate scrolls. A cursor tries to select text and gets nothing — it's an
image, not text. Three callouts land in sequence, each with a soft underline on the region it
points at:
`Tamil only` → `A scan — no text to copy` → `Covers 01-Jan-2018 → 18-Jun-2023`

**Camera / animation.** Locked-off frame; the document moves, the camera does not. The failed
text-selection is a single unbroken take — no cut, or it reads as a trick.

**Key business message.** Three separate walls — language, format, and scope — and the third one
is invisible.

**Why this moment matters to the customer.** The failed text-selection is the whole language
barrier in one gesture, with no explanation needed. And the third callout plants the idea the
film pays off later: *somebody chose that date range, before they knew anything.*

---

#### Scene 3 · 0:20–0:30 · What it costs you today

> **Narration** (25 words · 10 s)
> "So you hand it to a lawyer. Days of waiting, thousands of rupees, hours of reading — and an
> opinion you have no way to check."

**On screen.** Three stat cards fade up over a desaturated shot of a marked-up paper printout:
`3–7 days` · `₹3,000–15,000 per file` · `2.5–3 hours of reading`
The cards fade; one line remains alone on screen:
`And nothing tells you if the document covered enough history.`

**Camera / animation.** Hard cut in from Scene 2 — the rhythm change signals the turn from
*what it is* to *what it costs*. Cards animate in on a 120 ms stagger, no bounce.

**Key business message.** The delay and the fee are the visible cost. The invisible one is that
the work cannot be verified by the person paying for it.

**Why this moment matters to the customer.** Everyone in the audience has paid a professional for
an answer they had no way to evaluate. This names that feeling, then Scene 7 resolves it. Note
the closing line is a *gap*, not a complaint about lawyers — the advocate is the customer, and
the film never makes her the villain.

> **Fact-check.** Days and fees are labelled *Assumed* (A3) in
> [PROBLEM_AND_VALUE.md §2.3](PROBLEM_AND_VALUE.md); reading time is *Assumed* (A1/A2). Show them
> as ranges, exactly as written. **Do not** use national land-dispute or market-size statistics
> anywhere in this film — they are graded *Context only* and explicitly marked *not to be
> defended in a demo*.

---

### ACT II — INTRODUCING TITLECHAIN · 0:30–0:48

---

#### Scene 4 · 0:30–0:48 · The product

> **Narration** (37 words · 18 s)
> "TitleChain reads that document for you. Every transaction, in plain English. It follows the
> trail of ownership backwards — and tells you what no one could tell you before: whether the
> document you're holding goes back far enough."

**On screen.** The Tamil scan slides left and holds at 50% width; the TitleChain case view slides
in from the right against it — same property, same entry, side by side. Logo lockup lands
bottom-left. One line of type:
`Understand property ownership and legal history in minutes — not days.`

**Camera / animation.** A single horizontal slide, 600 ms, one easing curve. This is the only
"product reveal" beat in the film; it should feel like a door opening, not a feature list.
Resist all temptation to add a montage.

**Key business message.** Translation is the entry ticket. The product is the verdict on whether
the evidence reaches far enough.

**Why this moment matters to the customer.** The side-by-side does the persuading before the
narration finishes — same document, one unreadable, one answered. This is also the scene that
quietly makes the buyer/customer turn: the words are the buyer's ("understand a property"), the
screen is the professional's.

---

### ACT III — THE PRODUCT · 0:48–2:34

> **Filming note for the whole act.** This is one continuous session on one case — no jump cuts
> between unrelated screens. The app has exactly one route change in the entire product
> (`/` → `/case/{id}`); everything else fills in on the same page. Let the film inherit that.
> The absence of navigation *is* a product claim.

---

#### Scene 5 · 0:48–1:04 · Upload — *(brief's Flow 1)*

> **Narration** (30 words · 16 s)
> "Drop the certificate in. No typing, no translating, no forms. It reads every page — the Tamil
> tables, the columns, the numbers — and starts filling in the answer while you watch."

**On screen.** The home screen: logo, one dropzone reading **"Drop an Encumbrance Certificate
here."** A PDF is dragged in. The page changes once, to the case view, which is *already
rendered* — bands present, empty, and filling top-down. The status line ticks:
`Reading page 1 of 3` → `page 3 of 3` → `Typing entries into the schema`

**Which file to drag.** Use the Pollachi certificate (3 pages) — it carries both the insufficient
window and the cancelled lease, so Scenes 6–11 all run off one case with no switching. If you
prefer a longer, more impressive read on screen, Uthukuli is 6 pages and has the live mortgage,
but then Scene 9's cancelled-lease beat becomes the cutaway instead.

**Camera / animation.** Follow the file into the dropzone, then hold completely still. Speed-ramp
the processing to about 6 seconds of screen time; overlay a small persistent timestamp
(`0:00 → 1:04`) in the corner so the compression is disclosed rather than faked.

**Key business message.** One action, no setup, no account, no learning curve — and under ₹5 of
processing per certificate.

**Why this moment matters to the customer.** The entire onboarding is one drag. But the real
point is what *doesn't* happen: no "we'll email you when it's ready", no job queue, no screen to
leave. The wait is visible work on the page you'll be reading anyway — so the 60 seconds builds
confidence instead of spending it.

> **Fact-check.** ≤90 s for a ≤10-page certificate, under ₹5 — both *Measured* on real runs
> ([PRD §0.2](PRD.md)). Safe to say out loud.

---

#### Scene 6 · 1:04–1:16 · The verdict

> **Narration** (24 words · 12 s)
> "And here's the first thing it tells you. Not a summary. A warning — this certificate can't
> support the thirteen-year search the law asks for."

**On screen.** The verdict bar lands at the top of the case view, red rule down its left edge,
large type, legible from across a room:
> **▲ This certificate cannot support a 13-year search.**

**Camera / animation.** Push in until the verdict fills the frame. **Hold for a full three
seconds of silence after the narration ends.** This is the longest pause in the film and the most
important one.

**Key business message.** The product leads with the one thing no other tool in the market can
compute.

**Why this moment matters to the customer.** This sentence does not exist anywhere in the
document. It isn't translated, summarised, or extracted — it's the certificate's stated date
range measured against every ancestor document the certificate itself names. It is the moment the
audience realises they were sold a solved problem (translation) when the real one was never
addressed.

---

#### Scene 7 · 1:16–1:34 · The timeline — *(brief's Flow 4)*

> **Narration** (42 words · 18 s)
> "This is the property's history on a timeline. The blue band is what you paid for — five years.
> The red marks are documents this property came through: 2005, 2007, 2011. Every one of them
> sits outside the window. The chain is unverified."

**On screen.** The **Coverage** band. Red ticks above the axis at `2005` `2007` `2011`, a green
tick inside at `2019`, and the blue window band below spanning `2018 → 2023`. Beneath it, the
sentence the app itself renders:
> *It covers 01-Jan-2018 → 18-Jun-2023. 5 parent documents are named, the earliest from 2005.
> None of them fall inside this window.*

**Camera / animation.** Best shot in the film, and it's free: **capture this during live
processing.** The blue band is drawn from the header on page 1, then the red ticks land one at a
time as entries are typed. Don't animate it in post — the real thing is better, and it's true.
Then push in on the gap between the red cluster and the blue band.

**Key business message.** Decades of legal history, and the hole in it, readable in two seconds
without reading a word.

**Why this moment matters to the customer.** The gap between the red marks and the blue band is
the argument, and it lands before any sentence is read. Nobody has to trust us — they can see it,
and check it against the document. That is why it's a ruler and not a score.

---

#### Scene 8 · 1:34–1:52 · Plain English, and proof — *(brief's Flow 2)*

> **Narration** (40 words · 18 s)
> "Everything the document says, in English. Who transferred what, to whom, when, and what kind
> of deed it was. And if you don't believe a line — click it. You get the exact patch of the
> original page it came from."

**On screen.** Scroll to the **Entries** table: `#`, `Document`, `Registered`, `Nature`,
`Executants`, `Claimants`, `Parent docs` — `2520/2019 · 12-Mar-2019 · Lease deed`. Tamil party
names are shown **as they appear in the certificate**, alongside the English. Click **source** on
entry 1. The right-hand pane fills with the cropped image of that exact table cell, captioned
`page 1 · block …_003 · layout confidence 0.95`.

**Camera / animation.** One unbroken take: cursor → click → crop appears. No cut between the
click and the result — a cut here reads as a stitch. Then a slow diagonal push toward the crop.

**Key business message.** Nothing is asserted without the evidence attached to it.

**Why this moment matters to the customer.** Every summarisation tool asks you to trust it. This
one hands you the receipt. And keeping the Tamil visible is not a limitation — the Tamil
certificate is the only document with legal standing; an English rendering is a convenience.
Overwriting the original would be the actual error.

> **Do not say "translation" of names.** Party names are preserved verbatim and clustered across
> scripts. The distinction matters to anyone who has watched a general translator turn
> *sale deed*, *release deed* and *mortgage* into the same English word.

---

#### Scene 9 · 1:52–2:14 · What it catches — *(brief's Flow 3)*

> **Narration** (54 words · 22 s)
> "Then it tells you what to worry about — in order, in plain words. One thing to resolve. Three
> to check. Here's one no human reader should have to catch: a lease that looks live on the page,
> already cancelled by a later deed. And here's the other half — three things it checked and
> confirmed."

**On screen.** The **Findings** band, header reading `1 to resolve · 3 to check · 3 verified`.
Scroll slowly through the real ladder — each line carries a glyph, a word, and a colour, never
colour alone:

| | | |
|---|---|---|
| ▲ | **Resolve** | 5 parent documents predate this certificate's search period. The earliest is 4451/2005. |
| ● | **Check** | Entry 2 (8756/2020) cancels 2520/2019 (Lease deed). Read linearly this looks like a live encumbrance; it is not. |
| ⚑ | **Note** | Certificate issued 19-Jun-2023 — 1133 days ago. Transactions since then are not covered. |
| ✓ | **Verified** | Cancellation of 2520/2019 is confirmed inside this certificate by 8756/2020. |
| ✓ | **Verified** | Entry count matches the certificate's own declaration (2). |

**Camera / animation.** Highlight the **Check** line on the cancelled lease, then cut to the
Uthukuli case (A2) for two seconds to show a **live mortgage** standing unresolved —
`14483/2024 · Mortgage without possession deed` — and cut straight back. Land on the green
**Verified** rows and hold.

**Key business message.** It finds what a tired reader misses on page 40, and it says out loud
what it confirmed.

**Why this moment matters to the customer.** The cancelled lease is the perfect example of why
reading isn't enough: both rows are individually accurate, and only the relationship between them
is the truth. But the green rows are what make the film credible. A tool that only ever reports
problems becomes noise people learn to skim — showing what passed is what makes the warnings
worth reading.

---

#### Scene 10 · 2:14–2:26 · The gap, and the next step — *(brief's Flow 5)*

> **Narration** (28 words · 12 s)
> "Five documents this property came through aren't in here at all. So it works out exactly which
> certificate you need next — and fills in the order for you."

**On screen.** The **Chain** band: filled circles for documents present, hollow circles for the
five that aren't — `○ 4451/2005 not in this certificate`. Scroll up to the blue-edged **Next —
order this certificate** card:
> SRO **Pollachi** · Village **Puliyampatti** · Survey **95/2, 100/3A, 101/3, 116/A1, 116/B3,
> 113/1B, 116/B1** · Period **01-Jan-1993 → 31-Dec-2017**

Click **copy**. The button reads `copied`.

**Camera / animation.** Hold on the hollow circles long enough to be understood as absence — they
are drawn *in place*, never omitted. Then a quick tilt up to the order card. The `copy` →
`copied` micro-interaction is the button of the whole film; frame it tight.

**Key business message.** It doesn't just find the gap. It hands over the fix, ready to send.

**Why this moment matters to the customer.** This answers the objection every serious viewer is
already forming: *"so you've told me my document is inadequate — now what?"* Without this card
the product ends on bad news and a shrug. With it, the news becomes a same-day action. Reassembling
that order by hand from a Tamil certificate is twenty minutes of work; here it's one click.

---

#### Scene 11 · 2:26–2:34 · The report — *(brief's Flow 6)*

> **Narration** (20 words · 8 s)
> "It all comes out as one report — with a section most reports don't have: what this search
> does not cover."

**On screen.** Click **export**. The report opens: letterhead, **Property**, **What this search
does not cover**, **Findings**, **Entries as read**, **Corrections**. Then a quick dissolve to
the same report as a printed page on a desk.

**Camera / animation.** Fast scroll down the report, then rest on the heading *What this search
does not cover*. The dissolve to paper is the shot — it says *this goes in a file, to a bank, to
your family*, without a word of narration.

**Key business message.** A shareable artifact a lawyer, a bank, or a family member can act on.

**Why this moment matters to the customer.** Every other section is an answer. That one heading is
a documented record of the limits of the answer — and it's what makes the report trustworthy to
the person receiving it, and what protects the professional whose name is on it.

---

### ACT IV — THE IMPACT · 2:34–3:00

---

#### Scene 12 · 2:34–2:50 · What actually changed

> **Narration** (39 words · 16 s)
> "We ran this on real certificates from registrar offices across Tamil Nadu. Three of the four
> could not support the search they were bought for. Not one of them looked wrong. That's the
> problem TitleChain exists to make visible."

**On screen.** The four-row table, building one row at a time:

| Certificate | Registrar office | Covers the chain? |
|---|---|---|
| Pollachi | Pollachi SRO | **No** — 5 parents, 2005–2011 |
| Uthukuli | Pollachi SRO | **No** — earliest parent 2000 |
| Erumaipatti | Erumaipatti SRO | **Yes** — all 3 links resolve |
| Adyar | Adyar SRO | **No** — ~10 parents back to 1961 |

**Camera / animation.** Static frame. Rows build on a 400 ms stagger. Let the **Yes** row land
last and hold on it.

**Key business message.** This is not a hypothetical risk. It is measurable, and it was never
measured before.

**Why this moment matters to the customer.** The green **Yes** row is doing the heavy lifting. A
detector that fires on everything is broken; one that stays quiet on the clean certificate is
measuring something. Investors read the fourth row as evidence of calibration.

> **Fact-check.** *Measured* — five certificates in the sample, of which four were evaluable;
> those four come from three registrar offices, all obtainable from public filings. (A fifth,
> Thiruchengode, had a blank search period and could not be evaluated — which is why the narration
> says "across Tamil Nadu" rather than counting offices on screen.) Say **"three of four"**,
> never a percentage: four documents is a signal, not a
> base rate. And say **"could not support the search"** — never "the title was bad". Window
> insufficiency means the chain is *unverified*, not that anything is wrong with the property.
> **The Erumaipatti row must be on screen** — the credibility of the other three depends on it.

---

#### Scene 13 · 2:50–3:00 · Close

> **Narration** (18 words · 7 s, then 3 s of silence)
> "Understand what you are buying, in minutes. And know exactly what your evidence covers — and
> what it doesn't."

**On screen.** Four lines, building over the case view as it fades back:
`Understand property documents in minutes.`
`Reduce legal uncertainty.`
`Spot hidden risks before you buy.`
`Make property decisions with confidence.`
Then to a clean frame — logo, and one line: **Understand property ownership and legal history in
minutes — not days.**

**Camera / animation.** Everything settles. No push, no parallax. The last five seconds are still
and silent apart from the last note of the music bed.

**Key business message.** The category isn't document translation. It's making property due
diligence something an ordinary person can actually evaluate.

**Why this moment matters to the customer.** The final promise is deliberately not "we'll tell
you the property is safe" — the product never opines on title and the film must not either. It's
"you will know what you know, and what you don't." That is the honest promise, and it's the only
one that survives contact with a lawyer in the audience.

---

## 5. The MVP flows, and why each one earns its place

Ranked by what happens to the business if the flow is cut.

| # | Flow | Screen time | Business case for it existing |
|---|---|---|---|
| **1** | **Coverage verdict + timeline** | 0:30 | **The only thing here nobody else can do.** Access to certificates was solved years ago; translation is a commodity within twelve months. This is a computation over what the document *omits*, and omissions have no text — so it can't be reached by OCR, translation or summarisation. It is the pricing power and the reason to fund the company. Cut it and TitleChain is a faster reader competing on OCR quality, which is a worse business. |
| **2** | **Findings ladder with confirmations** | 0:22 | Converts one insight into a repeatable product. Each rule is a named, versioned check (`R1`…`R10`) that runs identically on every file — which is what a bank can mandate across an empanelled panel, and what turns a per-file tool into portfolio-level assurance. The **Verified** half is not decoration: it is what stops the tool becoming noise, and noise is how tools get uninstalled. |
| **3** | **Pre-filled next order** | 0:12 | The conversion mechanic. Without it the product ends on bad news with no next step, and a product that only creates work gets uninstalled. It's also the most obvious future revenue line — a per-order fee sitting exactly where the customer already spends money. |
| **4** | **Click-to-source evidence** | 0:18 | The trust mechanic, and the reason a professional will put their name near the output. Every finding is falsifiable in one click against a cropped image of the original page. This is what makes the product defensible in a domain where a confident wrong answer is worse than no answer. Not in the brief's list; it must be in the film. |
| **5** | **Upload → same-page processing** | 0:16 | Cost of entry, and the retention surface. Zero onboarding, no account, no configuration. It matters commercially because it removes every reason to not try it once — and one file is enough to see the verdict. |
| **6** | **Exportable report** | 0:08 | The distribution loop. It's the only artifact that leaves the building, and it's how the second buyer — the bank — first encounters the product, without ever logging in. Every report a professional sends is a sales call the company didn't make. |

**What the brief lists as separate flows, and where they actually live:** plain-English summary
is the Entries table plus the Findings band (Scenes 8–9); mortgage status is a finding, not a
field, because a mortgage that was discharged and one that wasn't are the same word on the page
and opposite facts (Scene 9); missing documents are the hollow circles in the Chain band plus the
pre-filled order (Scene 10).

---

## 6. Gaps between this script and the built product

Read this before scheduling a shoot. Three items; one is a blocker.

### 6.1 The clean sample isn't wired up — **blocker for Scene 12**

Scene 12's credibility rests on the Erumaipatti row, and the two samples in `SAMPLES`
(`app/fixtures.py`) are both insufficient cases. `ec_samples/ec4_erumaipatti_namakkal.pdf` is in
the repo but has no cached digitisation under `seed/output/`, so it cannot be opened offline.

**Fix:** run it once against Sarvam DI, commit the cached output alongside the other two, and add
a third `SAMPLES` entry. Roughly 60 seconds of API time and about ₹5. This also delivers what
[FRONTEND_MVP.md](FRONTEND_MVP.md) already calls non-optional — *"a detector that fires on 2 of 2
inputs looks like a rigged demo"* — and it gives Scene 9 a live on-screen **"three parent links
resolve inside this window. Verified."** instead of a table row.

### 6.2 Re-uploading a missing document doesn't extend the case — **cut from the script**

The brief's Flow 5 ends with *"upload the missing document, the analysis refreshes."* That is
described as target-state in [CUSTOMER_JOURNEY.md](CUSTOMER_JOURNEY.md) stage 9 and is **not
built**: `POST /upload` creates a new case every time, so there is no way to add a second
certificate to an existing one and re-derive the chain across both.

Scene 10 as written stops at the pre-filled order and does not imply otherwise. **Do not film the
re-upload.** If it ships before the shoot it slots in as a 6-second addition to Scene 10 — the
strongest available extension, since it closes the loop the order card opens.

What *is* built and could stand in if a second interaction is wanted: **inline correction**. Click
any unreadable `—` cell, type the right value, and every finding re-derives in place and survives
a restart. It's a good 6 seconds of proof that the product learns from its user, and it's real
today.

### 6.3 There is no traffic-light score — **deliberate; see [§1](#1-three-decisions-this-script-makes-and-why)**

The brief asks for one. The product refuses one by design, and this script backs that call. If it
is required anyway, the honest version is a three-state badge derived from the finding counts
already computed (`blocking > 0` → red; `material > 0` → amber; otherwise green) — roughly an
hour of work. It would be accurate. It would also flatten the coverage ruler, which is the film's
best moment, into a dot that invites argument. **Recommendation: don't.**

### 6.4 Minor — nothing that blocks a shot

- The verdict bar is the same component in processing and ready states, so the transition in
  Scene 6 is genuinely continuous. No editing trickery needed.
- Both cached samples reach the verdict with no network. Film in airplane mode to prove it.
- The report prints cleanly — the top bar is `display:none` and the logo carries the letterhead —
  so Scene 11's cut to paper needs no mockup.

---

## 7. Production notes

**Pace.** Thirteen scenes in three minutes averages 14 seconds each. The two longest holds are
deliberate and must survive the edit: the three-second silence after the verdict (Scene 6) and
the push into the coverage gap (Scene 7). Everything else can lose a beat.

**Type.** Match the product — system UI stack, generous weight contrast, high contrast on white.
The app was designed to be read from three metres on a projector; the video inherits that for
free and should not add a second typeface.

**Colour.** Take the palette from the app: red for *Resolve*, amber for *Check*, green for
*Verified*, blue for the certificate's own window. Do not introduce a brand accent that isn't
already on screen — the audience is learning a colour language during the film and it must still
be true when they open the product.

**Music.** One bed, no drops, resolving under Scene 13. If the music has to tell the audience
this is exciting, the script has failed.

**Voice.** One narrator, unhurried, no rising inflection on the feature names. The product's whole
posture is *we'd rather tell you what we can't establish than sound confident* — the read has to
match, or the two contradict each other and the audience will believe the voice.

**Localisation.** A Tamil-narration cut is a genuine asset for the Indian market and costs a
re-record, not a re-edit. Every on-screen element is already either the product's own English UI
or the Tamil source document. Worth doing before any customer visit in Coimbatore or Salem.
