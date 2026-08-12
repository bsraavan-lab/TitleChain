import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { Masthead } from "../components/Masthead";
import { ExplainControl } from "../components/case/ExplainControl";
import { TabWhatToCheck } from "../components/case/TabWhatToCheck";
import { TabHowItConnects } from "../components/case/TabHowItConnects";
import { TabWhatsMissing } from "../components/case/TabWhatsMissing";
import { TabWhatWeRead } from "../components/case/TabWhatWeRead";
import { TabWhatItCost } from "../components/case/TabWhatItCost";
import { useQuery } from "@tanstack/react-query";
import { caseQuery } from "../data/api";
import type { CaseMeta, CostPayload } from "../data/api";
import { Rail, RailProvider } from "../components/case/rail";
import { Loading, LoadError } from "../components/LoadState";
import type { DerivedView, GraphLayout } from "../data/types";

/* The tab is in the URL, because the thing she wants to send someone is never
   "the case" — it is the gap, or the entry she corrected, or the row that will
   not close. Held in useState it was neither linkable nor bookmarkable, and the
   back button walked out of the case instead of back a tab. The rendered app has
   had /case/{id}/tab/{name} throughout. */
const TABS = [
  { key: "review", label: "What to check" },
  { key: "chain", label: "How it connects" },
  { key: "missing", label: "What's missing" },
  { key: "entries", label: "What we read" },
  { key: "cost", label: "What it cost" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

const isTabKey = (v: unknown): v is TabKey => TABS.some((t) => t.key === v);

export const Route = createFileRoute("/case/$caseId/")({
  // Optional, and an unknown value is dropped rather than raised: a mistyped
  // link should still open the case, on the first tab. Required here instead
  // would mean every link to a case anywhere had to name a tab, which is a
  // demand the URL has no business making.
  validateSearch: (search: Record<string, unknown>): { tab?: TabKey } =>
    isTabKey(search["tab"]) ? { tab: search["tab"] } : {},
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

function CasePage() {
  const { caseId } = Route.useParams();
  const navigate = useNavigate();
  const q = useQuery(caseQuery(caseId));

  /* Arriving here on a case with no derivation behind it — a bookmark, a
     refresh, a link someone sent — would render every meter at zero and every
     tab empty, which reads as a certificate that proves nothing rather than one
     that has not been read, or could not be. Both of those have a screen.
     The working screen forwards back here when the pipeline finishes, so this
     is a handoff and not a redirect loop. */
  const processing = q.data?.case.processing === true;
  const refused = q.data?.case.status === "FAILED" || q.data?.case.status === "REFUSED";
  useEffect(() => {
    if (processing) void navigate({ to: "/case/$caseId/working", params: { caseId } });
    else if (refused) void navigate({ to: "/case/$caseId/refusal", params: { caseId } });
  }, [processing, refused, caseId, navigate]);

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
  if (processing || refused)
    return (
      <div className="page">
        <Loading what="the case" />
      </div>
    );
  return (
    <CaseScreen
      caseId={caseId}
      view={q.data.view}
      cost={q.data.cost}
      meta={q.data.case}
      graph={q.data.graph}
    />
  );
}

function CaseScreen({
  caseId,
  view,
  cost,
  meta,
  graph,
}: {
  caseId: string;
  view: DerivedView;
  cost: CostPayload;
  meta: CaseMeta;
  graph: GraphLayout;
}) {
  const { tab = "review" } = Route.useSearch();
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
  const pct = (done: number, total: number) => (total > 0 ? Math.round((done / total) * 100) : 0);

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
    <RailProvider>
      <div className="case">
        <Masthead bar>
          <span className="case-bar-meta">
            Case <span className="mono">{caseId}</span>
            {doc ? (
              <>
                {" · Certificate "}
                <span className="mono">{doc.label}</span>
              </>
            ) : null}
          </span>
        </Masthead>

        <div className="case-grid">
          <main className="case-main">
            <section className="section answer" aria-labelledby="answer-title">
              <p className="kicker">The finding</p>
              <h1 className="answer-title" id="answer-title">
                {c.headline}
              </h1>
              <p className="answer-detail">{c.detail}</p>
              <ExplainControl target={{ caseId }} label="Hear where this case stands" />
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

            {/* Links, not buttons: a tab is an address now, so it should middle-
              click into a new window and copy from the context menu like any
              other. `replace` keeps the back button meaning "out of this case"
              rather than a walk through every tab visited on the way. */}
            <nav className="tabs" aria-label="Case sections">
              {TABS.map((t) => (
                <Link
                  key={t.key}
                  to="/case/$caseId"
                  params={{ caseId }}
                  search={{ tab: t.key }}
                  replace
                  className={`tab${t.key === tab ? " tab--active" : ""}`}
                  aria-current={t.key === tab ? "page" : undefined}
                >
                  {t.label}
                </Link>
              ))}
            </nav>

            {tab === "review" ? <TabWhatToCheck view={view} caseId={caseId} /> : null}
            {tab === "chain" ? <TabHowItConnects view={view} graph={graph} /> : null}
            {tab === "missing" ? <TabWhatsMissing view={view} caseId={caseId} /> : null}
            {tab === "entries" ? <TabWhatWeRead view={view} caseId={caseId} /> : null}
            {tab === "cost" ? <TabWhatItCost view={view} cost={cost} meta={meta} /> : null}
          </main>

          <aside className="case-rail" aria-label="Source document">
            <Rail doc={doc} />
          </aside>
        </div>
      </div>
    </RailProvider>
  );
}
