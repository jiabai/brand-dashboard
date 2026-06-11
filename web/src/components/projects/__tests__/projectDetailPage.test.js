import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const sourcePath = resolve(__dirname, '../ProjectDetailPage.jsx');
const source = readFileSync(sourcePath, 'utf8');

describe('ProjectDetailPage contract', () => {
  it('returns to project overview when opened from platform tenant detail', () => {
    assert.match(source, /readProjectNavigationSource/);
    assert.match(source, /PROJECT_NAV_SOURCE_PLATFORM_TENANT_DETAIL/);
    assert.match(source, /buildPlatformTenantProjectOverviewPath/);
    assert.match(source, /返回项目概览/);
  });

  it('keeps project workspace as the default return target', () => {
    assert.match(source, /buildProjectListPath/);
    assert.match(source, /返回项目工作台/);
  });
});

describe('ProjectDetailPage dashboard entry contract', () => {
  it('exposes an enter-dashboard button that opens a job picker sheet', () => {
    assert.match(source, /进入看板/);
    assert.match(source, /fetchQueryJobStatus/);
    assert.match(source, /projectId/);
    assert.match(source, /normalizeProjectJobRecords/);
    assert.match(source, /SheetContent/);
  });

  it('navigates to the legacy dashboard for the selected job', () => {
    assert.match(source, /buildProjectDashboardPath/);
    assert.match(source, /getQueryJobStatusMeta/);
    assert.match(source, /该项目还没有采集任务/);
  });
});
