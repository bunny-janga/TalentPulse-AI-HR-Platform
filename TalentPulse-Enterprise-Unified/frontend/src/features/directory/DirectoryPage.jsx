import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '../../api/client.js';
import { useApp } from '../../app/store.jsx';
import { useRoute } from '../../hooks/useRoute.js';
import { Badge, Button, CardHead, Chip, Icon, Meter, Modal, PageHead, Table, Tabs, TextArea, useToast } from '../../components/ui/index.js';
import { Input, Select } from '../../components/ui/Field.jsx';
import { ROLE_LABEL, formatDate, initials } from '../../utils/format.js';

const AVATAR_TONES = ['', 'avatar--blue', 'avatar--green', 'avatar--purple', 'avatar--orange', 'avatar--yellow'];
const tone = (id) => AVATAR_TONES[Math.abs(Number(id) || 0) % AVATAR_TONES.length];
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const money = (n) => (Number.isFinite(n) ? `₹${Math.round(n).toLocaleString('en-IN')}` : '—');

/* ---------- Org chart: nested lists, collapsible ---------- */
function OrgNode({ node, depth = 0, query }) {
  const [open, setOpen] = useState(depth < 2);
  const kids = node.direct_reports ?? [];
  const hit = query && node.full_name.toLowerCase().includes(query);
  return (
    <li>
      <div className={`list-row ${hit ? 'tone-yellow' : ''}`} style={{ marginBottom: 10 }}>
        {kids.length ? (
          <button type="button" className="btn btn--xs btn--icon" style={{ width: 34 }} aria-expanded={open} aria-label={`${open ? 'Collapse' : 'Expand'} ${node.full_name}'s team`} onClick={() => setOpen((o) => !o)}>
            <Icon name={open ? 'chevronDown' : 'chevronRight'} size={16} strokeWidth={3} />
          </button>
        ) : <span style={{ width: 34 }} />}
        <span className={`avatar ${tone(node.user_id)}`}>{initials(node.full_name)}</span>
        <div className="grow"><div className="cell-name truncate">{node.full_name}</div><div className="cell-sub truncate">{node.job_title} · {node.department}</div></div>
        {kids.length ? <Badge>{kids.length} report{kids.length > 1 ? 's' : ''}</Badge> : null}
      </div>
      {open && kids.length ? <ul className="org-children">{kids.map((k) => <OrgNode key={k.user_id} node={k} depth={depth + 1} query={query} />)}</ul> : null}
    </li>
  );
}

/* ---------- Onboarding checklist inside the profile modal ---------- */
function Onboarding({ employeeId, canAssign, canToggle }) {
  const toast = useToast();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState('');
  const [adding, setAdding] = useState(false);
  const [busy, setBusy] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    api.get(`/onboarding/${employeeId}`).then(setData).catch(() => setData(null)).finally(() => setLoading(false));
  }, [employeeId]);
  useEffect(() => { load(); }, [load]);

  const toggle = async (t) => {
    setBusy(t.id);
    try { await api.put(`/onboarding/tasks/${t.id}/complete?completed=${!t.is_completed}`); load(); } catch (e) { toast.error('Could not update task', e.message); } finally { setBusy(null); }
  };
  const add = async (e) => {
    e.preventDefault();
    if (title.trim().length < 3) return;
    setAdding(true);
    try { await api.post(`/onboarding/${employeeId}`, { title: title.trim(), category: 'General' }); setTitle(''); load(); } catch (err) { toast.error('Could not add task', err.message); } finally { setAdding(false); }
  };

  if (loading) return <p className="dim">Loading checklist…</p>;
  if (!data) return <p className="dim">The checklist is not available for you.</p>;
  return (
    <div className="stack" style={{ '--gap': '12px' }}>
      <div className="row spread"><strong>{data.completed_tasks} of {data.total_tasks} done</strong><span className="num">{Math.round(data.completion_rate_percent)}%</span></div>
      <Meter large value={data.completion_rate_percent} tone="green" label="Onboarding progress" />
      {data.tasks.length === 0 ? <p className="dim">No onboarding tasks assigned.</p> : data.tasks.map((t) => (
        <label key={t.id} className="list-row" style={{ cursor: canToggle ? 'pointer' : 'default', background: t.is_completed ? 'var(--c-green)' : undefined, color: t.is_completed ? '#111' : undefined }}>
          <input type="checkbox" checked={t.is_completed} disabled={!canToggle || busy === t.id} onChange={() => toggle(t)} />
          <span className="grow"><span className="cell-name" style={{ textDecoration: t.is_completed ? 'line-through' : 'none' }}>{t.title}</span><span className="cell-sub" style={{ display: 'block', color: 'inherit', opacity: 0.8 }}>{t.category}{t.due_date ? ` · due ${formatDate(t.due_date)}` : ''}</span></span>
        </label>
      ))}
      {canAssign ? (
        <form onSubmit={add} className="row row--nowrap" style={{ alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}><Input label="Add a task" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Set up VPN and laptop" /></div>
          <Button type="submit" variant="primary" icon="plus" loading={adding}>Add</Button>
        </form>
      ) : null}
    </div>
  );
}

export default function DirectoryPage() {
  const { role, session } = useApp();
  const { query: routeQuery } = useRoute();
  const toast = useToast();
  const isAdmin = ['admin', 'superadmin'].includes(role);
  const isHR = ['hr', 'admin', 'superadmin'].includes(role);

  const [tab, setTab] = useState('people');
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [hierarchy, setHierarchy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState(routeQuery.q ?? '');
  const [dept, setDept] = useState('ALL');
  const [profile, setProfile] = useState(null);

  const [creating, setCreating] = useState(routeQuery.action === 'new' && isAdmin);
  const [form, setForm] = useState({ full_name: '', email: '', job_title: 'Software Engineer', department_id: '', manager_id: '', role: 'employee', salary: '850000', overtime: 'No' });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [issued, setIssued] = useState(null); // { name, email, password }
  const [resetting, setResetting] = useState(false);

  useEffect(() => { if (routeQuery.q != null) setSearch(routeQuery.q); }, [routeQuery.q]);

  const load = useCallback(() => {
    setLoading(true);
    Promise.allSettled([api.get('/employees'), api.get('/org/hierarchy'), api.get('/departments')]).then(([e, h, d]) => {
      if (e.status === 'fulfilled') setEmployees(e.value ?? []); else toast.error('Could not load directory', e.reason?.message);
      if (h.status === 'fulfilled') setHierarchy(h.value);
      if (d.status === 'fulfilled') { setDepartments(d.value ?? []); setForm((f) => ({ ...f, department_id: f.department_id || String(d.value?.[0]?.id ?? '') })); }
    }).finally(() => setLoading(false));
  }, [toast]);
  useEffect(() => { load(); }, [load]);

  const managers = useMemo(() => employees.filter((e) => ['manager', 'admin', 'superadmin', 'hr'].includes(e.role)), [employees]);
  const q = search.trim().toLowerCase();
  const shown = employees.filter((e) => (dept === 'ALL' || e.department_name === dept) && (!q || [e.full_name, e.email, e.employee_code, e.job_title, e.department_name].some((v) => v?.toLowerCase().includes(q))));
  const set = (k) => (e) => { setForm((f) => ({ ...f, [k]: e.target.value })); setErrors((er) => ({ ...er, [k]: undefined })); };

  const create = async (e) => {
    e?.preventDefault();
    const er = {};
    if (form.full_name.trim().length < 2) er.full_name = 'Enter the full name.';
    if (!EMAIL_RE.test(form.email.trim())) er.email = 'Enter a valid email.';
    if (!form.department_id) er.department_id = 'Choose a department.';
    if (!(Number(form.salary) > 0)) er.salary = 'Enter a salary above zero.';
    setErrors(er);
    if (Object.keys(er).length) return;
    setSaving(true);
    try {
      const sal = Number(form.salary);
      const res = await api.post('/employees/onboard', {
        full_name: form.full_name.trim(), email: form.email.trim().toLowerCase(), job_title: form.job_title.trim() || 'Software Engineer',
        department_id: Number(form.department_id), manager_id: form.manager_id ? Number(form.manager_id) : null, role: form.role,
        salary: sal, salary_band: sal >= 1500000 ? 'High' : sal >= 800000 ? 'Medium' : 'Low', overtime_status: form.overtime === 'Yes', location: 'Visakhapatnam',
      });
      toast.success('Employee added', `${res.full_name} (${res.employee_code})`);
      setCreating(false);
      if (res.temporary_password) setIssued({ name: res.full_name, email: res.email, password: res.temporary_password });
      setForm((f) => ({ ...f, full_name: '', email: '', salary: '850000' }));
      load();
    } catch (err) { toast.error('Could not add employee', err.message); } finally { setSaving(false); }
  };

  const resetPassword = async (p) => {
    setResetting(true);
    try {
      const r = await api.post(`/admin/users/${p.user_id}/reset-password`, {});
      setProfile(null);
      setIssued({ name: p.full_name, email: p.email, password: r.temporary_password });
    } catch (err) { toast.error('Could not reset', err.message); } finally { setResetting(false); }
  };

  const copy = async (text) => { try { await navigator.clipboard.writeText(text); toast.success('Copied', 'Paste it somewhere safe.'); } catch { toast.error('Copy blocked', 'Select the text and copy it manually.'); } };

  const isMine = profile && profile.user_id === session?.user_id;
  const canAssignTasks = profile && (isHR || (role === 'manager' && profile.manager_id === session?.user_id));
  const canToggleTasks = profile && (canAssignTasks || isMine);

  return (
    <div className="page stack" style={{ '--gap': '28px' }}>
      <PageHead icon="users" tone="purple" eyebrow="People" title="Directory & org chart"
        subtitle="Find anyone, see who reports to whom, and follow each new hire’s onboarding."
        actions={<><Button icon="refresh" onClick={load} loading={loading}>Refresh</Button>{isAdmin ? <Button variant="primary" icon="plus" onClick={() => setCreating(true)}>Add employee</Button> : null}</>} />

      <Tabs idBase="dir" label="Directory views" value={tab} onChange={setTab} tabs={[{ id: 'people', label: 'People', icon: 'users', count: shown.length }, { id: 'org', label: 'Org chart', icon: 'org' }, { id: 'depts', label: 'Departments', icon: 'building', count: departments.length }]} />

      {tab === 'people' ? (
        <section className="card card--pad stack" style={{ '--gap': '16px' }}>
          <CardHead title="Everyone" subtitle="Click a person to open their profile." actions={
            <div className="row">
              <div style={{ minWidth: 260 }}><Input aria-label="Search people" placeholder="Search name, email, code, title…" value={search} onChange={(e) => setSearch(e.target.value)} /></div>
              <div style={{ minWidth: 200 }}><Select aria-label="Department" value={dept} onChange={(e) => setDept(e.target.value)} options={[{ value: 'ALL', label: 'All departments' }, ...departments.map((d) => ({ value: d.name, label: d.name }))]} /></div>
            </div>} />
          <Table>
            <thead><tr><th>Person</th><th>Role</th><th>Department</th><th>Manager</th><th>Joined</th></tr></thead>
            <tbody>
              {loading ? <tr><td colSpan="5" className="empty-cell">Loading…</td></tr> : shown.length === 0 ? <tr><td colSpan="5" className="empty-cell">No one matches.</td></tr> : shown.map((e) => (
                <tr key={e.id} data-clickable="true" tabIndex={0} onClick={() => setProfile(e)} onKeyDown={(ev) => { if (ev.key === 'Enter') setProfile(e); }}>
                  <td><div className="row row--nowrap"><span className={`avatar ${tone(e.user_id)}`}>{initials(e.full_name)}</span><div><div className="cell-name">{e.full_name}</div><div className="cell-sub">{e.job_title} · {e.employee_code}</div></div></div></td>
                  <td><Badge tone={e.role === 'superadmin' ? 'accent' : e.role === 'admin' ? 'info' : e.role === 'manager' ? 'warn' : 'neutral'}>{ROLE_LABEL[e.role] ?? e.role}</Badge></td>
                  <td>{e.department_name ?? '—'}</td>
                  <td>{e.manager_name ?? '—'}</td>
                  <td className="cell-sub">{formatDate(e.hire_date)}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </section>
      ) : null}

      {tab === 'org' ? (
        <section className="card card--pad stack" style={{ '--gap': '14px' }}>
          <CardHead icon="org" title={hierarchy?.organization ?? 'Reporting lines'} subtitle={hierarchy ? `${hierarchy.total_headcount} active people` : ''} actions={<div style={{ minWidth: 240 }}><Input aria-label="Highlight a person" placeholder="Highlight a person…" value={search} onChange={(e) => setSearch(e.target.value)} /></div>} />
          {hierarchy?.hierarchy_trees?.length ? <ul className="org-tree">{hierarchy.hierarchy_trees.map((n) => <OrgNode key={n.user_id} node={n} query={q} />)}</ul> : <p className="dim">{loading ? 'Loading…' : 'No hierarchy found.'}</p>}
        </section>
      ) : null}

      {tab === 'depts' ? (
        <div className="grid grid--auto stagger" style={{ '--min': '260px', '--gap': '20px' }}>
          {departments.map((d, i) => (
            <article key={d.id} className="card card--pad stack" style={{ '--gap': '10px' }}>
              <div className="row spread"><span className={`icon-tile tone-${['yellow', 'pink', 'blue', 'green', 'purple', 'orange'][i % 6]}`}><Icon name="building" size={22} strokeWidth={2.4} /></span><Badge>{d.code}</Badge></div>
              <h3>{d.name}</h3>
              <p className="muted" style={{ fontSize: 'var(--fs-sm)' }}>{d.description}</p>
              <p className="stat__value" style={{ fontSize: '2rem' }}>{d.employee_count}<span className="dim" style={{ fontSize: '1rem' }}> people</span></p>
            </article>
          ))}
        </div>
      ) : null}

      <Modal open={Boolean(profile)} onClose={() => setProfile(null)} size="lg" title={profile?.full_name ?? ''} description={profile ? `${profile.job_title} · ${profile.department_name ?? ''}` : ''}>
        {profile ? (
          <div className="stack" style={{ '--gap': '22px' }}>
            <div className="grid grid--auto" style={{ '--min': '180px', '--gap': '10px' }}>
              {[['Employee code', profile.employee_code], ['Email', profile.email], ['Role', ROLE_LABEL[profile.role] ?? profile.role], ['Reports to', profile.manager_name ?? '—'], ['Hired', formatDate(profile.hire_date)], ['Last promotion', profile.last_promotion_date ? formatDate(profile.last_promotion_date) : '—'], ['Location', profile.location],
                ...(profile.salary != null ? [['Salary', money(profile.salary)], ['Salary band', profile.salary_band]] : [])].map(([k, v]) => (
                <div className="box" key={k}><p className="eyebrow">{k}</p><p style={{ fontWeight: 800, overflowWrap: 'anywhere' }}>{v}</p></div>
              ))}
            </div>
            <div className="stack" style={{ '--gap': '12px' }}><h3>Onboarding checklist</h3><Onboarding key={profile.id} employeeId={profile.id} canAssign={canAssignTasks} canToggle={canToggleTasks} /></div>
            {isAdmin && !isMine ? (
              <div className="box box--accent row spread">
                <div><strong>Forgot their password?</strong><p style={{ fontSize: 'var(--fs-sm)' }}>Issues a new one-time password. The old one stops working.</p></div>
                <Button icon="key" loading={resetting} onClick={() => resetPassword(profile)}>Reset password</Button>
              </div>
            ) : null}
          </div>
        ) : null}
      </Modal>

      <Modal open={creating} onClose={() => !saving && setCreating(false)} size="lg" title="Add employee" description="Creates the login and the HR record together. A one-time password is generated for you to hand over."
        footer={<><Button onClick={() => setCreating(false)} disabled={saving}>Cancel</Button><Button variant="primary" loading={saving} onClick={create}>Create employee</Button></>}>
        <form onSubmit={create} className="grid grid--2" style={{ '--gap': '16px' }} noValidate>
          <Input label="Full name" value={form.full_name} onChange={set('full_name')} error={errors.full_name} required />
          <Input label="Work email" type="email" value={form.email} onChange={set('email')} error={errors.email} placeholder="name@talentpulse.local" required />
          <Input label="Job title" value={form.job_title} onChange={set('job_title')} />
          <Select label="Department" value={form.department_id} onChange={set('department_id')} error={errors.department_id} options={departments.map((d) => ({ value: d.id, label: d.name }))} />
          <Select label="Reports to" value={form.manager_id} onChange={set('manager_id')} placeholder="No manager" options={managers.map((m) => ({ value: m.user_id, label: `${m.full_name} (${ROLE_LABEL[m.role] ?? m.role})` }))} />
          <Select label="Role" value={form.role} onChange={set('role')} options={[{ value: 'employee', label: 'Employee' }, { value: 'manager', label: 'Manager' }, { value: 'hr', label: 'HR Executive' }, ...(role === 'superadmin' ? [{ value: 'admin', label: 'Admin' }] : [])]} />
          <Input label="Annual salary (INR)" type="number" min="1" value={form.salary} onChange={set('salary')} error={errors.salary} />
          <Select label="Regular overtime / on-call" value={form.overtime} onChange={set('overtime')} options={[{ value: 'No', label: 'No' }, { value: 'Yes', label: 'Yes' }]} />
        </form>
      </Modal>

      <Modal open={Boolean(issued)} onClose={() => setIssued(null)} title="One-time password" description="Shown once. Share it securely; the person should change it after signing in."
        footer={<Button variant="primary" onClick={() => setIssued(null)}>I have copied it</Button>}>
        {issued ? (
          <div className="stack" style={{ '--gap': '14px' }}>
            <div className="box"><p className="eyebrow">Account</p><p style={{ fontWeight: 800 }}>{issued.name} · {issued.email}</p></div>
            <div className="callout row spread" style={{ alignItems: 'center' }}>
              <code style={{ fontSize: 'var(--fs-md)', fontWeight: 700, overflowWrap: 'anywhere' }}>{issued.password}</code>
              <Button size="sm" icon="mail" onClick={() => copy(issued.password)}>Copy</Button>
            </div>
            <p className="callout callout--danger"><Icon name="lock" size={18} /><span>We store only a hash, so this password cannot be shown again.</span></p>
          </div>
        ) : null}
      </Modal>
    </div>
  );
}
