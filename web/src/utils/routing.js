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

const ROUTE_IDENTITY_QUERY_KEYS = ['view', 'tenant_key', 'date'];
const ANALYSIS_ONLY_KEYS = ['executor_id', 'include_deleted', 'job_id'];
const TREND_ONLY_KEYS = ['trend_platform', 'trend_keyword'];

const encodePathSegment = (value) => encodeURIComponent(String(value || '').trim());

const normalizeSearch = (search) => {
  const raw = String(search || '');
  return raw.startsWith('?') ? raw.slice(1) : raw;
};

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

export const buildDefaultEntryUrl = ({ defaults = {} } = {}) =>
  buildViewPath(DEFAULT_VIEW_KEY, {
    tenantKey: defaults.tenantKey,
    jobId: defaults.jobId,
  });

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

const cleanSearchForView = (params, viewKey) => {
  ROUTE_IDENTITY_QUERY_KEYS.forEach((key) => params.delete(key));

  if (isAnalysisView(viewKey)) {
    params.delete('job_id');
    params.delete('executor_id');
    params.delete('include_deleted');
  }

  if (viewKey !== 'task-status') {
    params.delete('job_id');
    params.delete('include_deleted');
  }

  if (viewKey !== 'task-load') {
    params.delete('executor_id');
  }

  if (viewKey !== 'home') {
    params.delete('platform');
  }

  if (viewKey !== 'trend') {
    TREND_ONLY_KEYS.forEach((key) => params.delete(key));
  }

  return params;
};

export const buildRouteSearch = ({ search = '', nextViewKey } = {}) => {
  const normalizedView = normalizeViewKey(nextViewKey);
  const params = cleanSearchForView(
    new URLSearchParams(normalizeSearch(search)),
    normalizedView,
  );
  const query = params.toString();
  return query ? `?${query}` : '';
};
