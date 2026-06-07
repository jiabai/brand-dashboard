import test from 'node:test';
import assert from 'node:assert/strict';

import {
  LEGACY_PROJECT_VALUE,
  createInitialQueryJobForm,
  normalizeProjectOptions,
  normalizeQueryJobPayload,
  validateQueryJobForm,
} from '../queryJobForm.js';

test('normalizes query job payload with selected project id', () => {
  const values = createInitialQueryJobForm({
    tenantKey: 'tn_demo',
    executorId: 'exec_demo',
    projectId: ' proj_1 ',
  });
  values.job_id = 'job_1';
  values.data.category = ' 手机 ';
  values.data.brand = ' Atlas ';
  values.data.competitor = [' Northstar ', ''];
  values.data.content = [
    {
      keyword: ' 续航 ',
      query_content: [' 哪款手机适合长时间出差？ ', ''],
    },
  ];

  const payload = normalizeQueryJobPayload(values);

  assert.equal(payload.project_id, 'proj_1');
  assert.equal(payload.data.category, '手机');
  assert.deepEqual(payload.data.competitor, ['Northstar']);
  assert.deepEqual(payload.data.content, [
    {
      keyword: '续航',
      query_content: ['哪款手机适合长时间出差？'],
    },
  ]);
});

test('omits project id for legacy unlinked query jobs', () => {
  const values = createInitialQueryJobForm({
    tenantKey: 'tn_demo',
    executorId: 'exec_demo',
    projectId: LEGACY_PROJECT_VALUE,
  });
  values.job_id = 'job_legacy';
  values.data.category = '手机';
  values.data.brand = 'Atlas';
  values.data.competitor = ['Northstar'];
  values.data.content = [{ keyword: '续航', query_content: ['哪款手机适合长时间出差？'] }];

  const payload = normalizeQueryJobPayload(values);

  assert.equal(Object.hasOwn(payload, 'project_id'), false);
});

test('normalizes project list into select options', () => {
  assert.deepEqual(
    normalizeProjectOptions({
      projects: [
        { project_id: 'proj_1', name: '夏季竞品监测', status: 'active' },
        { project_id: '', name: 'Invalid', status: 'active' },
      ],
    }),
    [
      {
        value: 'proj_1',
        label: '夏季竞品监测',
        status: 'active',
      },
    ],
  );
});

test('validates query job form after payload normalization', () => {
  const values = createInitialQueryJobForm({ tenantKey: 'tn_demo', executorId: 'exec_demo' });
  values.job_id = 'job_1';
  values.data.category = '手机';
  values.data.brand = 'Atlas';
  values.data.competitor = ['Northstar'];
  values.data.content = [{ keyword: '续航', query_content: ['哪款手机适合长时间出差？'] }];

  const { errors, payload } = validateQueryJobForm(values);

  assert.deepEqual(errors, []);
  assert.equal(payload.tenant_key, 'tn_demo');
  assert.equal(payload.job_id, 'job_1');
});
