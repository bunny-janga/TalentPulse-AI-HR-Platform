import { Children, cloneElement, useId } from 'react';
import { cx } from '../../utils/cx.js';

/** CSS tooltip shown on hover and keyboard focus. Wraps a single focusable child. */
export function Tooltip({ label, side = 'top', children }) {
  const id = useId();
  const child = Children.only(children);
  return (
    <span className={cx('tip', side !== 'top' && `tip--${side}`)}>
      {cloneElement(child, { 'aria-describedby': id })}
      <span role="tooltip" id={id} className="tip__bubble">{label}</span>
    </span>
  );
}
