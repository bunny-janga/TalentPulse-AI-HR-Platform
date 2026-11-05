import { useMemo } from 'react';
import { IconButton } from '../components/ui/Button.jsx';
import { Icon, Logo } from '../components/ui/Icon.jsx';
import { Tooltip } from '../components/ui/Tooltip.jsx';
import { cx } from '../utils/cx.js';

/**
 * Collapsible solid sidebar. On phones the same nav becomes a bottom tab bar (CSS only).
 * The current page is the pink block with a hard shadow.
 */
export function Sidebar({ routes, activePath, collapsed, onToggle }) {
  const sections = useMemo(() => {
    const map = new Map();
    routes.forEach((r) => map.set(r.section, [...(map.get(r.section) ?? []), r]));
    return [...map.entries()];
  }, [routes]);

  return (
    <aside className={cx('sidebar glass', collapsed && 'is-collapsed')}>
      <div className="sidebar__brand">
        <Logo size={36} />
        <span className="sidebar__wordmark">TalentPulse<span className="grad-text">AI</span></span>
      </div>

      <nav className="nav" aria-label="Primary">
        {sections.map(([name, items]) => (
          <div className="nav__group" key={name}>
            <p className="nav__heading eyebrow">{name}</p>
            <ul>
              {items.map((route) => (
                <li key={route.path}>
                  <Tooltip label={route.label} side="right">
                    <a className="nav__item" href={`#${route.path}`} aria-current={route.path === activePath ? 'page' : undefined}>
                      <Icon name={route.icon} size={20} strokeWidth={2.4} />
                      <span className="nav__label">{route.label}</span>
                    </a>
                  </Tooltip>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      <div className="sidebar__foot">
        <IconButton icon="sidebar" label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'} aria-expanded={!collapsed} onClick={onToggle} />
      </div>
    </aside>
  );
}
