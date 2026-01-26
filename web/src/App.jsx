import React, { Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Badge, ConfigProvider, Layout, Segmented, Space, Spin, Typography, theme } from 'antd';

import ErrorBoundary from './components/ErrorBoundary';
import TaskName from './components/TaskName.jsx';
import Sidebar from './components/Sidebar.jsx';

const BrandMentionRate = React.lazy(() => import('./components/BrandMentionRate.jsx'));
const PlatformMentionRates = React.lazy(() => import('./components/PlatformMentionRates.jsx'));
const ReferencesTable = React.lazy(() => import('./components/ReferencesTable.jsx'));
const PlatformDetail = React.lazy(() => import('./components/PlatformDetail.jsx'));
const CreateQueryJob = React.lazy(() => import('./components/CreateQueryJob.jsx'));

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
  const [currentView, setCurrentView] = useState('home');
  const [selectedFilter, setSelectedFilter] = useState('7days');
  const [isLoading, setIsLoading] = useState(false);
  const [siderCollapsed, setSiderCollapsed] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const loadingTimerRef = useRef(null);

  const timeOptions = useMemo(() => TIME_OPTIONS, []);

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
    setSelectedPlatform(null);
  }, []);

  const renderContent = () => {
    return (
      <ErrorBoundary>
        <Suspense fallback={<Spin />}>
          {currentView === 'task-load' ? (
            <CreateQueryJob />
          ) : (
            <Spin spinning={isLoading}>
              {selectedPlatform ? (
                <PlatformDetail 
                  platformName={selectedPlatform.name} 
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
                    <BrandMentionRate timeframe={selectedFilter} />
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <PlatformMentionRates timeframe={selectedFilter} onPlatformClick={setSelectedPlatform} />
                  </div>
                  <div style={{ minWidth: 0, gridColumn: '1 / -1' }}>
                    <ReferencesTable timeframe={selectedFilter} />
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
