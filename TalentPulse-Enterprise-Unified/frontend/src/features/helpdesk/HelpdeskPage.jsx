import { useEffect, useRef, useState } from 'react';
import { api } from '../../api/client.js';
import { Badge, Button, Icon, PageHead } from '../../components/ui/index.js';
import { Input } from '../../components/ui/Field.jsx';
import { useToast } from '../../components/ui/Toast.jsx';

const SUGGESTIONS = [
  'How many days of casual leave do I get per year?',
  'How long is paternity leave?',
  'How many days can I work from home?',
  'What does the health insurance cover?',
  'What is the on-call allowance for night deployments?',
];
const MAX_LEN = 500;

export default function HelpdeskPage() {
  const toast = useToast();
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState('');
  const [thinking, setThinking] = useState(false);
  const [mode, setMode] = useState(null); // live | extractive, learned from the latest answer
  const bottomRef = useRef(null);

  useEffect(() => {
    const controller = new AbortController();
    api.get('/chat/history', { signal: controller.signal })
      .then((history) => {
        const items = (Array.isArray(history) ? history : []).slice().reverse(); // API returns newest first
        setMessages(items.flatMap((item, i) => [
          { sender: 'user', text: item.query, id: `u-${i}` },
          { sender: 'bot', text: item.answer, sources: item.sources ?? [], id: `b-${i}` },
        ]));
      })
      .catch(() => { /* an empty history is fine */ });
    return () => controller.abort();
  }, []);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }); }, [messages, thinking]);

  const send = async (text) => {
    const q = (text ?? query).trim();
    if (q.length < 2 || thinking) return;
    setMessages((m) => [...m, { sender: 'user', text: q, id: `u-${Date.now()}` }]);
    setQuery('');
    setThinking(true);
    try {
      const res = await api.post('/chat/ask', { query: q });
      if (res.mode) setMode(res.mode);
      setMessages((m) => [...m, { sender: 'bot', text: res.answer, sources: res.sources ?? [], id: `b-${Date.now()}` }]);
    } catch (err) {
      toast.error('Helpdesk unavailable', err.message);
      setMessages((m) => [...m, { sender: 'bot', text: 'I could not reach the helpdesk just now. Please try again, or email hr@talentpulse.local.', sources: [], id: `b-${Date.now()}` }]);
    } finally {
      setThinking(false);
    }
  };

  const uniqueSources = (sources) => [...new Map((sources ?? []).map((s) => [typeof s === 'string' ? s : s?.title, s])).keys()].filter(Boolean);

  return (
    <div className="page stack" style={{ '--gap': '20px' }}>
      <PageHead
        icon="chat" tone="blue" eyebrow="GenAI 1 · RAG" title="Policy helpdesk"
        subtitle="Ask in plain English. Answers come only from the HR policy library, with the source named."
        actions={mode ? <Badge tone={mode === 'live' ? 'ok' : 'warn'} icon={mode === 'live' ? 'sparkles' : 'info'}>{mode === 'live' ? 'Live LLM' : 'Offline excerpt mode'}</Badge> : null}
      />

      <div className="row" role="group" aria-label="Suggested questions">
        {SUGGESTIONS.map((s) => <button key={s} type="button" className="pill" disabled={thinking} onClick={() => send(s)}>{s}</button>)}
      </div>

      <section className="card" style={{ display: 'flex', flexDirection: 'column', height: 'min(640px, 70vh)' }} aria-label="Conversation">
        <div className="stack" style={{ '--gap': '18px', flex: 1, overflowY: 'auto', padding: 'var(--s-3)' }} role="log" aria-live="polite">
          {messages.length === 0 ? (
            <div className="state" style={{ margin: 'auto' }}>
              <div className="state__orb"><Icon name="chat" size={40} strokeWidth={2} /></div>
              <h2>Ask me about policy</h2>
              <p>Leave, benefits, hybrid work, overtime. If it is not in the documents, I will say so instead of guessing.</p>
            </div>
          ) : messages.map((m) => (
            <div key={m.id} className="stack" style={{ '--gap': '8px', alignItems: m.sender === 'user' ? 'flex-end' : 'flex-start' }}>
              <div className={`chat-bubble chat-bubble--${m.sender}`}><span className="prose-block">{m.text}</span></div>
              {m.sender === 'bot' && uniqueSources(m.sources).length > 0 ? (
                <div className="row">
                  <span className="eyebrow">Sources</span>
                  {uniqueSources(m.sources).map((t) => <span key={t} className="badge badge--info"><Icon name="file" size={12} />{t}</span>)}
                </div>
              ) : null}
            </div>
          ))}
          {thinking ? (
            <div className="chat-bubble chat-bubble--bot row row--nowrap" role="status">
              <Icon name="search" size={18} /><span>Finding the right passages…</span>
            </div>
          ) : null}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={(e) => { e.preventDefault(); send(); }} style={{ display: 'flex', gap: 12, padding: 'var(--s-2) var(--s-3) var(--s-3)', borderTop: 'var(--bw) solid var(--ink)' }}>
          <div style={{ flex: 1 }}>
            <Input aria-label="Your question" maxLength={MAX_LEN} placeholder="e.g. How does maternity leave work?" value={query} onChange={(e) => setQuery(e.target.value)} disabled={thinking} />
          </div>
          <Button type="submit" variant="primary" icon="send" disabled={query.trim().length < 2} loading={thinking}>Ask</Button>
        </form>
      </section>
    </div>
  );
}
