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

const LEGACY_KEYS = ['view', 'tenant_key', 'date'];

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

  LEGACY_KEYS.forEach((key) => params.delete(key));

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

export const buildLegacyRedirectUrl = ({ search = '', defaults = {} } = {}) => {
  const params = new URLSearchParams(normalizeSearch(search));
  const viewKey = normalizeViewKey(params.get('view') || DEFAULT_VIEW_KEY);
  const tenantKey = params.get('tenant_key') || defaults.tenantKey || '';
  const jobId = params.get('job_id') || defaults.jobId || '';
  const path = buildViewPath(viewKey, { tenantKey, jobId, defaults });
  const nextParams = new URLSearchParams(params);

  LEGACY_KEYS.forEach((key) => nextParams.delete(key));

  if (viewKey !== 'task-status') {
    nextParams.delete('job_id');
  }

  const query = nextParams.toString();
  return query ? `${path}?${query}` : path;
};

const normalizeSearch = (search) => {
  const raw = String(search || '');
  return raw.startsWith('?') ? raw.slice(1) : raw;
};
