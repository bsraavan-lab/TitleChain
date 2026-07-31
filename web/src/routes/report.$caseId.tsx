import { createFileRoute } from "@tanstack/react-router";
import { SiteNav } from "../components/SiteNav";
import { useQuery } from "@tanstack/react-query";
import { caseQuery } from "../data/api";
import { Loading, LoadError } from "../components/LoadState";
import type { DerivedView } from "../data/types";
import { OUTCOME_GLYPH, OUTCOME_TONE, OUTCOME_WORD } from "../data/types";

export const Route = createFileRoute("/report/$caseId")({
  head: () => ({
    meta: [
      { title: "Scrutiny report — Puliyampatti S.No 95/2 | TitleChain" },
      {
        name: "description",
        content:
          "The filed record: property, verdict, certificates read, every check with its outcome, how the documents connect, what is still missing and every entry as read.",
      },
      { property: "og:title", content: "Scrutiny report — Puliyampatti S.No 95/2 | TitleChain" },
      {
        property: "og:description",
        content: "A dated, printable record of what this certificate does and does not evidence.",
      },
      { property: "og:type", content: "article" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ReportPage,
});

function ReportPage() {
  const { caseId } = Route.useParams();
  const q = useQuery(caseQuery(caseId));
  if (q.isPending)
    return (
      <div className="report-wrap">
        <Loading what="the report" />
      </div>
    );
  if (q.isError)
    return (
      <div className="report-wrap">
        <LoadError what="The report" error={q.error} onRetry={() => void q.refetch()} />
      </div>
    );
  return <ReportSheet caseId={caseId} view={q.data.view} />;
}

function ReportSheet({ caseId, view }: { caseId: string; view: DerivedView }) {
  const doc = view.docs[0]!;
  const c = view.coverage;
  const k = view.completeness;
  const root = view.chain[0]!;

  return (
    <div className="report-wrap">
      <div className="report-nav">
        <SiteNav caseId={caseId} />
      </div>

      <article className="sheet">
        <header className="sheet-head">
          <span className="wordmark">TitleChain</span>
          <span className="sheet-meta mono">
            Case {caseId} · Rulebook {view.rulebook_version}
          </span>
        </header>

        <section className="sheet-section">
          <h1 className="sheet-title">Certificate scrutiny report</h1>
          <dl className="order">
            <Pair label="SRO" value={doc.header.sro} />
            <Pair label="Village" value={doc.header.village} />
            <Pair label="Survey numbers" value={doc.header.survey_details.join(" · ")} mono />
            <Pair
              label="Search required"
              value={`${c.required_from} → ${c.required_to}`}
              mono
            />
          </dl>
        </section>

        <section className="sheet-section sheet-verdict">
          <h2 className="section-title">Can this be signed off</h2>
          <p className="sheet-answer">
            <span className="glyph--seal" aria-hidden="true">
              ▲
            </span>{" "}
            <span className="status-word status-word--seal">FAIL</span> {c.headline}
          </p>
          <p className="row-detail row-detail--lead">{c.detail}</p>
        </section>

        <section className="sheet-section">
          <h2 className="section-title">Certificates read</h2>
          <table className="table">
            <thead>
              <tr>
                <th scope="col">Label</th>
                <th scope="col">File</th>
                <th scope="col">Period</th>
                <th scope="col">Issued</th>
                <th scope="col">Pages</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="mono">{doc.label}</td>
                <td className="mono">{doc.filename}</td>
                <td className="mono">
                  {doc.header.search_period_start} → {doc.header.search_period_end}
                </td>
                <td className="mono">{doc.header.issue_date}</td>
                <td className="mono">{doc.page_count}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section className="sheet-section">
          <h2 className="section-title">What this search cannot tell you</h2>
          <ul className="row-list">
            <li className="row row--one">
              <span className="row-glyph glyph--seal" aria-hidden="true">
                ▲
              </span>
              <p className="row-body">
                <span className="row-lead">
                  {k.years_required - k.years_covered} of {k.years_required} years are not covered.
                </span>{" "}
                The certificate covers {c.start_year}–{c.end_year}; the search needs{" "}
                {c.required_from}–{c.required_to}.
              </p>
            </li>
            <li className="row row--one">
              <span className="row-glyph glyph--stamp" aria-hidden="true">
                ⚑
              </span>
              <p className="row-body">
                <span className="row-lead">
                  {k.links_named - k.links_examined} named documents have not been read.
                </span>{" "}
                {k.links_examined} of {k.links_named} is here.
              </p>
            </li>
          </ul>
        </section>

        <section className="sheet-section">
          <h2 className="section-title">Every check we ran ({view.runs.length})</h2>
          <table className="table table--audit">
            <thead>
              <tr>
                <th scope="col">Rule</th>
                <th scope="col">Outcome</th>
                <th scope="col">Check</th>
                <th scope="col">Key</th>
                <th scope="col">Signed off</th>
              </tr>
            </thead>
            <tbody>
              {view.runs.map((r) => (
                <tr key={r.key}>
                  <td className="mono">{r.rule_id}</td>
                  <td>
                    <span className={`glyph--${OUTCOME_TONE[r.outcome]}`} aria-hidden="true">
                      {OUTCOME_GLYPH[r.outcome]}
                    </span>{" "}
                    <span className={`status-word status-word--${OUTCOME_TONE[r.outcome]}`}>
                      {OUTCOME_WORD[r.outcome]}
                    </span>
                  </td>
                  <td>
                    {r.title}
                    <span className="sheet-msg">{r.message}</span>
                    {r.reason ? <span className="sheet-msg">{r.reason}</span> : null}
                  </td>
                  <td className="mono sheet-key">{r.key}</td>
                  <td className="signoff mono">☐</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="sheet-section">
          <h2 className="section-title">How the documents connect</h2>
          <ul className="row-list">
            <li className="row row--one">
              <span className="row-glyph glyph--fee" aria-hidden="true">
                ●
              </span>
              <p className="row-body">
                <span className="mono">{root.doc_no}</span> · {root.nature} · read
                {root.cancelled_by ? (
                  <>
                    {" "}
                    · cancelled by <span className="mono">{root.cancelled_by}</span>
                  </>
                ) : null}
              </p>
            </li>
            {root.children.map((n) => (
              <li className="row row--one" key={n.doc_no}>
                <span className="row-glyph glyph--stamp" aria-hidden="true">
                  ○
                </span>
                <p className="row-body">
                  <span className="mono">{n.doc_no}</span> · named by{" "}
                  <span className="mono">{root.doc_no}</span> · not read
                </p>
              </li>
            ))}
          </ul>
        </section>

        <section className="sheet-section">
          <h2 className="section-title">Still missing</h2>
          {view.requests.map((r) => (
            <dl className="order" key={r.key}>
              <Pair label="Order" value={r.kind} mono />
              <Pair label="SRO" value={r.sro} />
              <Pair label="Village" value={r.village} />
              <Pair label="Survey numbers" value={r.survey_nos.join(" · ")} mono />
              <Pair label="Period" value={`${r.date_from} → ${r.date_to}`} mono />
              <Pair label="Closes" value={r.closes.join(" · ")} mono />
            </dl>
          ))}
        </section>

        <section className="sheet-section">
          <h2 className="section-title">Every entry as read</h2>
          <table className="table table--entries">
            <thead>
              <tr>
                <th scope="col">Sr</th>
                <th scope="col">Document</th>
                <th scope="col">Nature</th>
                <th scope="col">Executed</th>
                <th scope="col">Presented</th>
                <th scope="col">Registered</th>
                <th scope="col">Market value</th>
                <th scope="col">Earlier documents</th>
              </tr>
            </thead>
            <tbody>
              {doc.entries.map((e) => (
                <tr key={e.sr_no}>
                  <td className="mono">{e.sr_no}</td>
                  <td className="mono">{e.doc_no ?? <span className="absent">—</span>}</td>
                  <td>{e.nature ?? <span className="absent">—</span>}</td>
                  <td className="mono">{e.date_execution ?? <span className="absent">—</span>}</td>
                  <td className="mono">
                    {e.date_presentation ?? <span className="absent">—</span>}
                  </td>
                  <td className="mono">
                    {e.date_registration ?? <span className="absent">— not read</span>}
                  </td>
                  <td className="tamil">{e.market_value ?? <span className="absent">—</span>}</td>
                  <td className="mono">
                    {e.pr_numbers.length ? (
                      e.pr_numbers.map((p) => p.doc_no).join(" · ")
                    ) : (
                      <span className="absent">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="sheet-section">
          <h2 className="section-title">Corrections</h2>
          <p className="row-detail">
            {k.corrections === 0
              ? "No values were corrected by hand."
              : `${k.corrections} values were corrected by hand.`}
          </p>
        </section>

        <section className="sheet-section">
          <h2 className="section-title">Notes</h2>
          <div className="notes-box" aria-hidden="true" />
        </section>

        <footer className="footnote">
          TitleChain shows what a certificate does and does not evidence. It does not give an
          opinion on title.
        </footer>
      </article>
    </div>
  );
}

function Pair({ label, value, mono }: { label: string; value: string | null; mono?: boolean }) {
  return (
    <div className="inputs-pair">
      <dt className="inputs-label">{label}</dt>
      <dd className={`inputs-value${mono ? " mono" : ""}`}>
        {value ?? <span className="absent">—</span>}
      </dd>
    </div>
  );
}
