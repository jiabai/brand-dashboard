import test from 'node:test';
import assert from 'node:assert/strict';

import { changePassword, forgotPassword, resetPassword } from '../auth.js';
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

test('forgotPassword posts email to the public endpoint', async () => {
  let requestedUrl;
  let requestedOptions;
  globalThis.fetch = async (url, options) => {
    requestedUrl = url;
    requestedOptions = options;
    return jsonResponse({ status: 'success', message: '如果该邮箱已注册并激活，重置邮件已发送' });
  };

  await forgotPassword({ email: 'user@demo.test' });

  const parsed = new URL(requestedUrl, 'http://localhost');
  assert.equal(parsed.pathname, '/api/v1/public/auth/forgot-password');
  assert.equal(requestedOptions.method, 'POST');
  assert.equal(JSON.parse(requestedOptions.body).email, 'user@demo.test');
});

test('resetPassword posts token and passwords', async () => {
  let requestedUrl;
  let requestedOptions;
  globalThis.fetch = async (url, options) => {
    requestedUrl = url;
    requestedOptions = options;
    return jsonResponse({ status: 'success', message: '密码已重置' });
  };

  await resetPassword({ token: 't.t', password: 'NewPass12345', confirmPassword: 'NewPass12345' });

  const parsed = new URL(requestedUrl, 'http://localhost');
  assert.equal(parsed.pathname, '/api/v1/public/auth/reset-password');
  assert.equal(requestedOptions.method, 'POST');
  assert.equal(JSON.parse(requestedOptions.body).token, 't.t');
});

test('changePassword posts with authorization header', async () => {
  writeAuthSession({
    accessToken: 'user-token',
    currentTenantKey: 'tn_demo',
    user: { tenants: [{ tenantKey: 'tn_demo', status: 'active' }] },
  });

  let requestedUrl;
  let requestedOptions;
  globalThis.fetch = async (url, options) => {
    requestedUrl = url;
    requestedOptions = options;
    return jsonResponse({ status: 'success', message: '密码已修改' });
  };

  await changePassword({
    currentPassword: 'OldPass12345',
    newPassword: 'NewPass12345',
    confirmPassword: 'NewPass12345',
  });

  const parsed = new URL(requestedUrl, 'http://localhost');
  assert.equal(parsed.pathname, '/api/v1/auth/change-password');
  assert.equal(requestedOptions.method, 'POST');
  assert.equal(requestedOptions.headers.Authorization, 'Bearer user-token');
});
