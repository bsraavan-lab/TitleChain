# TitleChain — Launch Video Narration

*Voice-over script · ~2 minutes · continuous narration*
*Demo-matched: every beat corresponds to a real screen in the app, driven on the
built-in Pollachi sample (`ec2_pacollege.pdf`, the "Pollachi · 2018–23" button on
the home screen). Persona: Advocate Meena, per [CUSTOMER_JOURNEY.md](CUSTOMER_JOURNEY.md).*

---

This certificate looks clean. Two entries. A lease from 2019, and the deed that cancelled it a year later. An advocate with fifteen files on her desk could read it in ten minutes and move on. And she would have missed the only thing that matters, because it isn't written on either page.

Meena is a property advocate in Coimbatore. A bank has asked her to certify title on land in Puliyampatti village, near Pollachi. A thirteen-year search, her name on the opinion.

She drops the certificate into TitleChain. The screen shows each stage as it works, and under a minute later the same screen becomes her answer. At the top, in red: this certificate cannot support a 13-year search.

Below it, the reason, drawn so anyone can check it. A shaded band marks the years the certificate covers, 2018 to 2023. Above the line, five small marks: parent documents the certificate itself names, from 2005, 2007, and 2011. Every one sits outside the band. She doesn't have to trust a machine's verdict. The gap is right there, and she can do the arithmetic herself.

The next panel already holds her next move: order this certificate. Pollachi SRO, Puliyampatti, all the survey numbers, 1993 to 2017. One copy button.

Then the findings. The 2019 lease was cancelled, so it's not a live encumbrance. Verified, and the product says so. Entry two's registration dates never made it out of the scan, so they're flagged, even though the OCR was 96 percent confident. And every finding carries a source link that opens the exact patch of the original Tamil page it came from.

She exports the report. It states, in writing, what this search does not cover.

Ten minutes ago this certificate looked clean. Now she knows what it actually is: true about five years, silent about the fifteen before them. Understanding your property shouldn't depend on the language it was written in. It should be a right, not a privilege.

---

## Screen cues (for the person driving the demo)

| Narration beat | Screen | What to do / what's visible |
|---|---|---|
| "This certificate looks clean…" | The PDF itself (or `Entries as read` table) | Show the raw Tamil certificate: 2 entries, doc 2520/2019 (lease) and 8756/2020 (cancellation). |
| "She drops the certificate in…" | Home → case screen | Click **Pollachi · 2018–23** sample (or drop the PDF in the dropzone). Processing states stream in place; no page change. |
| "At the top, in red…" | Verdict bar | Headline: *"This certificate cannot support a 13-year search."* |
| "A shaded band… five small marks…" | **Coverage** ruler | Band = 01-Jan-2018 → 18-Jun-2023. Ticks at 2005, 2005, 2007, 2007, 2011 — all outside the band. Detail line repeats it in words. |
| "Order this certificate…" | **Next — order this certificate** | Pre-filled: Pollachi SRO · Puliyampatti · survey 95/2, 100/3A, 113/1B, 116/A1, 116/B1 · 01-Jan-1993 → 31-Dec-2017. Click **copy**. |
| "The 2019 lease was cancelled… flagged…" | **Findings** + **Chain** | Verified: lease 2520/2019 cancelled by 8756/2020 (⊘ tag in the chain). Flagged: R9 on entry 2 — all three date cells dropped at 0.96 block confidence. |
| "…the exact patch of the original Tamil page." | **Source** pane (right) | Click **source** on a finding → cropped table region; toggle **show on full page**. |
| "She exports the report." | **export** → scrutiny report | Point at the section *"What this search does not cover."* |

## How to read the output screen

Band order is Meena's question order, not the pipeline's (see `_derived.html`):

1. **Verdict bar** — can this certificate answer my question? One sentence, red or green.
2. **Coverage ruler** — why. A ruler, never a score: band = covered years, ticks = parent documents. You check it by looking, not by trusting.
3. **Order panel** — what do I do about it. The replacement EC, pre-filled and copyable.
4. **Findings** — what was found, ranked to-resolve / to-check / verified. The verified items are deliberate: reassurance only where evidence supports it.
5. **Chain** — how it connects. ● examined here, ○ named but not present (unexamined — absence is drawn, never omitted).
6. **Entries as read** — the raw rows, for auditing the extraction.
7. **Source pane** — click anything, see the pixels it came from. Nothing is asserted without evidence on the page.
