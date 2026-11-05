import { cx } from '../../utils/cx.js';
import { Icon } from './Icon.jsx';

/** Page header: big icon tile, title, one-line purpose and a slot for actions. */
export function PageHead({ icon, eyebrow, title, subtitle, actions, tone = 'yellow' }) {
  return (
    <div className="page__head">
      <div className="row row--nowrap" style={{ '--gap': '16px', alignItems: 'flex-start' }}>
        {icon ? <span className={cx('icon-tile', `tone-${tone}`)} style={{ width: 56, height: 56 }}><Icon name={icon} size={28} strokeWidth={2.4} /></span> : null}
        <div>
          {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
          <h1>{title}</h1>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
      </div>
      {actions ? <div className="row">{actions}</div> : null}
    </div>
  );
}

/** Colour-blocked KPI tile. */
export function Stat({ label, value, sub, tone, icon, className, children }) {
  return (
    <div className={cx('stat', tone && `tone-${tone}`, className)}>
      <div className="row spread row--nowrap">
        <span className="stat__label">{label}</span>
        {icon ? <Icon name={icon} size={18} strokeWidth={2.4} /> : null}
      </div>
      <span className="stat__value">{value}</span>
      {sub ? <span className="stat__sub">{sub}</span> : null}
      {children}
    </div>
  );
}

/** Horizontal bar. `value` and `max` are numbers; `tone` picks the fill colour. */
export function Meter({ value, max = 100, tone = 'green', label, large = false }) {
  const pct = max > 0 ? Math.max(0, Math.min(100, (value / max) * 100)) : 0;
  return (
    <div
      className={cx('meter', large && 'meter--lg')}
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={max}
      aria-valuenow={Math.round(value)}
      aria-label={label}
    >
      <div className={cx('meter__fill', `fill-${tone}`)} style={{ width: `${pct}%` }} />
    </div>
  );
}

/** Section card header used inside pages. */
export function CardHead({ icon, title, subtitle, actions }) {
  return (
    <div className="card-head">
      <div className="row row--nowrap" style={{ '--gap': '10px' }}>
        {icon ? <Icon name={icon} size={22} strokeWidth={2.4} /> : null}
        <div>
          <h2>{title}</h2>
          {subtitle ? <p className="dim" style={{ fontSize: 'var(--fs-sm)' }}>{subtitle}</p> : null}
        </div>
      </div>
      {actions ? <div className="row">{actions}</div> : null}
    </div>
  );
}
