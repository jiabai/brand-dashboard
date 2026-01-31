import React, { Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Badge, ConfigProvider, Layout, Segmented, Space, Spin, Typography, theme } from 'antd';

import ErrorBoundary from './components/ErrorBoundary';
import TaskName from './components/TaskName.jsx';
import Sidebar from './components/Sidebar.jsx';

import { CONFIG } from './config';
import { getQueryParam, updateQueryParams } from './utils';

const BrandMentionRate = React.lazy(() => import('./components/BrandMentionRate.jsx'));
const PlatformMentionRates = React.lazy(() => import('./components/PlatformMentionRates.jsx'));
const ReferencesTable = React.lazy(() => import('./components/ReferencesTable.jsx'));
const PlatformDetail = React.lazy(() => import('./components/PlatformDetail.jsx'));
const CreateQueryJob = React.lazy(() => import('./components/CreateQueryJob.jsx'));
const QueryJobStatus = React.lazy(() => import('./components/QueryJobStatus.jsx'));

const { Header, Content } = Layout;

const TIME_OPTIONS = [
  { label: '昨天', value: 'yesterday' },
  { label: '过去7天', value: '7days' },
  { label: '过去30天', value: '30days' }
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
  const { token } = theme.useToken();
  // State management
  const [currentView, setCurrentView] = useState(() => getQueryParam('view', 'home'));
  const [selectedFilter, setSelectedFilter] = useState(() => getQueryParam('timeframe', '7days'));
  const [isLoading, setIsLoading] = useState(false);
  const [siderCollapsed, setSiderCollapsed] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState(() => getQueryParam('platform', ''));

  // Business params from URL or defaults
  const [tenantKey] = useState(() => getQueryParam('tenant_key', CONFIG.DEFAULT_TENANT_KEY));
  const [jobId] = useState(() => getQueryParam('job_id', CONFIG.DEFAULT_JOB_ID));
  const [brand] = useState(() => getQueryParam('brand', CONFIG.DEFAULT_BRAND));

  const loadingTimerRef = useRef(null);

  const timeOptions = useMemo(() => TIME_OPTIONS, []);

  useEffect(() => {
    updateQueryParams({ 
      view: currentView,
      timeframe: selectedFilter,
      tenant_key: tenantKey,
      job_id: jobId,
      brand: brand,
      platform: selectedPlatform
    });
  }, [currentView, selectedFilter, tenantKey, jobId, brand, selectedPlatform]);

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
              jobId={jobId} 
              brand={brand} 
            />
          ) : currentView === 'task-status' ? (
            <QueryJobStatus 
              tenantKey={tenantKey} 
            />
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
                      tenantKey={tenantKey}
                      jobId={jobId}
                      brand={brand}
                    />
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <PlatformMentionRates 
                      timeframe={selectedFilter} 
                      tenantKey={tenantKey}
                      jobId={jobId}
                      brand={brand}
                      onPlatformClick={(platform) => setSelectedPlatform(platform?.name || '')} 
                    />
                  </div>
                  <div style={{ minWidth: 0, gridColumn: '1 / -1' }}>
                    <ReferencesTable 
                      timeframe={selectedFilter} 
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
