import React, { Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import './styles/app-shell.css';
import ErrorBoundary from './components/ErrorBoundary';
import DashboardLayout from './components/DashboardLayout.jsx';
import AnalysisLayout from './components/AnalysisLayout.jsx';
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
import { buildViewPath, isAnalysisView } from './utils/routing.js';

const BrandShareOfVoiceTable = React.lazy(() => import('./components/BrandShareOfVoiceTable.jsx'));
const CreateQueryJob = React.lazy(() => import('./components/CreateQueryJob.jsx'));
const QueryJobStatus = React.lazy(() => import('./components/QueryJobStatus.jsx'));
const AccountManagement = React.lazy(() => import('./components/AccountManagement.jsx'));
const AnswerSnapshotsPage = React.lazy(() => import('./components/AnswerSnapshotsPage.jsx'));
const PlatformExecutorsPage = React.lazy(() => import('./components/platform/PlatformExecutorsPage.jsx'));
const PlatformTenantDetailPage = React.lazy(() => import('./components/platform/PlatformTenantDetailPage.jsx'));
const PlatformTenantsPage = React.lazy(() => import('./components/platform/PlatformTenantsPage.jsx'));
const ProjectDetailPage = React.lazy(() => import('./components/projects/ProjectDetailPage.jsx'));
const ProjectDataQualityPage = React.lazy(() => import('./components/projects/ProjectDataQualityPage.jsx'));
const ProjectListPage = React.lazy(() => import('./components/projects/ProjectListPage.jsx'));
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
  projects: () => <ProjectListPage />,
  'project-detail': () => <ProjectDetailPage />,
  'project-quality': () => <ProjectDataQualityPage />,
  home: () => <HomeView />,
  trend: () => (
    <DashboardLoadingRoute>
      <TrendAnalysis />
    </DashboardLoadingRoute>
  ),
  platforms: () => <BrandShareOfVoiceTable />,
  sources: () => <SourceAnalysis />,
  sentiment: () => <SentimentAnalysis />,
  snapshots: () => <AnswerSnapshotsPage />,
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
    : buildViewPath('projects', { tenantKey: currentTenantKey });

  const routableRoutes = getRoutableRoutes();
  const standaloneRoutes = routableRoutes.filter((route) => !isAnalysisView(route.viewKey));
  const analysisRoutes = routableRoutes.filter((route) => isAnalysisView(route.viewKey));

  return (
    <Routes>
      <Route path="/" element={<Navigate to={isAuthenticated && hasDefaultPath ? defaultPath : '/login'} replace />} />
      <Route path="/login" element={<LoginView defaultTab="login" />} />
      <Route path="/activate" element={<LoginView defaultTab="activate" />} />
      <Route path="/register" element={<LoginView defaultTab="register" />} />
      <Route path="/reset-password" element={<LoginView defaultTab="reset" />} />
      <Route path="/platform" element={<PlatformRoute><PlatformLayout /></PlatformRoute>}>
        <Route index element={<Navigate to="/platform/tenants" replace />} />
        <Route path="tenants" element={<RouteShell><PlatformTenantsPage /></RouteShell>} />
        <Route path="tenants/:tenantKey" element={<RouteShell><PlatformTenantDetailPage /></RouteShell>} />
        <Route path="executors" element={<RouteShell><PlatformExecutorsPage /></RouteShell>} />
      </Route>
      <Route element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
        {standaloneRoutes.map((route) => (
          <Route
            key={route.viewKey}
            path={route.path}
            element={<RouteShell>{ROUTE_ELEMENT_FACTORIES[route.viewKey]?.()}</RouteShell>}
          />
        ))}
        <Route element={<AnalysisLayout />}>
          {analysisRoutes.map((route) => (
            <Route
              key={route.viewKey}
              path={route.path}
              element={<RouteShell>{ROUTE_ELEMENT_FACTORIES[route.viewKey]?.()}</RouteShell>}
            />
          ))}
        </Route>
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
