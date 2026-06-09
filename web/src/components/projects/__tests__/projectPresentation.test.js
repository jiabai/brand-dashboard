import test from 'node:test';
import assert from 'node:assert/strict';

import {
  PROJECT_NAV_SOURCE_PLATFORM_TENANT_DETAIL,
  buildProjectDataQualityPath,
  buildProjectDetailPath,
  buildProjectListPath,
  getProjectStatusMeta,
  normalizeProjectNavigationSource,
  normalizeProjectDataQualityResponse,
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

test('buildProjectListPath encodes tenant workspace path', () => {
  assert.equal(
    buildProjectListPath({ tenantKey: 'tn space' }),
    '/projects/tn%20space',
  );
  assert.equal(buildProjectListPath({ tenantKey: '' }), '');
});

test('buildProjectDetailPath encodes tenant and project segments', () => {
  assert.equal(
    buildProjectDetailPath({ tenantKey: 'tn space', projectId: 'proj space' }),
    '/projects/tn%20space/proj%20space',
  );
  assert.equal(
    buildProjectDetailPath({
      tenantKey: 'tn space',
      projectId: 'proj space',
      source: PROJECT_NAV_SOURCE_PLATFORM_TENANT_DETAIL,
    }),
    '/projects/tn%20space/proj%20space?from=platform-tenant-detail',
  );
  assert.equal(buildProjectDetailPath({ tenantKey: '', projectId: 'proj_1' }), '');
});

test('buildProjectDataQualityPath appends quality segment', () => {
  assert.equal(
    buildProjectDataQualityPath({ tenantKey: 'tn space', projectId: 'proj space' }),
    '/projects/tn%20space/proj%20space/quality',
  );
  assert.equal(
    buildProjectDataQualityPath({
      tenantKey: 'tn space',
      projectId: 'proj space',
      source: PROJECT_NAV_SOURCE_PLATFORM_TENANT_DETAIL,
    }),
    '/projects/tn%20space/proj%20space/quality?from=platform-tenant-detail',
  );
});

test('normalizes project navigation source to known values only', () => {
  assert.equal(
    normalizeProjectNavigationSource('platform-tenant-detail'),
    PROJECT_NAV_SOURCE_PLATFORM_TENANT_DETAIL,
  );
  assert.equal(normalizeProjectNavigationSource('external'), '');
});

test('normalizes project data quality with stable defaults', () => {
  const result = normalizeProjectDataQualityResponse({
    summary: {
      failed_collection_task_count: 2,
      retryable_failed_collection_task_count: 1,
      stale_analysis_run_count: 1,
      recomputable_analysis_run_count: 1,
      analysis_fact_count: 3,
      analysis_dimension_count: 1,
      analysis_coverage_rate: 0.75,
    },
    metric_coverage: {
      data_source: 'analysis_fact',
      analysis_coverage_rate: 0.75,
      expected_task_count: 4,
      succeeded_task_count: 3,
      failed_task_count: 1,
    },
    failed_collection_tasks: [{ collection_task_id: 'task_failed', can_retry: true }],
    stale_analysis_runs: [{ analysis_run_id: 'analysis_stale', can_recompute: true }],
    recompute_actions: [{ analysis_run_id: 'analysis_stale', enabled: true }],
  });

  assert.equal(result.summary.failedCollectionTaskCount, 2);
  assert.equal(result.summary.analysisCoverageLabel, '75.0%');
  assert.equal(result.summary.analysisFactCount, 3);
  assert.equal(result.metricCoverage.expectedTaskCount, 4);
  assert.equal(result.failedCollectionTasks[0].collectionTaskId, 'task_failed');
  assert.equal(result.staleAnalysisRuns[0].analysisRunId, 'analysis_stale');
  assert.equal(result.recomputeActions[0].analysisRunId, 'analysis_stale');

  const empty = normalizeProjectDataQualityResponse({});
  assert.equal(empty.summary.analysisCoverageLabel, '覆盖率待计算');
  assert.deepEqual(empty.failedCollectionTasks, []);
});
