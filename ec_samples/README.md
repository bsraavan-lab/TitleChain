# EC test corpus

Real, publicly-obtained Tamil Nadu Encumbrance Certificates. All sourced from government
or regulatory portals (TN RERA promoter filings, forest-clearance filings). Nothing here is
hand-authored or synthetic except `ec2_scan.*`, which is a re-rasterisation of `ec2_pacollege`.

ECs are public records, but they name real parties. Treat accordingly: no third-party
uploads beyond Sarvam, per PRD §9 (Privacy).

**Sourced 26 Jul 2026. Not yet run through the pipeline.**

---

## Corpus at a glance

| File | SRO | District | Pages | Entries | Search period | Text layer |
|---|---|---|---|---|---|---|
| `ec2_pacollege.pdf` | Pollachi | Coimbatore | 3 | 2 | 2018–2023 | yes |
| `ec3_rera.pdf` | Pollachi | Coimbatore | 6 | — | — | yes |
| `ec4_erumaipatti_namakkal.pdf` | Erumaipatti | Namakkal | 4 | 5 | 01-Jan-1975 → 26-Apr-2024 | yes |
| `ec5_adyar_chennai_bundle.pdf` | Adyar | Chennai | 5 | 2 (+ Nil EC) | 11-Sep-2023 → 04-Apr-2024 | **no — vision required** |
| `ec6_thiruchengode_namakkal.pdf` | Thiruchengode | Namakkal | 6 | 7 | **blank (`- - -`)** | yes |
| `negative_nil-ec-portal-screenshot.pdf` | — | — | 3 | — | — | negative case |

The three new files break the Pollachi-only formatting risk flagged as weakest link #2 in
PRD §0.3 — four distinct SROs across three districts, and two visually distinct TNREGINET
layout generations.

---

## `ec4_erumaipatti_namakkal.pdf`

Erumaipatti SRO, Namakkal district · village பொட்டிரெட்டிப்பட்டி · survey 169/3 · issued 27-Apr-2024
Declared entry count: 5. A 49-year search window, which is unusually long.

| # | Doc | Nature | PR |
|---|---|---|---|
| 1 | 204/1985 | சுவாதீனமில்லாத அடைமானம் (mortgage without possession), ₹3,300 to Pottireddipatti Agricultural Cooperative Society | — |
| 2 | 1085/1992 | Sale deed | — |
| 3 | 1733/2022 | Partition deed | 1085/1992 |
| 4 | 1278/2023 | Gift deed to village panchayat | 1733/2022 |
| 5 | 1279/2023 | Gift deed to TN Electricity Board | 1733/2022 |

**Why it earns its place:** entry 1 is a 1985 cooperative-society mortgage — remarks record
10% interest on a 10-year term — with **no discharge or release anywhere in a window that
runs to 2024**. That is a live-encumbrance candidate on the face of the record, which gives
**R2 (`LIVE_ENCUMBRANCE`) its first real firing** — PRD §10.5 currently lists no real data for R2.

It is also the corpus's only **clean-chain counter-example**: entries 3→2, 4→3 and 5→3 all
resolve to entries present in the certificate. Useful as a negative control — it should
*not* produce R4 for those edges. A rulebook that flags everything is not a rulebook.

## `ec5_adyar_chennai_bundle.pdf` — the demo document

Adyar SRO, Chennai · village கோட்டூர் (Kotturpuram) · survey 11/1 and 11/PART · 5,515 sq ft
Applicant: Khurinji Homes Pvt Ltd. Cert. ref ECIOnline/1170887172024.

This is **two certificates for the same property in one file**:

- **Pages 1–3** — EC for **11-Sep-2023 → 04-Apr-2024** (a 7-month window)
  - Entry 1 · 3482/2023 · General Power of Attorney · PR: `1112/2004, 1342/2009, 2843/2019, 315/2013, 986/2022`
  - Entry 2 · 1088/2024 · General Power of Attorney · market value **₹2,71,42,000** · PR: `1112/2004, 1342/2009, 1464/1961, 2122/2011, 2843/2019, 315/2013, 4148/1981, 953/2004, 954/2004, 986/2022`
- **Pages 4–5** — a **Nil EC** for the same property, **01-Apr-2024 → 09-May-2024**, issued 13-May-2024, certifying no encumbrance found.

**Why it is the strongest demo input in the corpus:**

1. **R3 (`WINDOW_INSUFFICIENT`) at maximum contrast.** A 7-month certificate on a ₹2.71 crore
   property whose declared parent documents run back to **1464/1961** and **4148/1981**.
   Roughly a dozen distinct PR pointers, not one of which falls inside the window. No
   advocate relying on this pair has verified anything about the chain.
2. **The Nil EC is the trap made literal.** Read alone, pages 4–5 say "clean." Read against
   pages 1–3, it covers five weeks of a chain that is 60+ years deep. This is the
   *R. Ravichandran* fact pattern (below) in a live document.
3. **No extractable text layer.** `pdftotext` returns zero characters; the Tamil glyphs carry
   no ToUnicode mapping. Any pipeline that shortcuts to text extraction fails outright here —
   it genuinely requires Sarvam Vision. This is the honest "hardest material" input the
   rubric's Document Intelligence L5 asks for.
4. **Different layout generation.** QR-coded newer TNREGINET template, different table
   structure and column order from the Pollachi certificates.
5. Contains real `(முத.)` / `(முக.)` role markers on party names — the exact normalisation
   case FR-6 and the §4.5 rulebook moat describe.
6. Exercises **F14 (multi-EC merge)** and the chunking path with a genuine multi-certificate bundle.

## `ec6_thiruchengode_namakkal.pdf`

Thiruchengode SRO, Namakkal district · village Animoor · survey 58/3B1A · issued 20-Feb-2024
Declared entry count: 7.

**Why it earns its place:**

- **Deepest chain in the corpus.** Document references span **1964 → 2023**: `2376/1964`,
  `1839/1979`, `1840/1979`, `731/1984`, `1929/1995`, `1941/1995`, `9335/2022`, `5095/2023`,
  `7507/2023`, `10125/2023`, `10126/2023`. Multi-hop graph assembly with real depth, and
  strong R4 (`DANGLING_PARENT`) material.
- **The search period field is blank — rendered `- - -`.** The certificate does not state its
  own window. R3 cannot be evaluated at all, which is a distinct and more dangerous
  condition than R3 firing. Worth handling explicitly rather than crashing or silently
  passing: a header-level structural gap (R9) that should block the sufficiency verdict.
- **Bilingual field values.** Unlike the other samples, `nature` and `property_type` come back
  in English ("Sale deed", "Agricultural Land") and the SRO/village names are romanised,
  while boundary descriptions stay in Tamil. Tests that the schema does not assume
  Tamil-script values in every field.

---

## Litigation context

I could not source an EC that is itself an exhibit in a reported judgment — court filings in
India do not publish annexures as separate PDFs, so those documents are not on the open web.
The certificates above come from regulatory filings instead.

The failure mode is nonetheless well documented in TN case law, and this is the citation to
lead with:

**R. Ravichandran v. State of Tamil Nadu (Madras High Court).** A purchaser was issued a
**Nil Encumbrance Certificate** which omitted an earlier sale deed the vendor had already
executed in favour of a third party. Induced by the clean certificate, he completed the
purchase and registered his sale deed. The registering officers admitted the omission,
attributing it to oversight and workload. The Court **rejected that explanation and held it
patent negligence per se**, finding serious prejudice to the petitioner, and observed that
while a registering officer's duties are administrative and exclude adjudication of title,
failure to maintain accurate records and issue correct encumbrance certificates is
negligence. It has since been cited for the proposition that a Sub-Registrar issuing an EC
without noting all relevant transfers may be proceeded against under the Consumer
Protection Act.

Related: *M. Gunasekaran v. District Registrar* (Madras HC, 2025) — pleadings in a civil suit
are not instruments and cannot be entered in an EC; registrar directed to delete the entry.
Useful for the inverse problem: entries that should not be there.

**How this connects to the product.** *Ravichandran* is a certificate that was wrong about
what it contained. TitleChain does not claim to catch that — no reader can detect an entry
the registry never wrote. What it catches is the adjacent and more common defect: a
certificate that is *right about what it contains and silent about what it omits by design*.
`ec5` is that document. The Nil EC is accurate for 01-Apr → 09-May-2024 and tells the buyer
nothing about the chain back to 1961, and nothing on either certificate announces the gap.
That is the risk §4.2 argues is invisible today, and it is the one R3 converts into a caught
defect with a pre-filled order for the certificate that would actually cover it.

---

## Sources

- [TN RERA promoter filing — Erumaipatti EC](https://rera.tn.gov.in/public/storage/upload/W9YP5Q2ETnZlncgmlbjvhst6qlczUIQTtw00wv3M.pdf)
- [TN RERA promoter filing — Adyar EC bundle](https://rera.tn.gov.in/public/storage/upload/k5cMIkoySDDc7CLGFXmWh2zZjHrOvvaBRxZ3NbBi.pdf)
- [TN RERA promoter filing — Thiruchengode EC](https://rera.tn.gov.in/public/storage/upload/kglQ8tmoGzTC48feMoinrXmoAncTIcmk0W6hdydy.pdf)
- [R. Ravichandran v. State of Tamil Nadu — Madras High Court](https://www.casemine.com/judgement/in/56ea7f4c607dba36cc747d77)
- [M. Gunasekaran v. District Registrar — LiveLaw report](https://www.livelaw.in/high-court/madras-high-court/madras-high-court-pleading-civil-suit-not-instrument-cannot-be-registered-286341)
- [Indian Bank v. Sub Registrar — SARFAESI sale certificate / undisclosed encumbrances](https://ibclaw.in/indian-bank-vs-the-sub-registrar-madras-high-court/)
