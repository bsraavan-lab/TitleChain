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
Icon button 26 × 26 · 4 radius
Segmented   22h inner · 6 radius outer / 4 inner · on-state = paper + 1px ring
Chip        22h · 9px pad · 20 radius · 11/500
Bar         52h · sticky · same bg as page + blur · 1px bottom hairline
Rail        max-height calc(100vh - 88px) · sticky top 68 · head 44h · view bg --sunk
Rule        78h · parents lane 38h · axis at 38 · window band 11h at 39
Spark       92 × 14 · hairline at y=6 · window 4h · ticks 12h
Finding     grid 84px / 1fr · 16px 12px pad · 8 radius · blocking msg 15/500, others 14/400
Answer      kicker 11/600 caps 0.09em · headline 33px serif -0.02em max 20ch · detail 15px
Section     title 11/600 caps 0.09em + 1px bottom hairline + 16px gap
```

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
