import { cx } from '../../utils/cx.js';
import { Icon } from './Icon.jsx';

/** Centred state block used for empty, error and restricted views. tone: accent | danger | calm */
export function EmptyState({ icon = 'inbox', title, description, action, tone = 'accent', className }) {
  return (
    <div className={cx('state', tone !== 'accent' && `state--${tone}`, 'page-enter', className)}>
      <div className="state__orb float" data-loop><Icon name={icon} size={34} strokeWidth={1.5} /></div>
      <h2>{title}</h2>
      {description ? <p>{description}</p> : null}
      {action}
    </div>
  );
}
