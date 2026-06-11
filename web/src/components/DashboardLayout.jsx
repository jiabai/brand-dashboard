import React, { useCallback, useEffect, useMemo, useState } from 'react';
import dayjs from 'dayjs';
import { CircleDot, LogOut, ShieldCheck, UserCircle } from 'lucide-react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';

import { fetchBrandMetrics } from '@/api';
import TaskName from './TaskName.jsx';
import ThemeToggle from './ThemeToggle.jsx';
import Sidebar from './Sidebar.jsx';
import { useAuth } from '../auth/AuthContext.jsx';
import { isPlatformReadonlyTenantAccess } from '@/auth/platformAccess.js';
import { Badge } from './ui/badge.jsx';
import { Button } from './ui/button.jsx';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select.jsx';
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from './ui/sidebar.jsx';
import { ToggleGroup, ToggleGroupItem } from './ui/toggle-group.jsx';
import { useDashboardParams } from '@/hooks/useDashboardParams';
import { useIsMobile } from '@/hooks/use-mobile';
import { TIME_OPTIONS, useTimeframeManager } from '@/hooks/useTimeframeManager';
import { buildRouteSearch, buildViewPath, getViewKeyFromPath, isAnalysisView } from '@/utils/routing';

const LiveClock = React.memo(function LiveClock() {
  const [currentTime, setCurrentTime] = useState(() => new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 30000);

    return () => clearInterval(timer);
  }, []);

  return (
    <span className="text-xs text-muted-foreground">
      更新: {currentTime.toLocaleTimeString()}
    </span>
  );
});

const DatePickerControl = ({ label, value, onChange }) => (
  <div className="flex items-center gap-2">
    <label className="text-xs font-medium text-muted-foreground">
      {label}
    </label>
    <input
      type="date"
      value={value && value.isValid() ? value.format('YYYY-MM-DD') : ''}
      onChange={(event) => onChange(event.target.value ? dayjs(event.target.value) : null)}
      className="h-8 min-w-[8.5rem] rounded-md border border-input bg-card px-2.5 text-xs font-medium text-foreground shadow-[var(--shadow-sm)] outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/25"
    />
  </div>
);

const DashboardLayout = () => {
  const isMobile = useIsMobile();
  const location = useLocation();
  const navigate = useNavigate();
  const {
    currentTenantKey,
    logout,
    selectTenant,
    tenants,
    user,
  } = useAuth();
  const dashboardParams = useDashboardParams();
  const {
    timeframe,
    selectedPlatform,
    updateParams,
  } = dashboardParams;
  const [siderCollapsed, setSiderCollapsed] = useState(false);
  const {
    end,
    handleEndDateChange,
    handleFilterChange,
    handleStartDateChange,
    isLoading,
    latestAvailableDate,
    selectedDateParam,
    selectedEndDateParam,
    start,
  } = useTimeframeManager(dashboardParams);
  const activeTenantKey = dashboardParams.tenantKey || currentTenantKey;
  const isReadonlyTenantAccess = isPlatformReadonlyTenantAccess({ user, tenantKey: activeTenantKey });
  const viewKey = getViewKeyFromPath(location.pathname);
  const [brandResolution, setBrandResolution] = useState({
    key: '',
    isLoading: false,
  });
  const brandResolutionKey = [
    activeTenantKey,
    dashboardParams.jobId,
    timeframe,
    selectedDateParam,
    selectedEndDateParam,
  ].join('|');
  const shouldResolveBrand =
    isAnalysisView(viewKey) &&
    Boolean(activeTenantKey) &&
    Boolean(dashboardParams.jobId) &&
    !dashboardParams.brand;
  const isBrandResolving =
    shouldResolveBrand &&
    (brandResolution.key !== brandResolutionKey || brandResolution.isLoading);

  useEffect(() => {
    const routeTenant = dashboardParams.tenantKey;
    const isKnownTenant = tenants.some((tenant) => tenant.tenantKey === routeTenant);
    if (routeTenant && routeTenant !== currentTenantKey && isKnownTenant) {
      selectTenant(routeTenant);
    }
  }, [currentTenantKey, dashboardParams.tenantKey, selectTenant, tenants]);

  useEffect(() => {
    if (!shouldResolveBrand) {
      return undefined;
    }

    const controller = new AbortController();
    setBrandResolution({ key: brandResolutionKey, isLoading: true });

    const run = async () => {
      const response = await fetchBrandMetrics(
        {
          tenantKey: activeTenantKey,
          jobId: dashboardParams.jobId,
          timeframe,
          startDate: selectedDateParam,
          endDate: selectedEndDateParam || selectedDateParam,
        },
        { signal: controller.signal },
      );
      const items = Array.isArray(response?.data)
        ? response.data
        : Array.isArray(response)
          ? response
          : [];
      const nextBrand = items.find((item) => item?.brand)?.brand || '';
      if (nextBrand) {
        updateParams({ brand: nextBrand }, { replace: true });
      }
    };

    run()
      .catch(() => {
        if (controller.signal.aborted) return;
        setBrandResolution({ key: brandResolutionKey, isLoading: false });
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setBrandResolution({ key: brandResolutionKey, isLoading: false });
        }
      });

    return () => {
      controller.abort();
    };
  }, [
    activeTenantKey,
    brandResolutionKey,
    dashboardParams.jobId,
    selectedDateParam,
    selectedEndDateParam,
    shouldResolveBrand,
    timeframe,
    updateParams,
  ]);

  const handlePlatformClick = useCallback(
    (platform) => {
      updateParams({ platform: platform?.name || '' });
    },
    [updateParams],
  );

  const handleBackFromPlatform = useCallback(() => {
    updateParams({ platform: null });
  }, [updateParams]);

  const handleTenantChange = useCallback(
    (nextTenantKey) => {
      if (!nextTenantKey || nextTenantKey === activeTenantKey) return;

      selectTenant(nextTenantKey);
      const viewKey = getViewKeyFromPath(location.pathname);
      const pathname = buildViewPath(viewKey, {
        tenantKey: nextTenantKey,
        jobId: dashboardParams.jobId,
      });
      const search = buildRouteSearch({
        search: location.search,
        nextViewKey: viewKey,
      });
      navigate(`${pathname}${search}`);
    },
    [
      activeTenantKey,
      dashboardParams.jobId,
      location.pathname,
      location.search,
      navigate,
      selectTenant,
    ],
  );

  const handleLogout = useCallback(() => {
    logout();
    navigate('/login', { replace: true });
  }, [logout, navigate]);

  const outletContext = useMemo(
    () => ({
      ...dashboardParams,
      selectedDateParam,
      selectedEndDateParam,
      selectedPlatform,
      isLoading: isLoading || isBrandResolving,
      onPlatformClick: handlePlatformClick,
      onBackFromPlatform: handleBackFromPlatform,
    }),
    [
      dashboardParams,
      handleBackFromPlatform,
      handlePlatformClick,
      isLoading,
      isBrandResolving,
      selectedDateParam,
      selectedEndDateParam,
      selectedPlatform,
    ],
  );

  return (
    <SidebarProvider open={!siderCollapsed} onOpenChange={(open) => setSiderCollapsed(!open)}>
      <div className="app-shell">
        <Sidebar />
        <SidebarInset className="app-shell-main">
          <header className="app-shell-header">
          <div className="app-shell-header-inner">
            <div className="flex min-w-0 items-center gap-3">
              <SidebarTrigger />
              <TaskName />
            </div>
            <div className="app-shell-controls">
              {user?.email ? (
                <Badge
                  variant="outline"
                  className="max-w-[14rem] gap-1.5 rounded-md border-border bg-card px-2.5 py-1 text-xs font-medium text-foreground"
                  title={user.realName ? `${user.realName} / ${user.email}` : user.email}
                >
                  <UserCircle className="size-3" aria-hidden="true" />
                  <span className="text-muted-foreground">当前账号</span>
                  <span className="truncate">{user.email}</span>
                </Badge>
              ) : null}
              {isReadonlyTenantAccess ? (
                <Badge
                  variant="secondary"
                  className="max-w-[14rem] gap-1.5 rounded-md border border-border bg-card px-2.5 py-1 text-xs font-medium text-foreground"
                  title={`平台管理员客户视角 / ${activeTenantKey}`}
                >
                  <ShieldCheck className="size-3 text-primary" aria-hidden="true" />
                  <span>客户视角</span>
                  <span className="truncate font-mono text-muted-foreground">{activeTenantKey}</span>
                </Badge>
              ) : null}
              <Badge variant="secondary" className="gap-1.5 rounded-md border border-border bg-card px-2.5 py-1 text-xs font-medium text-foreground">
                <CircleDot className="size-3 text-primary" aria-hidden="true" />
                实时数据
              </Badge>
              <LiveClock />
              {latestAvailableDate ? (
                <span className="text-xs text-muted-foreground">数据更新至: {latestAvailableDate}</span>
              ) : null}
              {tenants.length ? (
                <Select value={activeTenantKey || undefined} onValueChange={handleTenantChange}>
                  <SelectTrigger className="h-8 w-auto min-w-[9rem] max-w-[14rem] rounded-lg border-border bg-card text-xs font-medium shadow-[var(--shadow-sm)]">
                    <SelectValue placeholder="选择租户" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      {tenants.map((tenant) => (
                        <SelectItem key={tenant.tenantKey} value={tenant.tenantKey}>
                          {tenant.tenantName || tenant.tenantKey}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  </SelectContent>
                </Select>
              ) : null}
              {/* 条件渲染：避免 Radix Portal 在 display:none 容器中调用 getBoundingClientRect 报错 */}
              {isMobile ? (
                <Select
                  value={timeframe}
                  onValueChange={(nextValue) => {
                    if (nextValue) handleFilterChange(nextValue);
                  }}
                >
                  <SelectTrigger className="h-8 w-auto min-w-[7rem] rounded-lg border-border bg-card text-xs font-medium shadow-[var(--shadow-sm)]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      {TIME_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  </SelectContent>
                </Select>
              ) : (
                <ToggleGroup
                  type="single"
                  value={timeframe}
                  onValueChange={(nextValue) => {
                    if (nextValue) handleFilterChange(nextValue);
                  }}
                  variant="outline"
                  size="sm"
                  spacing={1}
                  className="flex-wrap rounded-lg border border-border bg-card p-1 shadow-[var(--shadow-sm)]"
                >
                  {TIME_OPTIONS.map((option) => (
                    <ToggleGroupItem key={option.value} value={option.value} className="mx-0.5 h-7 rounded-md border-0 px-2.5 text-xs font-medium data-[state=on]:bg-primary data-[state=on]:text-primary-foreground">
                      {option.label}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              )}
              {timeframe === 'specific_day' ? (
                <div className="app-shell-date-range">
                  <DatePickerControl
                    label="开始日期"
                    value={start}
                    onChange={handleStartDateChange}
                  />
                  <DatePickerControl
                    label="结束日期"
                    value={end}
                    onChange={handleEndDateChange}
                  />
                </div>
              ) : null}
              <ThemeToggle />
              <Button
                type="button"
                variant="outline"
                size="icon"
                title={user?.email ? `退出 ${user.email}` : '退出登录'}
                aria-label="退出登录"
                onClick={handleLogout}
              >
                <LogOut className="size-4" />
              </Button>
            </div>
          </div>
          </header>

          <main className="app-shell-content">
            <Outlet context={outletContext} />
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
};

export default React.memo(DashboardLayout);
