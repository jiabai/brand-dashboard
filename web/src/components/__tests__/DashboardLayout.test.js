import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';
import assert from 'node:assert/strict';

const dashboardLayoutSource = () =>
  readFileSync(
    join(import.meta.dirname, '..', 'DashboardLayout.jsx'),
    'utf8',
  );

test('dashboard header exposes current account and readonly customer context', () => {
  const source = dashboardLayoutSource();

  assert.match(source, /isPlatformReadonlyTenantAccess/);
  assert.match(source, /isReadonlyTenantAccess/);
  assert.match(source, /user\?\.email/);
  assert.match(source, /当前账号/);
  assert.match(source, /客户视角/);
  assert.match(source, /activeTenantKey/);
});
