import React, { Suspense, useEffect } from 'react';
import { ConfigProvider, Spin, theme } from 'antd';
import { Navigate, Route, Routes } from 'react-router-dom';

import './styles/app-shell.css';
import ErrorBoundary from './components/ErrorBoundary';
import DashboardLayout from './components/DashboardLayout.jsx';
import HomeView from './components/HomeView.jsx';

import { getRoutableRoutes } from './config/routes.js';
import { useDashboardRequestParams } from './hooks/useDashboardParams.js';
import { buildViewPath } from './utils/routing.js';
import { CONFIG } from './config.js';

const BrandShareOfVoiceTable = React.lazy(() => import('./components/BrandShareOfVoiceTable.jsx'));
const CreateQueryJob = React.lazy(() => import('./components/CreateQueryJob.jsx'));
const QueryJobStatus = React.lazy(() => import('./components/QueryJobStatus.jsx'));
const AccountManagement = React.lazy(() => import('./components/AccountManagement.jsx'));
const TrendAnalysis = React.lazy(() => import('./components/TrendAnalysis.jsx'));
const SourceAnalysis = React.lazy(() => import('./components/SourceAnalysis.jsx'));
const SentimentAnalysis = React.lazy(() => import('./components/SentimentAnalysis.jsx'));

const RouteShell = ({ children }) => (
  <ErrorBoundary>
    <Suspense fallback={<div className="app-shell-loading"><Spin /></div>}>
      {children}
    </Suspense>
  </ErrorBoundary>
);

const DashboardLoadingRoute = ({ children }) => {
  const { isLoading } = useDashboardRequestParams();
  return <Spin spinning={isLoading}>{children}</Spin>;
};

const ROUTE_ELEMENT_FACTORIES = {
  home: () => <HomeView />,
  trend: () => (
    <DashboardLoadingRoute>
      <TrendAnalysis />
    </DashboardLoadingRoute>
  ),
  platforms: () => <BrandShareOfVoiceTable />,
  sources: () => <SourceAnalysis />,
  sentiment: () => <SentimentAnalysis />,
  accounts: () => <AccountManagement />,
  'task-load': () => <CreateQueryJob />,
  'task-status': () => <QueryJobStatus />,
};

const AppRoutes = () => {
  const defaultPath = buildViewPath('home', {
    tenantKey: CONFIG.DEFAULT_TENANT_KEY,
    jobId: CONFIG.DEFAULT_JOB_ID,
  });

  return (
    <Routes>
      <Route path="/" element={<Navigate to={defaultPath} replace />} />
      <Route element={<DashboardLayout />}>
        {getRoutableRoutes().map((route) => (
          <Route
            key={route.viewKey}
            path={route.path}
            element={<RouteShell>{ROUTE_ELEMENT_FACTORIES[route.viewKey]?.()}</RouteShell>}
          />
        ))}
      </Route>
      <Route path="*" element={<Navigate to={defaultPath} replace />} />
    </Routes>
  );
};

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
          colorLink: '#fa8c16',
        },
      }}
    >
      <AppRoutes />
    </ConfigProvider>
  );
}

export default App;
