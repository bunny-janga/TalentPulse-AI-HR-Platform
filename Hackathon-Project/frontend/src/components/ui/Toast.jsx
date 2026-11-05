import { createContext, useCallback, useContext, useEffect, useMemo, useReducer, useRef } from 'react';
import { Icon } from './Icon.jsx';
import { GlassPanel } from './Card.jsx';
import { cx } from '../../utils/cx.js';

const ToastContext = createContext(null);
const DURATION = 4500;
const EXIT_MS = 250;

function reducer(state, action) {
  switch (action.type) {
    case 'add': return [...state.slice(-3), action.toast]; // keep at most four on screen
    case 'leave': return state.map((t) => (t.id === action.id ? { ...t, leaving: true } : t));
    case 'remove': return state.filter((t) => t.id !== action.id);
    default: return state;
  }
}

const ICONS = { success: 'check', error: 'alert', info: 'info' };

/** Provides useToast() and renders the live region. */
export function ToastProvider({ children }) {
  const [toasts, dispatch] = useReducer(reducer, []);
  const timers = useRef(new Set());
  const counter = useRef(0);

  useEffect(() => {
    const pending = timers.current;
    return () => pending.forEach(clearTimeout);
  }, []);

  const dismiss = useCallback((id) => {
    dispatch({ type: 'leave', id });
    const t = setTimeout(() => { dispatch({ type: 'remove', id }); timers.current.delete(t); }, EXIT_MS);
    timers.current.add(t);
  }, []);

  const push = useCallback((tone, title, message) => {
    counter.current += 1;
    const id = counter.current;
    dispatch({ type: 'add', toast: { id, tone, title, message } });
    const t = setTimeout(() => { dismiss(id); timers.current.delete(t); }, DURATION);
    timers.current.add(t);
  }, [dismiss]);

  const api = useMemo(() => ({
    success: (title, message) => push('success', title, message),
    error: (title, message) => push('error', title, message),
    info: (title, message) => push('info', title, message),
  }), [push]);

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="toasts" role="status" aria-live="polite" aria-relevant="additions">
        {toasts.map((t) => (
          <GlassPanel key={t.id} strong className={cx('toast', `toast--${t.tone}`, t.leaving && 'is-closing')} style={{ '--toast-ms': `${DURATION}ms` }}>
            <span className="toast__icon"><Icon name={ICONS[t.tone]} size={16} /></span>
            <div className="grow">
              <p className="toast__title">{t.title}</p>
              {t.message ? <p className="toast__msg">{t.message}</p> : null}
            </div>
            <button type="button" className="btn btn--ghost btn--icon btn--sm" aria-label="Dismiss notification" onClick={() => dismiss(t.id)}>
              <Icon name="x" size={16} />
            </button>
            <span className="toast__bar" aria-hidden="true" />
          </GlassPanel>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>');
  return ctx;
}
