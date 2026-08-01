import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { caseQuery } from "../data/api";
import { Loading, LoadError } from "../components/LoadState";
import { OUTCOME_GLYPH, OUTCOME_TONE, OUTCOME_WORD } from "../data/types";
import type { DerivedView } from "../data/types";

export const Route = createFileRoute("/case/$caseId/refusal")({
  head: () => ({
    meta: [
      { title: "This certificate cannot be used — TitleChain" },
      {
        name: "description",
        content:
          "Why TitleChain will not draw findings from this certificate, which checks could not run, and what to order instead.",
      },
      { property: "og:title", content: "This certificate cannot be used — TitleChain" },
      {
        property: "og:description",
        content: "The checks that could not run, the reason for each, and the one errand that fixes it.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: RefusalPage,
});

function RefusalPage() {
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
  return <RefusalScreen caseId={caseId} view={q.data.view} />;
}

function RefusalScreen({ caseId, view }: { caseId: string; view: DerivedView }) {
  const blocked = view.runs.filter((r) => r.outcome === "FAIL" || r.outcome === "NOT_EVALUABLE");
  const request = view.requests[0]!;

  return (
    <div className="page">
      <header className="masthead">
        <span className="wordmark">TitleChain</span>
      </header>

      <main>
        <section className="section answer" aria-labelledby="refusal-title">
          <p className="kicker">Case {caseId}</p>
          <h1 className="answer-title" id="refusal-title">
            {view.coverage.headline}
          </h1>
          <p className="answer-detail">{view.coverage.detail}</p>
        </section>

        <section className="section" aria-label="Checks that could not run">
          <h2 className="section-title">What could not be concluded</h2>
          <ul className="row-list">
            {blocked.map((r) => (
              <li className="row row--two" key={r.key}>
                <span
                  className={`row-glyph glyph--${OUTCOME_TONE[r.outcome]}`}
                  aria-hidden="true"
                >
                  {OUTCOME_GLYPH[r.outcome]}
                </span>
                <div className="row-body">
                  <h3 className="row-title">
                    <span
                      className={`status-word status-word--${OUTCOME_TONE[r.outcome]}`}
                    >
                      {OUTCOME_WORD[r.outcome]}
                    </span>
                    {r.title}
                    <span className="rule-id mono">{r.rule_id}</span>
                  </h3>
                  <p className="row-detail">{r.message}</p>
                  {r.reason ? <p className="row-reason">{r.reason}</p> : null}
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section className="section" aria-label="What to do instead">
          <h2 className="section-title">What to do instead</h2>
          <dl className="order">
            <div className="inputs-pair">
              <dt className="inputs-label">Order</dt>
              <dd className="inputs-value mono">{request.kind}</dd>
            </div>
            <div className="inputs-pair">
              <dt className="inputs-label">SRO</dt>
              <dd className="inputs-value">{request.sro}</dd>
            </div>
            <div className="inputs-pair">
              <dt className="inputs-label">Village</dt>
              <dd className="inputs-value">{request.village}</dd>
            </div>
            <div className="inputs-pair">
              <dt className="inputs-label">Survey numbers</dt>
              <dd className="inputs-value mono">{request.survey_nos.join(" · ")}</dd>
            </div>
            <div className="inputs-pair">
              <dt className="inputs-label">Period</dt>
              <dd className="inputs-value mono">
                {request.date_from} → {request.date_to}
              </dd>
            </div>
          </dl>
          <div className="findings-actions">
            <Link to="/case/$caseId" params={{ caseId }} className="btn btn--filled">
              Back to the case
            </Link>
          </div>
        </section>
      </main>

      <footer className="footnote">
        TitleChain shows what a certificate does and does not evidence. It does not give an opinion
        on title.
      </footer>
    </div>
  );
}
