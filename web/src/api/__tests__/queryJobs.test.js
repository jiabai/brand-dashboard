import test from 'node:test';
import assert from 'node:assert/strict';

import { fetchQueryJobStatus } from '../queryJobs.js';

const jsonResponse = (payload) => ({
  ok: true,
  status: 200,
  json: async () => payload,
  text: async () => JSON.stringify(payload),
});

test.afterEach(() => {
  delete globalThis.fetch;
});

test('fetchQueryJobStatus serializes project_id when provided', async () => {
  let requestedUrl;
  globalThis.fetch = async (url) => {
    requestedUrl = url;
    return jsonResponse({ success: true, count: 0, jobs: [] });
  };

  await fetchQueryJobStatus({ tenantKey: 'tn_demo', projectId: 'proj_a' });

  const parsed = new URL(requestedUrl, 'http://localhost');
  assert.equal(parsed.pathname, '/api/v1/query-jobs/status');
  assert.equal(parsed.searchParams.get('tenant_key'), 'tn_demo');
  assert.equal(parsed.searchParams.get('project_id'), 'proj_a');
});

test('fetchQueryJobStatus omits project_id when not provided', async () => {
  let requestedUrl;
  globalThis.fetch = async (url) => {
    requestedUrl = url;
    return jsonResponse({ success: true, count: 0, jobs: [] });
  };

  await fetchQueryJobStatus({ tenantKey: 'tn_demo' });

  const parsed = new URL(requestedUrl, 'http://localhost');
  assert.equal(parsed.searchParams.get('project_id'), null);
});
