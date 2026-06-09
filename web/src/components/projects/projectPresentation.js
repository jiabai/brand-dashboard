const encodePathSegment = (value) => encodeURIComponent(String(value || '').trim());
export const PROJECT_NAV_SOURCE_PLATFORM_TENANT_DETAIL = 'platform-tenant-detail';

const projectNavigationSources = new Set([
  PROJECT_NAV_SOURCE_PLATFORM_TENANT_DETAIL,
]);

export const normalizeProjectNavigationSource = (source) => {
  const normalized = String(source || '').trim();
  return projectNavigationSources.has(normalized) ? normalized : '';
};

export const readProjectNavigationSource = (searchParams) => {
  if (!searchParams?.get) return '';
  return normalizeProjectNavigationSource(searchParams.get('from'));
};

const appendProjectNavigationSource = (path, source) => {
  const normalizedSource = normalizeProjectNavigationSource(source);
  if (!path || !normalizedSource) return path;
  const params = new URLSearchParams({ from: normalizedSource });
  return `${path}?${params.toString()}`;
};

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
  if (rate === null) return '覆盖率待计算';
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

export const buildProjectDetailPath = ({ tenantKey, projectId, source } = {}) => {
  const nextTenantKey = String(tenantKey || '').trim();
  const nextProjectId = String(projectId || '').trim();
  if (!nextTenantKey || !nextProjectId) return '';
  const path = `/projects/${encodePathSegment(nextTenantKey)}/${encodePathSegment(nextProjectId)}`;
  return appendProjectNavigationSource(path, source);
};

export const buildProjectDataQualityPath = ({ tenantKey, projectId, source } = {}) => {
  const nextTenantKey = String(tenantKey || '').trim();
  const nextProjectId = String(projectId || '').trim();
  if (!nextTenantKey || !nextProjectId) return '';
  const path = `/projects/${encodePathSegment(nextTenantKey)}/${encodePathSegment(nextProjectId)}/quality`;
  return appendProjectNavigationSource(path, source);
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
      analysisFactCount: toCount(summary.analysis_fact_count),
      analysisDimensionCount: toCount(summary.analysis_dimension_count),
      analysisCoverageRate: toRate(summary.analysis_coverage_rate),
      analysisCoverageLabel: formatRate(summary.analysis_coverage_rate),
    },
    metricCoverage: {
      dataSource: metricCoverage.data_source || 'empty',
      coverageStatus: metricCoverage.coverage_status || 'missing',
      metricDefinitionVersion: metricCoverage.metric_definition_version || 'brand_metrics_v1',
      analysisRunId: metricCoverage.analysis_run_id || '',
      analysisFinishedAt: metricCoverage.analysis_finished_at || '',
      coverageRate: toRate(metricCoverage.analysis_coverage_rate),
      coverageLabel: formatRate(metricCoverage.analysis_coverage_rate),
      expectedTaskCount: toCount(metricCoverage.expected_task_count),
      succeededTaskCount: toCount(metricCoverage.succeeded_task_count),
      failedTaskCount: toCount(metricCoverage.failed_task_count),
      analyzedAnswerCount: toCount(metricCoverage.analyzed_answer_count),
      analysisFactCount: toCount(metricCoverage.analysis_fact_count),
      dimensionCount: toCount(metricCoverage.analysis_dimension_count),
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
