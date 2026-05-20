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

export const createPlatformTenant = (payload, options) => {
  return post('/api/v1/platform/tenants', payload, platformOptions(options));
};
