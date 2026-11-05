import { IconButton } from '../components/ui/Button.jsx';
import { GlobalSearch } from './GlobalSearch.jsx';
import { NotificationBell } from './NotificationBell.jsx';
import { UserMenu } from './UserMenu.jsx';
import { canSearchPeople } from './routes.js';
import { useApp } from './store.jsx';

/** Sticky top bar: breadcrumb, global search, DB link for HR/Admin, notifications, theme toggle and account menu. */
export function TopBar({ route, routes }) {
  const { role, theme, toggleTheme } = useApp();
  return (
    <header className="topbar glass">
      <div className="topbar__crumb">
        <p className="eyebrow">{route?.section ?? 'TalentPulse'}</p>
        <p className="topbar__title">{route?.label ?? 'Not found'}</p>
      </div>
      <GlobalSearch routes={routes} canSearchPeople={canSearchPeople(role)} />
      <div className="topbar__actions">
        {['superadmin', 'admin'].includes(role) ? (
          <a className="live-pill" href="/db" target="_blank" rel="noreferrer" title="Open the read-only database browser in a new tab (admins only)">
            <span className="live-pill__dot" aria-hidden="true" />
            DB Browser
          </a>
        ) : null}
        <NotificationBell />
        <IconButton
          icon={theme === 'dark' ? 'sun' : 'moon'}
          label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
          onClick={toggleTheme}
          className="theme-toggle"
        />
        <UserMenu />
      </div>
    </header>
  );
}
