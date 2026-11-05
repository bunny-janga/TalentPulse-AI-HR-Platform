import { useCallback, useMemo, useSyncExternalStore } from 'react';

const subscribe = (callback) => {
  window.addEventListener('hashchange', callback);
  return () => window.removeEventListener('hashchange', callback);
};
const getHash = () => window.location.hash;

/** Navigates to a hash route such as "/leave". */
export function navigate(to, { replace = false } = {}) {
  const target = `#${to.startsWith('/') ? to : `/${to}`}`;
  if (replace) window.history.replaceState(null, '', target);
  else window.location.hash = target;
  if (replace) window.dispatchEvent(new HashChangeEvent('hashchange'));
}

/** Hash router: returns { path, query, navigate } and re-renders on hashchange. */
export function useRoute() {
  const hash = useSyncExternalStore(subscribe, getHash, () => '');
  const parsed = useMemo(() => {
    const [rawPath, rawQuery = ''] = (hash.slice(1) || '/').split('?');
    const path = rawPath.startsWith('/') ? rawPath : `/${rawPath}`;
    return { path: path.length > 1 ? path.replace(/\/+$/, '') : path, query: Object.fromEntries(new URLSearchParams(rawQuery)) };
  }, [hash]);
  const go = useCallback(navigate, []);
  return { ...parsed, navigate: go };
}
