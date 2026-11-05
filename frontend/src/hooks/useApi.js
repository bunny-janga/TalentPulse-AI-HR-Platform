import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Declarative data loading with cancellation.
 * fetcher(signal) -> Promise. Re-runs when `deps` change or reload() is called.
 * status: idle | loading | refreshing | success | error. Previous data is kept while refreshing
 * so numbers and bars can animate between values instead of flashing a skeleton.
 */
export function useApi(fetcher, deps = [], { enabled = true } = {}) {
  const [state, setState] = useState({ status: enabled ? 'loading' : 'idle', data: null, error: null });
  const [nonce, setNonce] = useState(0);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  useEffect(() => {
    if (!enabled) return undefined;
    const controller = new AbortController();
    setState((s) => ({ ...s, status: s.data === null ? 'loading' : 'refreshing', error: null }));
    fetcherRef.current(controller.signal)
      .then((data) => setState({ status: 'success', data, error: null }))
      .catch((error) => {
        if (error?.kind === 'aborted') return;
        setState((s) => ({ status: 'error', data: s.data, error }));
      });
    return () => controller.abort();
  }, [enabled, nonce, ...deps]); // eslint-disable-line react-hooks/exhaustive-deps

  const reload = useCallback(() => setNonce((n) => n + 1), []);
  /** Local (optimistic) edit of the cached data. */
  const mutate = useCallback((updater) => {
    setState((s) => ({ ...s, data: typeof updater === 'function' ? updater(s.data) : updater }));
  }, []);

  return { ...state, loading: state.status === 'loading', reload, mutate };
}
