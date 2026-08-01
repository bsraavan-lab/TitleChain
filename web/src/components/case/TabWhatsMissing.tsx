import { useState } from "react";
import type { DerivedView, DocRequest } from "../../data/types";

function orderText(r: DocRequest) {
  return [
    `Encumbrance certificate`,
    `SRO: ${r.sro ?? "—"}`,
    `Village: ${r.village ?? "—"}`,
    `Survey numbers: ${r.survey_nos.join(", ")}`,
    `Period: ${r.date_from ?? "—"} to ${r.date_to ?? "—"}`,
  ].join("\n");
}

export function TabWhatsMissing({ view }: { view: DerivedView }) {
  return (
    <section className="section" aria-label="What's missing">
      <h2 className="section-title">Open requests ({view.requests.length})</h2>
      <ul className="row-list">
        {view.requests.map((r) => (
          <li key={r.key}>
            <RequestCard request={r} />
          </li>
        ))}
      </ul>
    </section>
  );
}

function RequestCard({ request }: { request: DocRequest }) {
  const [copied, setCopied] = useState(false);
  return (
    <article className="row row--grouped">
      <span className="row-glyph glyph--stamp" aria-hidden="true">
        ⚑
      </span>
      <div className="row-body">
        <h3 className="row-title">
          Order one more certificate
          <span className="rule-id mono">{request.kind}</span>
        </h3>
        <p className="row-detail">{request.because}</p>
        <dl className="order">
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
          <button
            type="button"
            className="btn btn--ghost"
            onClick={() => {
              void navigator.clipboard?.writeText(orderText(request));
              setCopied(true);
            }}
          >
            {copied ? "Copied" : "Copy the order"}
          </button>
        </div>
        <p className="row-reason">
          Closes {request.closes.length} checks:{" "}
          <span className="mono">{request.closes.join(" · ")}</span>
        </p>
      </div>
    </article>
  );
}
