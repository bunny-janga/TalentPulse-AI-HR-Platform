import { Suspense, lazy, useEffect, useMemo, useRef, useState } from 'react';
import { EmptyState } from '../components/ui/EmptyState.jsx';
import { ErrorBoundary } from '../components/ui/ErrorBoundary.jsx';
import { Skeleton, SkeletonCards } from '../components/ui/Skeleton.jsx';
import { Button } from '../components/ui/Button.jsx';
import { useReducedMotion } from '../hooks/useReducedMotion.js';
import { navigate, useRoute } from '../hooks/useRoute.js';
import { RestrictedByPolicy } from './RestrictedByPolicy.jsx';
import { Sidebar } from './Sidebar.jsx';
import { TopBar } from './TopBar.jsx';
import { canAccess, findRoute, routesFor } from './routes.js';
import { useApp } from './store.jsx';

import HomePage from '../features/home/HomePage.jsx';
import LeavePage from '../features/leave/LeavePage.jsx';
import ReviewsPage from '../features/reviews/ReviewsPage.jsx';
import HelpdeskPage from '../features/helpdesk/HelpdeskPage.jsx';
import SurveysPage from '../features/surveys/SurveysPage.jsx';
import PoliciesPage from '../features/policies/PoliciesPage.jsx';
import AttritionPage from '../features/attrition/AttritionPage.jsx';
import FlagsPage from '../features/flags/FlagsPage.jsx';
import MetricsPage from '../features/metrics/MetricsPage.jsx';
import DirectoryPage from '../features/directory/DirectoryPage.jsx';

const PAGES = {
  'home/HomePage': HomePage,
  'leave/LeavePage': LeavePage,
  'reviews/ReviewsPage': ReviewsPage,
  'helpdesk/HelpdeskPage': HelpdeskPage,
  'surveys/SurveysPage': SurveysPage,
  'policies/PoliciesPage': PoliciesPage,
  'attrition/AttritionPage': AttritionPage,
  'flags/FlagsPage': FlagsPage,
  'metrics/MetricsPage': MetricsPage,
  'directory/DirectoryPage': DirectoryPage,
};

function pageFor(route) {
  return PAGES[route.page] || null;
}

/** Animated Suspense fallback: shimmering header and cards. */
function RouteFallback() {
  return (
    <div className="page" role="status" aria-label="Loading screen">
      <div className="stack" style={{ '--gap': '12px', marginBottom: 32 }}>
        <Skeleton w={120} h={12} />
        <Skeleton w="42%" h={32} />
      </div>
      <SkeletonCards count={4} />
    </div>
  );
}

/**
 * Route change choreography: the old view blurs and fades out (140ms), then the new one
 * rises in. Under reduced motion the swap is immediate and CSS reduces entrances to fades.
 */
function useRouteTransition(path) {
  const reduced = useReducedMotion();
  const [shown, setShown] = useState(path);
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    if (path === shown) { setLeaving(false); return undefined; }
    if (reduced) { setShown(path); return undefined; }
    setLeaving(true);
    const id = setTimeout(() => { setShown(path); setLeaving(false); }, 140);
    return () => clearTimeout(id);
  }, [path, shown, reduced]);

  return { shown, leaving };
}

export function Shell() {
  const { role, collapsed, toggleSidebar } = useApp();
  const { path } = useRoute();
  const { shown, leaving } = useRouteTransition(path);
  const mainRef = useRef(null);
  const nav = useMemo(() => routesFor(role), [role]);

  const route = findRoute(shown);
  const activeRoute = findRoute(path);

  // After each swap: reset scroll, move focus to the main region and update the title.
  useEffect(() => {
    window.scrollTo({ top: 0 });
    mainRef.current?.focus({ preventScroll: true });
    document.title = `${route?.label ?? 'Not found'} · TalentPulse AI`;
  }, [shown, route]);

  let view;
  if (!route) {
    view = (
      <EmptyState
        icon="search"
        title="We could not find that page"
        description="The link may be out of date."
        action={<Button variant="secondary" icon="home" onClick={() => navigate('/')}>Back to Home</Button>}
      />
    );
  } else if (!canAccess(route, role)) {
    view = <RestrictedByPolicy area={route.label} />;
  } else {
    const Page = pageFor(route);
    view = <Page />;
  }

  return (
    <div className={`shell ${collapsed ? 'is-collapsed' : ''}`}>
      <a className="skip-link" href="#main" onClick={(e) => { e.preventDefault(); mainRef.current?.focus(); }}>Skip to content</a>
      <Sidebar routes={nav} activePath={activeRoute && canAccess(activeRoute, role) ? path : null} collapsed={collapsed} onToggle={toggleSidebar} />
      <div className="shell__main">
        <TopBar route={activeRoute} routes={nav} />
        <main id="main" ref={mainRef} tabIndex={-1} className="view">
          <div key={shown} className={leaving ? 'page-exit' : 'page-enter'}>
            <ErrorBoundary resetKey={shown}>
              <Suspense fallback={<RouteFallback />}>{view}</Suspense>
            </ErrorBoundary>
          </div>
        </main>
      </div>
    </div>
  );
}
