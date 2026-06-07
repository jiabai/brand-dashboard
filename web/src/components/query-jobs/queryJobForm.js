import dayjs from 'dayjs';

export const LEGACY_PROJECT_VALUE = '__legacy_unlinked__';

export const createInitialQueryJobForm = ({ tenantKey, executorId, projectId = '' } = {}) => ({
  tenant_key: tenantKey || '',
  project_id: projectId || '',
  job_id: '',
  executor_id: executorId || '',
  last_executed_date: dayjs().format('YYYY-MM-DD'),
  effective_from: dayjs().startOf('day').format('YYYY-MM-DDTHH:mm'),
  effective_to: '',
  total_runs: 15,
  executed_runs: 0,
  data: {
    category: '',
    brand: '',
    competitor: [''],
    content: [
      {
        keyword: '',
        query_content: [''],
      },
    ],
  },
});

export const normalizeProjectId = (value) => {
  const normalized = String(value || '').trim();
  return normalized === LEGACY_PROJECT_VALUE ? '' : normalized;
};

export const normalizeProjectOptions = (response) =>
  (Array.isArray(response?.projects) ? response.projects : [])
    .filter((project) => project?.project_id)
    .map((project) => ({
      value: project.project_id,
      label: project.name || project.project_id,
      status: project.status || '',
    }));

const formatDateTime = (value) => (value ? dayjs(value).format('YYYY-MM-DDTHH:mm:ss') : undefined);

export const normalizeQueryJobPayload = (values) => {
  const projectId = normalizeProjectId(values.project_id);
  const payload = {
    ...values,
    effective_from: formatDateTime(values.effective_from),
    effective_to: formatDateTime(values.effective_to),
    last_executed_date: values.last_executed_date || dayjs().format('YYYY-MM-DD'),
    total_runs: Number(values.total_runs || 15),
    executed_runs: Number(values.executed_runs || 0),
    data: {
      category: values.data.category.trim(),
      brand: values.data.brand.trim(),
      competitor: values.data.competitor.map((item) => item.trim()).filter(Boolean),
      content: values.data.content
        .map((item) => ({
          keyword: item.keyword.trim(),
          query_content: item.query_content.map((query) => query.trim()).filter(Boolean),
        }))
        .filter((item) => item.keyword && item.query_content.length),
    },
  };

  if (projectId) {
    payload.project_id = projectId;
  } else {
    delete payload.project_id;
  }

  return payload;
};

export const validateQueryJobForm = (values) => {
  const errors = [];
  const payload = normalizeQueryJobPayload(values);

  if (!payload.tenant_key) errors.push('请输入租户标识 Key');
  if (!payload.job_id) errors.push('请输入任务 ID');
  if (!payload.executor_id) errors.push('请输入执行器 ID');
  if (!payload.last_executed_date) errors.push('请选择最近执行日期');
  if (!payload.effective_from) errors.push('请选择生效开始时间');
  if (payload.total_runs < 1) errors.push('总执行次数必须大于 0');
  if (payload.executed_runs < 0) errors.push('已执行次数不能小于 0');
  if (payload.executed_runs > payload.total_runs) errors.push('已执行次数不能大于总执行次数');
  if (!payload.data.category) errors.push('请输入分类名称');
  if (!payload.data.brand) errors.push('请输入品牌名称');
  if (!payload.data.competitor.length) errors.push('至少需要一个竞品名称');
  if (!payload.data.content.length) errors.push('至少需要一个有效内容项和查询语句');

  return { errors, payload };
};
