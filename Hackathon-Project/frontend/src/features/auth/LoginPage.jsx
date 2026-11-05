import { useEffect, useRef, useState } from 'react';
import { ApiError, api } from '../../api/client.js';
import { useApp } from '../../app/store.jsx';
import { Button, IconButton } from '../../components/ui/Button.jsx';
import { Input } from '../../components/ui/Field.jsx';
import { Icon, Logo } from '../../components/ui/Icon.jsx';
import { SuccessCheck } from '../../components/ui/SuccessCheck.jsx';
import { useShake } from '../../hooks/useShake.js';
import { cx } from '../../utils/cx.js';

/** One-click demo roles. Set VITE_SHOW_DEMO_ACCOUNTS=false at build time to hide them for a real deployment. */
const SHOW_DEMO = import.meta.env?.VITE_SHOW_DEMO_ACCOUNTS !== 'false';
const DEMO_ACCOUNTS = [
  { id: 'superadmin', label: 'Super Admin', email: 'superadmin@talentpulse.local', password: 'super123!' },
  { id: 'admin', label: 'Admin', email: 'admin@talentpulse.local', password: 'Admin123!' },
  { id: 'hr', label: 'HR Executive', email: 'hr@talentpulse.local', password: 'Hr123!' },
  { id: 'manager', label: 'Manager', email: 'manager@talentpulse.local', password: 'Manager123!' },
  { id: 'employee', label: 'Employee', email: 'employee@talentpulse.local', password: 'Employee123!' },
];
const HIGHLIGHTS = [
  { icon: 'shield', text: 'Attrition risk with the top 3 reasons, per person' },
  { icon: 'chat', text: 'Policy answers that cite the document they came from' },
  { icon: 'sparkles', text: 'Rough manager notes turned into a full review draft' },
];
const EMAIL_RE = /^[^\s@]+@[^\s@]+$/;

export default function LoginPage({ onBack }) {
  const { login, theme, toggleTheme } = useApp();
  const [form, setForm] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [pill, setPill] = useState(null);
  const [pillError, setPillError] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [phase, setPhase] = useState('idle'); // idle | loading | success
  const shakeRef = useRef(null);
  const timers = useRef([]);
  const [shakeTick, setShakeTick] = useState(0);
  useShake(shakeRef, shakeTick);

  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  const fail = (message) => {
    setFormError(message);
    setPillError(true);
    setShakeTick((t) => t + 1);
    setPhase('idle');
    timers.current.push(setTimeout(() => setPillError(false), 900));
  };

  const signIn = async (email, password, onBadCredentials) => {
    setPhase('loading');
    try {
      const session = await api.post('/auth/login', { email, password }, { auth: false });
      setPhase('success');
      login(session);
    } catch (err) {
      if (err instanceof ApiError && err.kind === 'network') fail(err.message);
      else if (err instanceof ApiError && (err.kind === 'unauthorized' || err.kind === 'validation' || err.status === 400)) fail(onBadCredentials);
      else fail(err.message || 'Sign-in failed. Please try again.');
    }
  };

  const pick = (account) => {
    if (phase !== 'idle') return;
    setPill(account.id);
    setForm({ email: account.email, password: account.password });
    setErrors({});
    setFormError('');
    signIn(account.email, account.password, `The demo password for ${account.label} was rejected. Re-seed the database or sign in manually.`);
  };

  const submit = (e) => {
    e.preventDefault();
    if (phase !== 'idle') return; // double-submit guard
    const next = {};
    if (!EMAIL_RE.test(form.email.trim())) next.email = 'Enter a valid email address.';
    if (!form.password) next.password = 'Enter your password.';
    setErrors(next);
    setFormError('');
    if (Object.keys(next).length) { setShakeTick((t) => t + 1); return; }
    signIn(form.email.trim(), form.password, 'That email and password do not match.');
  };

  const update = (field) => (e) => {
    setForm((f) => ({ ...f, [field]: e.target.value }));
    setPill(null);
    setErrors((er) => ({ ...er, [field]: undefined }));
  };

  return (
    <div className="login">
      <div className="login__deco" aria-hidden="true">
        <span className="deco deco--a" /><span className="deco deco--b" /><span className="deco deco--c" /><span className="deco deco--d" />
      </div>
      <header className="login__top">
        <div className="row row--nowrap" style={{ gap: 12 }}>
          <Logo size={40} />
          <span className="login__brand">TalentPulse <span className="grad-text">AI</span></span>
        </div>
        <div className="row row--nowrap" style={{ gap: 10 }}>
          {onBack ? <Button variant="secondary" size="sm" icon="arrowLeft" onClick={onBack}>Project overview</Button> : null}
          <IconButton variant="secondary" icon={theme === 'dark' ? 'sun' : 'moon'} label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'} onClick={toggleTheme} />
        </div>
      </header>

      <main className="login__grid">
        <section className="login__hero stagger" aria-label="About TalentPulse AI">
          <span className="sticker">Workforce intelligence</span>
          <h1 className="login__headline">Spot who is <span className="hl">leaving</span> before they <span className="hl hl--pink">leave.</span></h1>
          <p className="login__sub">One loud, clear workspace for leave, reviews, policy answers and early attrition signals.</p>
          <ul className="login__points">
            {HIGHLIGHTS.map((h) => (
              <li key={h.text}><span className="login__point-icon"><Icon name={h.icon} size={20} strokeWidth={2.4} /></span>{h.text}</li>
            ))}
          </ul>
        </section>

        <div ref={shakeRef} className="login__cardwrap">
          <section className="card login-card">
            <div className={cx('login-card__success', phase === 'success' && 'is-on')} aria-hidden={phase !== 'success'}>
              {phase === 'success' ? <SuccessCheck size={72} /> : null}
              <p className="login-card__welcome">Welcome back</p>
            </div>
            <form onSubmit={submit} noValidate className={cx('stack', phase === 'success' && 'is-hidden')} style={{ '--gap': '20px' }} aria-label="Sign in">
              <div>
                <h2>Sign in</h2>
                <p className="muted">Use your work account{SHOW_DEMO ? ' or pick a demo role' : ''}.</p>
              </div>

              {SHOW_DEMO ? (
                <div role="group" aria-label="Demo accounts">
                  <p className="eyebrow" style={{ marginBottom: 8 }}>Demo accounts, one click</p>
                  <div className="pills">
                    {DEMO_ACCOUNTS.map((a) => (
                      <button
                        key={a.id}
                        type="button"
                        className={cx('pill', pill === a.id && 'is-active', pill === a.id && pillError && 'is-error')}
                        aria-pressed={pill === a.id}
                        disabled={phase !== 'idle'}
                        onClick={() => pick(a)}
                      >
                        {a.label}
                      </button>
                    ))}
                  </div>
                </div>
              ) : null}

              <Input label="Email" type="email" autoComplete="username" inputMode="email" value={form.email} onChange={update('email')} error={errors.email} placeholder="you@company.com" />
              <div className="password">
                <Input label="Password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" value={form.password} onChange={update('password')} error={errors.password} />
                <button type="button" className="password__toggle" aria-pressed={showPassword} onClick={() => setShowPassword((v) => !v)}>
                  <Icon name="eye" size={16} /> {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>

              {formError ? <p className="login__error" role="alert" key={shakeTick}><Icon name="alert" size={16} />{formError}</p> : null}

              <Button type="submit" variant="primary" size="lg" loading={phase === 'loading'} disabled={phase === 'success'} iconRight="arrowRight">Sign in</Button>
            </form>
          </section>
        </div>
      </main>
    </div>
  );
}
