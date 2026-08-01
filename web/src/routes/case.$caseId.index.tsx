import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { TabWhatToCheck } from "../components/case/TabWhatToCheck";
import { TabHowItConnects } from "../components/case/TabHowItConnects";
import { TabWhatsMissing } from "../components/case/TabWhatsMissing";
import { TabWhatWeRead } from "../components/case/TabWhatWeRead";
import { TabWhatItCost } from "../components/case/TabWhatItCost";
import { useQuery } from "@tanstack/react-query";
import { caseQuery, pageImageUrl } from "../data/api";
import { Loading, LoadError } from "../components/LoadState";
import type { DerivedView } from "../data/types";

export const Route = createFileRoute("/case/$caseId/")({
  // Generic on purpose. This named one property — "Puliyampatti", "a 13-year
  // search" — for every case id, so case 7 carried case 1's title. The real
  // headline is per-case and lives in the body, where it is true.
  head: () => ({
    meta: [
      { title: "Certificate scrutiny | TitleChain" },
      {
        name: "description",
        content:
          "What this encumbrance certificate covers, what it leaves out, and the page behind every finding.",
      },
      { property: "og:type", content: "website" },
    ],
  }),
  component: CasePage,
});

const TABS = [
  "What to check",
  "How it connects",
  "What's missing",
  "What we read",
  "What it cost",
] as const;

function CasePage() {
  const { caseId } = Route.useParams();
  const q = useQuery(caseQuery(caseId));
  if (q.isPending)
    return (
      <div className="page">
        <Loading what="the case" />
      </div>
    );
  if (q.isError)
    return (
      <div className="page">
        <LoadError what="The case" error={q.error} onRetry={() => void q.refetch()} />
      </div>
    );
  return <CaseScreen caseId={caseId} view={q.data.view} />;
}

function CaseScreen({ caseId, view }: { caseId: string; view: DerivedView }) {
  const [tab, setTab] = useState(0);
  const [page, setPage] = useState(1);
  const c = view.coverage;
  const k = view.completeness;
  // A case still being read has a header but no document rows yet. `docs[0]!`
  // threw straight to the error boundary on exactly the screens that exist to
  // show progress.
  const doc = view.docs[0];

  // The backend's Readiness.ready — all gates passed — recomputed here because
  // it is a plain @property and so never reaches the JSON.
  const ready = view.readiness.gates.every((g) => g.passed);

  // Nothing is read yet on a fresh case, so every denominator here can be 0.
  // Unguarded this rendered `NaN%` and `style={{ width: "NaN%" }}`.
  const pct = (done: number, total: number) =>
    total > 0 ? Math.round((done / total) * 100) : 0;

  const meters = [
    {
      label: "Documents",
      pct: pct(k.links_examined, k.links_named),
      detail: `${k.links_examined} of the ${k.links_named} named documents are here`,
    },
    {
      label: "Years",
      pct: pct(k.years_covered, k.years_required),
      detail: `${k.years_covered} of the ${k.years_required} years you need, ${k.span_from}–${k.span_to}`,
    },
    {
      label: "Checked by you",
      pct: pct(k.review_done, k.review_total),
      detail: `${k.review_done} of ${k.review_total} items`,
    },
  ];

  return (
    <div className="case">
      <header className="case-bar">
        <span className="wordmark">TitleChain</span>
        <span className="case-bar-meta">
          Case <span className="mono">{caseId}</span>
          {doc ? (
            <>
              {" · Certificate "}
              <span className="mono">{doc.label}</span>
            </>
          ) : null}
        </span>
      </header>

      <div className="case-grid">
        <main className="case-main">
          <section className="section answer" aria-labelledby="answer-title">
            <p className="kicker">The finding</p>
            <h1 className="answer-title" id="answer-title">
              {c.headline}
            </h1>
            <p className="answer-detail">{c.detail}</p>
          </section>

          <section className="section meters" aria-label="Coverage">
            {meters.map((m) => (
              <div className="meter" key={m.label}>
                <p className="kicker">{m.label}</p>
                <div className="meter-bar">
                  <span className="meter-fill" style={{ width: `${m.pct}%` }} />
                </div>
                <p className="meter-pct mono">{m.pct}%</p>
                <p className="meter-detail">{m.detail}</p>
              </div>
            ))}
          </section>

          {/* Never a percentage: a file is signable or it is not, and the gate
              chips beside this say which condition is in the way. Derived from
              the gates — this line read a hardcoded "FAIL … Not ready to sign
              off yet" until 2026-07-31, so a certificate that passed every check
              still told her it had failed. */}
          <section className="section verdict" aria-label="Readiness">
            <p className="verdict-line">
              <span className={ready ? "glyph--fee" : "glyph--seal"} aria-hidden="true">
                {ready ? "✓" : "▲"}
              </span>{" "}
              {ready ? "Ready to sign off" : "Not ready to sign off yet"}
            </p>
            <ul className="chips">
              {view.readiness.gates.map((g) => (
                <li className={`chip chip--${g.passed ? "fee" : "stamp"}`} key={g.id}>
                  <span aria-hidden="true">{g.passed ? "✓ " : "⚑ "}</span>
                  {g.label}
                </li>
              ))}
            </ul>
          </section>

          <nav className="tabs" aria-label="Case sections">
            {TABS.map((t, i) => (
              <button
                type="button"
                key={t}
                className={`tab${i === tab ? " tab--active" : ""}`}
                aria-current={i === tab ? "page" : undefined}
                onClick={() => setTab(i)}
              >
                {t}
              </button>
            ))}
          </nav>

          {tab === 0 ? <TabWhatToCheck view={view} /> : null}
          {tab === 1 ? <TabHowItConnects view={view} /> : null}
          {tab === 2 ? <TabWhatsMissing view={view} /> : null}
          {tab === 3 ? <TabWhatWeRead view={view} /> : null}
          {tab === 4 ? <TabWhatItCost view={view} /> : null}
        </main>

        <aside className="case-rail" aria-label="Source document">
          {!doc ? (
            <div className="rail-card">
              <p className="kicker">Source</p>
              <p className="rail-empty">
                Your certificate appears here as soon as the first page is read.
              </p>
            </div>
          ) : (
          <div className="rail-card">
            <div className="rail-head">
              <p className="kicker">Source</p>
              <p className="rail-meta mono">
                {doc.filename} · p. {page} of {doc.page_count}
              </p>
            </div>
            <img
              className="scan"
              src={pageImageUrl(doc.ec_id, page)}
              alt={`Scanned page ${page} of ${doc.filename}`}
            />
            <div className="rail-foot">
              <button
                type="button"
                className="btn btn--ghost"
                disabled={page === 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                ← Previous page
              </button>
              <button
                type="button"
                className="btn btn--ghost"
                disabled={page === doc.page_count}
                onClick={() => setPage((p) => Math.min(doc.page_count, p + 1))}
              >
                Next page →
              </button>
            </div>
          </div>
          )}
        </aside>
      </div>
    </div>
  );
}
