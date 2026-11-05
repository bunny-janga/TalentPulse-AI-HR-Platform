import { useEffect, useRef, useState } from 'react';
import { useReducedMotion } from './useReducedMotion.js';

const easeOutExpo = (p) => (p >= 1 ? 1 : 1 - 2 ** (-10 * p));

/**
 * Animates a number toward `target` with requestAnimationFrame. When the target
 * changes (data refresh) it continues from the value currently shown.
 * Pass enabled=false to hold at 0 until, for example, the card is in view.
 */
export function useCountUp(target, { duration = 1100, decimals = 0, enabled = true } = {}) {
  const reduced = useReducedMotion();
  const shown = useRef(0);
  const [value, setValue] = useState(0);

  useEffect(() => {
    if (!enabled || !Number.isFinite(target)) return undefined;
    if (reduced) {
      shown.current = target;
      setValue(target);
      return undefined;
    }
    const from = shown.current;
    const delta = target - from;
    if (delta === 0) return undefined;
    let raf = 0;
    let start = 0;
    const step = (now) => {
      if (!start) start = now;
      const p = Math.min(1, (now - start) / duration);
      shown.current = from + delta * easeOutExpo(p);
      setValue(shown.current);
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, enabled, reduced, duration]);

  return Number(value.toFixed(decimals));
}
