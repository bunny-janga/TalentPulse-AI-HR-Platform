// Inline SVG icon set (24px grid, stroke based). No icon packs.
const PATHS = {
  home: 'M3 11l9-8 9 8M5 10v10h5v-6h4v6h5V10',
  grid: 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z',
  calendar: 'M4 6h16v14H4zM4 10h16M8 3v4M16 3v4',
  star: 'M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z',
  chat: 'M4 5h16v11H9l-5 4z',
  shield: 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z',
  alert: 'M12 4l9 16H3zM12 10v4M12 17v.01',
  chart: 'M4 20V11M10 20V4M16 20v-6M2 20h20',
  pulse: 'M3 12h4l3-8 4 16 3-8h4',
  users: 'M9 11a3 3 0 100-6 3 3 0 000 6zM3 20c0-3 3-5 6-5s6 2 6 5M17 11a3 3 0 100-6M21 20c0-2.5-1.6-4.2-4-4.8',
  user: 'M12 12a4 4 0 100-8 4 4 0 000 8zM4 21c0-4 4-6 8-6s8 2 8 6',
  building: 'M5 21V4h9v17M14 9h5v12M8 8h3M8 12h3M8 16h3M3 21h18',
  org: 'M12 4v4M5 14v-3h14v3M12 8v3M3 14h4v5H3zM10 14h4v5h-4zM17 14h4v5h-4z',
  file: 'M6 3h8l5 5v13H6zM14 3v5h5M9 13h6M9 17h6',
  clipboard: 'M9 4h6v3H9zM6 5h3M15 5h3v16H6V5M9 12h6M9 16h4',
  bell: 'M6 17V11a6 6 0 0112 0v6l2 2H4zM10 21h4',
  search: 'M11 18a7 7 0 100-14 7 7 0 000 14zM20 20l-4-4',
  sun: 'M12 16a4 4 0 100-8 4 4 0 000 8zM12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M5 19l1.5-1.5M17.5 6.5L19 5',
  moon: 'M20 14.5A8 8 0 019.5 4 8 8 0 1020 14.5z',
  menu: 'M4 7h16M4 12h16M4 17h16',
  sidebar: 'M4 5h16v14H4zM9 5v14',
  x: 'M6 6l12 12M18 6L6 18',
  check: 'M5 12.5l4.5 4.5L19 7.5',
  plus: 'M12 5v14M5 12h14',
  chevronRight: 'M9 6l6 6-6 6',
  chevronLeft: 'M15 6l-6 6 6 6',
  chevronDown: 'M6 9l6 6 6-6',
  upload: 'M12 16V4M7 9l5-5 5 5M4 20h16',
  logout: 'M10 4H4v16h6M15 8l4 4-4 4M19 12H9',
  sparkles: 'M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8zM19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8z',
  trendDown: 'M3 7l6 6 4-4 8 8M21 11v6h-6',
  trendUp: 'M3 17l6-6 4 4 8-8M21 13V7h-6',
  clock: 'M12 21a9 9 0 100-18 9 9 0 000 18zM12 7v5l3 2',
  send: 'M4 12l16-8-6 16-3-7z',
  bolt: 'M13 3L5 14h6l-1 7 8-11h-6z',
  lock: 'M6 11h12v9H6zM8 11V8a4 4 0 018 0v3',
  refresh: 'M20 11a8 8 0 00-14.5-4M4 4v4h4M4 13a8 8 0 0014.5 4M20 20v-4h-4',
  info: 'M12 21a9 9 0 100-18 9 9 0 000 18zM12 11v5M12 8v.01',
  inbox: 'M4 13l2-8h12l2 8M4 13v6h16v-6M4 13h5l1 2h4l1-2h5',
  eye: 'M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12zM12 15a3 3 0 100-6 3 3 0 000 6z',
  arrowLeft: 'M19 12H5M11 6l-6 6 6 6',
  arrowRight: 'M5 12h14M13 6l6 6-6 6',
  key: 'M14 10a4 4 0 11-3.4 6.1L4 22v-3H2v-2h3l5.9-5.9A4 4 0 0114 10zM15.5 8.5v.01',
  download: 'M12 4v12M7 11l5 5 5-5M4 20h16',
  trash: 'M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v6M14 11v6',
  edit: 'M4 20h4L19 9l-4-4L4 16zM13 7l4 4',
  mail: 'M3 5h18v14H3zM3 6l9 7 9-7',
  list: 'M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01',
  target: 'M12 21a9 9 0 100-18 9 9 0 000 18zM12 16a4 4 0 100-8 4 4 0 000 8zM12 12h.01',
  door: 'M5 21V3h11v18M16 5h3v16h-3M12 12h.01M2 21h20',
  wifiOff: 'M3 3l18 18M8.5 8.5A11 11 0 003 12M16 11a7 7 0 012 1.5M12 19.5v.01M9 16a4 4 0 016 0',
};

export function Icon({ name, size = 20, strokeWidth = 1.8, className = '', title }) {
  const d = PATHS[name];
  return (
    <svg
      className={`icon ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      role={title ? 'img' : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
      focusable="false"
    >
      {d ? <path d={d} /> : null}
    </svg>
  );
}

/** Brand mark: flat yellow tile, hard ink outline, offset shadow and a pulse line. */
export function Logo({ size = 36 }) {
  return (
    <svg className="icon" width={size} height={size} viewBox="0 0 36 36" aria-hidden="true" focusable="false">
      <rect x="4" y="4" width="30" height="30" fill="#111" />
      <rect x="1.5" y="1.5" width="30" height="30" fill="#ffd23f" stroke="#111" strokeWidth="3" />
      <path d="M6 17h5l3-8 5 15 3-7h4" fill="none" stroke="#111" strokeWidth="3" strokeLinecap="square" strokeLinejoin="miter" />
      <circle cx="26" cy="9" r="3" fill="#ff7ab8" stroke="#111" strokeWidth="2" />
    </svg>
  );
}
