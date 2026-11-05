import { cx } from '../../utils/cx.js';
import { Icon } from './Icon.jsx';

/**
 * Neobrutalist button: thick ink border, hard offset shadow that "presses" on click.
 * While `loading` it is disabled, which prevents double submits.
 * variant: primary | secondary | ghost | danger | success | pink | blue    size: xs | sm | md | lg
 */
export function Button({
  variant = 'secondary', size = 'md', loading = false, disabled = false, icon, iconRight,
  className, children, type = 'button', magnetic: _magnetic, ...rest
}) {
  return (
    <button
      type={type}
      className={cx('btn', `btn--${variant}`, size !== 'md' && `btn--${size}`, loading && 'is-loading', className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? <span className="btn__spinner" aria-hidden="true" /> : null}
      <span className="btn__label">
        {icon ? <Icon name={icon} size={size === 'xs' ? 14 : 18} /> : null}
        {children}
        {iconRight ? <Icon name={iconRight} size={size === 'xs' ? 14 : 18} /> : null}
      </span>
    </button>
  );
}

/** Square icon-only button. `label` is required for accessibility. */
export function IconButton({ icon, label, variant = 'ghost', className, ...rest }) {
  return (
    <Button variant={variant} className={cx('btn--icon', className)} aria-label={label} title={label} {...rest}>
      <Icon name={icon} size={20} />
    </Button>
  );
}
