import test from 'node:test';
import assert from 'node:assert/strict';

import { clearAuthSession, writeAuthSession } from '../../auth/storage.js';
import { fetchProjectDetail, fetchProjects } from '../projects.js';

class MemoryStorage {
  constructor() {
    this.map = new Map();
  }

  getItem(key) {
    return this.map.has(key) ? this.map.get(key) : null;
  }

  setItem(key, value) {
    this.map.set(key, String(value));
  }

  removeItem(key) {
    this.map.delete(key);
  }
}

const jsonResponse = (payload, init = {}) => ({
  ok: init.ok ?? true,
  status: init.status ?? 200,
  json: async () => payload,
  text: async () => JSON.stringify(payload),
});

test.beforeEach(() => {
  globalThis.localStorage = new MemoryStorage();
});

test.afterEach(() => {
  clearAuthSession();
  delete globalThis.localStorage;
  delete globalThis.fetch;
});

test('fetchProjects uses tenant header without query tenant leakage', async () => {
  writeAuthSession({
    accessToken: 'tenant-token',
    currentTenantKey: 'tn_current',
    user: { tenants: [{ tenantKey: 'tn_current', status: 'active' }] },
  });
  let request;
  globalThis.fetch = async (url, options) => {
    request = { url, options };
    return jsonResponse({ success: true, projects: [] });
  };

  await fetchProjects({ tenantKey: 'tn_acme' });

  assert.equal(request.url, '/api/v1/projects');
  assert.equal(request.options.method, 'GET');
  assert.equal(request.options.headers.Authorization, 'Bearer tenant-token');
  assert.equal(request.options.headers['X-Tenant-Key'], 'tn_acme');
});

test('fetchProjectDetail encodes project id path segment', async () => {
  let requestedUrl;
  globalThis.fetch = async (url) => {
    requestedUrl = url;
    return jsonResponse({ success: true, project: { project_id: 'proj space' } });
  };

  await fetchProjectDetail({ tenantKey: 'tn_acme', projectId: 'proj space' });

  assert.equal(requestedUrl, '/api/v1/projects/proj%20space');
});
