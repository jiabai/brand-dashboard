import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const sourcePath = resolve(__dirname, '../ProjectDataQualityPage.jsx');
const source = readFileSync(sourcePath, 'utf8');

describe('ProjectDataQualityPage contract', () => {
  it('loads quality data and exposes recompute actions', () => {
    assert.match(source, /fetchProjectDataQuality/);
    assert.match(source, /retryAnalysisRun/);
    assert.match(source, /normalizeProjectDataQualityResponse/);
    assert.match(source, /failedCollectionTasks/);
    assert.match(source, /staleAnalysisRuns/);
    assert.match(source, /metricCoverage/);
  });

  it('renders the required data quality sections', () => {
    assert.match(source, /失败采集/);
    assert.match(source, /过期分析/);
    assert.match(source, /指标覆盖率/);
    assert.match(source, /重新分析/);
  });
});
