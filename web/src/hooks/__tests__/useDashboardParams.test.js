import test from 'node:test';
import assert from 'node:assert/strict';

import { resolveRouteParam } from '../useDashboardParams.js';

test('resolveRouteParam maps placeholder route values to explicit fallbacks only', () => {
  assert.equal(resolveRouteParam('default', '', ['default']), '');
  assert.equal(resolveRouteParam('latest', '', ['latest']), '');
  assert.equal(resolveRouteParam('actual', 'fallback', ['default']), 'actual');
  assert.equal(resolveRouteParam('', 'fallback', ['default']), 'fallback');
});
