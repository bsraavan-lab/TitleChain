import type { DerivedView } from "../../data/types";

export function TabHowItConnects({ view }: { view: DerivedView }) {
  const c = view.coverage;
  const span = c.axis_max - c.axis_min;
  const pos = (y: number) => ((y - c.axis_min) / span) * 100;
  const root = view.chain[0]!;

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
      <p className="row-detail row-detail--lead">
        {root.doc_no} is the only document that has been read. The five documents it points back to
        are named in it and nothing more — that one fact is why each circle below is hollow.
      </p>

      <ul className="chain">
        <li className="chain-node">
          <span className="chain-mark chain-mark--filled glyph--fee" aria-hidden="true">
            ●
          </span>
          <span className="chain-doc mono">{root.doc_no}</span>
          <span className="chain-note">
            {root.nature}
            {root.cancelled_by ? (
              <>
                {" "}
                · cancelled by <span className="mono">{root.cancelled_by}</span>
              </>
            ) : null}
          </span>
          <ul className="chain-children">
            {root.children.map((n) => (
              <li className="chain-node" key={n.doc_no}>
                <span className="chain-mark glyph--stamp" aria-hidden="true">
                  ○
                </span>
                <span className="chain-doc mono">{n.doc_no}</span>
                <span className="chain-note">not read</span>
              </li>
            ))}
          </ul>
        </li>
      </ul>
    </section>
  );
}
