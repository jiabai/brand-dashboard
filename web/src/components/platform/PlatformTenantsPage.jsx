import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ListChecks, RefreshCw, Search } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';

import { fetchPlatformTenants } from '../../api/platform.js';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert.jsx';
import { Badge } from '../ui/badge.jsx';
import { Button } from '../ui/button.jsx';
import { Input } from '../ui/input.jsx';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select.jsx';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table.jsx';
import CreateTenantPanel from './CreateTenantPanel.jsx';
import {
  formatDate,
  buildTenantTaskStatusPath,
  getAdminStatusLabel,
  getBillingCycleLabel,
  getPlanTypeLabel,
  getTenantStatusMeta,
  normalizeTenantListResponse,
  readTenantFiltersFromSearch,
} from './tenantPresentation.js';

const statusOptions = [
  { value: 'all', label: '全部状态' },
  { value: 'active', label: '启用' },
  { value: 'inactive', label: '未启用' },
  { value: 'suspended', label: '已暂停' },
];

const planOptions = [
  { value: 'all', label: '全部计划' },
  { value: 'trial', label: '试用版' },
  { value: 'basic', label: '基础版' },
  { value: 'pro', label: '专业版' },
  { value: 'enterprise', label: '企业版' },
];

const buildSearch = (filters) => {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '' || value === 'all') return;
    params.set(key, String(value));
  });
  const query = params.toString();
  return query ? `?${query}` : '';
};

const PlatformTenantsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const filters = useMemo(() => readTenantFiltersFromSearch(location.search), [location.search]);
  const [draftFilters, setDraftFilters] = useState(filters);
  const [tenants, setTenants] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0, totalPages: 0 });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshToken, setRefreshToken] = useState(0);
  const [createResult, setCreateResult] = useState(null);

  useEffect(() => {
    setDraftFilters(filters);
  }, [filters]);

  const loadTenants = useCallback(
    async (signal) => {
      setIsLoading(true);
      setError('');
      try {
        const response = await fetchPlatformTenants(filters, { signal });
        const normalized = normalizeTenantListResponse(response);
        setTenants(normalized.items);
        setPagination(normalized.pagination);
      } catch (loadError) {
        if (loadError.name !== 'AbortError') {
          setError(loadError.message || '租户列表加载失败');
        }
      } finally {
        if (!signal?.aborted) setIsLoading(false);
      }
    },
    [filters],
  );

  useEffect(() => {
    const controller = new AbortController();
    loadTenants(controller.signal);
    return () => controller.abort();
  }, [loadTenants, refreshToken]);

  const applyFilters = (nextFilters) => {
    navigate(`/platform/tenants${buildSearch(nextFilters)}`, { replace: false });
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    applyFilters({
      q: draftFilters.q.trim(),
      status: draftFilters.status,
      planType: draftFilters.planType,
      page: 1,
      pageSize: draftFilters.pageSize,
    });
  };

  const handlePageChange = (nextPage) => {
    applyFilters({ ...filters, page: nextPage });
  };

  const handleCreated = (result) => {
    setCreateResult(result);
    setRefreshToken((current) => current + 1);
  };

  const handleOpenTenantTasks = useCallback(
    (tenant) => {
      if (!tenant?.tenantKey || tenant.status !== 'active') return;
      navigate(buildTenantTaskStatusPath(tenant.tenantKey));
    },
    [navigate],
  );

  return (
    <div className="grid gap-5">
      <section className="flex flex-col gap-4 border-b border-border pb-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0">
          <h1 className="text-2xl font-medium text-foreground">租户管理</h1>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <span>共 {pagination.total} 个租户</span>
            <span className="text-border">/</span>
            <span>第 {pagination.page} 页</span>
          </div>
        </div>
        <CreateTenantPanel onCreated={handleCreated} latestResult={createResult} />
      </section>

      <form className="flex flex-col gap-3 rounded-md border border-border bg-card p-3 lg:flex-row lg:items-center" onSubmit={handleSubmit}>
        <div className="relative min-w-0 flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={draftFilters.q}
            onChange={(event) => setDraftFilters((current) => ({ ...current, q: event.target.value }))}
            className="pl-9"
            placeholder="搜索租户、tenantKey 或管理员邮箱"
          />
        </div>
        <Select
          value={draftFilters.status || 'all'}
          onValueChange={(value) => setDraftFilters((current) => ({ ...current, status: value === 'all' ? '' : value }))}
        >
          <SelectTrigger className="w-full lg:w-36">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              {statusOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
              ))}
            </SelectGroup>
          </SelectContent>
        </Select>
        <Select
          value={draftFilters.planType || 'all'}
          onValueChange={(value) => setDraftFilters((current) => ({ ...current, planType: value === 'all' ? '' : value }))}
        >
          <SelectTrigger className="w-full lg:w-36">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              {planOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
              ))}
            </SelectGroup>
          </SelectContent>
        </Select>
        <Button type="submit">
          <Search className="size-4" />
          查询
        </Button>
        <Button type="button" variant="outline" onClick={() => setRefreshToken((current) => current + 1)}>
          <RefreshCw className="size-4" />
          刷新
        </Button>
      </form>

      {error ? (
        <Alert variant="destructive">
          <AlertTitle>租户列表加载失败</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <section className="grid gap-3">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>租户</TableHead>
              <TableHead>状态</TableHead>
              <TableHead>计划</TableHead>
              <TableHead>管理员</TableHead>
              <TableHead>成员</TableHead>
              <TableHead>合同到期</TableHead>
              <TableHead>创建时间</TableHead>
              <TableHead className="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={8} className="h-24 text-center text-muted-foreground">
                  正在加载租户...
                </TableCell>
              </TableRow>
            ) : tenants.length ? (
              tenants.map((tenant) => {
                const status = getTenantStatusMeta(tenant.status);
                return (
                  <TableRow key={tenant.tenantKey}>
                    <TableCell>
                      <div className="grid gap-1">
                        <span className="font-medium text-foreground">{tenant.tenantName || tenant.tenantKey}</span>
                        <span className="text-xs text-muted-foreground">{tenant.tenantKey}</span>
                        {tenant.companyLegalName ? (
                          <span className="text-xs text-muted-foreground">{tenant.companyLegalName}</span>
                        ) : null}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={status.variant} className="rounded-md">{status.label}</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="grid gap-1">
                        <span>{getPlanTypeLabel(tenant.planType)}</span>
                        <span className="text-xs text-muted-foreground">{getBillingCycleLabel(tenant.billingCycle)}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="grid gap-1">
                        <span>{tenant.adminEmail || '未设置'}</span>
                        <span className="text-xs text-muted-foreground">{getAdminStatusLabel(tenant.adminStatus)}</span>
                      </div>
                    </TableCell>
                    <TableCell>{tenant.memberCount ?? 0} / {tenant.maxUsers || '不限'}</TableCell>
                    <TableCell>{formatDate(tenant.contractEndDate)}</TableCell>
                    <TableCell>{formatDate(tenant.createdAt)}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={tenant.status !== 'active'}
                        onClick={() => handleOpenTenantTasks(tenant)}
                      >
                        <ListChecks className="size-4" />
                        任务状态
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })
            ) : (
              <TableRow>
                <TableCell colSpan={8} className="h-24 text-center text-muted-foreground">
                  没有匹配的租户
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>

        <div className="flex flex-col gap-3 text-sm text-muted-foreground md:flex-row md:items-center md:justify-between">
          <span>
            每页 {pagination.pageSize} 条，共 {pagination.totalPages} 页
          </span>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={isLoading || pagination.page <= 1}
              onClick={() => handlePageChange(pagination.page - 1)}
            >
              上一页
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={isLoading || pagination.page >= pagination.totalPages || pagination.totalPages === 0}
              onClick={() => handlePageChange(pagination.page + 1)}
            >
              下一页
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default PlatformTenantsPage;
