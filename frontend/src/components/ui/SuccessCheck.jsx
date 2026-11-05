/** Animated success mark: the ring and the tick draw themselves with stroke-dashoffset. */
export function SuccessCheck({ size = 56 }) {
  return (
    <svg className="success-check" width={size} height={size} viewBox="0 0 56 56" fill="none" role="img" aria-label="Success">
      <circle className="check-ring" cx="28" cy="28" r="25" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" opacity=".35" />
      <path className="check-draw" d="M17 29l8 8 14-16" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
