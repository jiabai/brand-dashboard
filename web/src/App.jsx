import React, { Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Badge, ConfigProvider, Layout, Segmented, Select, Space, Spin, Typography, theme } from 'antd';

import ErrorBoundary from './components/ErrorBoundary';
import TaskName from './components/TaskName.jsx';
import Sidebar from './components/Sidebar.jsx';

import { CONFIG } from './config';
import { getQueryParam, updateQueryParams } from './utils';

const BrandMentionRate = React.lazy(() => import('./components/BrandMentionRate.jsx'));
const PlatformMentionRates = React.lazy(() => import('./components/PlatformMentionRates.jsx'));
const ReferencesTable = React.lazy(() => import('./components/ReferencesTable.jsx'));
const BrandShareOfVoiceTable = React.lazy(() => import('./components/BrandShareOfVoiceTable.jsx'));
const PlatformDetail = React.lazy(() => import('./components/PlatformDetail.jsx'));
const CreateQueryJob = React.lazy(() => import('./components/CreateQueryJob.jsx'));
const QueryJobStatus = React.lazy(() => import('./components/QueryJobStatus.jsx'));
const TrendAnalysis = React.lazy(() => import('./components/TrendAnalysis.jsx'));

const { Header, Content } = Layout;

const TIME_OPTIONS = [
  { label: '昨天', value: 'yesterday' },
  { label: '过去7天', value: '7days' },
  { label: '过去30天', value: '30days' },
  { label: '指定日期', value: 'specific_day' }
];

const normalizeDateToDisplay = (value) => {
  if (!value) return '';
  const text = String(value);
  if (/^\d{8}$/.test(text)) {
    return `${text.slice(0, 4)}-${text.slice(4, 6)}-${text.slice(6, 8)}`;
  }
  return text;
};

const normalizeDateToParam = (value) => {
  if (!value) return '';
  return String(value).replace(/-/g, '');
};

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
  const { token } = theme.useToken();
  // State management
  const [currentView, setCurrentView] = useState(() => getQueryParam('view', 'home'));
  const [selectedFilter, setSelectedFilter] = useState(() => getQueryParam('timeframe', '30days'));
  const [selectedDate, setSelectedDate] = useState(() =>
    normalizeDateToDisplay(getQueryParam('date', '')),
  );
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingDates, setIsLoadingDates] = useState(false);
  const [availableDates, setAvailableDates] = useState([]);
  const [availableDatesError, setAvailableDatesError] = useState('');
  const [siderCollapsed, setSiderCollapsed] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState(() => getQueryParam('platform', ''));

  // Business params from URL or defaults
  const [tenantKey] = useState(() => getQueryParam('tenant_key', CONFIG.DEFAULT_TENANT_KEY));
  const [jobId] = useState(() => getQueryParam('job_id', CONFIG.DEFAULT_JOB_ID));
  const [brand] = useState(() => getQueryParam('brand', CONFIG.DEFAULT_BRAND));
  const [executorId] = useState(() => getQueryParam('executor_id', CONFIG.DEFAULT_EXECUTOR_ID));
  const [includeDeleted] = useState(() => getQueryParam('include_deleted', CONFIG.DEFAULT_INCLUDE_DELETED));

  const loadingTimerRef = useRef(null);

  const selectedDateParam = useMemo(() => {
    if (selectedFilter !== 'specific_day') return '';
    return normalizeDateToParam(selectedDate);
  }, [selectedDate, selectedFilter]);

  const timeOptions = useMemo(() => TIME_OPTIONS, []);

  useEffect(() => {
    updateQueryParams({ 
      view: currentView,
      timeframe: selectedFilter,
      date: selectedDateParam,
      tenant_key: tenantKey,
      job_id: jobId,
      brand: brand,
      executor_id: executorId,
      include_deleted: includeDeleted,
      platform: selectedPlatform
    });
  }, [currentView, selectedFilter, selectedDateParam, tenantKey, jobId, brand, executorId, includeDeleted, selectedPlatform]);

  useEffect(() => {
    const controller = new AbortController();
    const run = async () => {
      try {
        setIsLoadingDates(true);
        setAvailableDatesError('');
        const searchParams = new URLSearchParams({ tenant_key: tenantKey });
        if (jobId) {
          searchParams.set('job_id', jobId);
        }
        const response = await fetch(`/api/v1/dashboard/available-dates?${searchParams.toString()}`, {
          method: 'GET',
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error(`请求失败(${response.status})`);
        }
        const result = await response.json();
        const list = Array.isArray(result?.data) ? result.data : [];
        setAvailableDates(list);
        setIsLoadingDates(false);
      } catch (error) {
        if (controller.signal.aborted) return;
        setAvailableDates([]);
        setAvailableDatesError(error?.message || '日期加载失败');
        setIsLoadingDates(false);
      }
    };

    run();

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
    if (filter !== 'specific_day') {
      setSelectedDate('');
    }
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
    if (!availableDates.length) return;
    if (!selectedDate || !availableDates.includes(selectedDate)) {
      setSelectedDate(availableDates[0]);
    }
  }, [availableDates, selectedDate, selectedFilter]);

  const handleBackFromPlatform = useCallback(() => {
    setSelectedPlatform('');
  }, []);

  const renderContent = () => {
    return (
      <ErrorBoundary>
        <Suspense fallback={<Spin />}>
          {currentView === 'task-load' ? (
            <CreateQueryJob 
              tenantKey={tenantKey}
              onNavigate={setCurrentView}
            />
          ) : currentView === 'task-status' ? (
            <QueryJobStatus 
              tenantKey={tenantKey} 
            />
          ) : currentView === 'platforms' ? (
            <BrandShareOfVoiceTable
              timeframe={selectedFilter}
              date={selectedDateParam}
              tenantKey={tenantKey}
              jobId={jobId}
            />
          ) : currentView === 'trend' ? (
            <Spin spinning={isLoading}>
              <TrendAnalysis
                timeframe={selectedFilter}
                date={selectedDateParam}
                tenantKey={tenantKey}
                jobId={jobId}
                brand={brand}
              />
            </Spin>
          ) : (
            <Spin spinning={isLoading}>
              {selectedPlatform ? (
                <PlatformDetail 
                  platformName={selectedPlatform} 
                  onBack={handleBackFromPlatform} 
                />
              ) : (
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'minmax(0, 1.2fr) minmax(0, 1.8fr)',
                    gap: 16
                  }}
                >
                  <div style={{ minWidth: 0 }}>
                    <BrandMentionRate 
                      timeframe={selectedFilter} 
                      date={selectedDateParam}
                      tenantKey={tenantKey}
                      jobId={jobId}
                      brand={brand}
                    />
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <PlatformMentionRates 
                      timeframe={selectedFilter} 
                      date={selectedDateParam}
                      tenantKey={tenantKey}
                      jobId={jobId}
                      brand={brand}
                      onPlatformClick={(platform) => setSelectedPlatform(platform?.name || '')} 
                    />
                  </div>
                  <div style={{ minWidth: 0, gridColumn: '1 / -1' }}>
                    <ReferencesTable 
                      timeframe={selectedFilter} 
                      date={selectedDateParam}
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
    <Layout style={{ minHeight: '100vh', position: 'relative', zIndex: 1 }}>
      <Sidebar 
        collapsed={siderCollapsed} 
        onCollapse={setSiderCollapsed} 
        selectedKey={currentView}
        onMenuClick={setCurrentView}
      />
      <Layout>
        <Header
          style={{
            position: 'sticky',
            top: 0,
            zIndex: 10,
            paddingInline: 24,
            display: 'flex',
            alignItems: 'center',
            background: token.colorBgContainer,
            borderBottom: `1px solid ${token.colorBorderSecondary}`
          }}
        >
          <Space
            size="middle"
            style={{
              width: '100%',
              justifyContent: 'space-between'
            }}
          >
            <TaskName />
            <Space size="middle" wrap>
              <Badge status="processing" text="实时数据" />
              <LiveClock />
              <Segmented
                options={timeOptions}
                value={selectedFilter}
                onChange={handleFilterChange}
              />
              {selectedFilter === 'specific_day' ? (
                <Select
                  value={selectedDate || undefined}
                  onChange={setSelectedDate}
                  placeholder={availableDatesError ? '日期加载失败' : '选择日期'}
                  options={availableDates.map((date) => ({ label: date, value: date }))}
                  loading={isLoadingDates}
                  disabled={Boolean(availableDatesError) || availableDates.length === 0}
                  showSearch
                  style={{ minWidth: 160 }}
                  notFoundContent={isLoadingDates ? '加载中' : '暂无日期'}
                />
              ) : null}
            </Space>
          </Space>
        </Header>

        <Content style={{ padding: 24 }}>
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
