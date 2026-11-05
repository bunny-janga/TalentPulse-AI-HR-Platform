import { createContext, useCallback, useContext, useEffect, useMemo, useReducer, useRef } from 'react';
import { setToken, setUnauthorizedHandler } from '../api/client.js';
import { clearSession, loadSession, saveSession } from '../api/session.js';
import { useToast } from '../components/ui/Toast.jsx';
import { navigate } from '../hooks/useRoute.js';

const AppContext = createContext(null);
const THEME_KEY = 'tp.theme.v2';
const SIDEBAR_KEY = 'tp.sidebar';

// localStorage can throw (private mode, quota), so preference reads/writes are guarded.
const readPref = (key) => { try { return localStorage.getItem(key); } catch { return null; } };
const writePref = (key, value) => { try { localStorage.setItem(key, value); } catch { /* preference simply will not persist */ } };

/** Restores the saved session. The token is set here, before any child effect can fire a request. */
function init() {
  const saved = loadSession();
  const session = saved?.access_token ? saved : null;
  if (session) setToken(session.access_token);
  return {
    session,
    theme: document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light',
    collapsed: readPref(SIDEBAR_KEY) === '1',
  };
}

function reducer(state, action) {
  switch (action.type) {
    case 'login': return { ...state, session: action.session };
    case 'logout': return { ...state, session: null };
    case 'theme': return { ...state, theme: action.theme };
    case 'collapsed': return { ...state, collapsed: action.value };
    default: return state;
  }
}

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, undefined, init);
  const toast = useToast();
  const hasSession = useRef(Boolean(state.session));
  hasSession.current = Boolean(state.session);

  const login = useCallback((session) => {
    setToken(session.access_token);
    saveSession(session);
    dispatch({ type: 'login', session });
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    clearSession();
    dispatch({ type: 'logout' });
    navigate('/', { replace: true });
  }, []);

  // A 401 on any authenticated request ends the session once (parallel requests would otherwise stack toasts).
  useEffect(() => {
    setUnauthorizedHandler(() => {
      if (!hasSession.current) return;
      hasSession.current = false;
      logout();
      toast.info('Session ended', 'Please sign in again.');
    });
    return () => setUnauthorizedHandler(null);
  }, [logout, toast]);

  useEffect(() => {
    document.documentElement.dataset.theme = state.theme;
    writePref(THEME_KEY, state.theme);
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', state.theme === 'dark' ? '#15151b' : '#fff4d6');
  }, [state.theme]);

  const toggleTheme = useCallback(() => dispatch({ type: 'theme', theme: state.theme === 'dark' ? 'light' : 'dark' }), [state.theme]);
  const toggleSidebar = useCallback(() => {
    const value = !state.collapsed;
    writePref(SIDEBAR_KEY, value ? '1' : '0');
    dispatch({ type: 'collapsed', value });
  }, [state.collapsed]);

  const value = useMemo(() => ({
    session: state.session,
    role: state.session?.role?.toLowerCase() ?? null,
    theme: state.theme,
    collapsed: state.collapsed,
    login, logout, toggleTheme, toggleSidebar,
  }), [state, login, logout, toggleTheme, toggleSidebar]);

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used inside <AppProvider>');
  return ctx;
}
