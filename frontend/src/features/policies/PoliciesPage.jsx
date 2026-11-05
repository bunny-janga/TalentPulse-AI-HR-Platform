import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '../../api/client.js';
import { useApp } from '../../app/store.jsx';
import { Badge, Button, CardHead, Chip, Icon, Modal, PageHead, Tabs, TextArea, useToast } from '../../components/ui/index.js';
import { Input, Select } from '../../components/ui/Field.jsx';
import { formatDate } from '../../utils/format.js';

const CATEGORIES = ['Leave', 'Benefits', 'Operations', 'HR Policy', 'Information Security', 'Code of Conduct'].map((c) => ({ value: c, label: c }));
const TONES = ['yellow', 'pink', 'blue', 'green', 'orange', 'purple'];
const MAX_MB = 8;

export default function PoliciesPage() {
  const { role } = useApp();
  const toast = useToast();
  const canManage = ['hr', 'admin', 'superadmin'].includes(role);

  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cat, setCat] = useState('All');
  const [reading, setReading] = useState(null); // detail object
  const [readingId, setReadingId] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const [mode, setMode] = useState('text');
  const [form, setForm] = useState({ title: '', category: 'HR Policy', raw_text: '' });
  const [file, setFile] = useState(null);
  const [errors, setErrors] = useState({});
  const [uploading, setUploading] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    api.get('/policies').then((d) => setPolicies(d ?? [])).catch((e) => toast.error('Could not load policies', e.message)).finally(() => setLoading(false));
  }, [toast]);
  useEffect(() => { load(); }, [load]);

  const categories = useMemo(() => ['All', ...new Set(policies.map((p) => p.category).filter(Boolean))], [policies]);
  const shown = cat === 'All' ? policies : policies.filter((p) => p.category === cat);

  const open = async (p) => {
    setReadingId(p.id);
    try { setReading(await api.get(`/policies/${p.id}`)); } catch (e) { toast.error('Could not open', e.message); } finally { setReadingId(null); }
  };

  const submit = async (e) => {
    e.preventDefault();
    const er = {};
    if (form.title.trim().length < 3) er.title = 'Give the policy a title.';
    if (mode === 'text' && form.raw_text.trim().length < 30) er.raw_text = 'Paste at least a few sentences.';
    if (mode === 'file') {
      if (!file) er.file = 'Choose a PDF or text file.';
      else if (file.size > MAX_MB * 1024 * 1024) er.file = `File is over ${MAX_MB} MB.`;
    }
    setErrors(er);
    if (Object.keys(er).length) return;
    const fd = new FormData();
    fd.append('title', form.title.trim());
    fd.append('category', form.category);
    if (mode === 'file') fd.append('file', file); else fd.append('raw_text', form.raw_text.trim());
    setUploading(true);
    try {
      const res = await api.upload('/policies/upload', fd);
      toast.success('Policy indexed', `${res.chunk_count} passage(s) are now searchable by the helpdesk.`);
      setForm({ title: '', category: form.category, raw_text: '' });
      setFile(null);
      load();
    } catch (err) { toast.error('Upload failed', err.message); } finally { setUploading(false); }
  };

  const remove = async () => {
    setDeleting(true);
    try {
      await api.del(`/policies/${confirmDelete.id}`);
      toast.success('Policy removed', confirmDelete.title);
      setConfirmDelete(null);
      load();
    } catch (err) { toast.error('Could not delete', err.message); } finally { setDeleting(false); }
  };

  return (
    <div className="page stack" style={{ '--gap': '28px' }}>
      <PageHead icon="file" tone="orange" eyebrow="Workspace" title="Policy library"
        subtitle="Every document here is what the helpdesk answers from."
        actions={<Button icon="refresh" onClick={load} loading={loading}>Refresh</Button>} />

      <div className="split" style={{ '--l': canManage ? '1.7fr' : '1fr', '--r': '1fr' }}>
        <section className="stack" style={{ '--gap': '16px' }}>
          <div className="row" role="group" aria-label="Filter by category">
            {categories.map((c) => <Chip key={c} selected={cat === c} onClick={() => setCat(c)}>{c}</Chip>)}
          </div>
          {loading ? <p className="dim">Loading…</p> : shown.length === 0 ? (
            <div className="card card--pad state"><div className="state__orb"><Icon name="file" size={36} /></div><h2>No documents yet</h2><p>{canManage ? 'Add the first policy using the form.' : 'HR has not published any policies.'}</p></div>
          ) : (
            <div className="grid grid--auto stagger" style={{ '--min': '280px', '--gap': '20px' }}>
              {shown.map((p, i) => (
                <article key={p.id} className="card card--pad stack" style={{ '--gap': '12px' }}>
                  <div className="row spread row--nowrap">
                    <span className={`icon-tile tone-${TONES[i % TONES.length]}`}><Icon name="file" size={22} strokeWidth={2.4} /></span>
                    <Badge>{p.category || 'General'}</Badge>
                  </div>
                  <h3>{p.title}</h3>
                  <p className="cell-sub">{p.chunk_count} passages · added {formatDate(p.created_at)}</p>
                  <div className="row" style={{ marginTop: 'auto' }}>
                    <Button size="sm" variant="primary" icon="eye" loading={readingId === p.id} onClick={() => open(p)}>Read</Button>
                    {canManage ? <Button size="sm" variant="danger" icon="trash" onClick={() => setConfirmDelete(p)} aria-label={`Delete ${p.title}`}>Delete</Button> : null}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        {canManage ? (
          <section className="card card--pad">
            <CardHead icon="upload" title="Add a policy" subtitle="It is chunked and indexed for the helpdesk instantly." />
            <form onSubmit={submit} className="stack" style={{ '--gap': '16px' }} noValidate>
              <Input label="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} error={errors.title} placeholder="Work From Home Policy 2026" />
              <Select label="Category" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} options={CATEGORIES} />
              <Tabs idBase="pol" label="Source" value={mode} onChange={setMode} tabs={[{ id: 'text', label: 'Paste text', icon: 'edit' }, { id: 'file', label: 'Upload file', icon: 'upload' }]} />
              {mode === 'text'
                ? <TextArea label="Policy text" rows={7} value={form.raw_text} onChange={(e) => setForm({ ...form, raw_text: e.target.value })} error={errors.raw_text} placeholder="1. Hybrid schedule: …" />
                : <Input label="PDF or .txt file" type="file" accept=".pdf,.txt,.md,application/pdf,text/plain" onChange={(e) => setFile(e.target.files?.[0] ?? null)} error={errors.file} hint={`Up to ${MAX_MB} MB. Scanned PDFs without a text layer cannot be read.`} />}
              <Button type="submit" variant="primary" icon="plus" loading={uploading}>Index for the helpdesk</Button>
            </form>
          </section>
        ) : null}
      </div>

      <Modal open={Boolean(reading)} onClose={() => setReading(null)} size="lg" title={reading?.title ?? ''} description={reading ? `${reading.category} · ${reading.chunk_count} passages` : ''}>
        <div className="box scroll-y"><p className="prose-block">{reading?.extracted_text}</p></div>
      </Modal>

      <Modal open={Boolean(confirmDelete)} onClose={() => !deleting && setConfirmDelete(null)} title="Delete this policy?"
        description="The helpdesk will stop answering from it immediately. This cannot be undone."
        footer={<><Button onClick={() => setConfirmDelete(null)} disabled={deleting}>Keep it</Button><Button variant="danger" loading={deleting} onClick={remove}>Delete</Button></>}>
        <p className="cell-name">{confirmDelete?.title}</p>
      </Modal>
    </div>
  );
}
