import test from 'node:test';
import assert from 'node:assert/strict';

import { fetchSentimentAnalysis } from '../dashboard.js';
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

const jsonResponse = (payload) => ({
  ok: true,
  status: 200,
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

test('fetchSentimentAnalysis serializes dashboard sentiment filters', async () => {
  writeAuthSession({
    accessToken: 'tenant-token',
    currentTenantKey: 'tenant_a',
    user: {
      tenants: [{ tenantKey: 'tenant_a', status: 'active' }],
    },
  });
  let request;
  globalThis.fetch = async (url, options) => {
    request = { url, options };
    return jsonResponse({ status: 'success', data: { distribution: [], keywords: [] }, metadata: {} });
  };

  await fetchSentimentAnalysis({
    tenantKey: 'tenant_a',
    jobId: 'job_a',
    timeframe: 'specific_day',
    startDate: '20260607',
    endDate: '20260607',
    brand: 'Brand A',
    platform: 'deepseek',
    keyword: 'math',
  });

  const parsed = new URL(request.url, 'http://localhost');
  assert.equal(parsed.pathname, '/api/v1/dashboard/sentiment-analysis');
  assert.equal(parsed.searchParams.get('tenant_key'), 'tenant_a');
  assert.equal(parsed.searchParams.get('job_id'), 'job_a');
  assert.equal(parsed.searchParams.get('timeframe'), 'specific_day');
  assert.equal(parsed.searchParams.get('start_date'), '20260607');
  assert.equal(parsed.searchParams.get('end_date'), '20260607');
  assert.equal(parsed.searchParams.get('brand'), 'Brand A');
  assert.equal(parsed.searchParams.get('platform'), 'deepseek');
  assert.equal(parsed.searchParams.get('keyword'), 'math');
  assert.equal(request.options.headers.Authorization, 'Bearer tenant-token');
  assert.equal(request.options.headers['X-Tenant-Key'], 'tenant_a');
});
