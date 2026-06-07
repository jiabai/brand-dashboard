import test from 'node:test';
import assert from 'node:assert/strict';

import {
  createPlatformTenant,
  fetchPlatformCollectionHealth,
  fetchPlatformTenants,
} from '../platform.js';
import { clearAuthSession, writeAuthSession } from '../../auth/storage.js';

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

test('fetchPlatformTenants serializes platform tenant filters', async () => {
  let requestedUrl;
  globalThis.fetch = async (url) => {
    requestedUrl = url;
    return jsonResponse({ data: { items: [], pagination: { page: 2 } } });
  };

  await fetchPlatformTenants({
    q: 'acme',
    status: 'active',
    planType: 'enterprise',
    page: 2,
    pageSize: 10,
  });

  const parsed = new URL(requestedUrl, 'http://localhost');
  assert.equal(parsed.pathname, '/api/v1/platform/tenants');
  assert.equal(parsed.searchParams.get('q'), 'acme');
  assert.equal(parsed.searchParams.get('status'), 'active');
  assert.equal(parsed.searchParams.get('planType'), 'enterprise');
  assert.equal(parsed.searchParams.get('page'), '2');
  assert.equal(parsed.searchParams.get('pageSize'), '10');
});

test('platform list API keeps authorization but skips tenant header', async () => {
  writeAuthSession({
    accessToken: 'platform-token',
    currentTenantKey: 'tn_customer',
    user: {
      platformRoles: ['platform_admin'],
      tenants: [{ tenantKey: 'tn_customer', status: 'active' }],
    },
  });
  let headers;
  globalThis.fetch = async (_url, options) => {
    headers = options.headers;
    return jsonResponse({ data: { items: [], pagination: { page: 1 } } });
  };

  await fetchPlatformTenants({ page: 1 });

  assert.equal(headers.Authorization, 'Bearer platform-token');
  assert.equal(headers['X-Tenant-Key'], undefined);
});

test('platform create API posts json without tenant header', async () => {
  writeAuthSession({
    accessToken: 'platform-token',
    currentTenantKey: 'tn_customer',
    user: {
      platformRoles: ['platform_admin'],
      tenants: [{ tenantKey: 'tn_customer', status: 'active' }],
    },
  });
  let request;
  globalThis.fetch = async (url, options) => {
    request = { url, options };
    return jsonResponse({ data: { tenantKey: 'tn_acme' } });
  };

  await createPlatformTenant({ tenantName: 'Acme', adminEmail: 'owner@acme.test' });

  assert.equal(request.url, '/api/v1/platform/tenants');
  assert.equal(request.options.method, 'POST');
  assert.equal(request.options.headers.Authorization, 'Bearer platform-token');
  assert.equal(request.options.headers['Content-Type'], 'application/json');
  assert.equal(request.options.headers['X-Tenant-Key'], undefined);
  assert.deepEqual(JSON.parse(request.options.body), {
    tenantName: 'Acme',
    adminEmail: 'owner@acme.test',
  });
});

test('platform collection health API skips tenant header', async () => {
  writeAuthSession({
    accessToken: 'platform-token',
    currentTenantKey: 'tn_customer',
    user: {
      platformRoles: ['platform_admin'],
      tenants: [{ tenantKey: 'tn_customer', status: 'active' }],
    },
  });
  let request;
  globalThis.fetch = async (url, options) => {
    request = { url, options };
    return jsonResponse({ data: { summary: {}, executors: [], queues: [], failedTasks: [] } });
  };

  await fetchPlatformCollectionHealth({ failedTaskLimit: 5 });

  const parsed = new URL(request.url, 'http://localhost');
  assert.equal(parsed.pathname, '/api/v1/platform/collection-health');
  assert.equal(parsed.searchParams.get('failedTaskLimit'), '5');
  assert.equal(request.options.headers.Authorization, 'Bearer platform-token');
  assert.equal(request.options.headers['X-Tenant-Key'], undefined);
});
