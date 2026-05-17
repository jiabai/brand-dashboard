import test from 'node:test';
import assert from 'node:assert/strict';
import {
  buildDefaultEntryUrl,
  buildRouteSearch,
  buildViewPath,
  getViewKeyFromPath,
} from '../routing.js';

const defaults = {
  tenantKey: 'tn_default',
  jobId: 'job_default',
};

test('buildDefaultEntryUrl ignores legacy root queries', () => {
  const result = buildDefaultEntryUrl({
    search:
      '?view=trend&timeframe=specific_day&tenant_key=tn_demo&job_id=job_demo&brand=QuickCEP&executor_id=exec_demo&include_deleted=false&start_date=20260212&end_date=20260212&date=20260212',
    defaults,
  });

  assert.equal(result, '/dashboard/tn_default/job_default');
});

test('buildRouteSearch strips legacy identity params on new analysis routes', () => {
  const result = buildRouteSearch({
    search:
      '?timeframe=specific_day&brand=QuickCEP&executor_id=exec_demo&include_deleted=false&start_date=20260212&end_date=20260212&view=home&date=20260212&tenant_key=tn_demo&job_id=job_demo',
    nextViewKey: 'home',
  });

  assert.equal(
    result,
    '?timeframe=specific_day&brand=QuickCEP&start_date=20260212&end_date=20260212',
  );
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
