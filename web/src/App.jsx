import React, { Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import './styles/app-shell.css';
import ErrorBoundary from './components/ErrorBoundary';
import DashboardLayout from './components/DashboardLayout.jsx';
import HomeView from './components/HomeView.jsx';
import LoadingSpinner from './components/LoadingSpinner.jsx';
import LoginView from './components/LoginView.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';
import { TooltipProvider } from './components/ui/tooltip.jsx';

import { useAuth } from './auth/AuthContext.jsx';
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
    <Suspense fallback={<div className="app-shell-loading"><LoadingSpinner text="加载中..." /></div>}>
      {children}
    </Suspense>
  </ErrorBoundary>
);

const DashboardLoadingRoute = ({ children }) => {
  const { isLoading } = useDashboardRequestParams();
  if (isLoading) {
    return <div className="app-shell-loading"><LoadingSpinner text="正在加载数据..." /></div>;
  }
  return children;
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
  const { currentTenantKey, isAuthenticated } = useAuth();
  const defaultPath = buildViewPath('home', {
    tenantKey: currentTenantKey || CONFIG.DEFAULT_TENANT_KEY,
    jobId: CONFIG.DEFAULT_JOB_ID,
  });

  return (
    <Routes>
      <Route path="/" element={<Navigate to={isAuthenticated ? defaultPath : '/login'} replace />} />
      <Route path="/login" element={<LoginView defaultTab="login" />} />
      <Route path="/activate" element={<LoginView defaultTab="activate" />} />
      <Route path="/register" element={<LoginView defaultTab="register" />} />
      <Route element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
        {getRoutableRoutes().map((route) => (
          <Route
            key={route.viewKey}
            path={route.path}
            element={<RouteShell>{ROUTE_ELEMENT_FACTORIES[route.viewKey]?.()}</RouteShell>}
          />
        ))}
      </Route>
      <Route path="*" element={<Navigate to={isAuthenticated ? defaultPath : '/login'} replace />} />
    </Routes>
  );
};

function App() {
  return (
    <TooltipProvider>
      <AppRoutes />
    </TooltipProvider>
  );
}

export default App;
