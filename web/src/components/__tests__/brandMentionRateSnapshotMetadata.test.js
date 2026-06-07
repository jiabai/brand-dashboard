import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const sourcePath = resolve(__dirname, '../BrandMentionRate.jsx');
const source = readFileSync(sourcePath, 'utf8');

describe('BrandMentionRate snapshot metadata presentation', () => {
  it('renders metric freshness, coverage, and analysis completeness labels', () => {
    assert.match(source, /normalizeMetricSnapshotMetadata/);
    assert.match(source, /指标生成/);
    assert.match(source, /采集覆盖/);
    assert.match(source, /分析完整性/);
    assert.match(source, /快照未生成/);
  });

  it('uses a non-misleading empty state for missing dashboard data', () => {
    assert.match(source, /等待分析和指标快照生成/);
  });
});
