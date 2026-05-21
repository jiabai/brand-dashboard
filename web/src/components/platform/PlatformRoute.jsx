import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { ShieldAlert } from 'lucide-react';

import { useAuth } from '../../auth/AuthContext.jsx';
import { getPlatformAccessState } from '../../auth/platformAccess.js';
import LoadingSpinner from '../LoadingSpinner.jsx';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert.jsx';
import { Button } from '../ui/button.jsx';

const PlatformForbidden = () => (
  <div className="min-h-screen bg-background px-4 py-10 text-foreground">
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <Alert variant="destructive">
        <ShieldAlert className="size-4" />
        <AlertTitle>无权访问平台运营后台</AlertTitle>
        <AlertDescription>
          当前账号没有平台管理员权限，请使用已加入 PLATFORM_ADMIN_EMAILS 白名单的账号登录。
        </AlertDescription>
      </Alert>
      <div>
        <Button asChild variant="outline">
          <a href="/login">返回登录</a>
        </Button>
      </div>
    </div>
  </div>
);

const PlatformRoute = ({ children }) => {
  const location = useLocation();
  const auth = useAuth();
  const state = getPlatformAccessState(auth);

  if (state === 'loading') {
    return <div className="app-shell-loading"><LoadingSpinner text="正在恢复登录态..." /></div>;
  }

  if (state === 'login') {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (state === 'forbidden') {
    return <PlatformForbidden />;
  }

  return children || <Outlet />;
};

export default PlatformRoute;
