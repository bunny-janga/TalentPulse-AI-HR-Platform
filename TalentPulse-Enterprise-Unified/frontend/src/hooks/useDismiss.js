import { useEffect } from 'react';

/** Calls onDismiss(event) on an outside pointer press or Escape while `active` is true. */
export function useDismiss(ref, active, onDismiss) {
  useEffect(() => {
    if (!active) return undefined;
    const onDown = (e) => { if (ref.current && !ref.current.contains(e.target)) onDismiss(e); };
    const onKey = (e) => { if (e.key === 'Escape') onDismiss(e); };
    document.addEventListener('pointerdown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('pointerdown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [ref, active, onDismiss]);
}
