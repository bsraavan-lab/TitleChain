/* The TitleChain mark: one house — pitched roof, chimney on the right slope,
 * eaves slightly past the walls, bottom corners open and curled inward —
 * holding a vertical two-link chain at its centre. Monoline, currentColor,
 * no fill. Scales cleanly from favicon size to hero size.
 *
 * `animated` is used by the working screen: the two links settle together
 * while the certificate is read. It is CSS-only and respects
 * prefers-reduced-motion.
 */
export function ChainMark({
  size = 24,
  muted = false,
  animated = false,
  className = "",
}: {
  size?: number;
  muted?: boolean;
  animated?: boolean;
  className?: string;
}) {
  const cls = [
    "chainmark",
    muted ? "chainmark--muted" : "",
    animated ? "chainmark--animated" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  // Hairline at 24px, held visually constant as the mark grows.
  const stroke = size >= 64 ? 2 : size >= 40 ? 2.2 : 2.6;

  return (
    <svg
      className={cls}
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      stroke="currentColor"
      strokeWidth={stroke}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {/* roof, with eaves running slightly past the walls */}
      <path d="M6.5 21.5 24 6.5l17.5 15" />
      {/* chimney on the right slope */}
      <path d="M35.5 15.8V9.5h3.6v9.6" />
      {/* left wall, bottom corner open and curled inward */}
      <path d="M11.5 20.5v14.8a3.2 3.2 0 0 0 3.2 3.2h3.6" />
      {/* right wall, mirrored */}
      <path d="M36.5 20.5v14.8a3.2 3.2 0 0 1-3.2 3.2h-3.6" />
      {/* the chain: two vertical links joined by a smaller connecting link */}
      <rect className="chainmark-link chainmark-link--top" x="19" y="12" width="10" height="13" rx="5" />
      <rect
        className="chainmark-link chainmark-link--bottom"
        x="19"
        y="26"
        width="10"
        height="13"
        rx="5"
      />
      <rect className="chainmark-join" x="21.6" y="20.5" width="4.8" height="10" rx="2.4" />
    </svg>
  );
}
