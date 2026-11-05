import { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react';
import { Icon } from '../components/ui/Icon.jsx';
import { useDismiss } from '../hooks/useDismiss.js';
import { navigate } from '../hooks/useRoute.js';
import { cx } from '../utils/cx.js';

/**
 * Global search combobox: jumps to any screen the role can open and, for roles with
 * directory access, searches people. Press "/" anywhere to focus it.
 */
export function GlobalSearch({ routes, canSearchPeople }) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const wrapRef = useRef(null);
  const inputRef = useRef(null);
  const listId = useId();

  const items = useMemo(() => {
    const q = query.trim().toLowerCase();
    const pages = routes
      .filter((r) => !q || r.label.toLowerCase().includes(q))
      .slice(0, 6)
      .map((r) => ({ key: r.path, icon: r.icon, label: r.label, hint: 'Go to', run: () => navigate(r.path) }));
    const people = q && canSearchPeople
      ? [{ key: 'people', icon: 'users', label: `Search people for “${query.trim()}”`, hint: 'Directory', run: () => navigate(`/directory?q=${encodeURIComponent(query.trim())}`) }]
      : [];
    return [...people, ...pages];
  }, [query, routes, canSearchPeople]);

  const close = useCallback(() => setOpen(false), []);
  useDismiss(wrapRef, open, close);

  useEffect(() => {
    const onKey = (e) => {
      const tag = e.target.tagName;
      if (e.key === '/' && !e.metaKey && !e.ctrlKey && tag !== 'INPUT' && tag !== 'TEXTAREA' && !e.target.isContentEditable) {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, []);

  const choose = (item) => {
    item.run();
    setQuery('');
    setOpen(false);
    inputRef.current?.blur();
  };

  const onKeyDown = (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setOpen(true); setActive((i) => (i + 1) % Math.max(items.length, 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive((i) => (i - 1 + items.length) % Math.max(items.length, 1)); }
    else if (e.key === 'Enter' && open && items[active]) { e.preventDefault(); choose(items[active]); }
    else if (e.key === 'Escape') { setOpen(false); inputRef.current?.blur(); }
  };

  return (
    <div className="search" ref={wrapRef}>
      <Icon name="search" size={18} className="search__icon" />
      <input
        ref={inputRef}
        className="search__input"
        type="search"
        placeholder="Search screens and people"
        aria-label="Global search"
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={open && items[active] ? `${listId}-${active}` : undefined}
        autoComplete="off"
        value={query}
        onChange={(e) => { setQuery(e.target.value); setActive(0); setOpen(true); }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
      />
      <kbd className="search__kbd" aria-hidden="true">/</kbd>
      {open ? (
        <ul className="dropdown dropdown--start glass glass--strong search__list" id={listId} role="listbox" aria-label="Search results">
          {items.length === 0 ? <li className="search__empty">No matching screens</li> : items.map((item, i) => (
            <li
              key={item.key}
              id={`${listId}-${i}`}
              role="option"
              aria-selected={i === active}
              className={cx('search__option', i === active && 'is-active')}
              onMouseEnter={() => setActive(i)}
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => choose(item)}
            >
              <Icon name={item.icon} size={18} />
              <span className="grow truncate">{item.label}</span>
              <span className="dim search__hint">{item.hint}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
