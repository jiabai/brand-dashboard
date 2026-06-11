import test from 'node:test';
import assert from 'node:assert/strict';

import {
  buildPlatformTenantDetailPath,
  buildPlatformTenantAdminPath,
  buildPlatformTenantProjectOverviewPath,
  buildTenantDashboardPath,
  buildTenantTaskStatusPath,
  getAdminStatusLabel,
  getEmailDeliveryMeta,
  getPlanTypeLabel,
  getTenantStatusMeta,
  normalizeTenantDetailResponse,
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

test('normalizes tenant detail response into tenant and projects', () => {
  assert.deepEqual(
    normalizeTenantDetailResponse({
      data: {
        tenantKey: 'tn_acme',
        tenantName: 'Acme',
        projects: [{ project_id: 'proj_1' }],
      },
    }),
    {
      tenant: { tenantKey: 'tn_acme', tenantName: 'Acme' },
      projects: [{ project_id: 'proj_1' }],
    },
  );
  assert.deepEqual(normalizeTenantDetailResponse({}), {
    tenant: null,
    projects: [],
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

test('maps activation email delivery status for create result display', () => {
  assert.deepEqual(getEmailDeliveryMeta({ status: 'sent', to: 'admin@acme.test' }), {
    title: '激活邮件已发送',
    description: '已发送至 admin@acme.test。',
    variant: 'default',
  });
  assert.deepEqual(getEmailDeliveryMeta({ status: 'not_configured', to: 'admin@acme.test' }), {
    title: 'SMTP 未配置',
    description: '尚未自动发送至 admin@acme.test，请复制激活链接人工发送。',
    variant: 'destructive',
  });
  assert.deepEqual(getEmailDeliveryMeta({ status: 'failed', to: 'admin@acme.test' }), {
    title: '激活邮件发送失败',
    description: '未能自动发送至 admin@acme.test，请复制激活链接人工发送。',
    variant: 'destructive',
  });
  assert.deepEqual(getEmailDeliveryMeta(null), {
    title: '激活邮件状态未知',
    description: '请复制激活链接人工确认发送状态。',
    variant: 'default',
  });
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

test('buildPlatformTenantDetailPath links platform tenant detail', () => {
  assert.equal(
    buildPlatformTenantDetailPath('tn_acme'),
    '/platform/tenants/tn_acme',
  );
  assert.equal(
    buildPlatformTenantDetailPath('tn space'),
    '/platform/tenants/tn%20space',
  );
  assert.equal(buildPlatformTenantDetailPath(''), '');
});

test('buildPlatformTenantProjectOverviewPath links the tenant detail project overview anchor', () => {
  assert.equal(
    buildPlatformTenantProjectOverviewPath('tn space'),
    '/platform/tenants/tn%20space#project-overview',
  );
  assert.equal(buildPlatformTenantProjectOverviewPath(''), '');
});

test('buildPlatformTenantAdminPath links the tenant administrator section', () => {
  assert.equal(
    buildPlatformTenantAdminPath('tn space'),
    '/platform/tenants/tn%20space#tenant-admin',
  );
  assert.equal(buildPlatformTenantAdminPath(''), '');
});

test('buildTenantDashboardPath links platform tenants with a real latest job and target brand', () => {
  assert.equal(
    buildTenantDashboardPath({
      tenantKey: 'tn_acme',
      latestJob: { jobId: 'job_20260521', brand: 'Quickcep' },
    }),
    '/dashboard/tn_acme/job_20260521?brand=Quickcep',
  );
  assert.equal(
    buildTenantDashboardPath({
      tenantKey: 'tn space',
      latestJob: { jobId: 'job space', brand: '快牛 智营' },
    }),
    '/dashboard/tn%20space/job%20space?brand=%E5%BF%AB%E7%89%9B+%E6%99%BA%E8%90%A5',
  );
  assert.equal(
    buildTenantDashboardPath({
      tenantKey: 'tn_acme',
      latestJob: { jobId: 'job_20260521' },
    }),
    '/dashboard/tn_acme/job_20260521',
  );
  assert.equal(buildTenantDashboardPath({ tenantKey: 'tn_acme', latestJob: null }), '');
  assert.equal(buildTenantDashboardPath({ tenantKey: '', latestJob: { jobId: 'job_1' } }), '');
});
