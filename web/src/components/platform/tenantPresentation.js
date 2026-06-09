import { buildViewPath } from '../../utils/routing.js';

const DEFAULT_PAGINATION = {
  page: 1,
  pageSize: 20,
  total: 0,
  totalPages: 0,
};

const tenantStatusMap = {
  active: { label: '启用', variant: 'default' },
  inactive: { label: '未启用', variant: 'secondary' },
  suspended: { label: '已暂停', variant: 'destructive' },
};

const adminStatusMap = {
  pending_activation: '待激活',
  active: '已激活',
  inactive: '未启用',
  suspended: '已暂停',
};

const planTypeMap = {
  trial: '试用版',
  basic: '基础版',
  pro: '专业版',
  enterprise: '企业版',
};

const billingCycleMap = {
  monthly: '按月',
  yearly: '按年',
};

const queryJobStatusMap = {
  0: { label: '未生效', variant: 'secondary' },
  1: { label: '生效中', variant: 'default' },
  2: { label: '已完成', variant: 'secondary' },
  3: { label: '已失效', variant: 'destructive' },
};

const emailDeliveryStatusMap = {
  sent: {
    title: '激活邮件已发送',
    description: (to) => `已发送至 ${to}。`,
    variant: 'default',
  },
  not_configured: {
    title: 'SMTP 未配置',
    description: (to) => `尚未自动发送至 ${to}，请复制激活链接人工发送。`,
    variant: 'destructive',
  },
  failed: {
    title: '激活邮件发送失败',
    description: (to) => `未能自动发送至 ${to}，请复制激活链接人工发送。`,
    variant: 'destructive',
  },
};

const toPositiveInt = (value, fallback) => {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
};

const stripEmpty = (payload) =>
  Object.fromEntries(
    Object.entries(payload).filter(([, value]) => value !== '' && value !== undefined && value !== null),
  );

export const normalizeTenantListResponse = (response) => ({
  items: Array.isArray(response?.data?.items) ? response.data.items : [],
  pagination: {
    ...DEFAULT_PAGINATION,
    ...(response?.data?.pagination || {}),
  },
});

export const normalizeTenantDetailResponse = (response) => {
  const data = response?.data;
  if (!data || typeof data !== 'object') {
    return { tenant: null, projects: [] };
  }
  const { projects, ...tenant } = data;
  return {
    tenant,
    projects: Array.isArray(projects) ? projects : [],
  };
};

export const getTenantStatusMeta = (status) =>
  tenantStatusMap[status] || { label: status || '未知', variant: 'outline' };

export const getAdminStatusLabel = (status) => adminStatusMap[status] || status || '未知';

export const getPlanTypeLabel = (planType) => planTypeMap[planType] || '未设置';

export const getBillingCycleLabel = (billingCycle) => billingCycleMap[billingCycle] || '未设置';

export const readTenantFiltersFromSearch = (search = '') => {
  const params = new URLSearchParams(search);
  return {
    q: params.get('q') || '',
    status: params.get('status') || '',
    planType: params.get('planType') || '',
    page: toPositiveInt(params.get('page'), 1),
    pageSize: toPositiveInt(params.get('pageSize'), 20),
  };
};

export const prepareTenantCreatePayload = (values = {}) =>
  stripEmpty({
    ...values,
    maxUsers: values.maxUsers ? Number(values.maxUsers) : undefined,
  });

export const buildTenantTaskStatusPath = (tenantKey) =>
  buildViewPath('task-status', { tenantKey });

export const buildPlatformTenantDetailPath = (tenantKey) => {
  const nextTenantKey = String(tenantKey || '').trim();
  if (!nextTenantKey) return '';
  return `/platform/tenants/${encodeURIComponent(nextTenantKey)}`;
};

export const buildPlatformTenantProjectOverviewPath = (tenantKey) => {
  const detailPath = buildPlatformTenantDetailPath(tenantKey);
  return detailPath ? `${detailPath}#project-overview` : '';
};

export const buildTenantDashboardPath = (tenant) => {
  const tenantKey = tenant?.tenantKey || '';
  const jobId = tenant?.latestJob?.jobId || '';
  if (!tenantKey || !jobId) return '';
  const path = buildViewPath('home', { tenantKey, jobId });
  const brand = tenant?.latestJob?.brand || '';
  if (!brand) return path;
  const params = new URLSearchParams({ brand });
  return `${path}?${params.toString()}`;
};

export const getQueryJobStatusMeta = (status) =>
  queryJobStatusMap[Number(status)] || { label: '未知', variant: 'outline' };

export const getEmailDeliveryMeta = (delivery) => {
  const status = delivery?.status;
  const to = delivery?.to || '管理员邮箱';
  const meta = emailDeliveryStatusMap[status];
  if (!meta) {
    return {
      title: '激活邮件状态未知',
      description: '请复制激活链接人工确认发送状态。',
      variant: 'default',
    };
  }
  return {
    title: meta.title,
    description: meta.description(to),
    variant: meta.variant,
  };
};

export const formatDate = (value) => {
  if (!value) return '未设置';
  return String(value).slice(0, 10);
};
