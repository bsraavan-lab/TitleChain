import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { addDocument, ApiRejection, caseQuery } from "../../data/api";
import type { DerivedView, DocRequest } from "../../data/types";

/* A gap is only useful if it comes with an errand.
 *
 * Each request is the order already filled in — office, village, every survey
 * number, the computed date range — so "your evidence is short" becomes a copy,
 * a paste into TNREGINET, and a file dropped back here. Without the drop target
 * this screen ends on bad news with no next step.
 */

function orderText(r: DocRequest) {
  return [
    `Encumbrance certificate`,
    `SRO: ${r.sro ?? "—"}`,
    `Village: ${r.village ?? "—"}`,
    `Survey numbers: ${r.survey_nos.join(", ")}`,
    `Period: ${r.date_from ?? "—"} to ${r.date_to ?? "—"}`,
  ].join("\n");
}

export function TabWhatsMissing({ view, caseId }: { view: DerivedView; caseId: string }) {
  if (view.requests.length === 0) {
    return (
      <section className="section" aria-label="What's missing">
        <p className="meta">
          {view.completeness.links_named === 0
            ? "These certificates do not point back to any earlier document. That tells you about these certificates, not about what happened before them."
            : "Every document these certificates point back to is here."}
        </p>
      </section>
    );
  }
  return (
    <section className="section" aria-label="What's missing">
      <h2 className="section-title">Open requests ({view.requests.length})</h2>
      <ul className="row-list">
        {view.requests.map((r) => (
          <li key={r.key}>
            <RequestCard request={r} caseId={caseId} />
          </li>
        ))}
      </ul>
    </section>
  );
}

function RequestCard({ request, caseId }: { request: DocRequest; caseId: string }) {
  const qc = useQueryClient();
  const [copied, setCopied] = useState(false);
  const [dragging, setDragging] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const [sent, setSent] = useState<number | null>(null);

  const add = useMutation({
    mutationFn: (file: File) =>
      addDocument({ caseId, file, requestKey: request.key, onProgress: setSent }),
    onMutate: () => setSent(0),
    onSettled: () => setSent(null),
    // The findings already on screen are not cleared while the new certificate
    // reads. The case does not go blank — which is the difference between
    // completing a title history and restarting an analysis.
    onSuccess: () => qc.invalidateQueries({ queryKey: caseQuery(caseId).queryKey }),
  });
  const rejection = add.error instanceof ApiRejection ? add.error : null;

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

        {/* Where the certificate comes back. Tagged with this request, so the
            case can say afterwards which gap it closed. */}
        <div
          className={`dropzone dropzone--inline${dragging ? " is-over" : ""}`}
          onDragEnter={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragOver={(e) => e.preventDefault()}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            const f = e.dataTransfer.files?.[0];
            if (f) add.mutate(f);
          }}
        >
          <p className="dropzone-meta">
            {add.isPending
              ? sent === null
                ? "On its way — the findings below stay while it reads."
                : `${sent}% sent — the findings below stay while it reads.`
              : "Got it back? Drop it here and it joins this case."}
          </p>
          <input
            ref={fileInput}
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            className="sr-only"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) add.mutate(f);
              e.target.value = "";
            }}
          />
          {add.isPending ? (
            <div
              className="upload-bar"
              role="progressbar"
              aria-label="Sending the certificate"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={sent ?? undefined}
            >
              <span
                className={`upload-fill${sent === null ? " upload-fill--unknown" : ""}`}
                style={sent === null ? undefined : { width: `${sent}%` }}
              />
            </div>
          ) : (
            <button
              type="button"
              className="btn btn--ghost"
              onClick={() => fileInput.current?.click()}
            >
              Add this certificate
            </button>
          )}
        </div>

        {rejection ? (
          <p className="reject-notice" role="alert">
            <span className="row-glyph glyph--seal" aria-hidden="true">
              ▲
            </span>
            <span>{rejection.detail}</span>
          </p>
        ) : add.isError ? (
          <p className="review-error" role="alert">
            That did not upload. Nothing was added to the case — try again.
          </p>
        ) : null}

        <p className="row-reason">
          Closes {request.closes.length} checks:{" "}
          <span className="mono">{request.closes.join(" · ")}</span>
        </p>
      </div>
    </article>
  );
}
