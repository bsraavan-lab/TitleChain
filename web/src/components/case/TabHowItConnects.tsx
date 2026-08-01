import type { ChainNode, DerivedView } from "../../data/types";

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

export function TabHowItConnects({ view }: { view: DerivedView }) {
  const c = view.coverage;
  // A single-year certificate makes axis_max === axis_min, and every `left` and
  // `width` on the ruler below divides by this.
  const span = c.axis_max - c.axis_min;
  const pos = (y: number) => (span > 0 ? ((y - c.axis_min) / span) * 100 : 0);
  const counts = tally(view.chain);

  return (
    <section className="section" aria-label="How it connects">
      <h2 className="section-title">The years on one line</h2>

      <div className="ruler">
        <div className="ruler-axis">
          {c.bands.map((b) => (
            <span
              key={b.label}
              className="ruler-band"
              style={{ left: `${pos(b.from_year)}%`, width: `${pos(b.to_year) - pos(b.from_year)}%` }}
            >
              <span className="sr-only">
                {b.label} covers {b.from_year} to {b.to_year}
              </span>
            </span>
          ))}
          <span
            className="ruler-required"
            style={{
              left: `${pos(c.required_from)}%`,
              width: `${pos(c.required_to) - pos(c.required_from)}%`,
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
          covers <span className="mono">{c.start_year}–{c.end_year}</span>
        </li>
        <li>
          <span className="legend-swatch legend-swatch--required" aria-hidden="true" /> Search needs{" "}
          <span className="mono">
            {c.required_from}–{c.required_to}
          </span>
        </li>
        <li>
          <span className="legend-swatch legend-swatch--tick" aria-hidden="true" /> Earlier
          documents dated outside the window
        </li>
      </ul>

      <h2 className="section-title">How the documents connect</h2>
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
