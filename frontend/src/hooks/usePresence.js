import { useEffect, useState } from 'react';

/**
 * Keeps a component mounted for `ms` after `open` turns false so an exit animation can play.
 * Returns { mounted, closing }.
 */
export function usePresence(open, ms = 250) {
  const [mounted, setMounted] = useState(open);
  const [closing, setClosing] = useState(false);

  useEffect(() => {
    if (open) {
      setMounted(true);
      setClosing(false);
      return undefined;
    }
    if (!mounted) return undefined;
    setClosing(true);
    const id = setTimeout(() => { setMounted(false); setClosing(false); }, ms);
    return () => clearTimeout(id);
  }, [open, ms]); // eslint-disable-line react-hooks/exhaustive-deps

  return { mounted, closing };
}
