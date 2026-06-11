import { fetchJson as fetch, postJson as post } from './client.js';
import { buildQueryString } from '../utils/url.js';

export const loadQueryJob = (payload, options) => {
  return post('/api/v1/query-jobs/load', payload, options);
};

export const fetchQueryJobStatus = ({ tenantKey, jobId, projectId, includeDeleted = false }, options) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId || undefined,
    project_id: projectId || undefined,
    include_deleted: includeDeleted ? 'true' : 'false',
  });
  return fetch(`/api/v1/query-jobs/status?${params}`, options);
};
