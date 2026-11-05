import { Button, IconButton } from '../../components/ui/Button.jsx';
import { Icon, Logo } from '../../components/ui/Icon.jsx';
import { useApp } from '../../app/store.jsx';
import './landing.css';

const MARQUEE = ['Attrition risk', 'Policy RAG helpdesk', 'AI review drafts', 'Leave workflow', 'Pulse surveys', 'Role-based access', 'Org hierarchy', 'Onboarding'];

const FEATURES = [
  { tone: 'pink', icon: 'shield', tag: 'AI 1', title: 'Attrition risk prediction', body: 'A Random Forest scores every employee LOW, MEDIUM or HIGH and names the top 3 drivers behind that person’s score. Only HR and the direct manager can see it.', chips: ['scikit-learn', 'Per-person drivers', 'Server-enforced access'] },
  { tone: 'yellow', icon: 'trendDown', tag: 'AI 2', title: 'Performance trend flags', body: 'Two or more declining review ratings in a row raises a WARNING or CRITICAL flag with a suggested manager action, and feeds the attrition model.', chips: ['Early warning', 'Manager scoped', 'Feeds AI 1'] },
  { tone: 'blue', icon: 'chat', tag: 'GenAI 1', title: 'Policy helpdesk (RAG)', body: 'TF-IDF finds the right passages in the HR policy library, an LLM answers only from them, and every answer lists its sources. No match means it says so.', chips: ['TF-IDF retrieval', 'Cited sources', 'Offline fallback'] },
  { tone: 'green', icon: 'sparkles', tag: 'GenAI 2', title: 'Review drafter', body: 'Managers jot rough bullets, the model returns a 4-part draft (summary, strengths, growth areas, goals). A human edits and saves. It never auto-submits.', chips: ['Human in the loop', '4-part structure', 'Editable'] },
];

const ROLES = [
  { tone: 'purple', name: 'Employee', body: 'Apply for leave, see own reviews, ask the helpdesk, answer pulse surveys, tick off the onboarding checklist.' },
  { tone: 'blue', name: 'Manager', body: 'Approve leave and write reviews for direct reports. Sees attrition risk for that team only.' },
  { tone: 'yellow', name: 'HR Executive', body: 'Manages people records, policies, surveys and the company-wide attrition dashboard.' },
  { tone: 'pink', name: 'Admin', body: 'Departments, roles, onboarding new hires, workforce metrics. Super Admin alone can grant Admin.' },
];

const LAYERS = [
  { icon: 'home', title: 'React + Vite', items: ['Hash-routed SPA', 'Role-aware navigation', 'No runtime CDN'] },
  { icon: 'shield', title: 'FastAPI', items: ['JWT + RoleChecker', 'Pydantic v2 validation', 'Swagger at /docs'] },
  { icon: 'sparkles', title: 'AI + GenAI', items: ['RandomForest + drivers', 'TF-IDF retrieval', 'Gemini with fallback'] },
  { icon: 'file', title: 'SQL database', items: ['SQLite (Postgres-ready)', '12 relational tables', 'Synthetic data only'] },
];

export default function LandingPage({ onSignIn }) {
  const { theme, toggleTheme } = useApp();
  const go = (id) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });

  return (
    <div className="landing">
      <header className="landing__nav">
        <a href="#overview" className="landing__brand">
          <Logo size={38} />
          <span>TalentPulse<span className="grad-text">AI</span></span>
        </a>
        <nav aria-label="Project sections">
          <ul className="landing__menu">
            <li><a href="#features" className="landing__menu-link">Features</a></li>
            <li><a href="#roles" className="landing__menu-link">Roles</a></li>
            <li><a href="#architecture" className="landing__menu-link">Architecture</a></li>
          </ul>
        </nav>
        <div className="landing__nav-actions">
          <IconButton variant="secondary" icon={theme === 'dark' ? 'sun' : 'moon'} label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'} onClick={toggleTheme} />
          <Button variant="primary" iconRight="arrowRight" onClick={onSignIn}>Sign in</Button>
        </div>
      </header>

      <main>
        <section id="overview" className="landing__hero">
          <div className="landing__hero-copy">
            <span className="sticker">Codegnan hackathon · Team 13 · GenAI Guardians</span>
            <h1 className="landing__headline">
              Know who’s about to <span className="hl hl--pink">quit.</span> Answer HR <span className="hl">instantly.</span>
            </h1>
            <p className="landing__subhead">
              A 1,200-person IT company in Visakhapatnam loses <strong>22% of its staff every year</strong> and finds out when the resignation lands. TalentPulse AI spots the risk early, tells managers what to do, and answers policy questions from the documents themselves.
            </p>
            <div className="landing__cta-row">
              <Button size="lg" variant="primary" iconRight="arrowRight" onClick={onSignIn}>Launch the portal</Button>
              <Button size="lg" variant="secondary" icon="chart" onClick={() => go('architecture')}>See the architecture</Button>
            </div>
          </div>
          <div className="landing__hero-art" aria-hidden="true">
            <div className="art-card art-card--a tone-pink"><span className="eyebrow">Attrition risk</span><strong className="art-num">HIGH</strong><span>Overtime · 3.4 yrs since promotion</span></div>
            <div className="art-card art-card--b tone-yellow"><span className="eyebrow">Helpdesk</span><strong>“How many sick days do I get?”</strong><span>→ Leave Policy, section 2</span></div>
            <div className="art-card art-card--c tone-green"><span className="eyebrow">Review draft</span><strong>4 sections, 1 click</strong></div>
          </div>
        </section>

        <div className="marquee" aria-hidden="true">
          <div className="marquee__track">
            {[...MARQUEE, ...MARQUEE].map((m, i) => <span className="marquee__item" key={i}>{m}</span>)}
          </div>
        </div>

        <section className="landing__section landing__stats-row">
          <div className="stat tone-yellow"><span className="stat__label">Staff in the brief</span><span className="stat__value">1,200</span></div>
          <div className="stat tone-red"><span className="stat__label">Yearly attrition</span><span className="stat__value">22%</span></div>
          <div className="stat tone-blue"><span className="stat__label">AI + GenAI features</span><span className="stat__value">2 + 2</span></div>
          <div className="stat tone-green"><span className="stat__label">User roles</span><span className="stat__value">4</span></div>
        </section>

        <section id="features" className="landing__section">
          <h2 className="landing__sec-title">The four AI features, built into the workflow</h2>
          <div className="landing__grid">
            {FEATURES.map((f) => (
              <article key={f.title} className="card landing__feature">
                <div className="row spread">
                  <span className={`icon-tile tone-${f.tone}`}><Icon name={f.icon} size={24} strokeWidth={2.4} /></span>
                  <span className="badge">{f.tag}</span>
                </div>
                <h3>{f.title}</h3>
                <p className="muted">{f.body}</p>
                <div className="row">{f.chips.map((c) => <span className="badge" key={c}>{c}</span>)}</div>
              </article>
            ))}
          </div>
          <p className="callout callout--info landing__note"><Icon name="info" size={20} /><span><strong>Honest about the data.</strong> All employee data is synthetic, and the attrition model is trained on a synthetic 1,470-row set shaped like the public IBM HR benchmark. Its score demonstrates the pipeline, not real-world accuracy.</span></p>
        </section>

        <section id="roles" className="landing__section">
          <h2 className="landing__sec-title">Four roles, enforced on the server</h2>
          <div className="landing__grid landing__grid--4">
            {ROLES.map((r) => (
              <article key={r.name} className={`card card--pad landing__role tone-${r.tone}`}>
                <h3>{r.name}</h3>
                <p>{r.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="architecture" className="landing__section">
          <h2 className="landing__sec-title">Four layers, one repo</h2>
          <div className="landing__arch">
            {LAYERS.map((l, i) => (
              <div className="landing__arch-layer card" key={l.title}>
                <span className="landing__arch-n">{i + 1}</span>
                <div className="row"><Icon name={l.icon} size={20} strokeWidth={2.4} /><h3>{l.title}</h3></div>
                <ul>{l.items.map((it) => <li key={it}>{it}</li>)}</ul>
              </div>
            ))}
          </div>
        </section>

        <section className="landing__cta card tone-yellow">
          <h2>Try every role in about a minute.</h2>
          <p>The sign-in screen has one-click demo accounts for all four roles plus Super Admin.</p>
          <Button size="lg" variant="secondary" iconRight="arrowRight" onClick={onSignIn}>Open sign in</Button>
        </section>
      </main>

      <footer className="landing__footer">
        <strong>TalentPulse AI</strong> · Employee attrition prediction and GenAI HR helpdesk · Problem GG-13, Human Resources
      </footer>
    </div>
  );
}
