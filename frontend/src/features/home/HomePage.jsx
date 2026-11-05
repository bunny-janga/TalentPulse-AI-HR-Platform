import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '../../api/client.js';
import { useApp } from '../../app/store.jsx';
import { Badge, Button, CardHead, Icon, Modal, PageHead, Stat, Table, useToast } from '../../components/ui/index.js';
import { Input } from '../../components/ui/Field.jsx';
import { navigate } from '../../hooks/useRoute.js';
import { ROLE_LABEL } from '../../utils/format.js';

const LINKS = {
  employee: [
    { to: '/leave', icon: 'calendar', tone: 'blue', title: 'Leave', text: 'Apply, check balances, track approvals.' },
    { to: '/reviews', icon: 'star', tone: 'yellow', title: 'My reviews', text: 'Ratings and feedback from your manager.' },
    { to: '/helpdesk', icon: 'chat', tone: 'green', title: 'Policy helpdesk', text: 'Ask HR questions, get cited answers.' },
    { to: '/surveys', icon: 'clipboard', tone: 'purple', title: 'Pulse surveys', text: 'Anonymous feedback to leadership.' },
  ],
  lead: [
    { to: '/attrition', icon: 'shield', tone: 'pink', title: 'Attrition radar', text: 'Risk bands with the top 3 reasons each.' },
    { to: '/flags', icon: 'trendDown', tone: 'red', title: 'Performance flags', text: 'Two or more falling ratings in a row.' },
    { to: '/reviews', icon: 'star', tone: 'yellow', title: 'Reviews + AI drafts', text: 'Turn rough notes into a full review.' },
    { to: '/helpdesk', icon: 'chat', tone: 'green', title: 'Policy helpdesk', text: 'Cited answers from the policy library.' },
  ],
};

function RoleControl() {
  const { role } = useApp();
  const toast = useToast();
  const isSuper = role === 'superadmin';
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');
  const [busy, setBusy] = useState(null);
  const [confirm, setConfirm] = useState(null); // { user, role }

  const load = useCallback(() => {
    setLoading(true);
    api.get('/admin/users').then((r) => setUsers(r.users ?? [])).catch((e) => toast.error('Could not load users', e.message)).finally(() => setLoading(false));
  }, [toast]);
  useEffect(() => { load(); }, [load]);

  const shown = useMemo(() => {
    const s = q.trim().toLowerCase();
    return users.filter((u) => !s || [u.full_name, u.email, u.role, u.department].some((v) => v?.toLowerCase().includes(s)));
  }, [users, q]);

  const apply = async () => {
    setBusy(confirm.user.id);
    try {
      await api.put(`/admin/users/${confirm.user.id}/role`, { role: confirm.role });
      toast.success('Role updated', `${confirm.user.full_name} is now ${ROLE_LABEL[confirm.role] ?? confirm.role}.`);
      setUsers((list) => list.map((u) => (u.id === confirm.user.id ? { ...u, role: confirm.role, is_admin: ['admin', 'superadmin'].includes(confirm.role), authority_category: confirm.role === 'admin' ? 'Administrator' : 'Standard User' } : u)));
      setConfirm(null);
    } catch (e) { toast.error('Could not change role', e.message); } finally { setBusy(null); }
  };

  return (
    <section className="card card--pad stack" style={{ '--gap': '16px' }}>
      <CardHead icon="shield" title="Roles and authority" subtitle={isSuper ? 'You are Super Admin: you alone can grant or revoke Admin.' : 'Admins can view roles. Only the Super Admin can change them.'}
        actions={<><div style={{ minWidth: 240 }}><Input aria-label="Search users" placeholder="Search name, email, role…" value={q} onChange={(e) => setQ(e.target.value)} /></div><Badge tone={isSuper ? 'accent' : 'neutral'}>{isSuper ? 'Higher authority' : 'View only'}</Badge></>} />
      <div className="scroll-y">
        <Table>
          <thead><tr><th>User</th><th>Department</th><th>Role</th>{isSuper ? <th className="is-right">Change</th> : null}</tr></thead>
          <tbody>
            {loading ? <tr><td colSpan="4" className="empty-cell">Loading…</td></tr> : shown.map((u) => (
              <tr key={u.id}>
                <td><div className="cell-name">{u.full_name}</div><div className="cell-sub">{u.email}</div></td>
                <td>{u.department}</td>
                <td><Badge tone={u.role === 'superadmin' ? 'accent' : u.role === 'admin' ? 'info' : 'neutral'}>{ROLE_LABEL[u.role] ?? u.role}</Badge></td>
                {isSuper ? (
                  <td className="is-right">
                    {u.role === 'superadmin' ? <span className="cell-sub">Primary authority</span> : (
                      <div className="row" style={{ justifyContent: 'flex-end' }}>
                        {u.role === 'admin' ? <Button size="xs" variant="danger" disabled={busy === u.id} onClick={() => setConfirm({ user: u, role: 'manager' })}>Revoke admin</Button> : <Button size="xs" disabled={busy === u.id} onClick={() => setConfirm({ user: u, role: 'admin' })}>Make admin</Button>}
                        {u.role !== 'admin' ? <Button size="xs" variant="ghost" disabled={busy === u.id} onClick={() => setConfirm({ user: u, role: u.role === 'hr' ? 'manager' : 'hr' })}>Make {u.role === 'hr' ? 'manager' : 'HR'}</Button> : null}
                      </div>
                    )}
                  </td>
                ) : null}
              </tr>
            ))}
          </tbody>
        </Table>
      </div>
      <Modal open={Boolean(confirm)} onClose={() => !busy && setConfirm(null)} title="Change this role?" description={confirm ? `${confirm.user.full_name}: ${ROLE_LABEL[confirm.user.role] ?? confirm.user.role} → ${ROLE_LABEL[confirm.role] ?? confirm.role}` : ''}
        footer={<><Button onClick={() => setConfirm(null)} disabled={Boolean(busy)}>Cancel</Button><Button variant="primary" loading={Boolean(busy)} onClick={apply}>Confirm</Button></>}>
        <p className="muted">Their access changes the next time they sign in or refresh.</p>
      </Modal>
    </section>
  );
}

export default function HomePage() {
  const { session, role } = useApp();
  const isEmployee = role === 'employee';
  const isManager = role === 'manager';
  const isHR = ['hr', 'admin', 'superadmin'].includes(role);
  const isAdmin = ['admin', 'superadmin'].includes(role);

  const [metrics, setMetrics] = useState(null);
  const [team, setTeam] = useState(null);
  const [balances, setBalances] = useState(null);
  const [pending, setPending] = useState(null);
  const [reviews, setReviews] = useState(null);

  useEffect(() => {
    const c = new AbortController();
    const opts = { signal: c.signal };
    if (isHR) api.get('/admin/metrics', opts).then(setMetrics).catch(() => {});
    if (isManager) api.get('/attrition/team', opts).then(setTeam).catch(() => {});
    api.get(isEmployee ? '/leave/my' : '/leave/team', opts).then((l) => setPending((l ?? []).filter((x) => x.status === 'PENDING').length)).catch(() => setPending(null));
    api.get('/leave/balance', opts).then((b) => setBalances(b.balances)).catch(() => {});
    if (isEmployee) api.get('/reviews/my', opts).then((r) => setReviews(r)).catch(() => {});
    return () => c.abort();
  }, [isHR, isManager, isEmployee]);

  const cl = balances?.find((b) => b.leave_type === 'Casual Leave');
  const latest = reviews?.[0];
  const links = isEmployee ? LINKS.employee : LINKS.lead;

  return (
    <div className="page stack" style={{ '--gap': '28px' }}>
      <section className="card card--pad tone-yellow home-hero" style={{ boxShadow: 'var(--sh-3)' }}>
        <div className="stack" style={{ '--gap': '12px' }}>
          <div className="row"><Badge tone="accent" icon="shield">{ROLE_LABEL[role] ?? role}</Badge><span className="eyebrow" style={{ color: '#111' }}>Visakhapatnam IT Center</span></div>
          <h1 style={{ fontSize: 'var(--fs-2xl)', letterSpacing: '-0.05em' }}>Hey {session?.full_name?.split(' ')[0]}.</h1>
          <p style={{ maxWidth: '60ch', fontWeight: 600 }}>
            {isEmployee ? 'Your leave, reviews and HR answers, all in one place.' : isManager ? 'Your team’s leave, reviews and flight risk, in one place.' : 'Workforce health at a glance: who might leave, what is pending, what to fix first.'}
          </p>
          <div className="row">
            <Button icon="chat" onClick={() => navigate('/helpdesk')}>Ask the helpdesk</Button>
            {isEmployee ? <Button variant="primary" icon="calendar" onClick={() => navigate('/leave')}>Apply for leave</Button> : <Button variant="pink" icon="shield" onClick={() => navigate('/attrition')}>Open attrition radar</Button>}
          </div>
        </div>
      </section>

      <div className="grid grid--3">
        {isHR ? (<>
          <Stat label="Headcount" value={metrics?.total_headcount ?? '…'} sub={metrics ? `${metrics.total_managers} managers` : ''} icon="users" />
          <Stat tone="red" label="High-risk people" value={metrics?.attrition_summary?.high_risk_headcount ?? '…'} sub={metrics ? `Expected attrition ${metrics.attrition_summary.projected_attrition_rate_percent}% (benchmark ${metrics.attrition_summary.industry_benchmark_attrition_percent}%)` : ''} icon="shield" />
          <Stat tone={pending ? 'yellow' : 'green'} label="Leave to review" value={pending ?? '…'} sub="Pending across the company" icon="calendar"><Button size="xs" onClick={() => navigate('/leave')}>Open queue</Button></Stat>
        </>) : isManager ? (<>
          <Stat label="Direct reports" value={team?.team_size ?? '…'} icon="users" />
          <Stat tone="red" label="High attrition risk" value={team?.risk_counts?.HIGH ?? '…'} sub={team ? `${team.risk_counts?.MEDIUM ?? 0} medium` : ''} icon="shield"><Button size="xs" onClick={() => navigate('/attrition')}>View team radar</Button></Stat>
          <Stat tone={pending ? 'yellow' : 'green'} label="Leave awaiting you" value={pending ?? '…'} icon="calendar"><Button size="xs" onClick={() => navigate('/leave')}>Open queue</Button></Stat>
        </>) : (<>
          <Stat tone="green" label="Casual leave left" value={cl ? <>{cl.remaining}<span className="dim" style={{ fontSize: '1rem' }}> / {cl.quota}</span></> : '…'} sub={cl ? `${cl.used} used this year` : ''} icon="calendar" />
          <Stat tone="yellow" label="Latest review" value={latest ? `${latest.rating}/5` : '–'} sub={latest ? `Cycle ${latest.review_cycle}` : 'None published yet'} icon="star"><Button size="xs" onClick={() => navigate('/reviews')}>Open</Button></Stat>
          <Stat tone={pending ? 'yellow' : 'blue'} label="Requests pending" value={pending ?? '…'} icon="clock"><Button size="xs" onClick={() => navigate('/leave')}>Track</Button></Stat>
        </>)}
      </div>

      <div className="grid grid--4 stagger">
        {links.map((l) => (
          <button key={l.to} type="button" className="card card--pad card--interactive stack home-link" style={{ '--gap': '10px', textAlign: 'left' }} onClick={() => navigate(l.to)}>
            <span className={`icon-tile tone-${l.tone}`}><Icon name={l.icon} size={22} strokeWidth={2.4} /></span>
            <h3>{l.title}</h3>
            <p className="muted" style={{ fontSize: 'var(--fs-sm)' }}>{l.text}</p>
          </button>
        ))}
      </div>

      {isAdmin ? <RoleControl /> : null}
    </div>
  );
}
