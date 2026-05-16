import React, { Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Badge, ConfigProvider, Layout, Segmented, DatePicker, Space, Spin, Typography, theme } from 'antd';
import dayjs from 'dayjs';

import './styles/app-shell.css';
import ErrorBoundary from './components/ErrorBoundary';
import TaskName from './components/TaskName.jsx';
import Sidebar from './components/Sidebar.jsx';

import { CONFIG } from './config';
import {
  fetchJson,
  formatDateDisplay,
  formatDateParam,
  getQueryParam,
  parseDateInput,
  updateQueryParams,
} from './utils';

const BrandMentionRate = React.lazy(() => import('./components/BrandMentionRate.jsx'));
const PlatformMentionRates = React.lazy(() => import('./components/PlatformMentionRates.jsx'));
const ReferencesTable = React.lazy(() => import('./components/ReferencesTable.jsx'));
const BrandShareOfVoiceTable = React.lazy(() => import('./components/BrandShareOfVoiceTable.jsx'));
const PlatformDetail = React.lazy(() => import('./components/PlatformDetail.jsx'));
const CreateQueryJob = React.lazy(() => import('./components/CreateQueryJob.jsx'));
const QueryJobStatus = React.lazy(() => import('./components/QueryJobStatus.jsx'));
const AccountManagement = React.lazy(() => import('./components/AccountManagement.jsx'));
const TrendAnalysis = React.lazy(() => import('./components/TrendAnalysis.jsx'));
const SourceAnalysis = React.lazy(() => import('./components/SourceAnalysis.jsx'));
const SentimentAnalysis = React.lazy(() => import('./components/SentimentAnalysis.jsx'));

const { Header, Content } = Layout;

const TIME_OPTIONS = [
  { label: '昨天', value: 'yesterday' },
  { label: '过去7天', value: '7days' },
  { label: '过去30天', value: '30days' },
  { label: '指定日期', value: 'specific_day' }
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

/**
 * Dashboard content component
 */
function Dashboard() {
  // State management
  const [currentView, setCurrentView] = useState(() => getQueryParam('view', 'home'));
  const [selectedFilter, setSelectedFilter] = useState(() => getQueryParam('timeframe', '30days'));
  const [isLoading, setIsLoading] = useState(false);
  const [siderCollapsed, setSiderCollapsed] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState(() => getQueryParam('platform', ''));

  // Business params from URL or defaults
  const [tenantKey] = useState(() => getQueryParam('tenant_key', CONFIG.DEFAULT_TENANT_KEY));
  const [jobId] = useState(() => getQueryParam('job_id', CONFIG.DEFAULT_JOB_ID));
  const [brand] = useState(() => getQueryParam('brand', CONFIG.DEFAULT_BRAND));
  const [executorId] = useState(() => getQueryParam('executor_id', CONFIG.DEFAULT_EXECUTOR_ID));
  const [includeDeleted] = useState(() => getQueryParam('include_deleted', CONFIG.DEFAULT_INCLUDE_DELETED));

  const loadingTimerRef = useRef(null);

  const [availableDates, setAvailableDates] = useState([]);

  const [startDate, setStartDate] = useState(() => {
    const fromUrl = parseDateInput(getQueryParam('start_date', '') || getQueryParam('date', ''));
    return fromUrl || dayjs();
  });
  const [endDate, setEndDate] = useState(() => {
    const fromUrl = parseDateInput(getQueryParam('end_date', ''));
    if (fromUrl) return fromUrl;
    const fallback = parseDateInput(getQueryParam('start_date', '') || getQueryParam('date', ''));
    return fallback || dayjs();
  });

  const startDateParam = useMemo(() => {
    if (selectedFilter !== 'specific_day') return '';
    return formatDateParam(startDate);
  }, [startDate, selectedFilter]);

  const endDateParam = useMemo(() => {
    if (selectedFilter !== 'specific_day') return '';
    return formatDateParam(endDate);
  }, [endDate, selectedFilter]);

  const selectedDateParam = useMemo(() => {
    if (selectedFilter !== 'specific_day') return '';
    return startDateParam;
  }, [selectedFilter, startDateParam]);

  const timeOptions = useMemo(() => TIME_OPTIONS, []);

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
    updateQueryParams({ 
      view: currentView,
      timeframe: selectedFilter,
      start_date: startDateParam,
      end_date: endDateParam,
      date: selectedDateParam,
      tenant_key: tenantKey,
      job_id: jobId,
      brand: brand,
      executor_id: executorId,
      include_deleted: includeDeleted,
      platform: selectedPlatform
    });
  }, [
    currentView,
    selectedFilter,
    startDateParam,
    endDateParam,
    selectedDateParam,
    tenantKey,
    jobId,
    brand,
    executorId,
    includeDeleted,
    selectedPlatform,
  ]);

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
    run().catch((err) => {
      if (controller.signal.aborted) return;
      setAvailableDates([]);
    });
    return () => {
      controller.abort();
    };
  }, [tenantKey, jobId]);

  // Cleanup loading timer on unmount
  useEffect(() => {
    return () => {
      if (loadingTimerRef.current) {
        clearTimeout(loadingTimerRef.current);
      }
    };
  }, []);

  /**
   * Handle filter change with loading state
   * @param {string} filter - The selected time filter
   */
  const handleFilterChange = useCallback((filter) => {
    setSelectedFilter(filter);
    // Clear any existing timer
    if (loadingTimerRef.current) {
      clearTimeout(loadingTimerRef.current);
    }
    // Simulate loading state for better UX
    setIsLoading(true);
    loadingTimerRef.current = setTimeout(() => setIsLoading(false), 800);
  }, []);

  useEffect(() => {
    if (selectedFilter !== 'specific_day') return;
    if (!startDate && endDate) {
      setStartDate(endDate);
      return;
    }
    if (startDate && !endDate) {
      setEndDate(startDate);
      return;
    }
    if (startDate && endDate && endDate.isBefore(startDate, 'day')) {
      setEndDate(startDate);
    }
  }, [selectedFilter, startDate, endDate]);

  useEffect(() => {
    if (selectedFilter !== 'specific_day') return;
    if (!latestAvailableDate) return;
    const latest = dayjs(latestAvailableDate, 'YYYY-MM-DD');
    if (!latest.isValid()) return;
    const startKey = startDate ? startDate.format('YYYY-MM-DD') : '';
    const endKey = endDate ? endDate.format('YYYY-MM-DD') : '';
    if (!startKey || !availableDateSet.has(startKey)) {
      setStartDate(latest);
      setEndDate(latest);
      return;
    }
    if (endKey && !availableDateSet.has(endKey)) {
      setEndDate(latest);
    }
  }, [selectedFilter, latestAvailableDate, availableDateSet, startDate, endDate]);

  const handleBackFromPlatform = useCallback(() => {
    setSelectedPlatform('');
  }, []);

  const renderContent = () => {
    return (
      <ErrorBoundary>
        <Suspense fallback={<div className="app-shell-loading"><Spin /></div>}>
          {currentView === 'task-load' ? (
            <CreateQueryJob 
              tenantKey={tenantKey}
              onNavigate={setCurrentView}
            />
          ) : currentView === 'accounts' ? (
            <AccountManagement />
          ) : currentView === 'task-status' ? (
            <QueryJobStatus 
              tenantKey={tenantKey} 
            />
          ) : currentView === 'platforms' ? (
            <BrandShareOfVoiceTable
              timeframe={selectedFilter}
              startDate={startDateParam}
              endDate={endDateParam}
              tenantKey={tenantKey}
              jobId={jobId}
            />
          ) : currentView === 'trend' ? (
            <Spin spinning={isLoading}>
              <TrendAnalysis
                timeframe={selectedFilter}
                date={selectedDateParam}
                endDate={endDateParam}
                tenantKey={tenantKey}
                jobId={jobId}
                brand={brand}
              />
            </Spin>
          ) : currentView === 'sources' ? (
            <SourceAnalysis 
              timeframe={selectedFilter}
              date={selectedDateParam}
              endDate={endDateParam}
              tenantKey={tenantKey}
              jobId={jobId}
              brand={brand}
            />
          ) : currentView === 'sentiment' ? (
            <SentimentAnalysis 
              timeframe={selectedFilter}
              date={selectedDateParam}
              endDate={endDateParam}
              tenantKey={tenantKey}
              jobId={jobId}
              brand={brand}
            />
          ) : (
            <Spin spinning={isLoading}>
              {selectedPlatform ? (
                <PlatformDetail 
                  platformName={selectedPlatform}
                  tenantKey={tenantKey}
                  jobId={jobId}
                  brand={brand}
                  timeframe={selectedFilter}
                  startDate={startDateParam}
                  endDate={endDateParam}
                  onBack={handleBackFromPlatform} 
                />
              ) : (
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'minmax(0, 1fr)',
                    gap: 16
                  }}
                >
                  <div style={{ minWidth: 0 }}>
                    <BrandMentionRate 
                      timeframe={selectedFilter} 
                      date={selectedDateParam}
                      endDate={endDateParam}
                      tenantKey={tenantKey}
                      jobId={jobId}
                      brand={brand}
                    />
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <PlatformMentionRates 
                      timeframe={selectedFilter} 
                      date={selectedDateParam}
                      endDate={endDateParam}
                      tenantKey={tenantKey}
                      jobId={jobId}
                      brand={brand}
                      onPlatformClick={(platform) => setSelectedPlatform(platform?.name || '')} 
                    />
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <ReferencesTable 
                      timeframe={selectedFilter} 
                      date={selectedDateParam}
                      endDate={endDateParam}
                      tenantKey={tenantKey}
                      jobId={jobId}
                      brand={brand}
                    />
                  </div>
                </div>
              )}
            </Spin>
          )}
        </Suspense>
      </ErrorBoundary>
    );
  };

  return (
    <Layout className="app-shell">
      <Sidebar 
        collapsed={siderCollapsed} 
        onCollapse={setSiderCollapsed} 
        selectedKey={currentView}
        onMenuClick={setCurrentView}
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
                options={timeOptions}
                value={selectedFilter}
                onChange={handleFilterChange}
              />
              {selectedFilter === 'specific_day' ? (
                <Space size="small" wrap align="center" className="app-shell-date-range">
                  <Typography.Text type="secondary">开始日期</Typography.Text>
                  <DatePicker
                    value={startDate}
                    onChange={(nextValue) => {
                      setStartDate(nextValue);
                      if (nextValue && endDate && endDate.isBefore(nextValue, 'day')) {
                        setEndDate(nextValue);
                      }
                      if (nextValue && !endDate) {
                        setEndDate(nextValue);
                      }
                    }}
                    format="YYYY-MM-DD"
                    allowClear
                    disabledDate={isDateDisabled}
                  />
                  <Typography.Text type="secondary">结束日期</Typography.Text>
                  <DatePicker
                    value={endDate}
                    onChange={(nextValue) => {
                      setEndDate(nextValue);
                      if (nextValue && startDate && nextValue.isBefore(startDate, 'day')) {
                        setStartDate(nextValue);
                      }
                      if (nextValue && !startDate) {
                        setStartDate(nextValue);
                      }
                    }}
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
          {renderContent()}
        </Content>
      </Layout>
    </Layout>
  );
}

/**
 * Main application component for Brand Analysis Dashboard
 *
 * @returns {JSX.Element} The rendered dashboard application
 */
function App() {
  useEffect(() => {
    document.documentElement.classList.add('dark');
  }, []);

  return (
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          fontFamily:
            "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji', sans-serif",
          colorPrimary: '#fa8c16',
          colorInfo: '#fa8c16',
          colorSuccess: '#52c41a',
          colorWarning: '#faad14',
          colorError: '#ff4d4f',
          colorLink: '#fa8c16'
        }
      }}
    >
      <Dashboard />
    </ConfigProvider>
  );
}

export default App;
