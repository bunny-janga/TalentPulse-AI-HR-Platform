import { cx } from '../../utils/cx.js';
import { Button } from './Button.jsx';
import { EmptyState } from './EmptyState.jsx';

/** Calm 403 state: never a crash, never alarming. */
export function RestrictedState({ message }) {
  return (
    <EmptyState
      tone="calm"
      icon="lock"
      title="Restricted"
      description={message || 'Your role does not include access to this area. If you think this is a mistake, contact HR.'}
    />
  );
}

export function ErrorState({ error, onRetry }) {
  const offline = error?.kind === 'network';
  return (
    <EmptyState
      tone="danger"
      icon={offline ? 'wifiOff' : 'alert'}
      title={offline ? 'You appear to be offline' : 'Something went wrong'}
      description={error?.message || 'We could not load this right now.'}
      action={onRetry ? <Button variant="secondary" icon="refresh" onClick={onRetry}>Try again</Button> : null}
    />
  );
}

/**
 * Renders the right view for a useApi() result: skeleton, restricted, error, empty or content.
 * `children` is a render function that receives the data.
 */
export function AsyncView({ state, skeleton, isEmpty, empty, children }) {
  const { status, data, error, reload } = state;
  if (status === 'loading' || status === 'idle') return skeleton ?? null;
  if (status === 'error' && data == null) {
    return error?.kind === 'forbidden' ? <RestrictedState message={error.message} /> : <ErrorState error={error} onRetry={reload} />;
  }
  if (data != null && isEmpty?.(data)) return empty ?? null;
  return <div className={cx('page-enter', status === 'refreshing' && 'is-refreshing')}>{children(data)}</div>;
}
