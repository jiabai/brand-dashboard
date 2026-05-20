import React, { Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import './styles/app-shell.css';
import ErrorBoundary from './components/ErrorBoundary';
import DashboardLayout from './components/DashboardLayout.jsx';
import HomeView from './components/HomeView.jsx';
import LoadingSpinner from './components/LoadingSpinner.jsx';
import LoginView from './components/LoginView.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';
import PlatformLayout from './components/platform/PlatformLayout.jsx';
import PlatformRoute from './components/platform/PlatformRoute.jsx';
import { TooltipProvider } from './components/ui/tooltip.jsx';

import { useAuth } from './auth/AuthContext.jsx';
import { hasPlatformAdminRole } from './auth/platformAccess.js';
import { getRoutableRoutes } from './config/routes.js';
import { useDashboardRequestParams } from './hooks/useDashboardParams.js';
import { buildViewPath } from './utils/routing.js';

const BrandShareOfVoiceTable = React.lazy(() => import('./components/BrandShareOfVoiceTable.jsx'));
const CreateQueryJob = React.lazy(() => import('./components/CreateQueryJob.jsx'));
const QueryJobStatus = React.lazy(() => import('./components/QueryJobStatus.jsx'));
const AccountManagement = React.lazy(() => import('./components/AccountManagement.jsx'));
const PlatformTenantsPage = React.lazy(() => import('./components/platform/PlatformTenantsPage.jsx'));
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
  const { currentTenantKey, isAuthenticated, user } = useAuth();
  const isPlatformAdmin = hasPlatformAdminRole(user);
  const hasDefaultPath = isPlatformAdmin || Boolean(currentTenantKey);
  const defaultPath = isPlatformAdmin
    ? '/platform/tenants'
    : buildViewPath('task-status', { tenantKey: currentTenantKey });

  return (
    <Routes>
      <Route path="/" element={<Navigate to={isAuthenticated && hasDefaultPath ? defaultPath : '/login'} replace />} />
      <Route path="/login" element={<LoginView defaultTab="login" />} />
      <Route path="/activate" element={<LoginView defaultTab="activate" />} />
      <Route path="/register" element={<LoginView defaultTab="register" />} />
      <Route path="/platform" element={<PlatformRoute><PlatformLayout /></PlatformRoute>}>
        <Route index element={<Navigate to="/platform/tenants" replace />} />
        <Route path="tenants" element={<RouteShell><PlatformTenantsPage /></RouteShell>} />
      </Route>
      <Route element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
        {getRoutableRoutes().map((route) => (
          <Route
            key={route.viewKey}
            path={route.path}
            element={<RouteShell>{ROUTE_ELEMENT_FACTORIES[route.viewKey]?.()}</RouteShell>}
          />
        ))}
      </Route>
      <Route path="*" element={<Navigate to={isAuthenticated && hasDefaultPath ? defaultPath : '/login'} replace />} />
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
