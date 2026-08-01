import type { ChainNode, DerivedView, ECDoc, GraphLayout } from "../../data/types";
import { ChainGraph } from "./ChainGraph";

/* A node is drawn read or unread by whether it HAS an entry, not by how deep it
   sits. derive.py sets `entry_id: None` for a document that is only named by
   another one — that is the hollow circle — and `children` recurses as far as
   the references go. This drew exactly two levels and called level two "not
   read", so a document named by a named document was dropped from the chain
   entirely, and a grandchild that was in fact read still showed as hollow. */
function ChainBranch({ node }: { node: ChainNode }) {
  const read = node.entry_id !== null;
  return (
    <li className="chain-node">
      <span
        className={`chain-mark${read ? " chain-mark--filled glyph--fee" : " glyph--stamp"}`}
        aria-hidden="true"
      >
        {read ? "●" : "○"}
      </span>
      <span className="chain-doc mono">{node.doc_no}</span>
      <span className="chain-note">
        {read ? (node.nature ?? "read") : "not read"}
        {node.cancelled_by ? (
          <>
            {" · cancelled by "}
            <span className="mono">{node.cancelled_by}</span>
          </>
        ) : null}
      </span>
      {node.children.length > 0 ? (
        <ul className="chain-children">
          {node.children.map((child) => (
            <ChainBranch node={child} key={child.doc_no} />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

/** Counts for the sentence above the chain, so it states what is there. */
function tally(nodes: ChainNode[]): { read: number; named: number } {
  return nodes.reduce(
    (acc, n) => {
      const sub = tally(n.children);
      return {
        read: acc.read + (n.entry_id !== null ? 1 : 0) + sub.read,
        named: acc.named + (n.entry_id === null ? 1 : 0) + sub.named,
      };
    },
    { read: 0, named: 0 },
  );
}

const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;

/* The window each certificate actually states, as dates rather than years.
   The header carries "01-Jan-2018" / "18-Jun-2023"; the ruler is drawn in
   years, and "2018–2023" does not tell you whether the last six months are
   covered. Falls back to the years when a header could not be read. */
function statedWindow(docs: ECDoc[], fallback: string): string {
  const windows = docs
    .map((d) => {
      const from = d.header?.search_period_start;
      const to = d.header?.search_period_end;
      return from && to ? `${from} → ${to}` : null;
    })
    .filter((w): w is string => w !== null);
  return windows.length ? windows.join(" · ") : fallback;
}

const years = (from: number | null, to: number | null) =>
  from !== null && to !== null ? `${from}–${to}` : "not stated";

export function TabHowItConnects({ view, graph }: { view: DerivedView; graph?: GraphLayout }) {
  const c = view.coverage;
  // A single-year certificate makes axis_max === axis_min, and every `left` and
  // `width` on the ruler below divides by this.
  const span = c.axis_max - c.axis_min;
  /* Clamped, and mirroring Coverage.pct() in app/models.py rather than
     inventing a second geometry: a band whose start predates the axis used to
     compute a negative `left`, which the browser drops silently. */
  const pos = (y: number | null) => {
    if (y === null) return 0;
    if (span <= 0) return 0;
    return Math.min(Math.max(((y - c.axis_min) / span) * 100, 0), 100);
  };
  /* Coverage.width_of()'s floor. A one-year band is 0% wide on a 40-year axis
     and would draw as nothing at all — the certificate would look absent. */
  const width = (from: number | null, to: number | null) =>
    from === null || to === null ? 0 : Math.max(pos(to) - pos(from), 1.5);

  const counts = tally(view.chain);

  return (
    <section className="section" aria-label="How it connects">
      <h2 className="section-title">The years on one line</h2>

      <dl className="ruler-dates">
        <div>
          <dt>This certificate covers</dt>
          <dd className="mono">{statedWindow(view.docs, years(c.start_year, c.end_year))}</dd>
        </div>
        <div>
          <dt>The search needs</dt>
          <dd className="mono">{years(c.required_from, c.required_to)}</dd>
        </div>
        <div>
          <dt>Drawn across</dt>
          <dd className="mono">
            {c.axis_min}–{c.axis_max}
          </dd>
        </div>
      </dl>

      <div className="ruler">
        <div className="ruler-axis">
          {c.bands.map((b) => (
            <span
              key={`${b.ec_id ?? b.label}-${b.start_year ?? "?"}`}
              className="ruler-band"
              style={{
                left: `${pos(b.start_year)}%`,
                width: `${width(b.start_year, b.end_year)}%`,
              }}
            >
              <span className="sr-only">
                {b.label} covers {b.start_year ?? "an unreadable start"} to{" "}
                {b.end_year ?? "an unreadable end"}
              </span>
            </span>
          ))}
          <span
            className="ruler-required"
            style={{
              left: `${pos(c.required_from)}%`,
              width: `${width(c.required_from, c.required_to)}%`,
            }}
          />
          {c.ticks.map((t) => (
            <span
              key={t.year}
              className={`ruler-tick${t.inside ? " ruler-tick--inside" : ""}`}
              style={{ left: `${pos(t.year)}%` }}
            >
              <span className="ruler-tick-year mono">{t.year}</span>
            </span>
          ))}
        </div>
        <p className="ruler-ends mono">
          <span>{c.axis_min}</span>
          <span>{c.axis_max}</span>
        </p>
      </div>

      <ul className="legend">
        <li>
          <span className="legend-swatch legend-swatch--band" aria-hidden="true" /> Certificate
          covers <span className="mono">{years(c.start_year, c.end_year)}</span>
        </li>
        <li>
          <span className="legend-swatch legend-swatch--required" aria-hidden="true" /> Search needs{" "}
          <span className="mono">{years(c.required_from, c.required_to)}</span>
        </li>
        <li>
          <span className="legend-swatch legend-swatch--tick" aria-hidden="true" /> Earlier
          documents dated outside the window
        </li>
      </ul>

      <h2 className="section-title">How the documents connect</h2>

      {/* The drawing the backend has been computing all along. The tree below
          stays: it is the accessible equivalent, and it is what reads when the
          chain is deeper than it is wide. */}
      <ChainGraph graph={graph} />
      {/* Counted, not asserted. This read "{doc} is the only document that has
          been read. The five documents it points back to…" for every case, so a
          case with two certificates and eleven references said one and five. */}
      {view.chain.length === 0 ? (
        <p className="row-detail row-detail--lead">
          Nothing has been read yet, so there is no chain to draw.
        </p>
      ) : (
        <>
          <p className="row-detail row-detail--lead">
            {counts.read > 0
              ? `${plural(counts.read, "document")} here ${counts.read === 1 ? "has" : "have"} been read.`
              : "No document here has been read."}{" "}
            {counts.named > 0
              ? `The ${plural(counts.named, "document")} below with a hollow circle ${counts.named === 1 ? "is" : "are"} named in what was read and nothing more — that one fact is why ${counts.named === 1 ? "it is" : "they are"} hollow.`
              : "Every document named along this chain is here."}
          </p>

          <ul className="chain">
            {view.chain.map((root) => (
              <ChainBranch node={root} key={root.doc_no} />
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
