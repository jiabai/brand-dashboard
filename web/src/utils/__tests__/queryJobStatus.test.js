import test from 'node:test';
import assert from 'node:assert/strict';
import { buildQueryJobStatusRowKey } from '../index.js';

test('buildQueryJobStatusRowKey returns a stable key from job identity fields', () => {
  const record = {
    tenant_key: 'tn_demo',
    job_id: 'job_20260517_001',
    brand: 'Demo Brand',
    query_content: 'compare demo brand mentions',
    effective_from: '2026-05-17T10:00:00Z',
  };

  const first = buildQueryJobStatusRowKey(record, 0);
  const second = buildQueryJobStatusRowKey(record, 0);

  assert.equal(first, second);
  assert.match(first, /tn_demo::job_20260517_001/);
});

test('buildQueryJobStatusRowKey falls back to index when identity fields are absent', () => {
  assert.equal(buildQueryJobStatusRowKey({}, 3), 'query-job-3');
});
