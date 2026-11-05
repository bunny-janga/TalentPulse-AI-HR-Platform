import { useCountUp } from '../../hooks/useCountUp.js';
import { useInView } from '../../hooks/useInView.js';

/** Tabular number that counts up when scrolled into view and re-animates when `value` changes. */
export function AnimatedNumber({ value, decimals = 0, prefix = '', suffix = '', className }) {
  const [ref, inView] = useInView({ threshold: 0.4 });
  const shown = useCountUp(Number(value) || 0, { decimals, enabled: inView });
  const final = (Number(value) || 0).toFixed(decimals);
  return (
    <span ref={ref} className={`num ${className ?? ''}`}>
      <span aria-hidden="true">{prefix}{shown.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}{suffix}</span>
      <span className="sr-only">{prefix}{final}{suffix}</span>
    </span>
  );
}
