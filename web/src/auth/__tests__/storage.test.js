import test from 'node:test';
import assert from 'node:assert/strict';

import {
  clearAuthSession,
  normalizeAuthSession,
  readAuthSession,
  writeAuthSession,
} from '../storage.js';

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

test.beforeEach(() => {
  globalThis.localStorage = new MemoryStorage();
});

test.afterEach(() => {
  delete globalThis.localStorage;
});

test('normalizeAuthSession chooses the first active tenant as the default tenant', () => {
  const session = normalizeAuthSession({
    accessToken: 'token-a',
    tokenType: 'Bearer',
    expiresIn: 43200,
    user: {
      userId: 7,
      email: 'admin@example.com',
      tenants: [
        { tenantKey: 'tn_disabled', status: 'disabled' },
        { tenantKey: 'tn_active', status: 'active' },
      ],
    },
  });

  assert.equal(session.accessToken, 'token-a');
  assert.equal(session.currentTenantKey, 'tn_active');
});

test('auth session can be written, read, and cleared', () => {
  writeAuthSession({
    accessToken: 'token-b',
    user: {
      email: 'member@example.com',
      tenants: [{ tenantKey: 'tn_demo', status: 'active' }],
    },
    currentTenantKey: 'tn_demo',
  });

  assert.equal(readAuthSession().accessToken, 'token-b');
  assert.equal(readAuthSession().currentTenantKey, 'tn_demo');

  clearAuthSession();

  assert.equal(readAuthSession(), null);
});
