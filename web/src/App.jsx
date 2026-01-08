import React, { useState, useEffect } from 'react';
import { Badge, ConfigProvider, Layout, Segmented, Space, Spin, Typography, theme } from 'antd';

// Components
import BrandMentionRate from './components/BrandMentionRate.jsx';
import ModelMentionRates from './components/ModelMentionRates.jsx';
import ReferencesTable from './components/ReferencesTable.jsx';
import ErrorBoundary from './components/ErrorBoundary';
import TaskName from './components/TaskName.jsx';
import Sidebar from './components/Sidebar.jsx';

const { Header, Content } = Layout;

/**
 * Main application component for Brand Analysis Dashboard
 *
 * @returns {JSX.Element} The rendered dashboard application
 */
function App() {
  const { token } = theme.useToken();
  // State management
  const [selectedFilter, setSelectedFilter] = useState('7days');
  const [currentTime, setCurrentTime] = useState(new Date());
  const [isLoading, setIsLoading] = useState(false);
  const [siderCollapsed, setSiderCollapsed] = useState(false);
  const loadingTimerRef = React.useRef(null);

  const timeOptions = [
    { label: '昨天', value: 'yesterday' },
    { label: '过去7天', value: '7days' },
    { label: '过去30天', value: '30days' }
  ];

  // Update current time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

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
  const handleFilterChange = (filter) => {
    setSelectedFilter(filter);
    // Clear any existing timer
    if (loadingTimerRef.current) {
      clearTimeout(loadingTimerRef.current);
    }
    // Simulate loading state for better UX
    setIsLoading(true);
    loadingTimerRef.current = setTimeout(() => setIsLoading(false), 800);
  };

  return (
    <ConfigProvider
      theme={{
        token: {
          fontFamily:
            "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji', sans-serif",
          colorPrimary: '#722ED1',
          colorInfo: '#722ED1',
          colorSuccess: '#52c41a',
          colorWarning: '#faad14',
          colorError: '#ff4d4f',
          colorLink: '#722ED1'
        }
      }}
    >
      <Layout style={{ minHeight: '100vh', position: 'relative', zIndex: 1 }}>
        <Sidebar collapsed={siderCollapsed} onCollapse={setSiderCollapsed} />
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
                <Typography.Text type="secondary">
                  更新: {currentTime.toLocaleTimeString()}
                </Typography.Text>
                <Segmented
                  options={timeOptions}
                  value={selectedFilter}
                  onChange={handleFilterChange}
                />
              </Space>
            </Space>
          </Header>

          <Content style={{ padding: 24 }}>
            <ErrorBoundary>
              <Spin spinning={isLoading} tip="正在加载数据...">
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'minmax(0, 1.2fr) minmax(0, 1.8fr)',
                    gap: 16
                  }}
                >
                  <div style={{ minWidth: 0 }}>
                    <BrandMentionRate />
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <ModelMentionRates />
                  </div>
                  <div style={{ minWidth: 0, gridColumn: '1 / -1' }}>
                    <ReferencesTable />
                  </div>
                </div>
              </Spin>
            </ErrorBoundary>
          </Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}

export default App;
