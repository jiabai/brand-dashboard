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

export const formatDate = (value) => {
  if (!value) return '未设置';
  return String(value).slice(0, 10);
};
