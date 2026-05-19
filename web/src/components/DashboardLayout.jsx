import React, { useCallback, useEffect, useMemo, useState } from 'react';
import dayjs from 'dayjs';
import { CircleDot } from 'lucide-react';
import { Outlet } from 'react-router-dom';

import TaskName from './TaskName.jsx';
import ThemeToggle from './ThemeToggle.jsx';
import Sidebar from './Sidebar.jsx';
import { Badge } from './ui/badge.jsx';
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

  const handlePlatformClick = useCallback(
    (platform) => {
      updateParams({ platform: platform?.name || '' });
    },
    [updateParams],
  );

  const handleBackFromPlatform = useCallback(() => {
    updateParams({ platform: null });
  }, [updateParams]);

  const outletContext = useMemo(
    () => ({
      ...dashboardParams,
      selectedDateParam,
      selectedEndDateParam,
      selectedPlatform,
      isLoading,
      onPlatformClick: handlePlatformClick,
      onBackFromPlatform: handleBackFromPlatform,
    }),
    [
      dashboardParams,
      handleBackFromPlatform,
      handlePlatformClick,
      isLoading,
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
              <Badge variant="secondary" className="gap-1.5 rounded-md border border-border bg-card px-2.5 py-1 text-xs font-medium text-foreground">
                <CircleDot className="size-3 text-primary" aria-hidden="true" />
                实时数据
              </Badge>
              <LiveClock />
              {latestAvailableDate ? (
                <span className="text-xs text-muted-foreground">数据更新至: {latestAvailableDate}</span>
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
