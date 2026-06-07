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
