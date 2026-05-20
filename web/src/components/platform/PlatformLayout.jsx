import React, { useCallback } from 'react';
import { Building2, LayoutDashboard, LogOut, ServerCog } from 'lucide-react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';

import { useAuth } from '../../auth/AuthContext.jsx';
import { Badge } from '../ui/badge.jsx';
import { Button } from '../ui/button.jsx';

const navItems = [
  { label: '租户管理', to: '/platform/tenants', icon: Building2, enabled: true },
  { label: '执行器', to: '/platform/executors', icon: ServerCog, enabled: false },
];

const PlatformLayout = () => {
  const navigate = useNavigate();
  const { logout, user } = useAuth();

  const handleLogout = useCallback(() => {
    logout();
    navigate('/login', { replace: true });
  }, [logout, navigate]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 px-4 py-3 backdrop-blur md:px-6">
        <div className="mx-auto flex max-w-[1440px] flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex min-w-0 items-center gap-3">
            <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <LayoutDashboard className="size-4" />
            </span>
            <div className="min-w-0">
              <div className="text-base font-medium">平台运营后台</div>
              <div className="truncate text-xs text-muted-foreground">Brand Dashboard Platform</div>
            </div>
          </div>
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <Badge variant="secondary" className="max-w-full truncate rounded-md px-2.5 py-1">
              {user?.email || 'platform_admin'}
            </Badge>
            <Button type="button" variant="outline" size="sm" onClick={handleLogout}>
              <LogOut className="size-4" />
              退出
            </Button>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-[1440px] gap-0 md:grid-cols-[220px_minmax(0,1fr)]">
        <aside className="border-b border-border px-4 py-3 md:min-h-[calc(100vh-65px)] md:border-b-0 md:border-r md:px-4 md:py-6">
          <nav className="flex gap-2 overflow-x-auto md:flex-col md:overflow-visible">
            {navItems.map((item) => {
              const Icon = item.icon;
              if (!item.enabled) {
                return (
                  <span
                    key={item.label}
                    className="inline-flex shrink-0 items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground opacity-60"
                  >
                    <Icon className="size-4" />
                    {item.label}
                    <Badge variant="outline" className="rounded-md text-[11px]">后续</Badge>
                  </span>
                );
              }
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    [
                      'inline-flex shrink-0 items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                    ].join(' ')
                  }
                >
                  <Icon className="size-4" />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>
        </aside>

        <main className="min-w-0 px-4 py-5 md:px-6 md:py-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default PlatformLayout;
