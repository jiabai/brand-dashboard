import test from 'node:test';
import assert from 'node:assert/strict';

import {
  buildProjectDetailPath,
  getProjectStatusMeta,
  normalizeProjectDetailResponse,
  normalizeProjectListResponse,
} from '../projectPresentation.js';

test('normalizes project list responses with stable defaults', () => {
  assert.deepEqual(
    normalizeProjectListResponse({
      success: true,
      count: 1,
      projects: [{ project_id: 'proj_1', name: 'Alpha' }],
    }),
    {
      count: 1,
      projects: [{ project_id: 'proj_1', name: 'Alpha' }],
    },
  );

  assert.deepEqual(normalizeProjectListResponse({}), {
    count: 0,
    projects: [],
  });
});

test('normalizes project detail responses with config collections', () => {
  assert.deepEqual(
    normalizeProjectDetailResponse({
      project: {
        project_id: 'proj_1',
        name: 'Alpha',
        brands: [{ brand_id: 'brand_1' }],
        prompt_sets: [{ prompt_set_id: 'ps_1', items: [{ prompt_item_id: 'pi_1' }] }],
      },
    }),
    {
      project_id: 'proj_1',
      name: 'Alpha',
      brands: [{ brand_id: 'brand_1' }],
      prompt_sets: [{ prompt_set_id: 'ps_1', items: [{ prompt_item_id: 'pi_1' }] }],
    },
  );

  assert.equal(normalizeProjectDetailResponse({}), null);
});

test('maps project status for badges', () => {
  assert.deepEqual(getProjectStatusMeta('active'), { label: '运行中', variant: 'default' });
  assert.deepEqual(getProjectStatusMeta('paused'), { label: '已暂停', variant: 'secondary' });
  assert.deepEqual(getProjectStatusMeta('archived'), { label: '已归档', variant: 'outline' });
  assert.deepEqual(getProjectStatusMeta('draft'), { label: '配置中', variant: 'secondary' });
  assert.deepEqual(getProjectStatusMeta('unknown'), { label: 'unknown', variant: 'secondary' });
});

test('buildProjectDetailPath encodes tenant and project segments', () => {
  assert.equal(
    buildProjectDetailPath({ tenantKey: 'tn space', projectId: 'proj space' }),
    '/projects/tn%20space/proj%20space',
  );
  assert.equal(buildProjectDetailPath({ tenantKey: '', projectId: 'proj_1' }), '');
});
