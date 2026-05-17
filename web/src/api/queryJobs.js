import { fetchJson as fetch, postJson as post } from './client.js';
import { buildQueryString } from '../utils/url.js';

export const loadQueryJob = (payload) => {
  return post('/api/v1/query-jobs/load', payload);
};

export const fetchQueryJobStatus = ({ tenantKey, jobId, includeDeleted = false }) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId || undefined,
    include_deleted: includeDeleted ? 'true' : 'false',
  });
  return fetch(`/api/v1/query-jobs/status?${params}`);
};
