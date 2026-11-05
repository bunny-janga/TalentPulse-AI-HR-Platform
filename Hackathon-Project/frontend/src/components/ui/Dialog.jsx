import { useId, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useDialog } from '../../hooks/useDialog.js';
import { usePresence } from '../../hooks/usePresence.js';
import { cx } from '../../utils/cx.js';
import { GlassPanel } from './Card.jsx';
import { IconButton } from './Button.jsx';

/** Shared accessible dialog used by Modal (centred) and Drawer (side sheet). */
function Dialog({ open, onClose, title, description, footer, children, variant, size, dismissible = true }) {
  const { mounted, closing } = usePresence(open, 250);
  const panelRef = useRef(null);
  const titleId = useId();
  const descId = useId();
  useDialog({ active: mounted && !closing, ref: panelRef, onClose: dismissible ? onClose : undefined });

  if (!mounted) return null;
  const isDrawer = variant === 'drawer';
  return createPortal(
    <div
      className={cx('overlay', isDrawer && 'overlay--drawer', closing && 'is-closing')}
      onMouseDown={(e) => { if (dismissible && e.target === e.currentTarget) onClose?.(); }}
    >
      <GlassPanel
        strong
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descId : undefined}
        tabIndex={-1}
        className={cx(isDrawer ? 'drawer' : 'dialog', size === 'lg' && 'dialog--lg')}
      >
        <div className="dialog__head">
          <div>
            <h2 id={titleId}>{title}</h2>
            {description ? <p id={descId}>{description}</p> : null}
          </div>
          {dismissible ? <IconButton icon="x" label="Close dialog" onClick={onClose} /> : null}
        </div>
        {children}
        {footer ? <div className="dialog__foot">{footer}</div> : null}
      </GlassPanel>
    </div>,
    document.body,
  );
}

export const Modal = (props) => <Dialog variant="modal" {...props} />;
export const Drawer = (props) => <Dialog variant="drawer" {...props} />;
