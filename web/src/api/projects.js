import { fetchJson as fetch } from './client.js';

const encodePathSegment = (value) => encodeURIComponent(String(value || '').trim());

export const fetchProjects = ({ tenantKey } = {}, options = {}) =>
  fetch('/api/v1/projects', {
    ...options,
    tenantKey,
  });

export const fetchProjectDetail = ({ tenantKey, projectId } = {}, options = {}) =>
  fetch(`/api/v1/projects/${encodePathSegment(projectId)}`, {
    ...options,
    tenantKey,
  });

export const fetchProjectDataQuality = ({ tenantKey, projectId } = {}, options = {}) =>
  fetch(`/api/v1/projects/${encodePathSegment(projectId)}/data-quality`, {
    ...options,
    tenantKey,
  });

export const fetchProjectCollectionJobs = ({ tenantKey, projectId } = {}, options = {}) =>
  fetch(`/api/v1/projects/${encodePathSegment(projectId)}/collection-jobs`, {
    ...options,
    tenantKey,
  });
