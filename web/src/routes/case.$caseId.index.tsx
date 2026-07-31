import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { SiteNav } from "../components/SiteNav";
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
  head: () => ({
    meta: [
      { title: "Certificate scrutiny — Puliyampatti | TitleChain" },
      {
        name: "description",
        content:
          "The working screen: what this encumbrance certificate covers, the five earlier documents nobody has read, and the sixteen years it leaves out.",
      },
      { property: "og:title", content: "Certificate scrutiny — Puliyampatti | TitleChain" },
      {
        property: "og:description",
        content:
          "This certificate cannot support a 13-year search. See every check, the years on one line, and the page behind each finding.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
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
  const doc = view.docs[0]!;

  const meters = [
    {
      label: "Documents",
      pct: Math.round((k.links_examined / k.links_named) * 100),
      detail: `${k.links_examined} of the ${k.links_named} named documents are here`,
    },
    {
      label: "Years",
      pct: Math.round((k.years_covered / k.years_required) * 100),
      detail: `${k.years_covered} of the ${k.years_required} years you need, ${k.span_from}–${k.span_to}`,
    },
    {
      label: "Checked by you",
      pct: Math.round((k.review_done / k.review_total) * 100),
      detail: `${k.review_done} of ${k.review_total} items`,
    },
  ];

  return (
    <div className="case">
      <header className="case-bar">
        <span className="wordmark">TitleChain</span>
        <span className="case-bar-meta">
          Case <span className="mono">{caseId}</span> · Certificate{" "}
          <span className="mono">{doc.label}</span>
        </span>
        <SiteNav caseId={caseId} />
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

          <section className="section verdict" aria-label="Readiness">
            <p className="verdict-line">
              <span className="glyph--seal" aria-hidden="true">
                ▲
              </span>{" "}
              <span className="status-word status-word--seal">FAIL</span> Not ready to sign off yet
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
        </aside>
      </div>
    </div>
  );
}
