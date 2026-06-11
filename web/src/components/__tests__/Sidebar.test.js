import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';
import assert from 'node:assert/strict';

const sidebarSource = () =>
  readFileSync(
    join(import.meta.dirname, '..', 'Sidebar.jsx'),
    'utf8',
  );

test('tenant sidebar hides join team entry for platform readonly tenant access', () => {
  const source = sidebarSource();

  assert.match(source, /useAuth/);
  assert.match(source, /isPlatformReadonlyTenantAccess/);
  assert.match(source, /visibleMenuItems/);
  assert.match(source, /viewKey\s*!==\s*['"]accounts['"]/);
  assert.match(source, /items=\{visibleMenuItems\}/);
});
