import { cx } from '../../utils/cx.js';
import { Icon } from './Icon.jsx';

/** Status badge. Always pair tone with text (and optionally an icon): colour is never the only signal. */
export function Badge({ tone = 'neutral', icon, dot = false, pulse = false, className, children }) {
  return (
    <span className={cx('badge', tone !== 'neutral' && `badge--${tone}`, pulse && 'badge--pulse', className)}>
      {dot ? <span className="badge__dot" aria-hidden="true" /> : null}
      {icon ? <Icon name={icon} size={14} /> : null}
      {children}
    </span>
  );
}

/** Toggleable filter chip (announced as a pressed button). */
export function Chip({ selected = false, onClick, icon, className, children }) {
  return (
    <button type="button" className={cx('chip', className)} aria-pressed={selected} onClick={onClick}>
      {icon ? <Icon name={icon} size={16} /> : null}
      {children}
    </button>
  );
}
