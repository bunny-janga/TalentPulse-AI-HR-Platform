import { Button } from '../components/ui/Button.jsx';
import { navigate } from '../hooks/useRoute.js';

/** Animated "Restricted by policy" screen shown on a direct visit to a route the role cannot use. */
export function RestrictedByPolicy({ area }) {
  return (
    <div className="restricted page-enter" role="status">
      <div className="restricted__lock" aria-hidden="true">
        <span className="restricted__ring" />
        <span className="restricted__ring restricted__ring--b" />
        <svg width="76" height="76" viewBox="0 0 48 48" fill="none">
          <g className="restricted__shackle">
            <path d="M15 21v-6a9 9 0 0118 0v6" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
          </g>
          <rect x="9" y="21" width="30" height="21" rx="6" fill="currentColor" opacity=".16" stroke="currentColor" strokeWidth="2.5" />
          <circle cx="24" cy="31" r="3" fill="currentColor" />
          <path d="M24 33v4" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
        </svg>
      </div>
      <p className="eyebrow">Access control</p>
      <h1>Restricted by policy</h1>
      <p className="muted">
        {area ? `${area} is not part of your role's workspace.` : 'This area is not part of your role\'s workspace.'}{' '}
        If you believe this is a mistake, please contact HR.
      </p>
      <Button variant="secondary" icon="home" onClick={() => navigate('/')}>Back to Home</Button>
    </div>
  );
}
