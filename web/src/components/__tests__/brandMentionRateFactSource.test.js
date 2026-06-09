import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const sourcePath = resolve(__dirname, '../BrandMentionRate.jsx');
const source = readFileSync(sourcePath, 'utf8');

const removedModuleName = 'metric' + 'Snapshot' + 'Metadata';
const removedNormalizerName = 'normalize' + 'Metric' + 'Snapshot' + 'Metadata';

describe('BrandMentionRate fact source presentation', () => {
  it('does not import or render the removed generated metric quality helpers', () => {
    assert(!source.includes(removedModuleName));
    assert(!source.includes(removedNormalizerName));
    assert(!source.includes('snapshotStatus'));
    assert(!source.includes('generatedAt'));
  });

  it('continues to read dashboard metrics directly from API fact aggregation', () => {
    assert(source.includes('fetchBrandMetrics'));
    assert(source.includes('fetchPostCitationRate'));
    assert(source.includes('EmptyState'));
  });
});
