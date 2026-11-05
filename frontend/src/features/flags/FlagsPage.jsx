import { useCallback, useEffect, useState } from 'react';
import { api } from '../../api/client.js';
import { Badge, Button, Icon, PageHead, Stat, Table, useToast } from '../../components/ui/index.js';

export default function FlagsPage() {
  const toast = useToast();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);
  const [notified, setNotified] = useState(() => new Set());

  const load = useCallback(() => {
    setLoading(true);
    api.get('/ai/performance-flags').then(setData).catch((e) => toast.error('Could not load flags', e.message)).finally(() => setLoading(false));
  }, [toast]);
  useEffect(() => { load(); }, [load]);

  const flagged = data?.flagged_employees ?? [];

  const requestOneOnOne = async (f) => {
    setBusyId(f.employee_id);
    try {
      const r = await api.post(`/ai/performance-flags/${f.employee_id}/one-on-one`, {});
      setNotified((s) => new Set(s).add(f.employee_id));
      toast.success('1-on-1 requested', r.message);
    } catch (e) { toast.error('Could not send', e.message); } finally { setBusyId(null); }
  };

  return (
    <div className="page stack" style={{ '--gap': '28px' }}>
      <PageHead icon="trendDown" tone="red" eyebrow="AI 2 · Intelligence" title="Performance flags"
        subtitle="Two or more review ratings in a row going down. Catch it while a conversation can still change the outcome."
        actions={<Button icon="refresh" onClick={load} loading={loading}>Re-scan</Button>} />

      <div className="grid grid--3">
        <Stat label="Flagged people" value={loading ? '…' : data?.total_flagged ?? 0} icon="users" sub="2+ declines in a row" />
        <Stat tone="red" label="Critical" value={loading ? '…' : data?.critical_count ?? 0} icon="alert" sub="Rating ≤ 2, or dropped 2+ points" />
        <Stat tone="yellow" label="Warning" value={loading ? '…' : data?.warning_count ?? 0} icon="clock" sub="Watch and check in" />
      </div>

      <section className="card card--pad">
        <Table>
          <thead><tr><th>Employee</th><th>Rating history</th><th>Declines</th><th>Severity</th><th>Suggested action</th><th /></tr></thead>
          <tbody>
            {loading ? <tr><td colSpan="6" className="empty-cell">Scanning review history…</td></tr>
              : flagged.length === 0 ? <tr><td colSpan="6" className="empty-cell">No multi-cycle declines. Ratings look stable.</td></tr>
              : flagged.map((f) => (
                <tr key={f.employee_id}>
                  <td><div className="cell-name">{f.full_name}</div><div className="cell-sub">{f.employee_code} · {f.department_name}</div>{f.attrition_risk_band ? <Badge tone={f.attrition_risk_band === 'HIGH' ? 'danger' : f.attrition_risk_band === 'MEDIUM' ? 'warn' : 'ok'}>{f.attrition_risk_band} attrition risk</Badge> : null}</td>
                  <td>
                    <div className="row" style={{ '--gap': '6px' }}>
                      {(f.previous_ratings ?? []).map((r, i, arr) => (
                        <span key={r.review_cycle + i} className="row row--nowrap" style={{ '--gap': '6px' }}>
                          <span className={`badge ${r.rating <= 2 ? 'badge--danger' : ''}`} title={r.review_cycle}>{r.review_cycle} · {r.rating}★</span>
                          {i < arr.length - 1 ? <Icon name="arrowRight" size={14} strokeWidth={3} /> : null}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td><div className="num" style={{ fontWeight: 900, fontSize: 'var(--fs-md)' }}>{f.consecutive_declines}×</div><div className="cell-sub">−{f.total_drop} pts total</div></td>
                  <td><Badge tone={f.severity === 'CRITICAL' ? 'danger' : 'warn'}>{f.severity}</Badge></td>
                  <td style={{ maxWidth: 300, fontSize: 'var(--fs-sm)' }}>{f.action_recommendation}</td>
                  <td className="is-right">
                    {notified.has(f.employee_id) ? <Badge tone="ok" icon="check">Requested</Badge>
                      : <Button size="xs" variant={f.severity === 'CRITICAL' ? 'danger' : 'secondary'} loading={busyId === f.employee_id} onClick={() => requestOneOnOne(f)}>Request 1-on-1</Button>}
                  </td>
                </tr>
              ))}
          </tbody>
        </Table>
      </section>
    </div>
  );
}
