import { useEffect } from 'react';

/** Replays the .shake animation on `ref` each time `trigger` changes to a truthy value. */
export function useShake(ref, trigger) {
  useEffect(() => {
    const el = ref.current;
    if (!el || !trigger) return;
    el.classList.remove('shake');
    void el.offsetWidth; // restart the animation: a single deliberate reflow
    el.classList.add('shake');
  }, [ref, trigger]);
}
