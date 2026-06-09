import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const sourcePath = resolve(__dirname, '../ProjectListPage.jsx');
const source = readFileSync(sourcePath, 'utf8');

describe('ProjectListPage contract', () => {
  it('provides a platform admin back link to tenant detail', () => {
    assert.match(source, /hasPlatformAdminRole/);
    assert.match(source, /buildPlatformTenantDetailPath/);
    assert.match(source, /返回租户详情/);
  });

  it('labels the route as the project workspace', () => {
    assert.match(source, /工作台 \/ 项目工作台/);
    assert.match(source, />项目工作台</);
  });
});
