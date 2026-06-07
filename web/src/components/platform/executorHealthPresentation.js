const DEFAULT_SUMMARY = {
  executorCount: 0,
  activeExecutorCount: 0,
  inactiveExecutorCount: 0,
  pendingTaskCount: 0,
  reservedTaskCount: 0,
  runningTaskCount: 0,
  failedTaskCount: 0,
  retryableFailedTaskCount: 0,
  expiredLeaseTaskCount: 0,
};

const executorHealthMap = {
  active: { label: '正常', variant: 'default' },
  idle: { label: '空闲', variant: 'secondary' },
  inactive: { label: '停用', variant: 'outline' },
  error: { label: '异常', variant: 'destructive' },
};

export const normalizeCollectionHealthResponse = (response) => ({
  summary: {
    ...DEFAULT_SUMMARY,
    ...(response?.data?.summary || {}),
  },
  executors: Array.isArray(response?.data?.executors) ? response.data.executors : [],
  queues: Array.isArray(response?.data?.queues) ? response.data.queues : [],
  failedTasks: Array.isArray(response?.data?.failedTasks) ? response.data.failedTasks : [],
});

export const getExecutorHealthMeta = (status) =>
  executorHealthMap[status] || { label: '未知', variant: 'outline' };

export const formatDateTime = (value) => {
  if (!value) return '未记录';
  return String(value).replace('T', ' ').slice(0, 19);
};

export const formatCount = (value) => Number(value || 0).toLocaleString('zh-CN');
