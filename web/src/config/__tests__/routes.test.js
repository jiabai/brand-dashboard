import test from 'node:test';
import assert from 'node:assert/strict';

import * as routeConfig from '../routes.js';
import {
  DEFAULT_VIEW_KEY,
  getRouteByPathSegment,
  getRouteByViewKey,
  getRoutableRoutes,
  getSidebarMenuRoutes,
  getTaskMenuRoutes,
} from '../routes.js';

test('route config describes analysis and tenant routes from one source', () => {
  assert.equal(DEFAULT_VIEW_KEY, 'projects');
  assert.equal(getRouteByViewKey('home').path, '/dashboard/:tenantKey/:jobId');
  assert.equal(getRouteByViewKey('snapshots').path, '/snapshots/:tenantKey/:jobId');
  assert.equal(getRouteByPathSegment('snapshots').viewKey, 'snapshots');
  assert.equal(getRouteByViewKey('projects').path, '/projects/:tenantKey');
  assert.equal(getRouteByViewKey('project-detail').path, '/projects/:tenantKey/:projectId');
  assert.equal(getRouteByViewKey('project-quality').path, '/projects/:tenantKey/:projectId/quality');
  assert.equal(getRouteByViewKey('accounts').path, '/accounts/:tenantKey');
  assert.equal(getRouteByViewKey('accounts').requiresJobId, false);
  assert.equal(getRouteByPathSegment('projects').viewKey, 'projects');
});

test('route config keeps the main sidebar project-first', () => {
  assert.deepEqual(
    getSidebarMenuRoutes().map((route) => route.viewKey),
    ['projects', 'accounts'],
  );
  assert.deepEqual(getTaskMenuRoutes(), []);
});

test('legacy job and task routes remain routable for compatibility', () => {
  assert.equal(getRouteByPathSegment('dashboard').viewKey, 'home');
  assert.deepEqual(
    getRoutableRoutes()
      .filter((route) => route.menuSection === 'legacy')
      .map((route) => route.viewKey),
    ['home', 'trend', 'platforms', 'sources', 'sentiment', 'snapshots', 'task-load', 'task-status'],
  );
});

test('route policy preserves historical assets without restoring legacy product shape', () => {
  assert.equal(typeof routeConfig.getProductShapeRoutes, 'function');
  assert.equal(typeof routeConfig.getLegacyCompatibilityRoutes, 'function');

  assert.deepEqual(
    routeConfig.getProductShapeRoutes().map((route) => route.viewKey),
    ['projects', 'project-detail', 'project-quality', 'accounts'],
  );
  assert.deepEqual(
    routeConfig.getProductShapeRoutes()
      .filter((route) => route.requiresJobId)
      .map((route) => route.viewKey),
    [],
  );
  assert.deepEqual(
    routeConfig.getLegacyCompatibilityRoutes().map((route) => route.viewKey),
    ['home', 'trend', 'platforms', 'sources', 'sentiment', 'snapshots', 'task-load', 'task-status'],
  );
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
