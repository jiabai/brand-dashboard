import {
  DEFAULT_VIEW_KEY,
  getRouteByPathSegment,
  getRouteByTaskAction,
  getRouteByViewKey,
} from '../config/routes.js';

const encodePathSegment = (value) => encodeURIComponent(String(value || '').trim());

export const isAnalysisView = (viewKey) => {
  const route = getRouteByViewKey(viewKey);
  return Boolean(route?.requiresJobId && route?.path && !route?.disabled);
};

export const normalizeViewKey = (viewKey) => {
  const route = getRouteByViewKey(viewKey);
  if (route?.viewKey === viewKey && route.path && !route.disabled) {
    return viewKey;
  }
  return DEFAULT_VIEW_KEY;
};

export const buildViewPath = (viewKey, { tenantKey, jobId, defaults = {} } = {}) => {
  const normalizedView = normalizeViewKey(viewKey);
  const route = getRouteByViewKey(normalizedView);
  const nextTenantKey = tenantKey || defaults.tenantKey || '';
  const nextJobId = jobId || defaults.jobId || '';

  if (route.parentSegment === 'tasks') {
    return `/${route.parentSegment}/${encodePathSegment(nextTenantKey)}/${route.taskAction}`;
  }

  if (route.requiresJobId) {
    return `/${route.routeSegment}/${encodePathSegment(nextTenantKey)}/${encodePathSegment(nextJobId)}`;
  }

  return `/${route.routeSegment}/${encodePathSegment(nextTenantKey)}`;
};

export const getViewKeyFromPath = (pathname = '') => {
  const segments = String(pathname || '')
    .split('/')
    .map((segment) => segment.trim())
    .filter(Boolean);

  if (segments[0] === 'tasks') {
    return getRouteByTaskAction(segments[2])?.viewKey || DEFAULT_VIEW_KEY;
  }

  return getRouteByPathSegment(segments[0])?.viewKey || DEFAULT_VIEW_KEY;
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
