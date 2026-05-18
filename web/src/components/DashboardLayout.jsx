import React, { useCallback, useEffect, useMemo, useState } from 'react';
import dayjs from 'dayjs';
import { CalendarIcon } from 'lucide-react';
import { Outlet } from 'react-router-dom';

import TaskName from './TaskName.jsx';
import Sidebar from './Sidebar.jsx';
import { Badge } from './ui/badge.jsx';
import { Button } from './ui/button.jsx';
import { Calendar } from './ui/calendar.jsx';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover.jsx';
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from './ui/sidebar.jsx';
import { ToggleGroup, ToggleGroupItem } from './ui/toggle-group.jsx';
import { useDashboardParams } from '@/hooks/useDashboardParams';
import { TIME_OPTIONS, useTimeframeManager } from '@/hooks/useTimeframeManager';

const LiveClock = React.memo(function LiveClock() {
  const [currentTime, setCurrentTime] = useState(() => new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <span className="text-sm text-muted-foreground">
      更新: {currentTime.toLocaleTimeString()}
    </span>
  );
});

const formatCalendarLabel = (value) =>
  value && value.isValid() ? value.format('YYYY-MM-DD') : '选择日期';

const toDate = (value) => (value && value.isValid() ? value.toDate() : undefined);

const DatePickerControl = ({ label, value, onChange, isDateDisabled }) => (
  <div className="flex items-center gap-2">
    <span className="text-sm text-muted-foreground">{label}</span>
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className="min-w-32 justify-start">
          <CalendarIcon data-icon="inline-start" />
          {formatCalendarLabel(value)}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="single"
          selected={toDate(value)}
          onSelect={(nextDate) => onChange(nextDate ? dayjs(nextDate) : null)}
          disabled={(date) => isDateDisabled(dayjs(date))}
        />
      </PopoverContent>
    </Popover>
  </div>
);

const DashboardLayout = () => {
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
    isDateDisabled,
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
            <div className="flex min-w-0 items-center gap-2">
              <SidebarTrigger />
              <TaskName />
            </div>
            <div className="app-shell-controls">
              <Badge variant="outline" className="gap-1.5">
                <span className="size-2 rounded-full bg-primary" aria-hidden="true" />
                实时数据
              </Badge>
              <LiveClock />
              {latestAvailableDate ? (
                <span className="text-sm text-muted-foreground">数据更新至: {latestAvailableDate}</span>
              ) : null}
              <ToggleGroup
                type="single"
                value={timeframe}
                onValueChange={(nextValue) => {
                  if (nextValue) handleFilterChange(nextValue);
                }}
                variant="outline"
                size="sm"
                spacing={0}
              >
                {TIME_OPTIONS.map((option) => (
                  <ToggleGroupItem key={option.value} value={option.value}>
                    {option.label}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
              {timeframe === 'specific_day' ? (
                <div className="app-shell-date-range">
                  <DatePickerControl
                    label="开始日期"
                    value={start}
                    onChange={handleStartDateChange}
                    isDateDisabled={isDateDisabled}
                  />
                  <DatePickerControl
                    label="结束日期"
                    value={end}
                    onChange={handleEndDateChange}
                    isDateDisabled={isDateDisabled}
                  />
                </div>
              ) : null}
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
