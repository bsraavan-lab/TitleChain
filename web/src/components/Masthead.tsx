import { Link } from "@tanstack/react-router";
import { ChainMark } from "./ChainMark";
import type { ReactNode } from "react";

/* The mark and the wordmark, locked up as one identity, and the way back to
 * your cases on every screen. */
export function Wordmark({ size = 26 }: { size?: number }) {
  return (
    <Link to="/" className="wordmark" title="Back to your cases">
      <ChainMark size={size} />
      <span className="wordmark-text">TitleChain</span>
    </Link>
  );
}

export function Masthead({
  bar = false,
  center = false,
  children,
}: {
  bar?: boolean;
  center?: boolean;
  children?: ReactNode;
}) {
  return (
    <header className={bar ? "case-bar" : `masthead${center ? " masthead--center" : ""}`}>
      <Wordmark size={bar ? 22 : 26} />
      {children}
    </header>
  );
}
