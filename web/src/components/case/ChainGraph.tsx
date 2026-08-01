import type { GraphEdge, GraphLayout, GraphNode } from "../../data/types";

/* The chain, drawn.
 *
 * app/layout.py has always computed this — one node per document, x from the
 * year, y a greedy lane — and /api/case/{id} has always returned it. The React
 * port simply never rendered it: `graph` was typed `unknown` and nothing read
 * it, so the one picture that shows a hole in a title chain existed on the wire
 * and nowhere on screen.
 *
 * Ported from app/templates/_graph_svg.html. The geometry is not recomputed
 * here — that would be a second opinion about where a node goes, and the two
 * would drift. The only thing computed on this side is the edge path, because
 * `GraphEdge.path` is a Python @property and @property does not serialise.
 *
 * The SVG is aria-hidden with a list beside it carrying the same facts, which
 * is the pattern the coverage ruler already uses: a picture for the eye, a
 * sentence for everything else.
 */

/** The cubic in app/layout.py:GraphEdge.path, recomputed from the endpoints. */
function edgePath(e: GraphEdge): string {
  const mid = (e.x1 + e.x2) / 2;
  return `M ${e.x1.toFixed(1)} ${e.y1.toFixed(1)} C ${mid.toFixed(1)} ${e.y1.toFixed(1)} ${mid.toFixed(1)} ${e.y2.toFixed(1)} ${e.x2.toFixed(1)} ${e.y2.toFixed(1)}`;
}

/** app/layout.py:GraphNode.title, same order, same separator. */
function nodeTitle(n: GraphNode): string {
  const bits = [n.doc_no, n.nature ?? "not present on this case"];
  if (n.ec_label) bits.push(n.ec_label);
  if (n.cancelled) bits.push("cancelled");
  if (n.open_encumbrance) bits.push("open encumbrance");
  if (!n.examined) bits.push("unexamined");
  return bits.join(" · ");
}

function NodeShapeMark({ n }: { n: GraphNode }) {
  switch (n.shape) {
    case "square":
      return <rect x={n.x - 10} y={n.y - 10} width={20} height={20} rx={2} />;
    case "diamond":
      return (
        <rect
          x={n.x - 9}
          y={n.y - 9}
          width={18}
          height={18}
          rx={2}
          transform={`rotate(45 ${n.x} ${n.y})`}
        />
      );
    case "bar":
      return <rect x={n.x - 13} y={n.y - 7} width={26} height={14} rx={7} />;
    case "ring":
      return <circle cx={n.x} cy={n.y} r={11} className="g-ring" />;
    default:
      return <circle cx={n.x} cy={n.y} r={11} />;
  }
}

export function ChainGraph({ graph }: { graph: GraphLayout | undefined }) {
  if (!graph || graph.nodes.length === 0) return null;

  return (
    <>
      <div className="graph-scroll">
        <svg
          className="graph"
          viewBox={`0 0 ${graph.width} ${graph.height}`}
          width={graph.width}
          height={graph.height}
          aria-hidden="true"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* year axis */}
          <line className="g-axis" x1={0} y1={26} x2={graph.width} y2={26} />
          {graph.ticks.map((t) => (
            <g key={t.year}>
              <line className="g-tick" x1={t.x} y1={20} x2={t.x} y2={32} />
              <text className="g-year" x={t.x} y={14} textAnchor="middle">
                {t.year}
              </text>
            </g>
          ))}

          {/* edges first, so nodes sit on top of them */}
          {graph.edges.map((e, i) => (
            <path
              key={`${e.x1}-${e.y1}-${e.x2}-${e.y2}-${i}`}
              className={`g-edge g-${e.kind.toLowerCase()} ${e.resolved ? "g-resolved" : "g-dangling"}`}
              d={edgePath(e)}
              fill="none"
            />
          ))}

          {graph.nodes.map((n) => (
            <g
              key={n.doc_no}
              className={[
                "g-node",
                n.examined ? "g-examined" : "g-unexamined",
                n.cancelled ? "g-cancelled" : "",
                n.open_encumbrance ? "g-open" : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              <title>{nodeTitle(n)}</title>
              <NodeShapeMark n={n} />

              {n.cancelled || n.shape === "slash" ? (
                <line className="g-slash" x1={n.x - 13} y1={n.y + 13} x2={n.x + 13} y2={n.y - 13} />
              ) : null}
              {n.corrected ? (
                <text className="g-mark" x={n.x + 13} y={n.y - 10}>
                  ✎
                </text>
              ) : null}

              <text className="g-label" x={n.x} y={n.y + 27} textAnchor="middle">
                {n.doc_no}
              </text>
            </g>
          ))}
        </svg>
      </div>

      <p className="graph-key">
        <span className="k-node k-examined" aria-hidden="true" /> you have this one
        <span className="k-node k-unexamined" aria-hidden="true" /> pointed to, but missing
        <span className="k-node k-open" aria-hidden="true" /> still open
      </p>

      {graph.undated.length > 0 ? (
        <p className="row-detail">
          Not on the line, because nothing dates them:{" "}
          <span className="mono">{graph.undated.join(", ")}</span>.
        </p>
      ) : null}
    </>
  );
}
