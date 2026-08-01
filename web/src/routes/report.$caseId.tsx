import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { caseQuery } from "../data/api";
import { Loading, LoadError } from "../components/LoadState";
import { Wordmark } from "../components/Masthead";
import type { ChainNode, DerivedView } from "../data/types";
import { OUTCOME_GLYPH, OUTCOME_TONE, OUTCOME_WORD } from "../data/types";

export const Route = createFileRoute("/report/$caseId")({
  head: () => ({
    meta: [
      { title: "Title scrutiny report | TitleChain" },
      {
        name: "description",
        content:
          "The filed record: property, verdict, certificates read, every check with its outcome, how the documents connect, what is still missing and every entry as read.",
      },
      { property: "og:title", content: "The checks that ran, the ones that could not, and what is still missing." },
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

/** Depth-first, carrying who named each document — a printed sheet reads better
    as one list than as nested indentation, but nothing may be dropped from it. */
function flattenChain(
  nodes: ChainNode[],
  namedBy: string | null = null,
): { node: ChainNode; namedBy: string | null }[] {
  return nodes.flatMap((node) => [
    { node, namedBy },
    ...flattenChain(node.children, node.doc_no),
  ]);
}

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
  return (
    <ReportSheet caseId={caseId} view={q.data.view} reviews={q.data.review_by_key} />
  );
}

/* Exported so the sheet can be rendered against a real derivation without a
   router. It is the artefact that goes to a bank; it is worth checking. */
export function ReportSheet({
  caseId,
  view,
  reviews,
}: {
  caseId: string;
  view: DerivedView;
  reviews: Record<string, unknown>;
}) {
  const c = view.coverage;
  const k = view.completeness;

  // Readiness.ready — every gate passed. A plain @property on the Python side,
  // so it never reaches the JSON and has to be recomputed. This sheet printed a
  // literal "▲ FAIL" for every case ever rendered; the case screen was fixed on
  // 2026-07-31 and this one was not, which left the artefact that goes to a bank
  // as the last place still saying it.
  const ready = view.readiness.gates.every((g) => g.passed);

  // Both counted, because both of the rows below assert a shortfall and neither
  // should appear when there is none.
  const yearsShort = Math.max(k.years_required - k.years_covered, 0);
  const docsShort = Math.max(k.links_named - k.links_examined, 0);

  const head = view.docs.find((d) => d.header)?.header ?? null;

  return (
    <div className="report-wrap">
      {/* This was an empty div with a border on it: a hairline across the top
          of the sheet and no way back. The report is the thing she files and
          forwards, so the two things to do with it belong here. */}
      <div className="report-nav">
        <Link to="/case/$caseId" params={{ caseId }} className="quiet-link">
          Back to the case
        </Link>
        <button type="button" className="quiet-link" onClick={() => window.print()}>
          Print this record
        </button>
      </div>

      <article className="sheet">
        <header className="sheet-head">
          <Wordmark />
          <span className="sheet-meta mono">
            Case {caseId} · Rulebook {view.rulebook_version}
          </span>
        </header>

        <section className="sheet-section">
          <h1 className="sheet-title">Certificate scrutiny report</h1>
          <dl className="order">
            {/* The property this case is about, from the first certificate that
                carries a header. `docs[0]!.header` threw to the error boundary
                on a case whose first document had not been read yet. */}
            <Pair label="SRO" value={head?.sro ?? null} />
            <Pair label="Village" value={head?.village ?? null} />
            <Pair label="Survey numbers" value={head?.survey_details.join(" · ") ?? null} mono />
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
            <span className={ready ? "glyph--fee" : "glyph--seal"} aria-hidden="true">
              {ready ? "✓" : "▲"}
            </span>{" "}
            <span className={`status-word status-word--${ready ? "fee" : "seal"}`}>
              {ready ? "Ready to sign off" : "Not ready to sign off yet"}
            </span>{" "}
            {c.headline}
          </p>
          <ul className="report-gates">
            {view.readiness.gates.map((g) => (
              <li key={g.id}>
                <span className={g.passed ? "glyph--fee" : "glyph--stamp"} aria-hidden="true">
                  {g.passed ? "✓" : "⚑"}
                </span>{" "}
                {g.label}
              </li>
            ))}
          </ul>
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
            {/* Every certificate on the case. A table with one hardcoded row,
                on a case that grows certificates by design — the second one she
                orders to close a gap was never listed in the record of what was
                read. */}
            <tbody>
              {view.docs.map((d) => (
                <tr key={d.label}>
                  <td className="mono">{d.label}</td>
                  <td className="mono">{d.filename}</td>
                  <td className="mono">
                    {d.header ? (
                      <>
                        {d.header.search_period_start} → {d.header.search_period_end}
                      </>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="mono">{d.header?.issue_date ?? "—"}</td>
                  <td className="mono">{d.page_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="sheet-section">
          <h2 className="section-title">What this search cannot tell you</h2>
          {/* Both rows used to print unconditionally, under a blocking glyph. On
              a complete case the sheet stated "0 of 13 years are not covered"
              beside a ▲ — an alarm raised about its own absence. A shortfall is
              listed when there is one; when there is not, that is the finding. */}
          {yearsShort === 0 && docsShort === 0 ? (
            <p className="row-detail">
              Nothing. The certificates cover every year the search needs, and every document
              they name is here.
            </p>
          ) : (
            <ul className="row-list">
              {yearsShort > 0 ? (
                <li className="row row--one">
                  <span className="row-glyph glyph--seal" aria-hidden="true">
                    ▲
                  </span>
                  <p className="row-body">
                    <span className="row-lead">
                      {yearsShort} of {k.years_required} years are not covered.
                    </span>{" "}
                    The certificate covers {c.start_year}–{c.end_year}; the search needs{" "}
                    {c.required_from}–{c.required_to}.
                  </p>
                </li>
              ) : null}
              {docsShort > 0 ? (
                <li className="row row--one">
                  <span className="row-glyph glyph--stamp" aria-hidden="true">
                    ⚑
                  </span>
                  <p className="row-body">
                    <span className="row-lead">
                      {docsShort} named {docsShort === 1 ? "document has" : "documents have"} not
                      been read.
                    </span>{" "}
                    {k.links_examined} of {k.links_named} {k.links_named === 1 ? "is" : "are"} here.
                  </p>
                </li>
              ) : null}
            </ul>
          )}
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
                  {/* Her record, not a blank box. This printed a literal ☐ on
                      every row of every report, so a check she had gone through
                      and signed off filed as unreviewed — which is the opposite
                      of what the sheet is for. */}
                  <td className="signoff mono">{r.key in reviews ? "☑" : "☐"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="sheet-section">
          <h2 className="section-title">How the documents connect</h2>
          {/* Flattened depth-first rather than nested, because this is a filed
              sheet that has to print. It used to render `chain[0]` and one level
              of its children, so on a case with more than one root certificate
              the record showed one of them, and any document named by a named
              document was left out of the record entirely. */}
          <ul className="row-list">
            {flattenChain(view.chain).map((row, i) => (
              <li className="row row--one" key={`${row.node.doc_no}-${i}`}>
                <span
                  className={`row-glyph glyph--${row.node.entry_id !== null ? "fee" : "stamp"}`}
                  aria-hidden="true"
                >
                  {row.node.entry_id !== null ? "●" : "○"}
                </span>
                <p className="row-body">
                  <span className="mono">{row.node.doc_no}</span>
                  {row.namedBy ? (
                    <>
                      {" · named by "}
                      <span className="mono">{row.namedBy}</span>
                    </>
                  ) : null}
                  {row.node.entry_id !== null ? ` · ${row.node.nature ?? "read"} · read` : " · not read"}
                  {row.node.cancelled_by ? (
                    <>
                      {" · cancelled by "}
                      <span className="mono">{row.node.cancelled_by}</span>
                    </>
                  ) : null}
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
            {/* Across every certificate, headed by which one each entry came
                from — "every entry as read" listed only the first document's,
                so on a case with two certificates the sheet under-reported what
                had been read while calling itself complete. */}
            <tbody>
              {view.docs.flatMap((d) =>
                d.entries.map((e) => (
                <tr key={`${d.label}-${e.sr_no}`}>
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
                )),
              )}
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
