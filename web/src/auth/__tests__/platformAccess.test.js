import test from 'node:test';
import assert from 'node:assert/strict';

import { getPlatformAccessState, hasPlatformAdminRole } from '../platformAccess.js';

test('hasPlatformAdminRole only accepts platform_admin role', () => {
  assert.equal(hasPlatformAdminRole({ platformRoles: ['platform_admin'] }), true);
  assert.equal(hasPlatformAdminRole({ platformRoles: ['tenant_admin'] }), false);
  assert.equal(hasPlatformAdminRole({}), false);
});

test('getPlatformAccessState maps auth state to route decisions', () => {
  assert.equal(getPlatformAccessState({ isInitializing: true }), 'loading');
  assert.equal(getPlatformAccessState({ isAuthenticated: false, user: null }), 'login');
  assert.equal(
    getPlatformAccessState({
      isAuthenticated: true,
      user: { platformRoles: [] },
    }),
    'forbidden',
  );
  assert.equal(
    getPlatformAccessState({
      isAuthenticated: true,
      user: { platformRoles: ['platform_admin'] },
    }),
    'allowed',
  );
});
