import test from 'node:test';
import assert from 'node:assert/strict';
import {
  buildLegacyRedirectUrl,
  buildRouteSearch,
  buildViewPath,
  getViewKeyFromPath,
} from '../routing.js';

const defaults = {
  tenantKey: 'tn_default',
  jobId: 'job_default',
};

test('buildLegacyRedirectUrl maps old dashboard queries to analysis routes', () => {
  const result = buildLegacyRedirectUrl({
    search:
      '?view=home&tenant_key=tn_demo&job_id=job_demo&brand=QuickCEP&timeframe=specific_day&start_date=20260212&end_date=20260212&date=20260212',
    defaults,
  });

  assert.equal(
    result,
    '/dashboard/tn_demo/job_demo?brand=QuickCEP&timeframe=specific_day&start_date=20260212&end_date=20260212',
  );
});

test('buildLegacyRedirectUrl keeps job_id as a task status filter', () => {
  const result = buildLegacyRedirectUrl({
    search: '?view=task-status&tenant_key=tn_demo&job_id=job_filter&include_deleted=true',
    defaults,
  });

  assert.equal(result, '/tasks/tn_demo/status?job_id=job_filter&include_deleted=true');
});

test('buildViewPath uses jobId only for analysis pages', () => {
  assert.equal(
    buildViewPath('trend', { tenantKey: 'tn_demo', jobId: 'job_demo' }),
    '/trend/tn_demo/job_demo',
  );
  assert.equal(
    buildViewPath('task-load', { tenantKey: 'tn_demo', jobId: 'job_demo' }),
    '/tasks/tn_demo/new',
  );
});

test('getViewKeyFromPath returns the selected sidebar key', () => {
  assert.equal(getViewKeyFromPath('/dashboard/tn_demo/job_demo'), 'home');
  assert.equal(getViewKeyFromPath('/tasks/tn_demo/status'), 'task-status');
  assert.equal(getViewKeyFromPath('/unknown/path'), 'home');
});

test('buildRouteSearch removes trend-only filters outside the trend page', () => {
  const result = buildRouteSearch({
    search: '?brand=QuickCEP&job_id=job_filter&include_deleted=true&trend_platform=all&trend_keyword=all',
    nextViewKey: 'task-status',
  });

  assert.equal(result, '?brand=QuickCEP&job_id=job_filter&include_deleted=true');
});
