// Route table: single source of truth for navigation, access control and code splitting.
const ALL = ['superadmin', 'admin', 'hr', 'manager', 'employee'];
const LEADS = ['superadmin', 'admin', 'hr', 'manager'];
const HR = ['superadmin', 'admin', 'hr'];
const SUPER = ['superadmin'];

/** `page` is resolved lazily from src/features/<page>.jsx (see Shell). */
export const ROUTES = [
  { path: '/', label: 'Home', icon: 'home', section: 'Workspace', roles: ALL, page: 'home/HomePage' },
  { path: '/leave', label: 'Leave', icon: 'calendar', section: 'Workspace', roles: ALL, page: 'leave/LeavePage' },
  { path: '/reviews', label: 'Reviews', icon: 'star', section: 'Workspace', roles: ALL, page: 'reviews/ReviewsPage' },
  { path: '/helpdesk', label: 'Policy Helpdesk', icon: 'chat', section: 'Workspace', roles: ALL, page: 'helpdesk/HelpdeskPage' },
  { path: '/surveys', label: 'Surveys', icon: 'clipboard', section: 'Workspace', roles: ALL, page: 'surveys/SurveysPage' },
  { path: '/policies', label: 'Policies', icon: 'file', section: 'Workspace', roles: ALL, page: 'policies/PoliciesPage' },
  { path: '/attrition', label: 'Attrition', icon: 'shield', section: 'Intelligence', roles: LEADS, page: 'attrition/AttritionPage' },
  { path: '/flags', label: 'Performance Flags', icon: 'trendDown', section: 'Intelligence', roles: LEADS, page: 'flags/FlagsPage' },
  { path: '/metrics', label: 'Org Metrics', icon: 'chart', section: 'Intelligence', roles: HR, page: 'metrics/MetricsPage' },
  { path: '/directory', label: 'Directory & Org', icon: 'users', section: 'People', roles: ALL, page: 'directory/DirectoryPage' },
];

export const findRoute = (path) => ROUTES.find((r) => r.path === path) ?? null;
export const canAccess = (route, role) => Boolean(route && role && route.roles.includes(role));
export const routesFor = (role) => ROUTES.filter((r) => canAccess(r, role));
export const canSearchPeople = (role) => canAccess(findRoute('/directory'), role);
