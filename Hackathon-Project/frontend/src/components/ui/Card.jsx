import { forwardRef } from 'react';
import { cx } from '../../utils/cx.js';

/** Glass card. `interactive` adds hover lift and shadow growth. */
export const Card = forwardRef(function Card({ as: Tag = 'section', interactive = false, padded = true, className, children, ...rest }, ref) {
  return (
    <Tag ref={ref} className={cx('card', padded && 'card--pad', interactive && 'card--interactive', className)} {...rest}>
      {children}
    </Tag>
  );
});

/** Larger blurred surface for shells, menus and floating panels. */
export const GlassPanel = forwardRef(function GlassPanel({ as: Tag = 'div', strong = false, glow = false, className, children, ...rest }, ref) {
  return (
    <Tag ref={ref} className={cx('glass', strong && 'glass--strong', glow && 'glass--glow', className)} {...rest}>
      {children}
    </Tag>
  );
});
