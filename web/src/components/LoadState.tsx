import { useEffect, useState } from "react";

/* A 3×3 pixel grid whose chevron wavefront drives right — the product's one
 * "still working" mark. The 650ms cycle is shorter than the sweep, so two
 * fronts are always in flight. Reduced motion freezes it to its dim state. */
const CHEVRON_DELAYS = Array.from({ length: 9 }, (_, i) => {
  const r = Math.floor(i / 3),
    c = i % 3;
  return (c + Math.abs(r - 1)) * 90;
});

export function PixelWait() {
  return (
    <span className="pixelwait" aria-hidden="true">
      {CHEVRON_DELAYS.map((d, i) => (
        <span key={i} className="pixelwait-cell" style={{ animationDelay: `${d}ms` }} />
      ))}
    </span>
  );
}

/* How long she has been watching this wait, in mono tabular figures. Ticks
 * even under reduced motion — a number changing is information, not motion. */
export function Elapsed() {
  const [ds, setDs] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setDs((d) => d + 1), 100);
    return () => clearInterval(t);
  }, []);
  const total = ds / 10;
  const text =
    total < 60 ? `${total.toFixed(1)}s` : `${Math.floor(total / 60)}m ${(total % 60).toFixed(1)}s`;
  return <span className="wait-elapsed">{text}</span>;
}

export function Loading({ what }: { what: string }) {
  return (
    <p className="loadline loadline--wait" role="status">
      <PixelWait />
      Reading {what}…
    </p>
  );
}

export function LoadError({
  what,
  error,
  onRetry,
}: {
  what: string;
  error: unknown;
  onRetry: () => void;
}) {
  const detail = error instanceof Error ? error.message : String(error);
  return (
    <div className="loaderr" role="alert">
      <p className="loadline">
        {what} could not be loaded. Nothing was lost — no document, finding or case was changed.
      </p>
      <p className="row-reason mono">{detail}</p>
      <p>
        <button type="button" className="quiet-link" onClick={onRetry}>
          Try again
        </button>
      </p>
    </div>
  );
}
