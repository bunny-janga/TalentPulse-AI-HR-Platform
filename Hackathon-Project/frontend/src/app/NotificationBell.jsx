import { useEffect } from 'react';
import { api } from '../api/client.js';
import { Button } from '../components/ui/Button.jsx';
import { Icon } from '../components/ui/Icon.jsx';
import { Popover } from '../components/ui/Popover.jsx';
import { Skeleton } from '../components/ui/Skeleton.jsx';
import { useToast } from '../components/ui/Toast.jsx';
import { useApi } from '../hooks/useApi.js';
import { cx } from '../utils/cx.js';
import { formatDateTime } from '../utils/format.js';

const POLL_MS = 60000;

/** Bell with a pop-in unread badge and a stagger-in dropdown. Polls once a minute while the tab is visible. */
export function NotificationBell() {
  const state = useApi((signal) => api.get('/notifications/my', { signal }), []);
  const { data, status, reload, mutate } = state;
  const toast = useToast();
  const items = data ?? [];
  const unread = items.filter((n) => !n.is_read).length;

  useEffect(() => {
    const id = setInterval(() => { if (!document.hidden) reload(); }, POLL_MS);
    return () => clearInterval(id);
  }, [reload]);

  /** Optimistic read-marking with rollback if the request fails. */
  const markRead = async (note) => {
    if (note.is_read) return;
    const flip = (value) => mutate((list) => (list ?? []).map((n) => (n.id === note.id ? { ...n, is_read: value } : n)));
    flip(true);
    try {
      await api.put(`/notifications/${note.id}/read`);
    } catch (err) {
      flip(false);
      toast.error('Could not update notification', err.message);
    }
  };

  return (
    <Popover
      label="Notifications"
      panelClassName="notifications"
      trigger={({ props }) => (
        <button type="button" className="btn btn--ghost btn--icon bell" aria-label={unread ? `Notifications, ${unread} unread` : 'Notifications'} {...props}>
          <Icon name="bell" size={20} />
          {unread > 0 ? <span key={unread} className="bell__badge pop" aria-hidden="true">{unread > 9 ? '9+' : unread}</span> : null}
        </button>
      )}
    >
      {() => (
        <>
          <div className="notifications__head">
            <h2>Notifications</h2>
            <span className="badge badge--accent">{unread} unread</span>
          </div>
          <div className="notifications__body">
            {status === 'loading' ? (
              <div className="stack" style={{ '--gap': '14px' }} aria-label="Loading notifications">
                {[0, 1, 2].map((i) => <Skeleton key={i} h={52} />)}
              </div>
            ) : status === 'error' && data == null ? (
              <div className="notifications__empty">
                <p className="muted">{state.error?.message ?? 'Could not load notifications.'}</p>
                <Button size="sm" variant="secondary" icon="refresh" onClick={reload}>Retry</Button>
              </div>
            ) : items.length === 0 ? (
              <div className="notifications__empty">
                <Icon name="check" size={28} />
                <p className="muted">You are all caught up.</p>
              </div>
            ) : (
              <ul className="stagger">
                {items.slice(0, 12).map((n, i) => (
                  <li key={n.id} style={{ '--i': i }}>
                    <button type="button" className={cx('note', !n.is_read && 'is-unread')} onClick={() => markRead(n)}>
                      <span className="note__dot" aria-hidden="true" />
                      <span className="grow">
                        <span className="note__title">{n.title}{!n.is_read ? <span className="sr-only"> (unread)</span> : null}</span>
                        <span className="note__msg">{n.message}</span>
                        <span className="note__time dim">{formatDateTime(n.created_at)}</span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </Popover>
  );
}
