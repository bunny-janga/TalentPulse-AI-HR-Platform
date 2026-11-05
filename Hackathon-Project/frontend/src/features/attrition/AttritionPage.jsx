import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '../../api/client.js';
import { useApp } from '../../app/store.jsx';
import { Badge, Button, CardHead, Chip, Icon, Meter, Modal, PageHead, Stat, Table, TextArea, useToast } from '../../components/ui/index.js';
import { Input } from '../../components/ui/Field.jsx';
import { RISK_TONE } from '../../utils/format.js';

const BAND_FILL = { HIGH: 'red', MEDIUM: 'yellow', LOW: 'green' };

const featureRows = (f = {}) => [
  ['Tenure', `${f.tenure ?? '–'} yrs`],
  ['Since last promotion', `${f.promotion_gap ?? '–'} yrs`],
  ['Overtime', f.overtime ? 'Yes' : 'No'],
  ['Latest rating', f.performance_rating ?? '–'],
  ['Rating trend', f.performance_trend > 0 ? `+${f.performance_trend}` : f.performance_trend ?? '–'],
  ['Leave requests (12 mo)', f.leave_frequency ?? '–'],
  ['Survey sentiment', f.survey_sentiment ?? '–'],
];

export default function AttritionPage() {
  const { role } = useApp();
  const toast = useToast();
  const isManager = role === 'manager';

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [recomputing, setRecomputing] = useState(false);
  const [band, setBand] = useState('ALL');
  const [search, setSearch] = useState('');
  const [detail, setDetail] = useState(null);

  const [exitOpen, setExitOpen] = useState(false);
  const [exit, setExit] = useState({ notes: '', job_title: '', department: '' });
  const [exitResult, setExitResult] = useState(null);
  const [exiting, setExiting] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    api.get(isManager ? '/attrition/team' : '/attrition/dashboard')
      .then(setData)
      .catch((e) => toast.error('Could not load attrition data', e.message))
      .finally(() => setLoading(false));
  }, [isManager, toast]);
  useEffect(() => { load(); }, [load]);

  const recompute = async () => {
    setRecomputing(true);
    try {
      const r = await api.post('/attrition/recompute');
      toast.success('Scores refreshed', `${r.total_scored} employees re-scored by the model.`);
      load();
    } catch (e) { toast.error('Recompute failed', e.message); } finally { setRecomputing(false); }
  };

  const runExit = async () => {
    if (exit.notes.trim().length < 20) { toast.error('Add more detail', 'Paste at least a couple of sentences of interview notes.'); return; }
    setExiting(true);
    try { setExitResult(await api.post('/ai/exit-summary', { notes: exit.notes.trim(), job_title: exit.job_title || undefined, department: exit.department || undefined })); }
    catch (e) { toast.error('Summary failed', e.message); } finally { setExiting(false); }
  };

  const dist = (isManager ? data?.risk_counts : data?.risk_distribution) ?? {};
  const total = (isManager ? data?.team_size : data?.total_headcount) ?? 0;
  const all = useMemo(() => data?.employees ?? [], [data]);
  const shown = useMemo(() => {
    const q = search.trim().toLowerCase();
    return all.filter((e) => (band === 'ALL' || e.risk_band === band) && (!q || [e.full_name, e.employee_code, e.job_title, e.department_name].some((v) => v?.toLowerCase().includes(q))));
  }, [all, band, search]);
  const depts = data?.department_breakdown ?? [];

  return (
    <div className="page stack" style={{ '--gap': '28px' }}>
      <PageHead icon="shield" tone="pink" eyebrow="AI 1 · Intelligence" title="Attrition radar"
        subtitle={isManager ? 'Who on your team might leave, why, and what to do about it. Only you and HR can see this.' : 'Company-wide flight risk. Visible to HR and Admin only; managers see their own team.'}
        actions={<>
          <Button icon="refresh" onClick={load} loading={loading}>Refresh</Button>
          {!isManager ? <Button variant="primary" icon="bolt" loading={recomputing} onClick={recompute}>Re-score everyone</Button> : null}
          {!isManager ? <Button variant="pink" icon="door" onClick={() => setExitOpen(true)}>Exit interview AI</Button> : null}
        </>} />

      <div className="grid grid--4">
        <Stat label={isManager ? 'Team size' : 'People scored'} value={loading ? '…' : total} icon="users" />
        {['HIGH', 'MEDIUM', 'LOW'].map((b) => (
          <Stat key={b} tone={b === 'HIGH' ? 'red' : b === 'MEDIUM' ? 'yellow' : 'green'} label={`${b} risk`} value={loading ? '…' : dist[b] ?? 0}
            sub={b === 'HIGH' ? 'Talk to them this week' : b === 'MEDIUM' ? 'Keep on the watchlist' : 'Stable'}>
            <Meter value={dist[b] ?? 0} max={Math.max(total, 1)} tone={BAND_FILL[b]} label={`${b} share`} />
          </Stat>
        ))}
      </div>

      {!isManager && data ? (
        <div className="split" style={{ '--l': '1.2fr', '--r': '1fr' }}>
          <section className="card card--pad stack" style={{ '--gap': '14px' }}>
            <CardHead icon="building" title="By department" subtitle="Average model risk per team" />
            {depts.length === 0 ? <p className="dim">No data.</p> : depts.slice().sort((a, b) => b.average_risk_score - a.average_risk_score).map((d) => (
              <div key={d.department_id} className="bar-row">
                <span className="cell-name truncate" title={d.department_name}>{d.department_name}</span>
                <Meter value={d.average_risk_score * 100} max={100} tone={d.average_risk_score >= 0.5 ? 'red' : d.average_risk_score >= 0.25 ? 'yellow' : 'green'} label={`${d.department_name} average risk`} />
                <span className="num" title={`${d.high_risk_count} high-risk of ${d.total_staff}`}>{Math.round(d.average_risk_score * 100)}% · {d.high_risk_count}/{d.total_staff}</span>
              </div>
            ))}
          </section>
          <section className="card card--pad stack tone-yellow" style={{ '--gap': '12px' }}>
            <CardHead icon="target" title="What is driving it" subtitle="Most common reasons across high and medium risk staff" />
            {(data.top_company_drivers ?? []).length === 0 ? <p>No dominant drivers found.</p> : (
              <ol className="stack" style={{ '--gap': '10px', paddingLeft: 0 }}>
                {data.top_company_drivers.map((d, i) => <li key={d} className="list-row" style={{ color: 'var(--text)' }}><span className="icon-tile" style={{ background: 'var(--c-pink)' }}>{i + 1}</span><span style={{ fontWeight: 700 }}>{d}</span></li>)}
              </ol>
            )}
          </section>
        </div>
      ) : null}

      <section className="card card--pad stack" style={{ '--gap': '16px' }}>
        <CardHead title={isManager ? 'Your team' : 'Everyone, highest risk first'} subtitle={`${shown.length} of ${all.length} shown. Click a row for the full picture.`} actions={
          <div className="row">
            {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((b) => <Chip key={b} selected={band === b} onClick={() => setBand(b)}>{b}</Chip>)}
            <div style={{ minWidth: 240 }}><Input aria-label="Search employees" placeholder="Search name, code, title…" value={search} onChange={(e) => setSearch(e.target.value)} /></div>
          </div>} />
        <Table onRowClick={undefined}>
          <thead><tr><th>Employee</th><th>Title</th><th style={{ minWidth: 190 }}>Risk</th><th>Top 3 reasons</th><th /></tr></thead>
          <tbody>
            {loading ? <tr><td colSpan="5" className="empty-cell">Scoring…</td></tr>
              : shown.length === 0 ? <tr><td colSpan="5" className="empty-cell">{all.length ? 'No one matches that filter.' : 'No scored employees yet. Press “Re-score everyone”.'}</td></tr>
              : shown.map((e) => (
                <tr key={e.employee_id} data-clickable="true" tabIndex={0} onClick={() => setDetail(e)} onKeyDown={(ev) => { if (ev.key === 'Enter') setDetail(e); }}>
                  <td><div className="cell-name">{e.full_name}</div><div className="cell-sub">{e.employee_code}</div></td>
                  <td><div style={{ fontWeight: 700 }}>{e.job_title}</div><div className="cell-sub">{e.department_name}</div></td>
                  <td>
                    <div className="row spread row--nowrap"><Badge tone={RISK_TONE[e.risk_band]}>{e.risk_band}</Badge><span className="num" style={{ fontWeight: 900 }}>{Math.round(e.risk_score * 100)}%</span></div>
                    <Meter value={e.risk_score * 100} tone={BAND_FILL[e.risk_band]} label={`${e.full_name} risk`} />
                  </td>
                  <td><ul className="stack" style={{ '--gap': '4px' }}>{(e.top_factors ?? []).map((f) => <li key={f} style={{ fontSize: 'var(--fs-xs)', fontWeight: 600 }}>• {f}</li>)}</ul></td>
                  <td className="is-right"><Icon name="chevronRight" size={20} strokeWidth={3} /></td>
                </tr>
              ))}
          </tbody>
        </Table>
      </section>

      <Modal open={Boolean(detail)} onClose={() => setDetail(null)} size="lg" title={detail?.full_name ?? ''} description={detail ? `${detail.job_title} · ${detail.department_name}${detail.manager_name ? ` · reports to ${detail.manager_name}` : ''}` : ''}>
        {detail ? (
          <div className="stack" style={{ '--gap': '20px' }}>
            <div className="row spread"><Badge tone={RISK_TONE[detail.risk_band]}>{detail.risk_band} risk</Badge><span className="stat__value" style={{ fontSize: '2.4rem' }}>{Math.round(detail.risk_score * 100)}%</span></div>
            <Meter large value={detail.risk_score * 100} tone={BAND_FILL[detail.risk_band]} label="Risk probability" />
            <div className="split" style={{ '--l': '1fr', '--r': '1fr' }}>
              <div className="stack" style={{ '--gap': '10px' }}>
                <h3>Why the model says so</h3>
                {(detail.top_factors ?? []).map((f, i) => <div className="list-row" key={f}><span className="icon-tile" style={{ background: 'var(--c-pink)' }}>{i + 1}</span>{f}</div>)}
              </div>
              <div className="stack" style={{ '--gap': '10px' }}>
                <h3>What to do next</h3>
                {(detail.suggested_actions ?? []).length ? detail.suggested_actions.map((a) => <div className="list-row" key={a} style={{ background: 'var(--c-green)', color: '#111' }}><Icon name="check" size={18} strokeWidth={3} />{a}</div>) : <p className="dim">No specific action needed.</p>}
              </div>
            </div>
            <div>
              <h3 style={{ marginBottom: 10 }}>Inputs the model saw</h3>
              <div className="grid grid--auto" style={{ '--min': '170px', '--gap': '10px' }}>
                {featureRows(detail.features).map(([k, v]) => <div className="box" key={k}><p className="eyebrow">{k}</p><p style={{ fontWeight: 900, fontSize: 'var(--fs-md)' }}>{String(v)}</p></div>)}
              </div>
            </div>
            <p className="cell-sub">Scored {detail.computed_at ? new Date(detail.computed_at.endsWith('Z') ? detail.computed_at : `${detail.computed_at}Z`).toLocaleString() : ''}. A prediction is a prompt for a conversation, never a decision about a person.</p>
          </div>
        ) : null}
      </Modal>

      <Modal open={exitOpen} onClose={() => !exiting && setExitOpen(false)} size="lg" title="Exit interview summariser" description="GenAI turns raw exit-interview notes into a reason, work-environment factors and prevention steps. Do not paste real personal data."
        footer={<><Button onClick={() => setExitOpen(false)} disabled={exiting}>Close</Button><Button variant="primary" icon="sparkles" loading={exiting} onClick={runExit}>Summarise</Button></>}>
        <div className="stack" style={{ '--gap': '14px' }}>
          <div className="date-range"><Input label="Job title" value={exit.job_title} onChange={(e) => setExit({ ...exit, job_title: e.target.value })} placeholder="Software Engineer" /><Input label="Department" value={exit.department} onChange={(e) => setExit({ ...exit, department: e.target.value })} placeholder="Software Engineering" /></div>
          <TextArea label="Interview notes" rows={6} maxLength={4000} value={exit.notes} onChange={(e) => setExit({ ...exit, notes: e.target.value })} placeholder="Left for a 40% higher offer. Felt stuck at the same level for 3 years. Frequent weekend deployments…" />
          {exitResult ? <div className="box box--accent stack" style={{ '--gap': '8px' }}><Badge tone={exitResult.mode === 'live' ? 'ok' : 'warn'}>{exitResult.mode === 'live' ? 'Live LLM' : 'Offline summary'}</Badge><p className="prose-block">{exitResult.exit_summary}</p></div> : null}
        </div>
      </Modal>
    </div>
  );
}
