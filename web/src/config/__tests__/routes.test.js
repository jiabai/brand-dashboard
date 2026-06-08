import test from 'node:test';
import assert from 'node:assert/strict';

import {
  getRouteByPathSegment,
  getRouteByViewKey,
  getRoutableRoutes,
  getSidebarMenuRoutes,
  getTaskMenuRoutes,
} from '../routes.js';

test('route config describes analysis and tenant routes from one source', () => {
  assert.equal(getRouteByViewKey('home').path, '/dashboard/:tenantKey/:jobId');
  assert.equal(getRouteByViewKey('snapshots').path, '/snapshots/:tenantKey/:jobId');
  assert.equal(getRouteByPathSegment('snapshots').viewKey, 'snapshots');
  assert.equal(getRouteByViewKey('projects').path, '/projects/:tenantKey');
  assert.equal(getRouteByViewKey('project-detail').path, '/projects/:tenantKey/:projectId');
  assert.equal(getRouteByViewKey('project-quality').path, '/projects/:tenantKey/:projectId/quality');
  assert.equal(getRouteByViewKey('accounts').path, '/accounts/:tenantKey');
  assert.equal(getRouteByViewKey('accounts').requiresJobId, false);
  assert.equal(getRouteByPathSegment('dashboard').viewKey, 'home');
  assert.equal(getRouteByPathSegment('projects').viewKey, 'projects');
});

test('route config separates task menu and main sidebar menu', () => {
  assert.deepEqual(
    getTaskMenuRoutes().map((route) => route.viewKey),
    ['task-load', 'task-status'],
  );
  assert.ok(getSidebarMenuRoutes().some((route) => route.viewKey === 'settings' && route.disabled));
});

test('only routable route entries are exposed to App route generation', () => {
  assert.deepEqual(
    getRoutableRoutes().map((route) => route.viewKey),
    [
      'projects',
      'project-detail',
      'project-quality',
      'home',
      'trend',
      'platforms',
      'sources',
      'sentiment',
      'snapshots',
      'accounts',
      'task-load',
      'task-status',
    ],
  );
});
