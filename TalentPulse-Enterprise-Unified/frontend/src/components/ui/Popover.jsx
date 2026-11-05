import { useCallback, useId, useRef, useState } from 'react';
import { useDismiss } from '../../hooks/useDismiss.js';
import { usePresence } from '../../hooks/usePresence.js';
import { cx } from '../../utils/cx.js';
import { GlassPanel } from './Card.jsx';

/**
 * Anchored dropdown panel with enter/exit animation, outside-click and Escape dismissal.
 * trigger({ props, open }) must spread `props` on its button.
 * children(close) renders the panel content.
 */
export function Popover({ trigger, children, label, align = 'end', className, panelClassName }) {
  const [open, setOpen] = useState(false);
  const { mounted, closing } = usePresence(open, 180);
  const ref = useRef(null);
  const panelId = useId();

  const close = useCallback((e) => {
    setOpen(false);
    if (e?.type === 'keydown') ref.current?.querySelector('[data-popover-trigger]')?.focus();
  }, []);
  useDismiss(ref, open, close);

  const props = {
    'data-popover-trigger': true,
    'aria-expanded': open,
    'aria-haspopup': 'dialog',
    'aria-controls': mounted ? panelId : undefined,
    onClick: () => setOpen((o) => !o),
  };

  return (
    <div ref={ref} className={cx('popover', className)}>
      {trigger({ props, open })}
      {mounted ? (
        <GlassPanel strong id={panelId} role="dialog" aria-label={label} className={cx('dropdown', `dropdown--${align}`, closing && 'is-closing', panelClassName)}>
          {children(() => setOpen(false))}
        </GlassPanel>
      ) : null}
    </div>
  );
}
