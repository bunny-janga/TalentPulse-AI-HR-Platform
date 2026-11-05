import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '../../api/client.js';
import { useApp } from '../../app/store.jsx';
import { Badge, Button, CardHead, Icon, Modal, PageHead, Stat, Table, TextArea, useToast } from '../../components/ui/index.js';
import { Select } from '../../components/ui/Field.jsx';
import { formatDate } from '../../utils/format.js';

const RATING_LABEL = { 5: 'Exceptional', 4: 'Exceeds expectations', 3: 'Meets expectations', 2: 'Needs improvement', 1: 'Unsatisfactory' };
const ratingTone = (r) => (r >= 4 ? 'ok' : r <= 2 ? 'danger' : 'warn');

/** Current half-year plus the three before it, e.g. 2026-H2, 2026-H1, 2025-H2, 2025-H1. */
function recentCycles() {
  const now = new Date();
  let year = now.getFullYear();
  let half = now.getMonth() < 6 ? 1 : 2;
  const out = [];
  for (let i = 0; i < 4; i += 1) {
    out.push(`${year}-H${half}`);
    if (half === 1) { half = 2; year -= 1; } else half = 1;
  }
  return out;
}

function Stars({ value, size = 18 }) {
  return (
    <span className="star-row" role="img" aria-label={`${value} out of 5`}>
      {[1, 2, 3, 4, 5].map((n) => <Icon key={n} name="star" size={size} strokeWidth={2.4} className={n <= value ? 'on' : 'off'} />)}
    </span>
  );
}

function RatingPicker({ value, onChange }) {
  return (
    <div className="field">
      <span className="field__label">Rating</span>
      <div role="radiogroup" aria-label="Rating" className="pill-row">
        {[1, 2, 3, 4, 5].map((n) => (
          <button key={n} type="button" role="radio" aria-checked={value === n} className={`pill ${value === n ? 'is-active' : ''}`} onClick={() => onChange(n)} title={RATING_LABEL[n]}>{n}★</button>
        ))}
      </div>
      <span className="field__hint">{value ? RATING_LABEL[value] : 'Pick a rating'}</span>
    </div>
  );
}

const SECTIONS = [
  ['feedback', 'Overall summary', 'pink'],
  ['strengths', 'Strengths', 'green'],
  ['growth_areas', 'Areas for growth', 'yellow'],
  ['goals', 'Goals for next cycle', 'blue'],
];

function ReviewBody({ review }) {
  return (
    <div className="grid grid--2" style={{ '--gap': '16px' }}>
      {SECTIONS.map(([key, title, tone]) => (
        <div key={key} className={`box tone-${tone}`} style={{ borderWidth: 3 }}>
          <p className="eyebrow" style={{ color: '#111' }}>{title}</p>
          <p className="prose-block" style={{ marginTop: 6, color: '#111' }}>{review[key] || 'Not provided.'}</p>
        </div>
      ))}
    </div>
  );
}

export default function ReviewsPage() {
  const { role, session } = useApp();
  const toast = useToast();
  const isEmployee = role === 'employee';
  const isManager = role === 'manager';
  const cycles = useMemo(recentCycles, []);

  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterEmp, setFilterEmp] = useState('');
  const [opened, setOpened] = useState(null);

  const [employees, setEmployees] = useState([]);
  const [form, setForm] = useState({ employee_id: '', cycle: cycles[0], rating: 0, notes: '', feedback: '', strengths: '', growth_areas: '', goals: '' });
  const [errors, setErrors] = useState({});
  const [draftMode, setDraftMode] = useState(null);
  const [drafting, setDrafting] = useState(false);
  const [saving, setSaving] = useState(null); // 'DRAFT' | 'COMPLETED'

  const loadHistory = useCallback((empId = '') => {
    setLoading(true);
    const path = isEmployee ? '/reviews/my' : empId ? `/reviews?employee_id=${empId}` : '/reviews';
    api.get(path).then((d) => setHistory(Array.isArray(d) ? d : [])).catch((e) => { setHistory([]); toast.error('Could not load reviews', e.message); }).finally(() => setLoading(false));
  }, [isEmployee, toast]);

  useEffect(() => { loadHistory(filterEmp); }, [loadHistory, filterEmp]);
  useEffect(() => {
    if (isEmployee) return;
    api.get(isManager && session?.user_id ? `/employees?manager_id=${session.user_id}` : '/employees')
      .then((d) => { const list = Array.isArray(d) ? d : []; setEmployees(list); setForm((f) => ({ ...f, employee_id: f.employee_id || (list[0] ? String(list[0].id) : '') })); })
      .catch(() => setEmployees([]));
  }, [isEmployee, isManager, session?.user_id]);

  const set = (k) => (e) => { setForm((f) => ({ ...f, [k]: e.target.value })); setErrors((er) => ({ ...er, [k]: undefined })); };
  const empName = (id) => employees.find((e) => String(e.id) === String(id))?.full_name ?? '';

  const generate = async () => {
    if (!form.employee_id) { setErrors({ employee_id: 'Choose an employee first.' }); return; }
    if (form.notes.trim().length < 10) { setErrors({ notes: 'Write at least a couple of bullet points.' }); return; }
    setDrafting(true);
    try {
      const res = await api.post('/reviews/draft', { employee_id: Number(form.employee_id), review_cycle: form.cycle, rating: form.rating || null, bullet_notes: form.notes.trim() });
      setForm((f) => ({ ...f, feedback: res.summary || res.draft_review || '', strengths: res.strengths || '', growth_areas: res.growth_areas || '', goals: res.goals || '' }));
      setDraftMode(res.mode);
      toast.success('Draft ready', 'Read it, edit it, then publish. Nothing is saved yet.');
    } catch (e) { toast.error('Drafting failed', e.message); } finally { setDrafting(false); }
  };

  const save = async (status) => {
    const er = {};
    if (!form.employee_id) er.employee_id = 'Choose an employee.';
    if (!form.rating) er.rating = 'Pick a rating.';
    if (status === 'COMPLETED' && form.feedback.trim().length < 10) er.feedback = 'Write or generate the summary before publishing.';
    setErrors(er);
    if (Object.keys(er).length) { toast.error('Check the form', Object.values(er)[0]); return; }
    setSaving(status);
    try {
      await api.post('/reviews', {
        employee_id: Number(form.employee_id), review_cycle: form.cycle, rating: form.rating, status,
        feedback: form.feedback.trim() || null, strengths: form.strengths.trim() || null, growth_areas: form.growth_areas.trim() || null, goals: form.goals.trim() || null,
      });
      toast.success(status === 'COMPLETED' ? 'Review published' : 'Draft saved', `${empName(form.employee_id)} · ${form.cycle}`);
      setForm((f) => ({ ...f, rating: 0, notes: '', feedback: '', strengths: '', growth_areas: '', goals: '' }));
      setDraftMode(null);
      loadHistory(filterEmp);
    } catch (e) { toast.error('Could not save', e.message); } finally { setSaving(null); }
  };

  const latest = history.find((r) => r.status === 'COMPLETED') ?? history[0];

  /* ---------------- Employee: read-only view ---------------- */
  if (isEmployee) {
    return (
      <div className="page stack" style={{ '--gap': '28px' }}>
        <PageHead icon="star" tone="yellow" eyebrow="Workspace" title="My reviews" subtitle="What your manager wrote about you, cycle by cycle." actions={<Button icon="refresh" onClick={() => loadHistory()} loading={loading}>Refresh</Button>} />
        <div className="grid grid--3">
          <Stat tone="yellow" label="Latest rating" value={latest ? `${latest.rating}/5` : '–'} sub={latest ? RATING_LABEL[latest.rating] : 'No reviews yet'} icon="star" />
          <Stat label="Latest cycle" value={latest?.review_cycle ?? '–'} sub={latest?.reviewer_name ? `by ${latest.reviewer_name}` : ''} icon="calendar" />
          <Stat tone="blue" label="Reviews on file" value={history.length} icon="clipboard" />
        </div>
        {latest ? (
          <section className="card card--pad stack" style={{ '--gap': '18px' }}>
            <CardHead title={`Cycle ${latest.review_cycle}`} subtitle={`Reviewed by ${latest.reviewer_name ?? 'your manager'} · ${formatDate(latest.created_at)}`} actions={<><Stars value={latest.rating} /><Badge tone={ratingTone(latest.rating)}>{latest.rating}/5</Badge></>} />
            <ReviewBody review={latest} />
          </section>
        ) : !loading ? <div className="card card--pad state"><div className="state__orb"><Icon name="star" size={36} /></div><h2>No published reviews yet</h2><p>When your manager publishes a review it shows up here.</p></div> : null}
        {history.length > 1 ? (
          <section className="card card--pad">
            <CardHead title="History" />
            <Table>
              <thead><tr><th>Cycle</th><th>Rating</th><th>Reviewer</th><th>Date</th><th /></tr></thead>
              <tbody>{history.map((r) => (
                <tr key={r.id}><td className="cell-name">{r.review_cycle}</td><td><Badge tone={ratingTone(r.rating)}>{r.rating}/5</Badge></td><td>{r.reviewer_name}</td><td className="cell-sub">{formatDate(r.created_at)}</td><td className="is-right"><Button size="xs" onClick={() => setOpened(r)}>Open</Button></td></tr>
              ))}</tbody>
            </Table>
          </section>
        ) : null}
        <Modal open={Boolean(opened)} onClose={() => setOpened(null)} size="lg" title={`Cycle ${opened?.review_cycle ?? ''}`} description={opened ? `${opened.rating}/5 · ${opened.reviewer_name ?? ''}` : ''}>{opened ? <ReviewBody review={opened} /> : null}</Modal>
      </div>
    );
  }

  /* ---------------- Manager / HR / Admin ---------------- */
  return (
    <div className="page stack" style={{ '--gap': '28px' }}>
      <PageHead icon="star" tone="yellow" eyebrow="GenAI 2 · Workspace" title="Performance reviews"
        subtitle={isManager ? 'Write reviews for your direct reports. Jot rough notes and let the AI draft the rest.' : 'Review any employee, or browse every review on file.'}
        actions={<Button icon="refresh" onClick={() => loadHistory(filterEmp)} loading={loading}>Refresh</Button>} />

      <div className="split" style={{ '--l': '1fr', '--r': '1fr' }}>
        <section className="card card--pad stack" style={{ '--gap': '16px' }}>
          <CardHead icon="sparkles" title="1 · Notes to draft" subtitle="Rough bullets are fine." />
          <Select label="Employee" value={form.employee_id} onChange={set('employee_id')} error={errors.employee_id} placeholder={employees.length ? 'Choose…' : 'No eligible employees'} options={employees.map((e) => ({ value: e.id, label: `${e.full_name} (${e.employee_code})` }))} />
          <Select label="Review cycle" value={form.cycle} onChange={set('cycle')} options={cycles.map((c, i) => ({ value: c, label: i === 0 ? `${c} (current)` : c }))} />
          <TextArea label="Your bullet notes" rows={6} maxLength={3000} value={form.notes} onChange={set('notes')} error={errors.notes} placeholder={'- Led the cloud migration ahead of schedule\n- Great mentor to juniors\n- Needs to speak up more in design reviews'} />
          <Button variant="primary" icon="sparkles" loading={drafting} onClick={generate}>Draft with AI</Button>
        </section>

        <section className="card card--pad stack" style={{ '--gap': '16px' }}>
          <CardHead icon="edit" title="2 · Review" subtitle="You stay in control. Edit anything." actions={draftMode ? <Badge tone={draftMode === 'live' ? 'ok' : 'warn'}>{draftMode === 'live' ? 'Live LLM draft' : 'Offline structure'}</Badge> : null} />
          <RatingPicker value={form.rating} onChange={(n) => { setForm((f) => ({ ...f, rating: n })); setErrors((er) => ({ ...er, rating: undefined })); }} />
          {errors.rating ? <p className="field__error">{errors.rating}</p> : null}
          <TextArea label="Overall summary" rows={4} value={form.feedback} onChange={set('feedback')} error={errors.feedback} />
          <TextArea label="Strengths" rows={3} value={form.strengths} onChange={set('strengths')} />
          <TextArea label="Areas for growth" rows={3} value={form.growth_areas} onChange={set('growth_areas')} />
          <TextArea label="Goals for next cycle" rows={3} value={form.goals} onChange={set('goals')} />
          <div className="row">
            <Button icon="file" loading={saving === 'DRAFT'} disabled={Boolean(saving)} onClick={() => save('DRAFT')}>Save draft</Button>
            <Button variant="success" icon="check" loading={saving === 'COMPLETED'} disabled={Boolean(saving)} onClick={() => save('COMPLETED')}>Publish to employee</Button>
          </div>
        </section>
      </div>

      <section className="card card--pad stack" style={{ '--gap': '16px' }}>
        <CardHead icon="clipboard" title="Reviews on file" actions={<div style={{ minWidth: 240 }}><Select aria-label="Filter by employee" value={filterEmp} onChange={(e) => setFilterEmp(e.target.value)} placeholder="All employees" options={employees.map((e) => ({ value: e.id, label: e.full_name }))} /></div>} />
        <Table>
          <thead><tr><th>Employee</th><th>Cycle</th><th>Rating</th><th>Status</th><th>Reviewer</th><th>Date</th><th /></tr></thead>
          <tbody>
            {loading ? <tr><td colSpan="7" className="empty-cell">Loading…</td></tr> : history.length === 0 ? <tr><td colSpan="7" className="empty-cell">No reviews yet.</td></tr>
              : history.map((r) => (
                <tr key={r.id}>
                  <td><div className="cell-name">{r.employee_name}</div><div className="cell-sub">{r.employee_code}</div></td>
                  <td className="cell-name">{r.review_cycle}</td>
                  <td><Stars value={r.rating} size={14} /></td>
                  <td><Badge tone={r.status === 'COMPLETED' ? 'ok' : 'neutral'}>{r.status}</Badge></td>
                  <td>{r.reviewer_name}</td>
                  <td className="cell-sub">{formatDate(r.created_at)}</td>
                  <td className="is-right"><Button size="xs" onClick={() => setOpened(r)}>Open</Button></td>
                </tr>
              ))}
          </tbody>
        </Table>
      </section>

      <Modal open={Boolean(opened)} onClose={() => setOpened(null)} size="lg" title={opened ? `${opened.employee_name} · ${opened.review_cycle}` : ''} description={opened ? `${opened.rating}/5 · by ${opened.reviewer_name ?? ''}` : ''}>{opened ? <ReviewBody review={opened} /> : null}</Modal>
    </div>
  );
}
