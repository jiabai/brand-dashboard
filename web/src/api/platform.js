import { fetchJson as fetch, postJson as post } from './client.js';
import { buildQueryString } from '../utils/url.js';

const platformOptions = (options = {}) => ({
  ...options,
  skipTenantHeader: true,
});

export const fetchPlatformTenants = (
  { q, status, planType, page = 1, pageSize = 20 } = {},
  options,
) => {
  const params = buildQueryString({ q, status, planType, page, pageSize });
  const suffix = params ? `?${params}` : '';
  return fetch(`/api/v1/platform/tenants${suffix}`, platformOptions(options));
};

const encodePathSegment = (value) => encodeURIComponent(String(value || '').trim());

export const fetchPlatformTenantDetail = (tenantKey, options) => {
  return fetch(
    `/api/v1/platform/tenants/${encodePathSegment(tenantKey)}`,
    platformOptions(options),
  );
};

export const fetchPlatformTenantMembers = (tenantKey, options) => {
  return fetch(
    `/api/v1/platform/tenants/${encodePathSegment(tenantKey)}/members`,
    platformOptions(options),
  );
};

export const updatePlatformTenantMember = (tenantKey, userId, payload, options) => {
  return fetch(
    `/api/v1/platform/tenants/${encodePathSegment(tenantKey)}/members/${encodePathSegment(userId)}`,
    {
      ...platformOptions(options),
      method: 'PATCH',
      body: payload,
    },
  );
};

export const createPlatformTenant = (payload, options) => {
  return post('/api/v1/platform/tenants', payload, platformOptions(options));
};

export const resendPlatformTenantActivation = (tenantKey, options) => {
  return post(
    `/api/v1/platform/tenants/${encodePathSegment(tenantKey)}/resend-activation`,
    undefined,
    platformOptions(options),
  );
};

export const fetchPlatformCollectionHealth = ({ failedTaskLimit = 20 } = {}, options) => {
  const params = buildQueryString({ failedTaskLimit });
  const suffix = params ? `?${params}` : '';
  return fetch(`/api/v1/platform/collection-health${suffix}`, platformOptions(options));
};
