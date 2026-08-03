import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { cropImageUrl, pageImageUrl, pageviewImageUrl } from "../../data/api";
import type { ECDoc } from "../../data/types";

/* The rail is a pane, never a modal.
 *
 * She checks several findings in a row, and a modal would make that open, close,
 * lose your place, open again. It is also never empty: it holds the certificate
 * itself from the first frame, so half the screen is not blank until the first
 * click.
 *
 * Two modes, one shell, so the controls do not move under the cursor when the
 * mode changes:
 *
 *   document  — page through the scan. What the rail shows on arrival.
 *   evidence  — one entry pinned, as a close-up crop or the whole page, with a
 *               way back to the document at that entry's page.
 */

export type RailTarget =
  | { kind: "document"; page: number }
  | { kind: "entry"; entryId: number; close: boolean }
  | { kind: "page"; ecId: number; page: number };

interface RailApi {
  target: RailTarget;
  show: (t: RailTarget) => void;
}

const RailContext = createContext<RailApi | null>(null);

export function RailProvider({ children }: { children: ReactNode }) {
  const [target, setTarget] = useState<RailTarget>({ kind: "document", page: 1 });
  const api = useMemo(() => ({ target, show: setTarget }), [target]);
  return <RailContext.Provider value={api}>{children}</RailContext.Provider>;
}

export function useRail(): RailApi {
  const ctx = useContext(RailContext);
  if (!ctx) throw new Error("useRail outside a RailProvider");
  return ctx;
}

/* The one way back to the page.
 *
 * Every "see it on the page" in the product is this button — the checklist, the
 * entries table, the chain. One class, one behaviour: a second way to say the
 * same thing is a second thing to keep in step. */
export function SourceButton({
  entryId,
  children = "See it on the page",
}: {
  entryId: number;
  children?: ReactNode;
}) {
  const { show } = useRail();
  return (
    <button
      className="link"
      type="button"
      onClick={() => show({ kind: "entry", entryId, close: true })}
    >
      {children}
    </button>
  );
}

export function PageButton({ ecId, page }: { ecId: number; page: number }) {
  const { show } = useRail();
  return (
    <button className="link" type="button" onClick={() => show({ kind: "page", ecId, page })}>
      Open page {page}
    </button>
  );
}

export function Rail({ doc }: { doc: ECDoc | undefined }) {
  const { target, show } = useRail();

  if (!doc) {
    return (
      <div className="rail-card">
        <p className="kicker">Source</p>
        <p className="rail-empty">
          Your certificate appears here as soon as the first page is read.
        </p>
      </div>
    );
  }

  if (target.kind === "entry") {
    const entry = doc.entries.find((e) => e.db_id === target.entryId);
    return (
      <div className="rail-card">
        <div className="rail-head">
          <p className="kicker">Entry {entry ? entry.sr_no : target.entryId}</p>
          <div className="seg" role="group" aria-label="How much of the page to show">
            <button
              type="button"
              className={`seg-btn${target.close ? " seg-on" : ""}`}
              aria-pressed={target.close}
              onClick={() => show({ ...target, close: true })}
            >
              Close up
            </button>
            <button
              type="button"
              className={`seg-btn${target.close ? "" : " seg-on"}`}
              aria-pressed={!target.close}
              onClick={() => show({ ...target, close: false })}
            >
              Whole page
            </button>
          </div>
        </div>
        <img
          className="scan"
          src={target.close ? cropImageUrl(target.entryId) : pageviewImageUrl(target.entryId)}
          alt={
            entry
              ? `Entry ${entry.sr_no}${entry.doc_no ? `, document ${entry.doc_no}` : ""}, as it appears on the scanned page`
              : "The region of the scanned page this finding came from"
          }
        />
        <div className="rail-foot">
          <button
            type="button"
            className="btn btn--ghost"
            onClick={() => show({ kind: "document", page: 1 })}
          >
            ✕ Back to the certificate
          </button>
        </div>
      </div>
    );
  }

  const ecId = target.kind === "page" ? target.ecId : doc.ec_id;
  const page = target.page;
  return (
    <div className="rail-card">
      <div className="rail-head">
        <p className="kicker">Certificate</p>
        <p className="rail-meta mono">
          {doc.filename} · p. {page} of {doc.page_count}
        </p>
      </div>
      <img
        className="scan"
        src={pageImageUrl(ecId, page)}
        alt={`Scanned page ${page} of ${doc.filename}`}
      />
      <div className="rail-foot">
        <button
          type="button"
          className="btn btn--ghost"
          disabled={page <= 1}
          onClick={() => show({ kind: "document", page: Math.max(1, page - 1) })}
        >
          ← Previous page
        </button>
        <button
          type="button"
          className="btn btn--ghost"
          disabled={page >= doc.page_count}
          onClick={() =>
            show({ kind: "document", page: Math.min(doc.page_count, page + 1) })
          }
        >
          Next page →
        </button>
      </div>
    </div>
  );
}
