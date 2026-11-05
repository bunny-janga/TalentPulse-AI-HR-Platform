import { forwardRef, useId, useRef } from 'react';
import { useShake } from '../../hooks/useShake.js';
import { cx } from '../../utils/cx.js';
import { Icon } from './Icon.jsx';

/** Label + control + hint/error wrapper. The wrapper shakes whenever a new error appears. */
function FieldShell({ id, label, error, hint, required, className, children }) {
  const ref = useRef(null);
  useShake(ref, error);
  return (
    <div ref={ref} className={cx('field', error && 'is-invalid', className)}>
      {label ? (
        <label className="field__label" htmlFor={id}>
          {label}{required ? <span className="req" aria-hidden="true">*</span> : null}
        </label>
      ) : null}
      {children}
      {hint && !error ? <p className="field__hint" id={`${id}-hint`}>{hint}</p> : null}
      {error ? (
        <p className="field__error" id={`${id}-err`} role="alert" key={error}>
          <Icon name="alert" size={14} />{error}
        </p>
      ) : null}
    </div>
  );
}

const describedBy = (id, error, hint) => (error ? `${id}-err` : hint ? `${id}-hint` : undefined);

export const Input = forwardRef(function Input({ label, error, hint, required, className, ...rest }, ref) {
  const id = useId();
  return (
    <FieldShell id={id} label={label} error={error} hint={hint} required={required} className={className}>
      <input ref={ref} id={id} className="field__control" required={required} aria-invalid={Boolean(error) || undefined} aria-describedby={describedBy(id, error, hint)} {...rest} />
    </FieldShell>
  );
});

export const TextArea = forwardRef(function TextArea({ label, error, hint, required, className, ...rest }, ref) {
  const id = useId();
  return (
    <FieldShell id={id} label={label} error={error} hint={hint} required={required} className={className}>
      <textarea ref={ref} id={id} className="field__control" required={required} aria-invalid={Boolean(error) || undefined} aria-describedby={describedBy(id, error, hint)} {...rest} />
    </FieldShell>
  );
});

/** options: [{ value, label }] */
export const Select = forwardRef(function Select({ label, error, hint, required, options, placeholder, className, ...rest }, ref) {
  const id = useId();
  return (
    <FieldShell id={id} label={label} error={error} hint={hint} required={required} className={className}>
      <select ref={ref} id={id} className="field__control" required={required} aria-invalid={Boolean(error) || undefined} aria-describedby={describedBy(id, error, hint)} {...rest}>
        {placeholder ? <option value="">{placeholder}</option> : null}
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </FieldShell>
  );
});

/** Start/end date pair. Ordering is validated by the caller and surfaced through `error`. */
export function DateRange({ start, end, onStart, onEnd, min, error, startLabel = 'Start date', endLabel = 'End date' }) {
  const startId = useId();
  const endId = useId();
  const ref = useRef(null);
  useShake(ref, error);
  return (
    <div ref={ref} className={cx('field', error && 'is-invalid')}>
      <div className="date-range">
        <div className="field">
          <label className="field__label" htmlFor={startId}>{startLabel}</label>
          <input id={startId} type="date" className="field__control" value={start} min={min} onChange={(e) => onStart(e.target.value)} aria-invalid={Boolean(error) || undefined} />
        </div>
        <div className="field">
          <label className="field__label" htmlFor={endId}>{endLabel}</label>
          <input id={endId} type="date" className="field__control" value={end} min={start || min} onChange={(e) => onEnd(e.target.value)} aria-invalid={Boolean(error) || undefined} />
        </div>
      </div>
      {error ? <p className="field__error" role="alert" key={error}><Icon name="alert" size={14} />{error}</p> : null}
    </div>
  );
}

/** Spring toggle switch. */
export function Switch({ checked, onChange, label }) {
  return (
    <button type="button" role="switch" aria-checked={checked} aria-label={label} className="switch" onClick={() => onChange(!checked)} />
  );
}
