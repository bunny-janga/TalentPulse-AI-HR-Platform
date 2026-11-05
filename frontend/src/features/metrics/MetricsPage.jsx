import { useCallback, useEffect, useState } from 'react';
import { api } from '../../api/client.js';
import { Badge, Button, CardHead, Meter, PageHead, Stat, useToast } from '../../components/ui/index.js';

const DEPT_TONES = ['pink', 'blue', 'yellow', 'green', 'purple', 'orange'];

export default function MetricsPage() {
  const toast = useToast();
  const [m, setM] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    api.get('/admin/metrics').then(setM).catch((e) => toast.error('Could not load metrics', e.message)).finally(() => setLoading(false));
  }, [toast]);
  useEffect(() => { load(); }, [load]);

  const depts = m?.department_headcounts ?? [];
  const attr = m?.attrition_summary;
  const leave = m?.leave_trends;
  const rev = m?.review_metrics;
  const maxDept = Math.max(1, ...depts.map((d) => d.headcount));
  const rating = rev?.rating_distribution ?? {};
  const maxRating = Math.max(1, ...Object.values(rating));
  const leaveTypes = Object.entries(leave?.breakdown_by_type ?? {}).sort((a, b) => b[1] - a[1]);
  const maxLeave = Math.max(1, ...leaveTypes.map(([, v]) => v));
  const expected = attr?.projected_attrition_rate_percent;
  const bench = attr?.industry_benchmark_attrition_percent ?? 22;

  return (
    <div className="page stack" style={{ '--gap': '28px' }}>
      <PageHead icon="chart" tone="green" eyebrow="Intelligence" title="Org metrics"
        subtitle="Headcount, expected attrition, leave and review health in one place."
        actions={<Button icon="refresh" onClick={load} loading={loading}>Refresh</Button>} />

      <div className="grid grid--4">
        <Stat tone="yellow" label="Headcount" value={m ? m.total_headcount : '…'} sub={m ? `${m.total_managers} managers` : ''} icon="users" />
        <Stat tone={expected > bench ? 'red' : 'green'} label="Expected attrition" value={m ? `${expected}%` : '…'} sub={`Model average vs ${bench}% benchmark`} icon="shield" />
        <Stat tone="blue" label="Leave approval" value={m ? `${leave?.approval_rate_percent ?? 0}%` : '…'} sub={m ? `${leave?.approved_count} approved · ${leave?.pending_count} pending` : ''} icon="calendar" />
        <Stat tone="pink" label="Average rating" value={m ? `${rev?.average_rating ?? 0}★` : '…'} sub={m ? `${rev?.flagged_declining_count} declining flags` : ''} icon="star" />
      </div>

      <div className="split" style={{ '--l': '1fr', '--r': '1fr' }}>
        <section className="card card--pad stack" style={{ '--gap': '14px' }}>
          <CardHead icon="building" title="Headcount by department" />
          {depts.length === 0 ? <p className="dim">{loading ? 'Loading…' : 'No department data.'}</p> : depts.map((d, i) => (
            <div key={d.department_id} className="bar-row">
              <span className="cell-name truncate" title={d.department_name}>{d.department_name}</span>
              <Meter value={d.headcount} max={maxDept} tone={DEPT_TONES[i % DEPT_TONES.length]} label={`${d.department_name} headcount`} />
              <span className="num">{d.headcount} · {d.percentage}%</span>
            </div>
          ))}
        </section>

        <section className="card card--pad stack" style={{ '--gap': '14px' }}>
          <CardHead icon="shield" title="Attrition risk bands" subtitle="From the latest model run" />
          {attr ? (
            <>
              {['HIGH', 'MEDIUM', 'LOW'].map((b) => (
                <div key={b} className="bar-row">
                  <span className="cell-name">{b}</span>
                  <Meter value={attr.risk_distribution?.[b] ?? 0} max={Math.max(1, m.total_headcount)} tone={b === 'HIGH' ? 'red' : b === 'MEDIUM' ? 'yellow' : 'green'} label={`${b} risk share`} />
                  <span className="num">{attr.risk_distribution?.[b] ?? 0}</span>
                </div>
              ))}
              <div className="box"><span className="eyebrow">Hot departments</span><div className="row" style={{ marginTop: 8 }}>{attr.critical_departments?.length ? attr.critical_departments.map((d) => <Badge key={d} tone="danger">{d}</Badge>) : <span className="dim">Balanced across units</span>}</div></div>
            </>
          ) : <p className="dim">{loading ? 'Loading…' : 'No data.'}</p>}
        </section>
      </div>

      <div className="split" style={{ '--l': '1fr', '--r': '1fr' }}>
        <section className="card card--pad stack" style={{ '--gap': '14px' }}>
          <CardHead icon="star" title="Rating distribution" subtitle={rev ? `${rev.total_reviews_conducted} reviews` : ''} />
          {[5, 4, 3, 2, 1].map((n) => (
            <div key={n} className="bar-row"><span className="cell-name">{n} ★</span><Meter value={rating[n] ?? 0} max={maxRating} tone={n >= 4 ? 'green' : n === 3 ? 'yellow' : 'red'} label={`${n} star reviews`} /><span className="num">{rating[n] ?? 0}</span></div>
          ))}
        </section>
        <section className="card card--pad stack" style={{ '--gap': '14px' }}>
          <CardHead icon="calendar" title="Leave by type" subtitle={leave ? `${leave.total_requests} requests · ${leave.rejected_count} rejected` : ''} />
          {leaveTypes.length === 0 ? <p className="dim">No leave data.</p> : leaveTypes.map(([k, v], i) => (
            <div key={k} className="bar-row"><span className="cell-name truncate" title={k}>{k}</span><Meter value={v} max={maxLeave} tone={DEPT_TONES[(i + 2) % DEPT_TONES.length]} label={`${k} requests`} /><span className="num">{v}</span></div>
          ))}
        </section>
      </div>
    </div>
  );
}
