import test from 'node:test';
import assert from 'node:assert/strict';

import { getLoginRedirectTarget } from '../redirect.js';

test('platform admin direct login redirects to platform tenants', () => {
  assert.equal(
    getLoginRedirectTarget({
      location: { state: null },
      session: { user: { platformRoles: ['platform_admin'] } },
      tenantKey: '',
    }),
    '/platform/tenants',
  );
});

test('login keeps original protected destination before role defaults', () => {
  assert.equal(
    getLoginRedirectTarget({
      location: {
        state: {
          from: {
            pathname: '/dashboard/tn_customer/job_1',
            search: '?timeframe=7days',
          },
        },
      },
      session: { user: { platformRoles: ['platform_admin'] } },
      tenantKey: '',
    }),
    '/dashboard/tn_customer/job_1?timeframe=7days',
  );
});

test('tenant user direct login redirects to project list', () => {
  assert.equal(
    getLoginRedirectTarget({
      location: { state: null },
      session: { user: { platformRoles: [] } },
      tenantKey: 'tn_member',
    }),
    '/projects/tn_member',
  );
});

test('tenant user direct login without tenant returns to login', () => {
  assert.equal(
    getLoginRedirectTarget({
      location: { state: null },
      session: { user: { platformRoles: [] } },
      tenantKey: '',
    }),
    '/login',
  );
});
