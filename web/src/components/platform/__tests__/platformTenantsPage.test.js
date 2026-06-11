import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const sourcePath = resolve(__dirname, '../PlatformTenantsPage.jsx');
const source = readFileSync(sourcePath, 'utf8');

describe('PlatformTenantsPage contract', () => {
  it('keeps tenant administrator navigation in the administrator column', () => {
    assert.match(source, /buildPlatformTenantAdminPath/);
    assert.match(source, /handleOpenTenantAdmin/);
    assert.match(source, /adminName/);
    assert.match(source, /adminPhone/);

    const adminStatusIndex = source.indexOf('getAdminStatusLabel(tenant.adminStatus)');
    const actionCellIndex = source.indexOf('<TableCell className="text-right">', adminStatusIndex);
    const adminCellSource = source.slice(adminStatusIndex - 800, actionCellIndex);
    const actionCellSource = source.slice(actionCellIndex, source.indexOf('</TableCell>', actionCellIndex));

    assert.match(adminCellSource, /handleOpenTenantAdmin/);
    assert.match(adminCellSource, /查看/);
    assert.match(actionCellSource, /handleOpenTenantDetail/);
    assert.doesNotMatch(actionCellSource, /handleOpenTenantAdmin/);
    assert.doesNotMatch(actionCellSource, /租户管理员/);
  });
});
