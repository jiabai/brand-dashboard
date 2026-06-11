import test from 'node:test';
import assert from 'node:assert/strict';

import {
  getPlatformAccessState,
  hasPlatformAdminRole,
  hasTenantMembership,
  isPlatformReadonlyTenantAccess,
} from '../platformAccess.js';

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

test('hasTenantMembership checks real tenant membership only', () => {
  const user = {
    platformRoles: ['platform_admin'],
    tenants: [{ tenantKey: 'tn_member' }],
  };

  assert.equal(hasTenantMembership(user, 'tn_member'), true);
  assert.equal(hasTenantMembership(user, 'tn_other'), false);
  assert.equal(hasTenantMembership(user, ''), false);
});

test('isPlatformReadonlyTenantAccess treats platform admins as readonly in tenant workspaces', () => {
  assert.equal(
    isPlatformReadonlyTenantAccess({
      user: { platformRoles: ['platform_admin'], tenants: [{ tenantKey: 'tn_member' }] },
      tenantKey: 'tn_other',
    }),
    true,
  );
  assert.equal(
    isPlatformReadonlyTenantAccess({
      user: { platformRoles: ['platform_admin'], tenants: [{ tenantKey: 'tn_member' }] },
      tenantKey: 'tn_member',
    }),
    true,
  );
  assert.equal(
    isPlatformReadonlyTenantAccess({
      user: { platformRoles: ['platform_admin'], tenants: [{ tenantKey: 'tn_member' }] },
      tenantKey: '',
    }),
    false,
  );
  assert.equal(
    isPlatformReadonlyTenantAccess({
      user: { platformRoles: [], tenants: [] },
      tenantKey: 'tn_other',
    }),
    false,
  );
});
