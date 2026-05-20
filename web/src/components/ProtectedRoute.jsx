import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { useAuth } from '../auth/AuthContext.jsx';
import LoadingSpinner from './LoadingSpinner.jsx';

const ProtectedRoute = ({ children }) => {
  const location = useLocation();
  const { isAuthenticated, isInitializing } = useAuth();

  if (isInitializing) {
    return <div className="app-shell-loading"><LoadingSpinner text="正在恢复登录态..." /></div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children || <Outlet />;
};

export default ProtectedRoute;
