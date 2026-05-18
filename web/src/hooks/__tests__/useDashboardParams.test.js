import test from 'node:test';
import assert from 'node:assert/strict';

import { resolveRouteParam } from '../useDashboardParams.js';

test('resolveRouteParam maps placeholder route values to environment defaults', () => {
  assert.equal(resolveRouteParam('default', 'tenant-from-env', ['default']), 'tenant-from-env');
  assert.equal(resolveRouteParam('latest', 'job-from-env', ['latest']), 'job-from-env');
  assert.equal(resolveRouteParam('actual', 'fallback', ['default']), 'actual');
  assert.equal(resolveRouteParam('', 'fallback', ['default']), 'fallback');
});
