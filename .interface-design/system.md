# TitleChain — interface system

Saved so future sessions do not re-derive this. If a value is written here, hold to it.
Full reasoning: [`docs/UX_REDESIGN.md`](../docs/UX_REDESIGN.md).

## Who, what, how it should feel

- **Human:** Advocate Meena, ~45, Coimbatore. 8–15 title-scrutiny files a month, her name on
  the opinion. At her desk, mid-afternoon, a bank's SLA clock running.
- **Verb:** *decide* whether this certificate can support the opinion she is about to sign —
  and if not, order the one that can.
- **Feel:** a case file on a clean desk. Legal-grade, quiet, print-adjacent, authoritative
  without volume. Dense where it must be, calm where it counts. Not a SaaS dashboard.

## Domain and colour world

Ledger paper · the search window · the parent document (PR) · the chain of title · the SRO
counter · the survey number · the certified copy · red-ink marginalia.

The palette comes from that room: ledger paper gone warm, photocopy grey, blue-black
endorsement ink, the registrar's red seal, stamp-paper ochre, court-fee green. **Warm, not
cool** — the rail shows a warm-white scan all day, and cool grey chrome makes it look dirty.

## Signature

**The rule** — a horizontal year axis with parent documents above and the certificate's own
window below. Drawn at three scales from one macro (`_rule.html`): 6px spark in a case row,
full width in the answer, printed in the report. Never a badge, never a score.

Second: **the rail is never empty** — it holds the certificate itself from the first frame.

## Tokens

```
surfaces   --ledger #fcfbf8 · --paper #fff · --sunk #f4f2ec · --folder #f7f5f0
borders    --rule-soft rgba(25,23,19,.06) · --rule-line .10 · --rule-firm .18
ink        --ink #191713 · --ink-2 #55504a · --ink-3 #837c72 · --ink-4 #a9a29a
meaning    --seal #a32330 (blocking) · --stamp #8a5a0b (check)
           --fee #15653f (verified) · --endorse #2b4c8c (the certificate's window, focus)
           each has a -soft tint for chips and wells
           --fee-line #bfe0cd · --stamp-line #e6d3b0 — the same meanings at border
           strength, for the one case a -soft fill is too weak to draw an edge with
--ink-hover #2b2721 — the only ink below --ink, and only so the single filled
           button on a view has somewhere to go on hover
space      --s1..--s8 = 4 8 12 16 24 32 48 64
radius     --r1 4 (control) · --r2 6 (input/button) · --r3 8 (card) · --r4 12 (rail/dialog)
ease       cubic-bezier(0.23, 1, 0.32, 1)
```

## Type

Three registers, all offline — no CDN, no webfont (PRD §11).

| Register | Stack | Used for |
|---|---|---|
| `--serif` | Iowan Old Style / Palatino / Georgia | the answer headline only — the argument, not the UI |
| `--sans` | ui-sans-serif system stack | everything interface |
| `--mono` | ui-monospace / Menlo | registry identifiers, dates, counts — always `tabular-nums` |
| `--tamil` | Noto Sans Tamil / Nirmala UI / Latha | `*_native` content. Never transform, never letter-space. |

Scale 14px base × 1.25 → **11 · 12 · 14 · 17 · 21 · 26 · 33**. Hierarchy is built from size +
weight + colour together, never size alone. 13 and 15 are the two ratified exceptions, and
only where the component table below names them (button, finding, answer detail).

**Every uppercase label is `11/600 caps 0.09em`** — section title, answer kicker, table
column header, menu group, meter label, report heading. There is one such register and no
second one; a label at 12/700/0.06em beside a label at 11/600/0.09em reads as two systems.
Sizes below 11 are for glyphs and chart labels only, where the sizing is optical, never for
words the eye reads as text.

## Density and depth

- 12px inside controls · 20px within a section · 40px between sections.
- **Borders only.** One hairline weight. Shadow is spent solely on things that float:
  switcher menu, palette, toast (`--lift-menu`).
- Case grid **58/42**, rail floor 380px, collapses to one column ≤1080px.

## Component measurements

```
Button      32h · 12px pad · 6 radius · 13/500 · scale(.975) on :active
  quiet     26h · 8px pad · 12px
  tiny      22h · min 28w · 7px pad · 4 radius · 11/500 mono · on = --endorse-soft
Icon button 26 × 26 · 4 radius
Segmented   22h inner · 6 radius outer / 4 inner · on-state = paper + 1px ring
Chip        22h · 9px pad · 20 radius · 11/500
Link        13px · --endorse · underline at 2px offset · hover → --ink · plain --ink-2 in print
Bar         52h · sticky · same bg as page + blur · 1px bottom hairline
Rail        max-height calc(100vh - 88px) · sticky top 68 · head 44h · view bg --sunk
Rule        78h · parents lane 38h · axis at 38 · window band 11h at 39
Ruler       axis at 44 · ticks own 0–44 · bands 12h at 50+20n · name inside its band
Spark       92 × 14 · hairline at y=6 · window 4h · ticks 12h
Finding     grid 84px / 1fr · 16px 12px pad · 8 radius · blocking msg 15/500, others 14/400
Answer      kicker 11/600 caps 0.09em · headline 33px serif -0.02em max 20ch · detail 15px
Section     title 11/600 caps 0.09em + 1px bottom hairline + 16px gap
Severity edge  3px solid, left, on every card or section that carries one
Points      grid 18px / 1fr · 10px 0 pad · bottom hairline · 14/1.55 --ink-2
              lead-in <strong> 600 --ink · glyph 10px, centred in its column
Facts       3-up · mono figure 26px tabular-nums · body 13px --ink-2
Check tiers failed  17px title · 15px msg --ink · s4 pad · r3 · 3px --seal edge
            open    14px title · 14px msg --ink-2 · s2 pad · top hairline
            settled behind <details> · 13px msg --ink-3
Subject chip 11px mono tabular-nums · --sunk · 1px --rule-line · r1 · 1px 6px
```

**The checklist is tiered, and a family is one row.** Three weights, not one:
the failed check is the whole answer to "can I sign this yet" and is the only
17px title in the list; open work sits at 14px; settled work goes behind a
`<details>` summary. It was sixteen rows of identical height and weight until
2026-07-31, so FAILED and NOT APPLICABLE read the same and the eye had nowhere
to land.

Runs that share a rule, an outcome and a key family collapse to one row
(`runs_grouped`), because R4 fires once per unresolved parent and five rows that
differ only in the number inside them teach the eye to skim. The collapse is
presentational only: every member keeps its key and stays individually
expandable, citable and signable, one level down. A group states its case over
the set — never the lead member's sentence, which names one subject and would
contradict a title that just counted five.

The report does **not** group. Its audit table carries a per-run "Signed off"
cell, and an audit record's job is completeness, not speed of reading.

**The home pitch is bullets, not paragraphs.** Each line is one bold lead-in plus
one clause, and it stays that way. It was six prose paragraphs of three-to-four
lines until 2026-07-31; nobody reads a paragraph to decide whether a tool is worth
a click. If a point needs two lines, it is two points or it is cut. Figures lead
the section because a stranger believes a number before prose — and the sample
size is printed, never rounded into a rate (n=4 is a signal, not a base rate).

## One name per thing

Every mark and control in the product has exactly one class and one rule:

- **`.link`** is the only way back to the page — `_macros.html` `source_button` /
  `page_button`, used by the chain, entries, encumbrance cards, rule rows, timeline
  and the report. Never a bare `<button>`, never a second "see the source" style.
- **`.rule-key` / `.key` / `.sw-*`** is the key for *both* charts. A swatch means the
  same thing on the case rule and on the coverage ruler.
- **`.chip` + `chip-open` / `chip-clear` / `chip-fail` / `chip-wait`** is the only
  badge family. Not `.tag`, not a bespoke pill.
- **`.shot` / `.evidence-fig`** are one image treatment: `margin: 0`, r2, 1px pure-rgba
  inset outline.

Rename a component and its rule renames with it, in the same commit. Three separate
components had been renamed in the templates and left behind in the stylesheet, so
they rendered with no styling at all until 2026-07-28.

## Rules that must hold

1. **One filled button per view.** `Copy request` is it on the case screen.
2. **Colour is never the only carrier** — glyph + word + colour, every severity, every time.
3. **Any absence of evidence is rendered where the evidence would have been**: a missing date
   is a `—` button in its cell, an unread page is a table row, an unexamined parent is an open
   circle. Never a toast, never silently omitted.
4. **Native element first** — `<button>`, `<a>`, `<details>`, `<dialog>`. No `div onClick`.
5. **Repeated actions get no animation.** Palette opens instantly; only menus and the toast
   move. Everything respects `prefers-reduced-motion`.
6. **No dark mode** — the subject is a white page and the report is printed. Tokens are one
   hue with lightness-only steps, so it stays a token swap if that ever changes.
7. **No CDN, no webfont, no icon library.** Four typographic glyphs (`▲ ● ⚑ ✓ ○ ⊘`) and two
   inline SVGs.
8. **Nothing bolder than 600.** The sheet builds hierarchy from size + weight + colour, and
   600 is the top of it. A 700 anywhere is a second bold register.
9. **One border weight in the chrome.** `--rule-soft / --rule-line / --rule-firm` change the
   *tone* of a hairline, never its width. Widths above 1px belong to chart marks only
   (`.ruler-required`, `.k-req`, the SVG strokes, the spinner).
10. **Every state, on every control.** A control that has `:hover` has `:focus-visible` too,
    and a drop target lights on `:focus-within` exactly as it does on hover — the two
    dropzones in this product are the same control and must not disagree.

## Checks worth re-running

Both catch the failure mode this codebase actually has — markup and stylesheet drifting apart:

```bash
# 1. classes the templates emit that no rule matches
#    (jinja-built names like `enc-{{ }}` and `g-{{ }}` are expected noise)
# 2. rules that match no markup — dead weight, and the thing that silently
#    overrode the live .chip rule in July
```
Both were run against every flow — home, five case tabs, working, merged, refusal,
report, and 390px — on 2026-07-28.
