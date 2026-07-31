import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/system")({
  head: () => ({
    meta: [
      { title: "TitleChain Specimen Sheet — One row grammar, three densities" },
      {
        name: "description",
        content:
          "The unified TitleChain component grammar: one status row and one numeric register, shown plainly, as a checklist, and counted.",
      },
      { property: "og:title", content: "TitleChain Specimen Sheet" },
      {
        property: "og:description",
        content:
          "One row component across three densities, plus a single numeric register. The reference the value screen and the working screen are rebuilt from.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: SystemPage,
});

/* ---------- static specimen data ---------- */

const plainly = [
  {
    glyph: "▲",
    tone: "seal",
    status: "Blocking",
    lead: "You pick the years blind.",
    clause: "The search window is chosen before anything is known about the plot.",
  },
  {
    glyph: "⚑",
    tone: "stamp",
    status: "Needs a check",
    lead: "Trails run off the edge.",
    clause: "Entries point at deeds dated outside the range that was paid for.",
  },
  {
    glyph: "○",
    tone: "muted",
    status: "Indistinguishable",
    lead: "Clean and useless look alike.",
    clause: "“Nothing found” prints exactly the same as “wrong years”.",
  },
];

const grouped = ["DOC-1994-0412", "DOC-1997-1180", "DOC-2001-0033", "DOC-2004-2917", "DOC-2009-0561"];

function SystemPage() {
  return (
    <div className="sys-page">
      <header className="sys-masthead">
        <span className="wordmark">TitleChain</span>
        <span className="masthead-note">Specimen sheet · one grammar, three contexts</span>
      </header>

      <main>
        {/* 1 — Stated plainly */}
        <section className="sys-section" aria-labelledby="sys-plain">
          <p className="kicker" id="sys-plain">
            Stated plainly
          </p>
          <ul className="row-list">
            {plainly.map((r) => (
              <li className="row row--one" key={r.lead}>
                <span className={`row-glyph glyph--${r.tone}`} aria-hidden="true">
                  {r.glyph}
                </span>
                <p className="row-body">
                  <span className="sr-only">{r.status}: </span>
                  <strong className="row-lead">{r.lead}</strong> {r.clause}
                </p>
              </li>
            ))}
          </ul>
        </section>

        {/* 2 — A checklist */}
        <section className="sys-section" aria-labelledby="sys-check">
          <p className="kicker" id="sys-check">
            A checklist
          </p>

          <ul className="row-list">
            <li className="row row--two row--failed">
              <span className="row-glyph glyph--seal" aria-hidden="true">
                ▲
              </span>
              <div className="row-body">
                <h3 className="row-title row-title--lead">
                  <span className="status-word status-word--seal">Failed</span>
                  The certificate stops eleven years short of the sale it is meant to cover.
                  <span className="rule-id mono">EC-04</span>
                </h3>
                <p className="row-detail row-detail--lead">
                  Range ends 31 Mar 2013; the deed relied on is dated 12 Aug 2024. Nothing between
                  those dates has been searched.
                </p>
                <details className="row-more">
                  <summary className="row-more-summary">Show the reasoning</summary>
                  <p className="row-detail">
                    Rule EC-04 compares the certificate’s stated range against every date cited in
                    the schedule. Two citations fall outside it.
                  </p>
                </details>
              </div>
            </li>

            <li className="row row--two row--grouped">
              <span className="row-glyph glyph--stamp" aria-hidden="true">
                ⚑
              </span>
              <div className="row-body">
                <h3 className="row-title">
                  <span className="status-word status-word--stamp">Couldn’t check</span>
                  Five documents are named but never read.
                  <span className="rule-id mono">EC-11</span>
                </h3>
                <p className="row-detail">
                  Each is cited in the schedule with no corresponding entry in the body.
                </p>
                <ul className="chip-row">
                  {grouped.map((id) => (
                    <li key={id}>
                      <a className="doc-chip mono" href="#doc">
                        {id}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            </li>

            <li className="row row--two">
              <span className="row-glyph glyph--stamp" aria-hidden="true">
                ⚑
              </span>
              <div className="row-body">
                <h3 className="row-title">
                  <span className="sr-only">To review: </span>
                  Sale deed and mortgage share a registration number.
                  <span className="rule-id mono">EC-07</span>
                </h3>
                <p className="row-detail">
                  Both entries print 1180/1997. One of them is a transcription error.
                </p>
              </div>
            </li>
          </ul>

          <details className="quiet">
            <summary className="quiet-summary">Settled — 9 checks passed, 3 not applicable</summary>
            <ul className="quiet-list">
              <li className="row row--compact">
                <span className="row-glyph glyph--fee" aria-hidden="true">
                  ✓
                </span>
                <p className="row-detail">
                  <span className="sr-only">Passed: </span>
                  Plot description matches the schedule.
                  <span className="rule-id mono">EC-01</span>
                </p>
              </li>
              <li className="row row--compact">
                <span className="row-glyph glyph--fee" aria-hidden="true">
                  ✓
                </span>
                <p className="row-detail">
                  <span className="sr-only">Passed: </span>
                  Registrar seal present on every page.
                  <span className="rule-id mono">EC-02</span>
                </p>
              </li>
              <li className="row row--compact">
                <span className="row-glyph glyph--muted" aria-hidden="true">
                  ⊘
                </span>
                <p className="row-detail">
                  <span className="sr-only">Not applicable: </span>
                  Agricultural conversion order — not a farm plot.
                  <span className="rule-id mono">EC-19</span>
                </p>
              </li>
            </ul>
          </details>
        </section>

        {/* 3 — Counted */}
        <section className="sys-section" aria-labelledby="sys-count">
          <p className="kicker" id="sys-count">
            Counted
          </p>

          <ul className="register">
            <li className="figure">
              <span className="figure-value mono">3 of 4</span>
              <span className="figure-label">Certificates that fell short</span>
            </li>
            <li className="figure">
              <span className="figure-value mono">~60s</span>
              <span className="figure-label">To read one certificate</span>
            </li>
            <li className="figure">
              <span className="figure-value mono">5–10 yrs</span>
              <span className="figure-label">Before the gap surfaces</span>
            </li>
          </ul>

          <ul className="register register--bars">
            <li className="figure">
              <span className="figure-value mono">17%</span>
              <span className="figure-label">Documents read</span>
              <span className="figure-bar">
                <span className="figure-fill" style={{ width: "17%" }} />
              </span>
            </li>
            <li className="figure">
              <span className="figure-value mono">27%</span>
              <span className="figure-label">Years covered</span>
              <span className="figure-bar">
                <span className="figure-fill" style={{ width: "27%" }} />
              </span>
            </li>
            <li className="figure">
              <span className="figure-value mono">0%</span>
              <span className="figure-label">Chain checked</span>
              <span className="figure-bar">
                <span className="figure-fill" style={{ width: "0%" }} />
              </span>
            </li>
          </ul>
        </section>
      </main>

      <footer className="footnote">
        One status column, one label register, one numeric face. Everything else is tier.
      </footer>
    </div>
  );
}
