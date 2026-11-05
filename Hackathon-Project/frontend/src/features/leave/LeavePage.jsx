import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '../../api/client.js';
import { useApp } from '../../app/store.jsx';
import { Badge, Button, CardHead, Chip, Meter, Modal, PageHead, Stat, Table, TextArea, useToast } from '../../components/ui/index.js';
import { Input, Select } from '../../components/ui/Field.jsx';
import { LEAVE_TYPES, formatDate, todayISO, weekdaysBetween } from '../../utils/format.js';

const STATUS_TONE = { APPROVED: 'ok', REJECTED: 'danger', PENDING: 'warn', CANCELLED: 'neutral' };
const BAL_TONE = { 'Casual Leave': 'green', 'Sick Leave': 'blue', 'Earned Leave': 'pink' };

export default function LeavePage() {
  const { role } = useApp();
  const toast = useToast();
  const isLead = ['manager', 'admin', 'superadmin', 'hr'].includes(role);
  const canApplyOnBehalf = ['hr', 'admin', 'superadmin'].includes(role);

  const [leaves, setLeaves] = useState([]);
  const [balances, setBalances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');
  const [scope, setScope] = useState('team'); // leads can flip between the team queue and their own requests
  const queueView = isLead && scope === 'team';
  const [employees, setEmployees] = useState([]);
  const [decision, setDecision] = useState(null); // { leave, action }
  const [comment, setComment] = useState('');
  const [deciding, setDeciding] = useState(false);

  const [form, setForm] = useState({ leave_type: 'Casual Leave', start_date: '', end_date: '', reason: '', employee_id: '' });
  const [errors, setErrors] = useState({});
  const [applying, setApplying] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    Promise.allSettled([
      api.get(isLead && scope === 'team' ? '/leave/team' : '/leave/my'),
      api.get('/leave/balance'),
    ]).then(([l, b]) => {
      if (l.status === 'fulfilled') setLeaves(Array.isArray(l.value) ? l.value : []);
      else { setLeaves([]); toast.error('Could not load leave', l.reason?.message); }
      if (b.status === 'fulfilled') setBalances(b.value?.balances ?? []);
    }).finally(() => setLoading(false));
  }, [isLead, scope, toast]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (!canApplyOnBehalf) return;
    api.get('/employees').then((d) => setEmployees(Array.isArray(d) ? d : [])).catch(() => setEmployees([]));
  }, [canApplyOnBehalf]);

  const counts = useMemo(() => ({
    PENDING: leaves.filter((l) => l.status === 'PENDING').length,
    APPROVED: leaves.filter((l) => l.status === 'APPROVED').length,
    REJECTED: leaves.filter((l) => l.status === 'REJECTED').length,
  }), [leaves]);
  const shown = filter === 'ALL' ? leaves : leaves.filter((l) => l.status === filter);
  const days = weekdaysBetween(form.start_date, form.end_date);
  const set = (k) => (e) => { setForm((f) => ({ ...f, [k]: e.target.value })); setErrors((er) => ({ ...er, [k]: undefined })); };

  const validate = () => {
    const er = {};
    const today = todayISO();
    if (!form.start_date) er.start_date = 'Pick a start date.';
    if (!form.end_date) er.end_date = 'Pick an end date.';
    if (form.start_date && form.end_date && form.end_date < form.start_date) er.end_date = 'End date is before the start date.';
    if (form.start_date && form.leave_type !== 'Sick Leave' && form.start_date < today) er.start_date = 'Only sick leave can be back-dated.';
    if (form.start_date && form.end_date && form.end_date >= form.start_date && days === 0) er.end_date = 'That range is only weekend days.';
    if (form.reason.trim().length < 3) er.reason = 'Give a short reason (3+ characters).';
    return er;
  };

  const apply = async (e) => {
    e.preventDefault();
    const er = validate();
    setErrors(er);
    if (Object.keys(er).length) return;
    setApplying(true);
    try {
      const payload = { leave_type: form.leave_type, start_date: form.start_date, end_date: form.end_date, reason: form.reason.trim() };
      if (canApplyOnBehalf && form.employee_id) payload.employee_id = Number(form.employee_id);
      await api.post('/leave/apply', payload);
      toast.success('Leave submitted', `${days} working ${days === 1 ? 'day' : 'days'} sent for approval.`);
      setForm((f) => ({ ...f, start_date: '', end_date: '', reason: '', employee_id: '' }));
      load();
    } catch (err) {
      toast.error('Could not submit', err.message);
    } finally {
      setApplying(false);
    }
  };

  const openDecision = (leave, action) => {
    setDecision({ leave, action });
    setComment(action === 'approve' ? 'Approved.' : '');
  };
  const confirmDecision = async () => {
    if (decision.action === 'reject' && comment.trim().length < 3) { toast.error('Add a reason', 'Rejections need a short reason for the employee.'); return; }
    setDeciding(true);
    try {
      await api.put(`/leave/${decision.leave.id}/${decision.action}`, { comment: comment.trim() || 'Approved.' });
      toast.success(decision.action === 'approve' ? 'Leave approved' : 'Leave rejected', decision.leave.employee_name);
      setDecision(null);
      load();
    } catch (err) {
      toast.error('Action failed', err.message);
    } finally {
      setDeciding(false);
    }
  };

  return (
    <div className="page stack" style={{ '--gap': '28px' }}>
      <PageHead
        icon="calendar" tone="blue" eyebrow="Workspace" title="Leave"
        subtitle={isLead ? 'Approve requests from the people you manage, and apply for your own leave.' : 'Apply for leave and track every request.'}
        actions={<Button icon="refresh" onClick={load} loading={loading}>Refresh</Button>}
      />

      <div className="grid grid--4">
        {balances.length === 0 && loading ? [0, 1, 2].map((i) => <div key={i} className="stat"><span className="stat__label">Loading…</span></div>) : balances.map((b) => (
          <Stat key={b.leave_type} label={b.leave_type} value={<>{b.remaining}<span className="dim" style={{ fontSize: '1rem', fontWeight: 700 }}> / {b.quota}</span></>} sub={`${b.used} used${b.pending ? ` · ${b.pending} pending` : ''}`}>
            <Meter value={b.remaining} max={b.quota} tone={BAL_TONE[b.leave_type] ?? 'green'} label={`${b.leave_type} remaining`} />
          </Stat>
        ))}
        <Stat tone={counts.PENDING ? 'yellow' : 'green'} label={queueView ? 'Waiting on you' : 'Pending'} value={counts.PENDING} sub={`${counts.APPROVED} approved · ${counts.REJECTED} rejected`} icon="clock" />
      </div>

      <div className="split" style={{ '--l': '1.8fr', '--r': '1fr' }}>
        <section className="card card--pad">
          <CardHead title={queueView ? 'Team requests' : 'My requests'} subtitle={`Showing ${shown.length} of ${leaves.length}`} actions={
            <div className="row" role="group" aria-label="Filter by status">
              {['ALL', 'PENDING', 'APPROVED', 'REJECTED'].map((s) => <Chip key={s} selected={filter === s} onClick={() => setFilter(s)}>{s}</Chip>)}
            </div>
          } />
          {isLead ? <div className="row" role="group" aria-label="Which requests" style={{ marginBottom: 16 }}>
            <Chip selected={scope === 'team'} onClick={() => setScope('team')}>Team queue</Chip>
            <Chip selected={scope === 'mine'} onClick={() => setScope('mine')}>My requests</Chip>
          </div> : null}
          <Table>
            <thead><tr><th>Who</th><th>Leave</th><th>Days</th><th>Status</th><th className="is-right">{queueView ? 'Action' : 'Note'}</th></tr></thead>
            <tbody>
              {loading ? <tr><td colSpan="5" className="empty-cell">Loading…</td></tr>
                : shown.length === 0 ? <tr><td colSpan="5" className="empty-cell">Nothing here for this filter.</td></tr>
                : shown.map((l) => (
                  <tr key={l.id}>
                    <td><div className="cell-name">{l.employee_name || 'Staff member'}</div><div className="cell-sub">{l.employee_code}</div></td>
                    <td>
                      <div style={{ fontWeight: 700 }}>{l.leave_type}</div>
                      <div className="cell-sub">{formatDate(l.start_date)} → {formatDate(l.end_date)}</div>
                      {l.reason ? <div className="dim" style={{ fontSize: 'var(--fs-xs)' }}>“{l.reason}”</div> : null}
                    </td>
                    <td><span className="badge">{l.days_count}d</span></td>
                    <td><Badge tone={STATUS_TONE[l.status] ?? 'neutral'}>{l.status}</Badge></td>
                    <td className="is-right">
                      {queueView && l.status === 'PENDING' ? (
                        <div className="row" style={{ justifyContent: 'flex-end' }}>
                          <Button size="xs" variant="success" onClick={() => openDecision(l, 'approve')}>Approve</Button>
                          <Button size="xs" variant="danger" onClick={() => openDecision(l, 'reject')}>Reject</Button>
                        </div>
                      ) : <span className="dim" style={{ fontSize: 'var(--fs-xs)' }}>{l.approver_comment || '—'}{l.approver_name ? ` (${l.approver_name})` : ''}</span>}
                    </td>
                  </tr>
                ))}
            </tbody>
          </Table>
        </section>

        <section className="card card--pad">
          <CardHead icon="plus" title="Apply for leave" />
          <form onSubmit={apply} className="stack" style={{ '--gap': '16px' }} noValidate>
            {canApplyOnBehalf ? (
              <Select label="Apply on behalf of" value={form.employee_id} onChange={set('employee_id')} hint="Leave empty to apply for yourself."
                placeholder="Myself" options={employees.map((e) => ({ value: e.id, label: `${e.full_name} (${e.employee_code})` }))} />
            ) : null}
            <Select label="Leave type" value={form.leave_type} onChange={set('leave_type')} options={LEAVE_TYPES} />
            <div className="date-range">
              <Input label="Start date" type="date" value={form.start_date} min={form.leave_type === 'Sick Leave' ? undefined : todayISO()} onChange={set('start_date')} error={errors.start_date} />
              <Input label="End date" type="date" value={form.end_date} min={form.start_date || undefined} onChange={set('end_date')} error={errors.end_date} />
            </div>
            {days > 0 ? <p className="callout callout--info" style={{ padding: '8px 12px' }}>Counts as <strong>{days} working {days === 1 ? 'day' : 'days'}</strong> (Mon–Fri).</p> : null}
            <TextArea label="Reason and coverage" rows={3} value={form.reason} onChange={set('reason')} error={errors.reason} placeholder="Who covers your tickets while you are away?" />
            <Button type="submit" variant="primary" loading={applying} style={{ width: '100%' }}>Submit application</Button>
          </form>
        </section>
      </div>

      <Modal
        open={Boolean(decision)} onClose={() => !deciding && setDecision(null)}
        title={decision?.action === 'approve' ? 'Approve this leave?' : 'Reject this leave?'}
        description={decision ? `${decision.leave.employee_name}: ${decision.leave.leave_type}, ${decision.leave.days_count} day(s)` : ''}
        footer={<>
          <Button onClick={() => setDecision(null)} disabled={deciding}>Cancel</Button>
          <Button variant={decision?.action === 'approve' ? 'success' : 'danger'} loading={deciding} onClick={confirmDecision}>{decision?.action === 'approve' ? 'Approve' : 'Reject'}</Button>
        </>}
      >
        <TextArea label={decision?.action === 'reject' ? 'Reason (shown to employee)' : 'Comment (optional)'} rows={3} value={comment} onChange={(e) => setComment(e.target.value)} />
      </Modal>
    </div>
  );
}
