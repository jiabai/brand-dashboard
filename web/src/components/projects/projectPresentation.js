const encodePathSegment = (value) => encodeURIComponent(String(value || '').trim());

const toCount = (value) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
};

const toRate = (value) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
};

const formatRate = (value) => {
  const rate = toRate(value);
  if (rate === null) return '覆盖率待生成';
  return `${(rate * 100).toFixed(1)}%`;
};

export const normalizeProjectListResponse = (response) => {
  const projects = Array.isArray(response?.projects) ? response.projects : [];
  return {
    count: Number.isFinite(response?.count) ? response.count : projects.length,
    projects,
  };
};

export const normalizeProjectDetailResponse = (response) => {
  const project = response?.project;
  if (!project || typeof project !== 'object') {
    return null;
  }

  return {
    ...project,
    brands: Array.isArray(project.brands) ? project.brands : [],
    prompt_sets: Array.isArray(project.prompt_sets)
      ? project.prompt_sets.map((promptSet) => ({
        ...promptSet,
        items: Array.isArray(promptSet.items) ? promptSet.items : [],
      }))
      : [],
  };
};

export const getProjectStatusMeta = (status) => {
  const normalized = String(status || '').trim();
  const map = {
    active: { label: '运行中', variant: 'default' },
    paused: { label: '已暂停', variant: 'secondary' },
    archived: { label: '已归档', variant: 'outline' },
    draft: { label: '配置中', variant: 'secondary' },
  };
  return map[normalized] || { label: normalized || '未知', variant: 'secondary' };
};

export const buildProjectListPath = ({ tenantKey } = {}) => {
  const nextTenantKey = String(tenantKey || '').trim();
  if (!nextTenantKey) return '';
  return `/projects/${encodePathSegment(nextTenantKey)}`;
};

export const buildProjectDetailPath = ({ tenantKey, projectId } = {}) => {
  const nextTenantKey = String(tenantKey || '').trim();
  const nextProjectId = String(projectId || '').trim();
  if (!nextTenantKey || !nextProjectId) return '';
  return `/projects/${encodePathSegment(nextTenantKey)}/${encodePathSegment(nextProjectId)}`;
};

export const buildProjectDataQualityPath = ({ tenantKey, projectId } = {}) => {
  const detailPath = buildProjectDetailPath({ tenantKey, projectId });
  return detailPath ? `${detailPath}/quality` : '';
};

export const countProjectBrandsByRole = (brands = []) => {
  const items = Array.isArray(brands) ? brands : [];
  return items.reduce(
    (acc, brand) => {
      const role = brand?.role || 'watch_only';
      if (role === 'target') acc.target += 1;
      else if (role === 'competitor') acc.competitor += 1;
      else acc.watchOnly += 1;
      return acc;
    },
    { target: 0, competitor: 0, watchOnly: 0 },
  );
};

export const normalizeProjectDataQualityResponse = (response = {}) => {
  const summary = response?.summary || {};
  const metricCoverage = response?.metric_coverage || {};
  const failedCollectionTasks = Array.isArray(response?.failed_collection_tasks)
    ? response.failed_collection_tasks
    : [];
  const staleAnalysisRuns = Array.isArray(response?.stale_analysis_runs)
    ? response.stale_analysis_runs
    : [];
  const recomputeActions = Array.isArray(response?.recompute_actions)
    ? response.recompute_actions
    : [];

  return {
    projectId: response?.project_id || '',
    summary: {
      failedCollectionTaskCount: toCount(summary.failed_collection_task_count),
      retryableFailedCollectionTaskCount: toCount(
        summary.retryable_failed_collection_task_count,
      ),
      staleAnalysisRunCount: toCount(summary.stale_analysis_run_count),
      recomputableAnalysisRunCount: toCount(summary.recomputable_analysis_run_count),
      metricSnapshotCount: toCount(summary.metric_snapshot_count),
      metricDimensionCount: toCount(summary.metric_dimension_count),
      metricCoverageRate: toRate(summary.metric_coverage_rate),
      metricCoverageLabel: formatRate(summary.metric_coverage_rate),
    },
    metricCoverage: {
      dataSource: metricCoverage.data_source || 'empty',
      snapshotStatus: metricCoverage.snapshot_status || 'missing',
      metricDefinitionVersion: metricCoverage.metric_definition_version || 'brand_metrics_v1',
      analysisRunId: metricCoverage.analysis_run_id || '',
      generatedAt: metricCoverage.metric_generated_at || '',
      coverageRate: toRate(metricCoverage.metric_coverage_rate),
      coverageLabel: formatRate(metricCoverage.metric_coverage_rate),
      expectedTaskCount: toCount(metricCoverage.metric_expected_task_count),
      succeededTaskCount: toCount(metricCoverage.metric_succeeded_task_count),
      failedTaskCount: toCount(metricCoverage.metric_failed_task_count),
      analyzedAnswerCount: toCount(metricCoverage.metric_analyzed_answer_count),
      snapshotCount: toCount(metricCoverage.metric_snapshot_count),
      dimensionCount: toCount(metricCoverage.metric_dimension_count),
    },
    failedCollectionTasks: failedCollectionTasks.map((item) => ({
      collectionTaskId: item.collection_task_id || '',
      collectionJobId: item.collection_job_id || '',
      platform: item.platform || '',
      keyword: item.keyword || '',
      queryContent: item.query_content || '',
      status: item.status || '',
      attemptCount: toCount(item.attempt_count),
      maxAttempts: toCount(item.max_attempts),
      canRetry: Boolean(item.can_retry),
      lastErrorCode: item.last_error_code || '',
      lastErrorMessage: item.last_error_message || '',
      leaseOwner: item.lease_owner || '',
      updatedAt: item.updated_at || '',
    })),
    staleAnalysisRuns: staleAnalysisRuns.map((item) => ({
      analysisRunId: item.analysis_run_id || '',
      collectionJobId: item.collection_job_id || '',
      status: item.status || '',
      staleAt: item.stale_at || '',
      errorCode: item.error_code || '',
      errorMessage: item.error_message || '',
      canRecompute: Boolean(item.can_recompute),
      recomputeEndpoint: item.recompute_endpoint || '',
    })),
    recomputeActions: recomputeActions.map((item) => ({
      actionType: item.action_type || '',
      analysisRunId: item.analysis_run_id || '',
      label: item.label || '',
      method: item.method || 'POST',
      endpoint: item.endpoint || '',
      enabled: Boolean(item.enabled),
    })),
  };
};
