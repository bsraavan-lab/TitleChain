# Frontend Redesign — First Principles

**TitleChain · v2.0 · 27 Jul 2026**

Supersedes the *implementation* of [FRONTEND_MVP.md](FRONTEND_MVP.md) while keeping its
thesis intact. Where the two disagree on layout, hierarchy, or component structure, this
document wins; where they disagree on *what the product is for*, FRONTEND_MVP wins, because
it was right.

> **The thesis, unchanged:** Meena cannot tell whether the certificate she was given is
> capable of answering the question she was asked. Everything on screen exists to answer
> that in thirty seconds and hand her the next certificate to order.

What changed is that the previous build stated that thesis in five identical white cards, in
a layout where half the viewport was empty on arrival and a blocking finding looked exactly
like a receipt.

---

# 1 · Critique of the existing dashboard

Audited against the running build at 1440×900 and 390×844.

### 1.1 The structural failure: half the screen was empty

The case page was a 50/50 grid. The right column held one sentence — *"Select a finding or
an entry to see the region of the certificate it came from"* — until the user clicked
something. The single largest surface in the product was, on arrival, its least useful one,
and it was **advertising work rather than doing any**.

The document is right there. It is already rendered by `crops.py`. Not showing it was a
decision by omission.

### 1.2 The verdict was under-weighted and the property identity was the smallest text on screen

| Element | What it got | What it deserved |
|---|---|---|
| `This certificate cannot support a 13-year search.` | 19px bold, inside a bordered card, sharing a row with a ghost `export` button | The one focal element of the screen |
| `Pollachi SRO · Puliyampatti` — *which property this is* | 13px, muted grey, far top-right, visually last | Second-strongest thing in the chrome |
| `rulebook v1.0` | Permanent top-bar real estate on every screen | Provenance, belongs next to findings and in the report |

The hierarchy was close to inverted: the identity of the file was the quietest text on the
page, and a version string was permanent chrome.

### 1.3 Findings: eight items, one visual weight, four severities

`▲ Resolve`, `● Check ×3`, `⚑ Note`, `✓ Verified ×3` rendered as one flat list with identical
type, spacing and rule between them. Three "Verified — nothing to do" receipts occupied the
same square inches as the single blocking finding.

That is eight decisions where there are three, and it trains exactly the skimming habit the
product exists to remove. Confirmations are load-bearing — a tool that only reports problems
becomes noise — but they do not deserve equal space.

### 1.4 Monotone: same card, same border, same padding, same radius, five times

Coverage, Order, Findings, Chain, Entries were five `.band` elements: `1px solid`, `6px`
radius, `16px` padding, white. Nothing led. The eye had nowhere to go, so it started at the
top and read everything — which is precisely the behaviour we removed from her EC reading.

### 1.5 Two real rendering bugs found in audit

- **The rule collapsed on short windows.** On the Uthukuli sample the band labels rendered as
  `20242025` (two absolutely-positioned labels at nearly the same percentage), and the parent
  labels `2023`/`2024` collided. The mark that carries the entire argument became unreadable
  on any certificate with a narrow window — i.e. exactly the certificates most likely to be
  insufficient.
- **The chain tree rendered sideways.** `.chain-node { display: flex; flex-wrap: wrap }` made
  the nested `<ul>` a flex *item of its own parent row*, so any node with children drew its
  children in a second column beside itself. The tree read as two unrelated lists.

### 1.6 Section-by-section verdict

| Section | Exist? | Position right? | Hierarchy right? | Noise | Decision |
|---|---|---|---|---|---|
| Top bar | Yes | — | **No** — identity demoted, version promoted | rulebook string | Rebuilt: identity + switcher + actions + ⌘K |
| Verdict banner | Yes | Yes (first) | **No** — under-scaled, competing export button | sticky rail + border-left + card | **Merged** into the Answer block |
| Coverage card | Yes | Yes | **No** — separate card from the claim it proves | own card, own title, 3-row legend | **Merged** into the Answer block |
| Order block | Yes | Yes (second) | Yes | `dl` cramped, lowercase `copy` button | Kept, promoted to the one filled CTA |
| Findings | Yes | Yes (third) | **No** — flat across four severities | 8 equal rows | **Split**: open vs cleared |
| Chain | Yes | Yes (fourth) | Yes | broken layout, near-decorative at 2 entries | Kept, fixed, quietened |
| Entries | Yes | Yes (last, folded) | Yes | fold hid an unread page | Kept; auto-opens when it contains a task |
| Evidence pane | Yes | **No** — empty by default | — | 700px of nothing | **Rebuilt** as the always-on document rail |
| Home: 220px logo | **No** | — | — | dominates a screen whose job is "drop a file" | Cut to 132px, and only before the first case |
| Home: case list | Yes | **No** — below the fold, last | **No** — filename-grade rows | "Cases are read from disk" caption | Promoted to *the* page; rows carry state |
| Home: `rulebook v1.0` | **No** | — | — | — | Removed |

**Nothing was cut for being cheap.** Two things were cut for having no reader: the
`rulebook` chrome string, and the "cases survive a restart" caption — the row's existence
after a restart *is* that claim, so writing it down is telling rather than showing.

---

# 2 · The ideal user journey

The verb is **decide**: can this certificate support the opinion I am about to sign, and if
not, what do I order? Nine numbered steps is a workflow diagram, not a journey. Here it is as
questions, which is how she actually experiences it.

```
   HER QUESTION                        WHAT THE INTERFACE DOES         COST
─────────────────────────────────────────────────────────────────────────────
0  "Where was I?"                      Case list is the landing page.  0 clicks
                                       Rows carry chain state, not
                                       filenames.

1  "Read this one."                    Drop / choose. The dropzone is  1 click
                                       the first row of that list, so
                                       it is never hunted for.

2  "Is anything happening?"            Same URL, same screen. Honest   0 — she
                                       progress: "page 3 of 12".       may leave
                                       The rule is drawn from the
                                       header at ~8s, and each parent
                                       year lands on it as entries type.

3  "Can this answer my question?"      THE ANSWER. Kicker + headline   0 clicks
                                       + rule + sentence, above the
                                       fold, one block.

4  "Do I believe it?"                  The certificate is already on   1 click
                                       screen. "Show me" swaps the
                                       rail to the exact region;
                                       "In context" proves the crop
                                       sits in entry 2, not entry 3.

5  "What do I do about it?"            The order block: SRO, village,  1 click
                                       every survey number, computed   (Copy)
                                       period. Pre-filled.

6  "What else is wrong?"               "Needs you (4)". Ranked. The    0–4
                                       four passed checks are folded   clicks
                                       to one line.

7  "That date is wrong."               Click the "—". Its crop opens   2 keys
                                       in the rail. Type, Enter.       (⏎)
                                       Findings re-derive and flash.

8  "Prove it later."                   Export report — carries the     1 click
                                       rule, the findings, the rows,
                                       and the correction log.
```

**Login is not step zero.** v1 is a single advocate with a local database. Auth is pure cost
(STACK.md cut #2) and case scoping already demonstrates memory. When it arrives it goes in
front of step 0 and changes nothing below it.

**Best case: four clicks from a cold start to a copied order.** Open → drop → wait → Copy.

---

# 3 · Redesigned information architecture

Two routes. Everything else is a fragment swap.

```
/                       CASES — the landing page for a returning user
                        ├── row 0: drop / choose a file        (always visible)
                        ├── samples                            (quiet, one line)
                        └── case rows: state · property · rule spark · open count

/case/{id}              THE CASE — one screen, three states
                        ├── state: WORKING    progress + rule + skeletons
                        ├── state: READY      answer → action → findings → chain → entries
                        └── state: REFUSED    reason → checks that ran → recovery

  fragments (no route change)
      #case-body        polls itself while working, stops on its own
      #derived          swapped whole on correction — the memory proof
      #rail             the document; or one entry's region

/report/{id}            THE REPORT — printable, the only artifact that leaves

  ⌘K                    palette: jump to any property, or "All cases"
```

### What was asked for, and where each thing went

The brief lists eleven candidate surfaces. Building all eleven is how a tool becomes a
dashboard. Here is the disposition, with reasons:

| Candidate | Disposition |
|---|---|
| Landing dashboard | **Is the case list.** There is nothing to aggregate: one advocate, 8–15 files a month. A KPI row would be a chart of two numbers she already knows. |
| Recent analyses | **Is the case list.** Ordered newest-first; there is no second list to be "recent" relative to. |
| Upload flow | **Row zero of that list.** Not a screen, not a modal, not a wizard. One pipeline, always the same, so there is nothing to configure. |
| Current processing jobs | **Is a state of the case row and of the case page.** A jobs queue is a second place to look for one fact that is already on the row. |
| Property timeline | **Is the rule** — at three scales: 6px in a case row, full width in the answer, printed in the report. |
| AI-generated insights | **Deliberately absent.** Every finding is deterministic code against a versioned rulebook, and the page says so. An "AI insights" panel would put unfalsifiable text next to falsifiable text and cost us the trust the crops buy. |
| Risk summary | **Is the answer block** plus `Needs you (n)`. A separate risk score invites *"how did you compute 62%?"* |
| Missing documents | **Is the chain's open circles** and the R4 finding — rendered where the evidence would have been, never as its own tab. |
| Cost & token usage | **Absent from her product.** She is not paying per token and cannot act on it. It is an operator concern; it belongs in logs, not in a scrutiny tool. |
| Activity history | **Is the corrections log**, inside Entries, append-only. There is no other actor to have activity. |
| Settings | **One setting exists** (the 90-day staleness threshold) and it is rendered inside the R8 finding that uses it. A settings screen for one value is a screen that teaches people to look for settings. |

**Five of the eleven dissolved into things that already existed.** That is the redesign's
main claim: the previous IA was not missing sections, it was missing hierarchy.

---

# 4 · Wireframes

### 4.1 `/` — first run

```
┌ TitleChain ───────────────────────────────────────────────── ⌘K ┐
│                                                                 │
│                          [ mark ]                               │
│         Does this certificate cover the chain you are           │
│                 about to sign on?                               │
│      Drop a Tamil Nadu Encumbrance Certificate. TitleChain      │
│      reads it, computes what its window can evidence, and       │
│      shows the region of the page behind every finding.         │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │   ⬆   Drop an Encumbrance Certificate here                │  │
│  │       PDF, JPEG or PNG · up to 50 MB                      │  │
│  │                    [ Choose file ]                        │  │
│  └───────────────────────────────────────────────────────────┘  │
│  No certificate to hand?  [Pollachi · 2018–23] [Uthukuli ·…]    │
└─────────────────────────────────────────────────────────────────┘
```
No feature grid, no sign-up, no testimonial. The dropzone is the pitch. The two samples are
the entire onboarding: a first-time user reaches a verdict in three seconds without owning a
Tamil EC.

### 4.2 `/` — returning

```
┌ TitleChain ───────────────────────────────────────────────── ⌘K ┐
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ ⬆  Drop a certificate, or choose a file    [ Choose file ] │   │  ← row zero
│ └───────────────────────────────────────────────────────────┘   │
│  No certificate to hand?  [Pollachi · 2018–23] [Uthukuli ·…]    │
│                                                                 │
│  CASES  2                                                       │
│ ─────────────────────────────────────────────────────────────── │
│  ▲  Uthukuli · S.No 332/18A1 +2      ╷  ╷▌    ══      2 open    │
│     Pollachi SRO · 30-Nov-2024 → 11-Jul-2025                    │
│ ─────────────────────────────────────────────────────────────── │
│  ▲  Puliyampatti · S.No 95/2 +5      ╷╷ ╷  ▌══       4 open    │
│     Pollachi SRO · 01-Jan-2018 → 18-Jun-2023                    │
└─────────────────────────────────────────────────────────────────┘
```
Rows lead with **property identity and chain state**. `ec2_pacollege.pdf` means nothing to
her; *Puliyampatti, survey 95/2* is how the file sits in her head. The 92px spark is the same
mark as the full rule — she learns it once and reads it everywhere.

### 4.3 `/case/{id}` — WORKING

```
┌ TitleChain │ Kotturpuram · S.No 11/1 ⌄ ─────────────────── ⌘K ┐
│                                          ┌────────────────────┐│
│ ◴ READING PAGE 3 OF 12                   │ CERTIFICATE        ││
│ Reading the certificate…                 │ ┌────────────────┐ ││
│ ████████░░░░░░░░░░░░░░░░                 │ │                │ ││
│ page 3 of 12 · the job runs on the       │ │   [ skeleton ] │ ││
│ server — closing this tab loses nothing  │ │                │ ││
│                                          │ └────────────────┘ ││
│ FINDINGS                                 │ The certificate    ││
│ ▬▬▬  ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬                 │ appears here as    ││
│ ▬▬▬  ▬▬▬▬▬▬▬▬▬▬▬▬▬                       │ soon as the first  ││
│ ▬▬▬  ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬                 │ page is read.      ││
└──────────────────────────────────────────┴────────────────────┘
```
Bands are present and empty, not absent, so nothing jumps position when data lands. The
moment the header is typed, the rule replaces the headline and parent years begin landing on
it. She is not waiting for a result; she is watching one assemble.

### 4.4 `/case/{id}` — READY (the money screen)

```
┌ TitleChain │ Puliyampatti · S.No 95/2 +5  Pollachi SRO ⌄ │ [Copy request]* [Export report] ⌘K ┐
│                                                     ┌──────────────────────────────────┐│
│ ▲ INSUFFICIENT COVERAGE                             │ CERTIFICATE  ec2_pacollege.pdf   ││
│                                                     │                       ‹ 1 / 3 ›  ││
│ This certificate cannot                             │ ┌──────────────────────────────┐ ││
│ support a 13-year search.                           │ │                              │ ││
│                                                     │ │   the page itself, from      │ ││
│  2005  2007      2011              2019             │ │   the first frame — not      │ ││
│   ╷     ╷         ╷                 ╷               │ │   after the first click      │ ││
│ ──┴─────┴─────────┴─────────────────┴────────────   │ │                              │ ││
│                            ▓▓▓▓▓▓▓▓▓▓▓▓             │ │                              │ ││
│                           2018        2023          │ └──────────────────────────────┘ ││
│  ▭ this certificate ╷ 3 parents outside ╷ 1 inside  │                                  ││
│                                                     │  (a finding swaps this for its   ││
│ It covers 01-Jan-2018 → 18-Jun-2023. 5 parent       │   crop; "In context" draws the   ││
│ documents are named, the earliest from 2005.        │   same rectangle on the page)    ││
│ None of them fall inside this window.               │                                  ││
│                                                     └──────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────┐                                     │
│ │ NEXT STEP                      [ Copy request ] │  ← the only filled button           │
│ │ Order the certificate that closes this gap      │                                     │
│ │ SRO Pollachi          VILLAGE Puliyampatti      │                                     │
│ │ SURVEY NUMBERS 95/2 · 100/3A · 101/3 · 116/A1 … │                                     │
│ │ PERIOD 01-Jan-1993 → 31-Dec-2017                │                                     │
│ │ ─────────────────────────────────────────────── │                                     │
│ │ Period computed from the earliest parent named  │                                     │
│ │ here, less a 12-year buffer, up to the day      │                                     │
│ │ before this certificate's window opens.         │                                     │
│ └─────────────────────────────────────────────────┘                                     │
│                                                                                         │
│ NEEDS YOU  4                                                                            │
│ ▲ Resolve   5 parent documents predate this certificate's search period…                │
│             [Show me]  R3 · v1.0                                                        │
│ ● Check     Entry 2 (8756/2020) cancels 2520/2019. Read linearly this looks like a       │
│             live encumbrance; it is not.   [Show me] [Source 2]  R1 · v1.0               │
│ ● Check     5 parent documents are named but not present…   [Show me]  R4 · v1.0         │
│ ● Check     Entry 2: date registration could not be read.   [Show me]  R9 · v1.0         │
│ ───────────────────────────────────────────────────────────────────────────────         │
│ ✓ 4 checks passed — nothing to do                                                    ⌄  │
│                                                                                         │
│ CHAIN  5 unexamined                                                                     │
│ ● 8756/2020  Cancellation Deed                                                          │
│   ● 2520/2019  Lease deed   ⊘ cancelled by 8756/2020                                    │
│     ○ 4451/2005  not in this certificate                                                │
│     ○ 4453/2005  …                                                                      │
│                                                                                         │
│ › ENTRIES  2  certificate declares 2                                          (folded)  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
   * revealed only once the order card scrolls out of view
```

### 4.5 The rail — two modes, one shell

```
document mode                          evidence mode
┌────────────────────────────────┐     ┌────────────────────────────────┐
│ CERTIFICATE  file.pdf  ‹ 1/3 › │     │ ENTRY 2  page 2 [Crop|Context] ✕│
├────────────────────────────────┤     ├────────────────────────────────┤
│ ┌────────────────────────────┐ │     │ ┌────────────────────────────┐ │
│ │  the whole page, browsable │ │     │ │ 8756/2020 ரத்து ஆவணம்     │ │
│ │                            │ │     │ │ PR: 2520/2019 …            │ │
│ └────────────────────────────┘ │     │ └────────────────────────────┘ │
│                                │     ├────────────────────────────────┤
│                                │     │ page 2 · block …lock_003 ·     │
│                                │     │ layout 0.95                    │
│                                │     │ ▸ What layout confidence is not│
└────────────────────────────────┘     └────────────────────────────────┘
```
Identical header geometry in both modes, so nothing moves under the cursor when she switches.

### 4.6 Correction

```
before                                after (one hx-post)
  REGISTERED  [ — ]  ← a button         REGISTERED  14-08-2020
     click                              NEEDS YOU  4 → 3
  ┌──────────────────────┐              ● Entry 2 registration date  ← gone
  │ [ 14-08-2020    ] ⏎  │              (#derived flashes once, 900 ms)
  └──────────────────────┘
  …and the crop of that very block opens in the rail, so the value
  is read off the page rather than typed from memory.
```

### 4.7 Refusal

```
⊘ REFUSED

Nothing was read
from this certificate.

No registration-entry table was found on any page, and the document
declares no entry count.

┌ WHAT WE LOOKED FOR ───────────────────────────┐
│ ✗ a registration-entry table                  │
│ ✗ a declared entry count (பதிவுகளின் எண்ணிக்கை) │
│ ✗ a search-period header                      │
└───────────────────────────────────────────────┘

[ Upload a different file ]  [ Open Pollachi · 2018–23 ]  [ Open Uthukuli · 2024–25 ]
```
No rail: there is no document to corroborate anything with, and an empty pane beside a
refusal reads as a second failure.

### 4.8 Mobile ≤720px

Single column. Bar drops our own wordmark text and keeps the property name — she knows which
app she opened; she needs to know which file she is in. The rail moves below the findings and
**scrolls itself into view** when "Show me" is pressed, because a control that changes
something 2000px off-screen has done nothing. Entries scroll horizontally rather than
wrapping: a wrapped registry number is a misread registry number.

---

# 5 · Rationale for every layout decision

**5.1 · 58/42, not 50/50.** A ratio is a statement about rank. Equal columns say "these are
peers"; she comes for the conclusion and consults the page to falsify it. 58/42 says the
answer leads and the document corroborates. The rail has a 380px floor because below that a
table crop is unreadable, at which point the split should collapse entirely.

**5.2 · The rail is never empty.** The previous pane advertised a feature instead of
performing one. Showing the certificate from the first frame costs one route
(`/page/{case}/{n}.png`, using the renderer `crops.py` already had) and converts the largest
surface in the product from a placeholder into the thing that makes every finding checkable.

**5.3 · Verdict + rule + sentence are one block, not three cards.** They are claim, evidence
and working — one argument. Splitting an argument across three bordered boxes is how you make
a reader treat the parts as unrelated.

**5.4 · Serif for the answer, sans for the interface, mono for registry identifiers.** Three
registers, all available offline (PRD §11: no CDN, no webfont). The serif marks the sentence
as *the document's claim* rather than UI text, and it is the one place a 45-year-old reader at
the end of a long day will not mistake for chrome. Mono on `4451/2005` and `01-Jan-1993` is
functional: registry numbers are codes, and a code in a proportional font cannot be scanned
down a column. Every number that changes carries `tabular-nums`.

**5.5 · Warm neutrals, not SaaS grey.** The rail shows a scan of warm white paper all day. A
cool `#f7f8fa` chrome around it makes the document look yellow and dirty. The palette comes
from the room the product lives in: ledger paper, photocopy grey, endorsement blue-black, the
registrar's seal red, stamp-paper ochre, court-fee green. It is not a mood; it is what makes
the evidence look clean.

**5.6 · Findings split into "needs you" and "cleared".** Four severities are our vocabulary.
Her question is binary: *does this cost me a decision?* Open items are expanded and ranked;
confirmations fold to one line. The receipts are never dropped — a tool that only reports
problems becomes noise she learns to skim, and **the reassurance is what makes the warnings
credible** — they just do not deserve equal space.

**5.7 · One filled button on the screen.** `Copy request` is black; everything else is ghost
or quiet. If two things are emphasised, neither is. The bar's duplicate appears only once the
card explaining it has scrolled away, because the same button twice in one viewport reads as
two different buttons.

**5.8 · Entries stay folded, but unfold themselves when they contain a task.** A fold that
hides work is a trap. An unread page range or an unreadable cell opens the section on render.

**5.9 · The rule is the signature, drawn at three scales.** 6px in a case row, full width in
the answer, printed in the report. She learns one mark and reads it everywhere. Collision is
resolved in the data (`Coverage.clusters`, `Coverage.band_labels_merge`) rather than left to
CSS luck, because a label landing on a label destroys the only thing the mark exists to show.

**5.10 · Depth is borders-only.** One hairline weight, `rgba(25,23,19,0.06–0.18)`. Shadow is
spent only on things that genuinely float: the switcher menu, the palette, the toast. Mixing
elevation strategies is the fastest way to make a dense tool look assembled rather than
designed.

**5.11 · No dark mode, on purpose.** The subject matter is a white page. Dark chrome around a
white raster is measurably worse for comparison, and the report is printed. The token
architecture is nonetheless one hue with lightness-only steps, so a future dark chrome is a
token swap, not a redesign — see §10.

**5.12 · Colour is never the only carrier.** Glyph + word + colour, every time
(`▲ Resolve`, `● Check`, `⚑ Note`, `✓ Verified`). That settles colour-blindness without a
separate accessibility pass, and it survives printing in greyscale.

---

# 6 · Navigation structure

```
Bar (persistent, 52px, same background as the page — a tinted bar
     fragments the app into "chrome world" and "content world")

  ┌ TitleChain ─────────────┐   → /            all cases
  ┌ Puliyampatti · S.No 95/2 +5  Pollachi SRO ⌄ ┐
  │   Other cases                               │  ← the switcher: moving between
  │     Uthukuli · S.No 332/18A1 +2             │     files never routes through
  │   Go                                        │     the home screen
  │     All cases                               │
  └─────────────────────────────────────────────┘
                              ┌ [Copy request] [Export report]  ⌘K ┐
```

There is **no sidebar**. A sidebar is for products with many nouns; this one has two — the
case list and a case. A 240px icon rail holding two items is furniture.

**Keyboard.** Every shortcut has a visible control as well; none of them is the only path to
anything.

| Key | Action |
|---|---|
| `⌘K` / `Ctrl K` / `/` | Command palette — jump to any property by name |
| `j` / `k` | Move between open findings |
| `↵` | Open the focused finding's source in the rail |
| `c` | Copy the order request |
| `e` | Export the report |
| `Esc` | Close the palette, or abandon a cell edit without committing |

The palette has **no open animation**: a control used many times a day must never feel slow.

---

# 7 · Component hierarchy

```
base.html ─ bar · palette · toast
│
├── home.html
│   ├── welcome                 (first run only — disappears at case #1)
│   ├── dropzone                 idle · hover · dragover · rejected
│   ├── samples
│   └── case-list
│       └── case-row  ← state glyph · identity · [_rule.spark] · chip
│
├── case.html
│   ├── switcher                 (bar_context)
│   ├── bar-cta                  (bar_actions, scroll-revealed)
│   ├── _body.html               ← the ONLY polling element
│   │   ├── _working.html        answer(muted) · progress · [_rule.rule] · skeletons
│   │   ├── _refusal.html        kicker · headline · checks · recovery
│   │   └── _derived.html        ← swapped whole on correction
│   │       ├── _answer.html     kicker · headline · [_rule.rule] · detail
│   │       ├── _order.html      spec grid · Copy request
│   │       ├── _findings.html   open list · cleared fold
│   │       ├── _chain.html      recursive node()
│   │       ├── _entries.html    table · _cell.html → _edit_field.html · corrections
│   │       └── provenance
│   └── _rail.html               modes: document | evidence
│
├── report.html                  head · property · coverage(+rule) · findings ·
│                                entries · corrections · footer   (print-ready)
│
└── _rule.html                   macro rule()  — full scale
                                 macro spark() — row scale
```

**Shared primitives:** `.btn` (`primary` · `ghost` · `quiet` · `sm`), `.icon-btn`, `.seg`,
`.chip`, `.count`, `.section-title`, `.spec`, `.fold`, `.mono`, `.glyph`.

Two rules held throughout: **native element first** (`<button>`, `<a>`, `<details>`,
`<dialog>` — focus, keyboard and semantics for free, and the palette's focus trap and Escape
handling cost zero lines), and **the rule is a macro, not a copy** — the case page, the case
row and the report all call the same two functions, so the mark cannot drift.

---

# 8 · UX improvements that remove friction

| # | Friction removed | How |
|---|---|---|
| 1 | Half the viewport was empty until the first click | The rail shows the certificate on arrival |
| 2 | "Which property am I in?" was 13px grey, top-right | It is now the second-strongest element in the bar, and it is the switcher |
| 3 | Going to another case meant going home first | The switcher lists the others; `⌘K` jumps by name |
| 4 | Eight findings at one weight | Four open, four folded; the blocking one is the largest text in the list |
| 5 | Filling in a missing date from memory | Clicking the `—` opens that block's crop in the rail *and* the editor |
| 6 | "Where do I click to check this?" | `Show me` on every finding, chain node and row; the clicked row stays marked |
| 7 | The primary action scrolled away | It reappears in the bar exactly when the card leaves the viewport |
| 8 | Case rows said `opened` | They say `4 open`, carry a state glyph, the search window, and the rule spark |
| 9 | The rule was unreadable on narrow windows | Collisions merged in data; band labels merge under 14% width |
| 10 | The chain rendered sideways | Row and subtree are separate elements |
| 11 | A folded section could hide an unread page | Entries auto-open when they contain a task |
| 12 | No keyboard path | `⌘K`, `j`/`k`, `↵`, `c`, `e`, `Esc` |
| 13 | Copy gave no confirmation beyond the button's own label | A toast that names the next step: *"paste it into TNREGINET"* |
| 14 | `rulebook v1.0` in permanent chrome, provenance nowhere useful | Per-finding rule id, and one provenance line at the end of the case |
| 15 | Report dropped the figure that convinced her | The report carries the rule |

---

# 9 · Edge cases

| Case | Interface behaviour |
|---|---|
| **No cases (first run)** | The welcome block explains in one question and one sentence; the dropzone is the focal element. It vanishes permanently at case #1 — onboarding that persists is clutter. |
| **Loading, 60–90 s** | Same URL. Determinate progress with real page counts, plus *"the job runs on the server — closing this tab loses nothing."* Skeletons hold layout so nothing jumps. |
| **Queued behind other jobs** | `status_detail` renders verbatim: *"Queued — 2 jobs ahead, ~40 s."* Never a spinner pretending to work. |
| **Nil EC — no encumbrances** | The most dangerous "empty state", because it looks like success. Never *"No findings."* The rule shows the window is five weeks wide, and the sentence says so. |
| **Genuinely clean EC** | `Nothing in this certificate needs a decision from you. N checks ran and passed.` — a claim, not an absence. |
| **Not an EC** | Refusal with the checks that *actually ran*, each marked `✗`. Recovery actions get the same weight the order block gets on a good case. No rail. |
| **Invalid input** (>50 MB, wrong type) | Named inline under the dropzone, in the seal red, with the limit stated. No modal: the fix is to pick another file and that control is six pixels away. |
| **Partial results — pages unread** | A row *inside* the entries table: `▲ pages 11–20 were not read — retry`. A toast is dismissible; an unread page must not be. The section auto-opens. |
| **A field could not be read** | The cell is a `—` that is a button, in ochre with an ochre border. Clicking opens the crop *and* the editor. |
| **Correction saved** | No save button in the keyboard's way: Enter commits, Escape restores. `derive()` re-runs server-side, `#derived` swaps, and the panel flashes once. |
| **Correction that changes nothing** | The panel still flashes. Silence after an edit reads as a dropped edit. |
| **Tab closed / network drops** | The job is server-side and persisted; the page only polls. Reopening resumes the same view. Nothing lives in browser state. |
| **Multiple sources on one finding** | First button is `Show me`; the rest are `Source 2`, `Source 3` — never entry numbers, which would collide with the entry column. |
| **Long survey-number lists** | The spec grid gives them a full-width row and breaks on `·` separators rather than truncating. A truncated survey number is a wrong order. |
| **Tamil content** | Renders verbatim in a Tamil stack. No `text-transform`, no `letter-spacing`, ever. The romanised form appears *beside* it, never instead of it. There is no language switcher: the data is bilingual, the interface is not. |
| **Screen reader on the evidence layer** | The whole rule is `aria-hidden` and its sentence is the accessible equivalent, permanently visible rather than a tooltip. Crop `alt` text is built from that block's own typed values — the rare accessibility win that falls out of the data model. |
| **Reduced motion** | All animation collapses to ~0 ms; the spinner becomes a static ring. Colour and opacity transitions remain. |
| **Printing** | Bar, palette and toast are removed; the report loses its card and fills the sheet; findings keep their severity colour and their word. |

---

# 10 · Future enhancements that need no redesign

Each of these lands in a slot the current structure already has.

1. **Multi-EC merge into one chain (F14).** The replacement certificate she ordered arrives and
   extends the chain. *Slot:* the rail's `document` mode already has a pager — it becomes a
   document switcher; the chain gains a second colour of examined node. This is the retention
   feature, and the order block manufactures demand for it.
2. **"Show the rule's working."** A per-finding panel naming the rule, its inputs, and the
   rulebook version. *Slot:* the `rule-id` chip is already there and already carries a
   tooltip — it becomes a disclosure.
3. **Entries at scale (30–40 rows).** Sort, filter, jump-to-entry, `j/k/↵/c` triage.
   *Slot:* the `j`/`k` handler is written against a list selector; pointing it at table rows
   is a one-line change. The table already scrolls with sticky headers.
4. **Dark chrome.** Tokens are one hue with lightness-only steps and semantic names; a dark
   theme is a second `:root` block. The rail keeps its light "desk" surface so the raster
   never sits on black.
5. **Login and multi-advocate.** `advocate_id` is already a column on `cases`. It goes in
   front of step 0 of the journey and changes nothing after it; the switcher already scopes
   by list.
6. **Saved views / triage inbox** ("everything with an open blocking finding"). *Slot:* the
   case list is already computed from `derive()` per row, so a filter is a predicate, not a
   new screen.
7. **TNREGINET submission.** The order block's `Copy request` becomes `Order` beside it. The
   spec grid is already the exact payload.
8. **Comment / handover on a finding.** *Slot:* the finding row's footer, beside the source
   buttons.
9. **Staleness countdown.** *Slot:* inside the R8 finding, next to the threshold it uses —
   which is where the product's one setting already lives.

---

## The one-line summary

> One screen, one answer, one action, and the document never leaves the room.
