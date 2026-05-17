import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Badge, DatePicker, Layout, Segmented, Space, Typography } from 'antd';
import { Outlet } from 'react-router-dom';
import dayjs from 'dayjs';

import TaskName from './TaskName.jsx';
import Sidebar from './Sidebar.jsx';
import { fetchJson, formatDateDisplay, formatDateParam, parseDateInput } from '@/utils';
import { useDashboardParams } from '@/hooks/useDashboardParams';

const { Header, Content } = Layout;

const TIME_OPTIONS = [
  { label: '昨天', value: 'yesterday' },
  { label: '过去7天', value: '7days' },
  { label: '过去30天', value: '30days' },
  { label: '指定日期', value: 'specific_day' },
];

const LiveClock = React.memo(function LiveClock() {
  const [currentTime, setCurrentTime] = useState(() => new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <Typography.Text type="secondary">
      更新: {currentTime.toLocaleTimeString()}
    </Typography.Text>
  );
});

const getNormalizedDateRange = (startDateParam, endDateParam) => {
  const start = parseDateInput(startDateParam) || dayjs();
  const rawEnd = parseDateInput(endDateParam) || start;
  const end = rawEnd.isBefore(start, 'day') ? start : rawEnd;
  return { start, end };
};

const DashboardLayout = () => {
  const dashboardParams = useDashboardParams();
  const {
    tenantKey,
    jobId,
    timeframe,
    startDateParam,
    endDateParam,
    selectedPlatform,
    updateParams,
  } = dashboardParams;
  const [siderCollapsed, setSiderCollapsed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [availableDates, setAvailableDates] = useState([]);
  const loadingTimerRef = useRef(null);

  const { start, end } = useMemo(
    () => getNormalizedDateRange(startDateParam, endDateParam),
    [startDateParam, endDateParam],
  );

  const selectedDateParam = useMemo(() => {
    if (timeframe !== 'specific_day') return '';
    return formatDateParam(start);
  }, [start, timeframe]);

  const selectedEndDateParam = useMemo(() => {
    if (timeframe !== 'specific_day') return '';
    return formatDateParam(end);
  }, [end, timeframe]);

  const availableDateSet = useMemo(() => new Set(availableDates), [availableDates]);

  const latestAvailableDate = useMemo(() => {
    if (!availableDates.length) return '';
    return availableDates.reduce((latest, current) => {
      if (!latest) return current;
      return dayjs(current).isAfter(dayjs(latest), 'day') ? current : latest;
    }, '');
  }, [availableDates]);

  const isDateDisabled = useCallback(
    (current) => {
      if (!current || availableDates.length === 0) return false;
      return !availableDateSet.has(current.format('YYYY-MM-DD'));
    },
    [availableDateSet, availableDates.length],
  );

  useEffect(() => {
    if (!tenantKey) {
      setAvailableDates([]);
      return;
    }
    const controller = new AbortController();
    const params = new URLSearchParams();
    params.set('tenant_key', tenantKey);
    if (jobId) {
      params.set('job_id', jobId);
    }
    const run = async () => {
      const result = await fetchJson(
        `/api/v1/dashboard/available-dates?${params.toString()}`,
        { signal: controller.signal },
      );
      const list = Array.isArray(result?.data) ? result.data : [];
      const normalized = list
        .map((item) => formatDateDisplay(item))
        .filter(Boolean);
      setAvailableDates(normalized);
    };
    run().catch(() => {
      if (controller.signal.aborted) return;
      setAvailableDates([]);
    });
    return () => {
      controller.abort();
    };
  }, [tenantKey, jobId]);

  useEffect(() => {
    return () => {
      if (loadingTimerRef.current) {
        clearTimeout(loadingTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (timeframe !== 'specific_day') return;
    if (startDateParam && endDateParam && !end.isBefore(start, 'day')) return;
    updateParams(
      {
        start_date: selectedDateParam,
        end_date: selectedEndDateParam,
        date: null,
      },
      { replace: true },
    );
  }, [
    end,
    endDateParam,
    selectedDateParam,
    selectedEndDateParam,
    start,
    startDateParam,
    timeframe,
    updateParams,
  ]);

  useEffect(() => {
    if (timeframe !== 'specific_day') return;
    if (!latestAvailableDate) return;
    const latest = dayjs(latestAvailableDate, 'YYYY-MM-DD');
    if (!latest.isValid()) return;

    const startKey = start.format('YYYY-MM-DD');
    const endKey = end.format('YYYY-MM-DD');
    const hasValidStart = availableDateSet.has(startKey);
    const hasValidEnd = availableDateSet.has(endKey);

    if (hasValidStart && hasValidEnd) return;

    updateParams(
      {
        start_date: formatDateParam(latest),
        end_date: formatDateParam(latest),
        date: null,
      },
      { replace: true },
    );
  }, [availableDateSet, end, latestAvailableDate, start, timeframe, updateParams]);

  const handleFilterChange = useCallback(
    (filter) => {
      if (loadingTimerRef.current) {
        clearTimeout(loadingTimerRef.current);
      }

      setIsLoading(true);
      loadingTimerRef.current = setTimeout(() => setIsLoading(false), 800);

      if (filter === 'specific_day') {
        const nextStart = parseDateInput(startDateParam) || parseDateInput(latestAvailableDate) || dayjs();
        const nextEnd = parseDateInput(endDateParam) || nextStart;
        const normalizedEnd = nextEnd.isBefore(nextStart, 'day') ? nextStart : nextEnd;
        updateParams({
          timeframe: filter,
          start_date: formatDateParam(nextStart),
          end_date: formatDateParam(normalizedEnd),
          date: null,
        });
        return;
      }

      updateParams({
        timeframe: filter,
        start_date: null,
        end_date: null,
        date: null,
      });
    },
    [endDateParam, latestAvailableDate, startDateParam, updateParams],
  );

  const handleStartDateChange = useCallback(
    (nextValue) => {
      const nextStart = nextValue || end || dayjs();
      const nextEnd = end && !end.isBefore(nextStart, 'day') ? end : nextStart;
      updateParams({
        timeframe: 'specific_day',
        start_date: formatDateParam(nextStart),
        end_date: formatDateParam(nextEnd),
        date: null,
      });
    },
    [end, updateParams],
  );

  const handleEndDateChange = useCallback(
    (nextValue) => {
      const nextEnd = nextValue || start || dayjs();
      const nextStart = start && !nextEnd.isBefore(start, 'day') ? start : nextEnd;
      updateParams({
        timeframe: 'specific_day',
        start_date: formatDateParam(nextStart),
        end_date: formatDateParam(nextEnd),
        date: null,
      });
    },
    [start, updateParams],
  );

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
    <Layout className="app-shell">
      <Sidebar
        collapsed={siderCollapsed}
        onCollapse={setSiderCollapsed}
      />
      <Layout className="app-shell-main">
        <Header className="app-shell-header">
          <div className="app-shell-header-inner">
            <TaskName />
            <Space size="middle" wrap className="app-shell-controls">
              <Badge status="processing" text="实时数据" />
              <LiveClock />
              {latestAvailableDate ? (
                <Typography.Text type="secondary">数据更新至: {latestAvailableDate}</Typography.Text>
              ) : null}
              <Segmented
                options={TIME_OPTIONS}
                value={timeframe}
                onChange={handleFilterChange}
              />
              {timeframe === 'specific_day' ? (
                <Space size="small" wrap align="center" className="app-shell-date-range">
                  <Typography.Text type="secondary">开始日期</Typography.Text>
                  <DatePicker
                    value={start}
                    onChange={handleStartDateChange}
                    format="YYYY-MM-DD"
                    allowClear
                    disabledDate={isDateDisabled}
                  />
                  <Typography.Text type="secondary">结束日期</Typography.Text>
                  <DatePicker
                    value={end}
                    onChange={handleEndDateChange}
                    format="YYYY-MM-DD"
                    allowClear
                    disabledDate={isDateDisabled}
                  />
                </Space>
              ) : null}
            </Space>
          </div>
        </Header>

        <Content className="app-shell-content">
          <Outlet context={outletContext} />
        </Content>
      </Layout>
    </Layout>
  );
};

export default React.memo(DashboardLayout);
