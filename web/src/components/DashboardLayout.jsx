import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Badge, DatePicker, Layout, Segmented, Space, Typography } from 'antd';
import { Outlet } from 'react-router-dom';

import TaskName from './TaskName.jsx';
import Sidebar from './Sidebar.jsx';
import { useDashboardParams } from '@/hooks/useDashboardParams';
import { TIME_OPTIONS, useTimeframeManager } from '@/hooks/useTimeframeManager';

const { Header, Content } = Layout;

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
