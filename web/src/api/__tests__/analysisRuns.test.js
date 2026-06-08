import test from 'node:test';
import assert from 'node:assert/strict';

import { retryAnalysisRun } from '../analysisRuns.js';

const jsonResponse = (payload, init = {}) => ({
  ok: init.ok ?? true,
  status: init.status ?? 200,
  json: async () => payload,
  text: async () => JSON.stringify(payload),
});

test.afterEach(() => {
  delete globalThis.fetch;
});

test('retryAnalysisRun posts to the analysis retry endpoint', async () => {
  let request;
  globalThis.fetch = async (url, options) => {
    request = { url, options };
    return jsonResponse({ success: true });
  };

  await retryAnalysisRun({
    tenantKey: 'tn_acme',
    analysisRunId: 'analysis stale',
    retryAnalysisRunId: 'analysis retry',
  });

  assert.equal(request.url, '/api/v1/analysis-runs/analysis%20stale/retry');
  assert.equal(request.options.method, 'POST');
  assert.equal(request.options.headers['X-Tenant-Key'], 'tn_acme');
  assert.equal(
    request.options.body,
    JSON.stringify({ analysis_run_id: 'analysis retry' }),
  );
});
