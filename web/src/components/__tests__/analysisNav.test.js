import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';
import assert from 'node:assert/strict';

const analysisNavSource = () =>
  readFileSync(join(import.meta.dirname, '..', 'AnalysisNav.jsx'), 'utf8');

test('analysis nav renders tabs from the shared analysis route source', () => {
  const source = analysisNavSource();
  assert.match(source, /getAnalysisNavRoutes/);
  assert.match(source, /useDashboardParams/);
  assert.match(source, /buildViewPath/);
  assert.match(source, /buildRouteSearch/);
  assert.match(source, /getViewKeyFromPath/);
  assert.match(source, /NavLink/);
});
