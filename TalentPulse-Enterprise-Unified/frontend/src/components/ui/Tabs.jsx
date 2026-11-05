import { useRef } from 'react';
import { cx } from '../../utils/cx.js';
import { Icon } from './Icon.jsx';

/**
 * Accessible tablist (arrow keys, Home/End). The selected tab is the pressed-in yellow block.
 * tabs: [{ id, label, icon?, count? }]
 */
export function Tabs({ tabs, value, onChange, label, idBase }) {
  const listRef = useRef(null);

  const onKeyDown = (e) => {
    const index = tabs.findIndex((t) => t.id === value);
    let next = index;
    if (e.key === 'ArrowRight') next = (index + 1) % tabs.length;
    else if (e.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
    else if (e.key === 'Home') next = 0;
    else if (e.key === 'End') next = tabs.length - 1;
    else return;
    e.preventDefault();
    onChange(tabs[next].id);
    listRef.current?.querySelectorAll('[role="tab"]')[next]?.focus();
  };

  return (
    <div className="tabs" role="tablist" aria-label={label} ref={listRef} onKeyDown={onKeyDown}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          id={`${idBase}-tab-${tab.id}`}
          aria-selected={tab.id === value}
          aria-controls={`${idBase}-panel-${tab.id}`}
          tabIndex={tab.id === value ? 0 : -1}
          className="tab"
          onClick={() => onChange(tab.id)}
        >
          {tab.icon ? <Icon name={tab.icon} size={16} /> : null}
          {tab.label}
          {tab.count != null ? <span className="badge">{tab.count}</span> : null}
        </button>
      ))}
    </div>
  );
}

/** Panel paired with a Tab through `idBase` + `id`. Renders children only while active. */
export function TabPanel({ idBase, id, active, className, children }) {
  return (
    <div role="tabpanel" id={`${idBase}-panel-${id}`} aria-labelledby={`${idBase}-tab-${id}`} hidden={!active} tabIndex={0} className={cx(active && 'page-enter', className)}>
      {active ? children : null}
    </div>
  );
}
