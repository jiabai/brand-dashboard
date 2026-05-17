const DEFAULT_VIEW_KEY = 'home';

const ANALYSIS_ROUTE_SEGMENTS = {
  home: 'dashboard',
  trend: 'trend',
  platforms: 'platforms',
  sources: 'sources',
  sentiment: 'sentiment',
};

const TENANT_ROUTE_BUILDERS = {
  accounts: ({ tenantKey }) => `/accounts/${encodePathSegment(tenantKey)}`,
  'task-load': ({ tenantKey }) => `/tasks/${encodePathSegment(tenantKey)}/new`,
  'task-status': ({ tenantKey }) => `/tasks/${encodePathSegment(tenantKey)}/status`,
};

const SEGMENT_TO_VIEW = {
  dashboard: 'home',
  trend: 'trend',
  platforms: 'platforms',
  sources: 'sources',
  sentiment: 'sentiment',
  accounts: 'accounts',
};

const encodePathSegment = (value) => encodeURIComponent(String(value || '').trim());

export const isAnalysisView = (viewKey) =>
  Object.prototype.hasOwnProperty.call(ANALYSIS_ROUTE_SEGMENTS, viewKey);

export const normalizeViewKey = (viewKey) => {
  if (isAnalysisView(viewKey) || TENANT_ROUTE_BUILDERS[viewKey]) {
    return viewKey;
  }
  return DEFAULT_VIEW_KEY;
};

export const buildViewPath = (viewKey, { tenantKey, jobId, defaults = {} } = {}) => {
  const normalizedView = normalizeViewKey(viewKey);
  const nextTenantKey = tenantKey || defaults.tenantKey || '';
  const nextJobId = jobId || defaults.jobId || '';

  if (isAnalysisView(normalizedView)) {
    const routeSegment = ANALYSIS_ROUTE_SEGMENTS[normalizedView];
    return `/${routeSegment}/${encodePathSegment(nextTenantKey)}/${encodePathSegment(nextJobId)}`;
  }

  return TENANT_ROUTE_BUILDERS[normalizedView]({ tenantKey: nextTenantKey });
};

export const getViewKeyFromPath = (pathname = '') => {
  const segments = String(pathname || '')
    .split('/')
    .map((segment) => segment.trim())
    .filter(Boolean);

  if (segments[0] === 'tasks') {
    if (segments[2] === 'new') return 'task-load';
    if (segments[2] === 'status') return 'task-status';
  }

  return SEGMENT_TO_VIEW[segments[0]] || DEFAULT_VIEW_KEY;
};

export const buildRouteSearch = ({ search = '', nextViewKey }) => {
  const normalizedView = normalizeViewKey(nextViewKey);
  const params = new URLSearchParams(normalizeSearch(search));

  if (normalizedView !== 'task-status') {
    params.delete('job_id');
    params.delete('include_deleted');
  }

  if (normalizedView !== 'task-load') {
    params.delete('executor_id');
  }

  if (normalizedView !== 'home') {
    params.delete('platform');
  }

  if (normalizedView !== 'trend') {
    params.delete('trend_platform');
    params.delete('trend_keyword');
  }

  const query = params.toString();
  return query ? `?${query}` : '';
};

const normalizeSearch = (search) => {
  const raw = String(search || '');
  return raw.startsWith('?') ? raw.slice(1) : raw;
};
