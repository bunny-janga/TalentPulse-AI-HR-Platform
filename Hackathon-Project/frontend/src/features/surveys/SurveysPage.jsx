import { useCallback, useEffect, useState } from 'react';
import { api } from '../../api/client.js';
import { useApp } from '../../app/store.jsx';
import { Badge, Button, CardHead, Icon, Meter, Modal, PageHead, Stat, TextArea, useToast } from '../../components/ui/index.js';
import { Input } from '../../components/ui/Field.jsx';
import { formatDate } from '../../utils/format.js';

const SENT_TONE = { Positive: 'ok', Neutral: 'warn', Negative: 'danger' };
const SCORE_LABEL = ['', 'Very unhappy', 'Unhappy', 'Okay', 'Happy', 'Very happy'];

export default function SurveysPage() {
  const { role } = useApp();
  const toast = useToast();
  const isHR = ['hr', 'admin', 'superadmin'].includes(role);

  const [surveys, setSurveys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [results, setResults] = useState(null);
  const [loadingResults, setLoadingResults] = useState(false);
  const [themes, setThemes] = useState(null);
  const [extracting, setExtracting] = useState(false);

  const [responding, setResponding] = useState(null);
  const [answer, setAnswer] = useState({ score: 0, comments: '' });
  const [sending, setSending] = useState(false);

  const [creating, setCreating] = useState(false);
  const [draft, setDraft] = useState({ title: '', description: '' });
  const [saving, setSaving] = useState(false);

  const loadResults = useCallback(async (survey) => {
    setSelected(survey); setThemes(null); setResults(null); setLoadingResults(true);
    try { setResults(await api.get(`/surveys/${survey.id}/results`)); } catch (e) { toast.error('Could not load results', e.message); } finally { setLoadingResults(false); }
  }, [toast]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const list = await api.get('/surveys');
      setSurveys(Array.isArray(list) ? list : []);
      return list;
    } catch (e) { toast.error('Could not load surveys', e.message); return []; } finally { setLoading(false); }
  }, [toast]);

  useEffect(() => { load().then((list) => { if (isHR && list?.length) loadResults(list[0]); }); }, [load, isHR, loadResults]);

  const sendAnswer = async () => {
    if (!answer.score) { toast.error('Pick a score', 'Choose 1 to 5 first.'); return; }
    setSending(true);
    try {
      await api.post(`/surveys/${responding.id}/respond`, { score: answer.score, comments: answer.comments.trim() || null });
      toast.success('Thanks for your feedback', 'Your answer is anonymous to HR.');
      setResponding(null); setAnswer({ score: 0, comments: '' });
      load();
    } catch (e) { toast.error('Could not submit', e.message); } finally { setSending(false); }
  };

  const createSurvey = async (e) => {
    e.preventDefault();
    if (draft.title.trim().length < 4) { toast.error('Title too short', 'Use at least 4 characters.'); return; }
    setSaving(true);
    try {
      await api.post('/surveys', { title: draft.title.trim(), description: draft.description.trim() || null, is_active: true });
      toast.success('Survey published', 'Employees can answer it now.');
      setCreating(false); setDraft({ title: '', description: '' });
      load();
    } catch (err) { toast.error('Could not create', err.message); } finally { setSaving(false); }
  };

  const toggleActive = async (s) => {
    try {
      await api.put(`/surveys/${s.id}/status`, { is_active: !s.is_active });
      toast.success(s.is_active ? 'Survey closed' : 'Survey reopened', s.title);
      const list = await load();
      if (selected?.id === s.id) loadResults(list.find((x) => x.id === s.id) ?? s);
    } catch (err) { toast.error('Could not update', err.message); }
  };

  const extractThemes = async () => {
    setExtracting(true);
    try {
      setThemes(await api.post(`/surveys/${selected.id}/ai-themes`, {}));
    } catch (e) { toast.error('Theme analysis failed', e.message); } finally { setExtracting(false); }
  };

  const total = results?.total_responses ?? 0;
  const dist = results?.score_distribution ?? {};

  return (
    <div className="page stack" style={{ '--gap': '28px' }}>
      <PageHead icon="clipboard" tone="purple" eyebrow="Workspace" title="Pulse surveys"
        subtitle={isHR ? 'Create surveys, watch sentiment, and let the AI pull out the themes.' : 'Short, anonymous check-ins. Your answers help leadership fix real problems.'}
        actions={<>
          <Button icon="refresh" onClick={() => load()} loading={loading}>Refresh</Button>
          {isHR ? <Button variant="primary" icon="plus" onClick={() => setCreating(true)}>New survey</Button> : null}
        </>} />

      <section className="stack" style={{ '--gap': '16px' }} aria-label="Surveys">
        {loading && surveys.length === 0 ? <p className="dim">Loading…</p> : surveys.length === 0 ? (
          <div className="card card--pad state"><div className="state__orb"><Icon name="clipboard" size={36} /></div><h2>No surveys yet</h2><p>{isHR ? 'Publish the first one.' : 'Nothing to answer right now.'}</p></div>
        ) : (
          <div className="grid grid--auto stagger" style={{ '--min': '300px', '--gap': '20px' }}>
            {surveys.map((s) => (
              <article key={s.id} className={`card card--pad stack ${selected?.id === s.id ? 'tone-yellow' : ''}`} style={{ '--gap': '12px' }}>
                <div className="row spread"><Badge tone={s.is_active ? 'ok' : 'neutral'} dot>{s.is_active ? 'Open' : 'Closed'}</Badge><span className="cell-sub">{formatDate(s.created_at)}</span></div>
                <h3>{s.title}</h3>
                <p className="muted" style={{ fontSize: 'var(--fs-sm)' }}>{s.description || 'Company-wide pulse check.'}</p>
                <p className="cell-sub">{s.response_count} responses</p>
                <div className="row" style={{ marginTop: 'auto' }}>
                  {s.has_responded ? <Badge tone="ok" icon="check">You answered</Badge>
                    : s.is_active ? <Button size="sm" variant="primary" onClick={() => { setResponding(s); setAnswer({ score: 0, comments: '' }); }}>Answer</Button> : null}
                  {isHR ? <>
                    <Button size="sm" onClick={() => loadResults(s)}>Results</Button>
                    <Button size="sm" variant="ghost" onClick={() => toggleActive(s)}>{s.is_active ? 'Close' : 'Reopen'}</Button>
                  </> : null}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      {isHR && selected ? (
        <section className="stack" style={{ '--gap': '20px' }} aria-label="Survey results">
          <h2>Results: {selected.title}</h2>
          {loadingResults ? <p className="dim">Loading analysis…</p> : total === 0 ? (
            <div className="callout callout--info"><Icon name="info" size={20} /><span>No responses yet. Results appear as soon as the first person answers.</span></div>
          ) : (
            <>
              <div className="grid grid--3">
                <Stat tone="green" label="Average score" value={`${results.average_score} / 5`} sub={`${total} responses`} />
                <Stat label="Sentiment of comments" value={<span style={{ fontSize: '1.4rem' }}>{['Positive', 'Neutral', 'Negative'].map((k) => `${results.sentiment_distribution?.[k] ?? 0} ${k.slice(0, 3).toLowerCase()}`).join(' · ')}</span>} sub="Lexicon-based, comments only" />
                <Stat tone="pink" label="Anonymity" value="On" sub="HR never sees who answered" icon="lock" />
              </div>
              <div className="split" style={{ '--l': '1fr', '--r': '1.2fr' }}>
                <div className="card card--pad stack" style={{ '--gap': '14px' }}>
                  <CardHead title="Score distribution" />
                  {[5, 4, 3, 2, 1].map((n) => (
                    <div className="bar-row" key={n}><span className="cell-name">{n} · {SCORE_LABEL[n]}</span><Meter value={dist[n] ?? 0} max={Math.max(total, 1)} tone={n >= 4 ? 'green' : n === 3 ? 'yellow' : 'red'} label={`${n} star answers`} /><span className="num">{dist[n] ?? 0}</span></div>
                  ))}
                </div>
                <div className="card card--pad stack" style={{ '--gap': '14px' }}>
                  <CardHead icon="sparkles" title="GenAI theme analysis" subtitle="Groups the written comments into themes and suggests actions."
                    actions={<Button size="sm" variant="primary" icon="sparkles" loading={extracting} onClick={extractThemes}>Analyse comments</Button>} />
                  {themes ? (
                    <div className="box box--accent stack" style={{ '--gap': '8px' }}>
                      <div className="row"><Badge tone={themes.mode === 'live' ? 'ok' : 'warn'}>{themes.mode === 'live' ? 'Live LLM' : 'Offline summary'}</Badge><span className="cell-sub">{themes.total_analyzed} comments</span></div>
                      <p className="prose-block">{themes.themes_summary}</p>
                    </div>
                  ) : <p className="dim">Press the button to generate themes.</p>}
                </div>
              </div>
              <div className="card card--pad stack" style={{ '--gap': '12px' }}>
                <CardHead icon="chat" title="Written feedback" subtitle="Anonymous. Latest 15." />
                {results.feedback_samples?.length ? results.feedback_samples.map((fb) => (
                  <div key={fb.id} className="list-row" style={{ alignItems: 'flex-start' }}>
                    <Badge tone={SENT_TONE[fb.sentiment_label] ?? 'neutral'}>{fb.sentiment_label} · {fb.score}/5</Badge>
                    <p style={{ flex: 1 }}>“{fb.comments}”</p>
                  </div>
                )) : <p className="dim">Nobody left a written comment.</p>}
              </div>
            </>
          )}
        </section>
      ) : null}

      <Modal open={Boolean(responding)} onClose={() => !sending && setResponding(null)} title={responding?.title ?? ''} description="How are you feeling about work right now?"
        footer={<><Button onClick={() => setResponding(null)} disabled={sending}>Cancel</Button><Button variant="primary" loading={sending} onClick={sendAnswer}>Submit anonymously</Button></>}>
        <div className="stack" style={{ '--gap': '16px' }}>
          <div role="radiogroup" aria-label="Score" className="pill-row">
            {[1, 2, 3, 4, 5].map((n) => (
              <button key={n} type="button" role="radio" aria-checked={answer.score === n} className={`pill ${answer.score === n ? 'is-active' : ''}`} style={{ flexDirection: 'column', minHeight: 64, minWidth: 74 }} onClick={() => setAnswer({ ...answer, score: n })}>
                <span style={{ fontSize: '1.3rem', fontWeight: 900 }}>{n}</span><span style={{ fontSize: 11 }}>{SCORE_LABEL[n]}</span>
              </button>
            ))}
          </div>
          <TextArea label="Anything to add? (optional)" rows={4} maxLength={1000} value={answer.comments} onChange={(e) => setAnswer({ ...answer, comments: e.target.value })} placeholder="What is working, and what is not?" />
        </div>
      </Modal>

      <Modal open={creating} onClose={() => !saving && setCreating(false)} title="New pulse survey" description="It opens immediately for every employee."
        footer={<><Button onClick={() => setCreating(false)} disabled={saving}>Cancel</Button><Button variant="primary" loading={saving} onClick={createSurvey}>Publish</Button></>}>
        <form onSubmit={createSurvey} className="stack" style={{ '--gap': '16px' }}>
          <Input label="Title" value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} placeholder="Q4 2026 Pulse Check" maxLength={255} />
          <TextArea label="Description" rows={3} value={draft.description} onChange={(e) => setDraft({ ...draft, description: e.target.value })} placeholder="What do you want to learn?" />
        </form>
      </Modal>
    </div>
  );
}
