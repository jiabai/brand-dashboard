import test from 'node:test';
import assert from 'node:assert/strict';

import {
  buildTenantTaskStatusPath,
  getAdminStatusLabel,
  getPlanTypeLabel,
  getTenantStatusMeta,
  normalizeTenantListResponse,
  prepareTenantCreatePayload,
  readTenantFiltersFromSearch,
} from '../tenantPresentation.js';

test('normalizes tenant list response with stable defaults', () => {
  const response = {
    data: {
      items: [{ tenantKey: 'tn_acme', tenantName: 'Acme' }],
      pagination: { page: 2, pageSize: 10, total: 23, totalPages: 3 },
    },
  };

  assert.deepEqual(normalizeTenantListResponse(response), {
    items: [{ tenantKey: 'tn_acme', tenantName: 'Acme' }],
    pagination: { page: 2, pageSize: 10, total: 23, totalPages: 3 },
  });
  assert.deepEqual(normalizeTenantListResponse({}), {
    items: [],
    pagination: { page: 1, pageSize: 20, total: 0, totalPages: 0 },
  });
});

test('maps tenant status, admin status, and plan labels for display', () => {
  assert.deepEqual(getTenantStatusMeta('active'), { label: '启用', variant: 'default' });
  assert.deepEqual(getTenantStatusMeta('inactive'), { label: '未启用', variant: 'secondary' });
  assert.deepEqual(getTenantStatusMeta('suspended'), { label: '已暂停', variant: 'destructive' });
  assert.equal(getAdminStatusLabel('pending_activation'), '待激活');
  assert.equal(getAdminStatusLabel('active'), '已激活');
  assert.equal(getPlanTypeLabel('enterprise'), '企业版');
  assert.equal(getPlanTypeLabel(''), '未设置');
});

test('reads tenant filters from URL search params', () => {
  assert.deepEqual(readTenantFiltersFromSearch('?q=acme&status=active&planType=pro&page=3'), {
    q: 'acme',
    status: 'active',
    planType: 'pro',
    page: 3,
    pageSize: 20,
  });
  assert.equal(readTenantFiltersFromSearch('?page=bad').page, 1);
});

test('prepareTenantCreatePayload strips empty fields and normalizes numbers', () => {
  assert.deepEqual(
    prepareTenantCreatePayload({
      tenantName: 'Acme',
      industry: 'Software',
      adminName: 'Alice',
      adminEmail: 'alice@acme.test',
      maxUsers: '25',
      planType: '',
      billingCycle: null,
    }),
    {
      tenantName: 'Acme',
      industry: 'Software',
      adminName: 'Alice',
      adminEmail: 'alice@acme.test',
      maxUsers: 25,
    },
  );
});

test('buildTenantTaskStatusPath links platform tenants without requiring a default job', () => {
  assert.equal(
    buildTenantTaskStatusPath('tn_acme'),
    '/tasks/tn_acme/status',
  );
  assert.equal(
    buildTenantTaskStatusPath('tn space'),
    '/tasks/tn%20space/status',
  );
});
