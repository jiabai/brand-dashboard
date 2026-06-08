import test from 'node:test';
import assert from 'node:assert/strict';
import {
  buildRouteSearch,
  buildViewPath,
  getViewKeyFromPath,
} from '../routing.js';

test('buildViewPath uses jobId only for analysis pages', () => {
  assert.equal(
    buildViewPath('projects', { tenantKey: 'tn_demo', jobId: 'job_demo' }),
    '/projects/tn_demo',
  );
  assert.equal(
    buildViewPath('project-detail', {
      tenantKey: 'tn_demo',
      jobId: 'job_demo',
      projectId: 'proj_demo',
    }),
    '/projects/tn_demo/proj_demo',
  );
  assert.equal(
    buildViewPath('project-quality', {
      tenantKey: 'tn_demo',
      jobId: 'job_demo',
      projectId: 'proj_demo',
    }),
    '/projects/tn_demo/proj_demo/quality',
  );
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
  assert.equal(getViewKeyFromPath('/projects/tn_demo'), 'projects');
  assert.equal(getViewKeyFromPath('/projects/tn_demo/proj_demo'), 'projects');
  assert.equal(getViewKeyFromPath('/projects/tn_demo/proj_demo/quality'), 'projects');
  assert.equal(getViewKeyFromPath('/dashboard/tn_demo/job_demo'), 'home');
  assert.equal(getViewKeyFromPath('/tasks/tn_demo/status'), 'task-status');
  assert.equal(getViewKeyFromPath('/unknown/path'), 'projects');
});

test('buildRouteSearch removes trend-only filters outside the trend page', () => {
  const result = buildRouteSearch({
    search: '?brand=QuickCEP&job_id=job_filter&include_deleted=true&trend_platform=all&trend_keyword=all',
    nextViewKey: 'task-status',
  });

  assert.equal(result, '?brand=QuickCEP&job_id=job_filter&include_deleted=true');
});
