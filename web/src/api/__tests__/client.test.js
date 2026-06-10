import test from 'node:test';
import assert from 'node:assert/strict';

import { fetchJson, postJson } from '../client.js';
import { writeAuthSession, clearAuthSession } from '../../auth/storage.js';

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

test('fetchJson injects auth token and tenant header from stored session', async () => {
  writeAuthSession({
    accessToken: 'token-c',
    currentTenantKey: 'tn_current',
    user: { tenants: [{ tenantKey: 'tn_current', status: 'active' }] },
  });
  let request;
  globalThis.fetch = async (url, options) => {
    request = { url, options };
    return jsonResponse({ ok: true });
  };

  await fetchJson('/api/v1/dashboard/available-dates?job_id=job_demo');

  assert.equal(request.options.headers.Authorization, 'Bearer token-c');
  assert.equal(request.options.headers['X-Tenant-Key'], 'tn_current');
});

test('fetchJson prefers request tenant over stored tenant', async () => {
  writeAuthSession({
    accessToken: 'token-d',
    currentTenantKey: 'tn_current',
    user: { tenants: [{ tenantKey: 'tn_current', status: 'active' }] },
  });
  let headers;
  globalThis.fetch = async (_url, options) => {
    headers = options.headers;
    return jsonResponse({ ok: true });
  };

  await fetchJson('/api/v1/dashboard/available-dates?tenant_key=tn_route');

  assert.equal(headers['X-Tenant-Key'], 'tn_route');
});

test('postJson can derive tenant header from json body', async () => {
  writeAuthSession({
    accessToken: 'token-e',
    currentTenantKey: 'tn_current',
    user: { tenants: [{ tenantKey: 'tn_current', status: 'active' }] },
  });
  let request;
  globalThis.fetch = async (url, options) => {
    request = { url, options };
    return jsonResponse({ ok: true });
  };

  await postJson('/api/v1/query-jobs/load', { tenant_key: 'tn_body', job_name: 'demo' });

  assert.equal(request.options.headers.Authorization, 'Bearer token-e');
  assert.equal(request.options.headers['X-Tenant-Key'], 'tn_body');
  assert.equal(request.options.headers['Content-Type'], 'application/json');
});

test('fetchJson surfaces envelope message from error responses', async () => {
  globalThis.fetch = async () => ({
    ok: false,
    status: 400,
    json: async () => ({}),
    text: async () => JSON.stringify({ status: 'error', message: '账号已激活', code: 400 }),
  });

  await assert.rejects(
    () => fetchJson('/api/v1/platform/tenants/tn_demo/resend-activation'),
    (error) => {
      assert.equal(error.message, '请求失败(400): 账号已激活');
      return true;
    },
  );
});

test('fetchJson falls back to detail field from error responses', async () => {
  globalThis.fetch = async () => ({
    ok: false,
    status: 404,
    json: async () => ({}),
    text: async () => JSON.stringify({ detail: '租户不存在' }),
  });

  await assert.rejects(
    () => fetchJson('/api/v1/platform/tenants/tn_missing'),
    (error) => {
      assert.equal(error.message, '请求失败(404): 租户不存在');
      return true;
    },
  );
});
