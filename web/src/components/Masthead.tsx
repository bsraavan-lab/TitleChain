import { Link } from "@tanstack/react-router";
import type { ReactNode } from "react";

/* The mark, and the way back to your cases.
 *
 * It was a plain <span> on all five screens — the Jinja original it was ported
 * from was an <a href="/">, and the port dropped the link. Clicking the name of
 * the product is the first thing anyone tries when they want out of a case, and
 * on every screen it did nothing.
 *
 * `bar` picks the case screen's sticky rule over the home screen's masthead;
 * both carry the same mark, so it lives in one place rather than five.
 */
export function Wordmark() {
  return (
    <Link to="/" className="wordmark" title="Back to your cases">
      TitleChain
    </Link>
  );
}

export function Masthead({ bar = false, children }: { bar?: boolean; children?: ReactNode }) {
  return (
    <header className={bar ? "case-bar" : "masthead"}>
      <Wordmark />
      {children}
    </header>
  );
}
