import { Badge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Popover } from '../components/ui/Popover.jsx';
import { Switch } from '../components/ui/Field.jsx';
import { initials, ROLE_LABEL } from '../utils/format.js';
import { useApp } from './store.jsx';

/** Avatar button with identity, theme switch and sign-out. */
export function UserMenu() {
  const { session, role, theme, toggleTheme, logout } = useApp();
  return (
    <Popover
      label="Account menu"
      panelClassName="usermenu"
      trigger={({ props }) => (
        <button type="button" className="avatar-btn" aria-label={`Account menu for ${session.full_name}`} {...props}>
          <span className="avatar">{initials(session.full_name)}</span>
        </button>
      )}
    >
      {(close) => (
        <div className="stack" style={{ '--gap': '16px' }}>
          <div className="usermenu__id">
            <span className="avatar avatar--lg">{initials(session.full_name)}</span>
            <div className="grow">
              <p className="usermenu__name truncate">{session.full_name}</p>
              <p className="dim truncate">{session.email}</p>
            </div>
          </div>
          <Badge tone="accent" icon="shield">{ROLE_LABEL[role] ?? role}</Badge>
          <hr className="hairline" />
          <div className="row spread">
            <span className="muted">Dark mode</span>
            <Switch checked={theme === 'dark'} onChange={toggleTheme} label="Dark mode" />
          </div>
          <Button variant="secondary" icon="logout" onClick={() => { close(); logout(); }}>Sign out</Button>
        </div>
      )}
    </Popover>
  );
}
