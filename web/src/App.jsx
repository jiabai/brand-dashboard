import React, { Suspense, useCallback, useEffect } from 'react';
import { ConfigProvider, Spin, theme } from 'antd';
import { Navigate, Route, Routes, useNavigate, useOutletContext } from 'react-router-dom';

import './styles/app-shell.css';
import ErrorBoundary from './components/ErrorBoundary';
import DashboardLayout from './components/DashboardLayout.jsx';
import HomeView from './components/HomeView.jsx';
import { CONFIG } from './config.js';
import { buildDefaultEntryUrl, buildRouteSearch, buildViewPath } from './utils/routing.js';

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

const PlatformsRoute = () => {
  const {
    tenantKey,
    jobId,
    timeframe,
    selectedDateParam,
    selectedEndDateParam,
  } = useOutletContext();

  return (
    <BrandShareOfVoiceTable
      timeframe={timeframe}
      startDate={selectedDateParam}
      endDate={selectedEndDateParam}
      tenantKey={tenantKey}
      jobId={jobId}
    />
  );
};

const TrendRoute = () => {
  const {
    tenantKey,
    jobId,
    brand,
    timeframe,
    selectedDateParam,
    selectedEndDateParam,
    isLoading,
  } = useOutletContext();

  return (
    <Spin spinning={isLoading}>
      <TrendAnalysis
        timeframe={timeframe}
        date={selectedDateParam}
        endDate={selectedEndDateParam}
        tenantKey={tenantKey}
        jobId={jobId}
        brand={brand}
      />
    </Spin>
  );
};

const SourceRoute = () => {
  const {
    tenantKey,
    jobId,
    brand,
    timeframe,
    selectedDateParam,
    selectedEndDateParam,
  } = useOutletContext();

  return (
    <SourceAnalysis
      timeframe={timeframe}
      date={selectedDateParam}
      endDate={selectedEndDateParam}
      tenantKey={tenantKey}
      jobId={jobId}
      brand={brand}
    />
  );
};

const SentimentRoute = () => {
  const {
    tenantKey,
    jobId,
    brand,
    timeframe,
    selectedDateParam,
    selectedEndDateParam,
  } = useOutletContext();

  return (
    <SentimentAnalysis
      timeframe={timeframe}
      date={selectedDateParam}
      endDate={selectedEndDateParam}
      tenantKey={tenantKey}
      jobId={jobId}
      brand={brand}
    />
  );
};

const CreateQueryJobRoute = () => {
  const { tenantKey, jobId, searchParams } = useOutletContext();
  const navigate = useNavigate();

  const handleNavigate = useCallback(
    (viewKey) => {
      const pathname = buildViewPath(viewKey, { tenantKey, jobId });
      const search = buildRouteSearch({
        search: searchParams.toString(),
        nextViewKey: viewKey,
      });
      navigate(`${pathname}${search}`);
    },
    [jobId, navigate, searchParams, tenantKey],
  );

  return <CreateQueryJob tenantKey={tenantKey} onNavigate={handleNavigate} />;
};

const QueryJobStatusRoute = () => {
  const { tenantKey } = useOutletContext();
  return <QueryJobStatus tenantKey={tenantKey} />;
};

const DefaultEntryRedirect = () => (
  <Navigate
    to={buildDefaultEntryUrl({
      defaults: {
        tenantKey: CONFIG.DEFAULT_TENANT_KEY,
        jobId: CONFIG.DEFAULT_JOB_ID,
      },
    })}
    replace
  />
);

const AppRoutes = () => (
  <Routes>
    <Route path="/" element={<DefaultEntryRedirect />} />
    <Route element={<DashboardLayout />}>
      <Route path="/dashboard/:tenantKey/:jobId" element={<RouteShell><HomeView /></RouteShell>} />
      <Route path="/trend/:tenantKey/:jobId" element={<RouteShell><TrendRoute /></RouteShell>} />
      <Route path="/platforms/:tenantKey/:jobId" element={<RouteShell><PlatformsRoute /></RouteShell>} />
      <Route path="/sources/:tenantKey/:jobId" element={<RouteShell><SourceRoute /></RouteShell>} />
      <Route path="/sentiment/:tenantKey/:jobId" element={<RouteShell><SentimentRoute /></RouteShell>} />
      <Route path="/accounts/:tenantKey" element={<RouteShell><AccountManagement /></RouteShell>} />
      <Route path="/tasks/:tenantKey/new" element={<RouteShell><CreateQueryJobRoute /></RouteShell>} />
      <Route path="/tasks/:tenantKey/status" element={<RouteShell><QueryJobStatusRoute /></RouteShell>} />
    </Route>
    <Route path="*" element={<DefaultEntryRedirect />} />
  </Routes>
);

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
