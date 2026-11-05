import { cx } from '../../utils/cx.js';

/** Hash-route link with an animated underline. */
export function Link({ to, className, children, ...rest }) {
  return (
    <a href={`#${to}`} className={cx('link', className)} {...rest}>
      {children}
    </a>
  );
}
