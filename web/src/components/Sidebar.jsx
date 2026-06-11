import React, { useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  BarChart3,
  BookOpen,
  FolderKanban,
  Home,
  Image,
  List,
  MessageSquare,
  Plus,
  Settings,
  Smile,
  TrendingUp,
  User,
} from 'lucide-react';
import {
  Sidebar as UiSidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
} from './ui/sidebar.jsx';
import { useAuth } from '../auth/AuthContext.jsx';
import { isPlatformReadonlyTenantAccess } from '@/auth/platformAccess.js';
import { getSidebarMenuRoutes, getTaskMenuRoutes } from '@/config/routes';
import { useDashboardParams } from '@/hooks/useDashboardParams';
import { buildRouteSearch, buildViewPath, getViewKeyFromPath } from '@/utils/routing';

const MENU_ICON_MAP = {
  BarChartOutlined: BarChart3,
  BookOutlined: BookOpen,
  FolderKanbanOutlined: FolderKanban,
  HomeOutlined: Home,
  LineChartOutlined: TrendingUp,
  MessageOutlined: MessageSquare,
  PictureOutlined: Image,
  PlusOutlined: Plus,
  SettingOutlined: Settings,
  SmileOutlined: Smile,
  UnorderedListOutlined: List,
  UserOutlined: User,
};

const MENU_ITEMS = getSidebarMenuRoutes();
const TASK_MENU_ITEMS = getTaskMenuRoutes();

const SidebarMenuSection = ({ label, items, selectedKey, onSelect }) => (
  <SidebarGroup>
    <SidebarGroupLabel>{label}</SidebarGroupLabel>
    <SidebarGroupContent>
      <SidebarMenu>
        {items.map((item) => {
          const Icon = MENU_ICON_MAP[item.menuIcon] || Home;
          return (
            <SidebarMenuItem key={item.viewKey}>
              <SidebarMenuButton
                isActive={selectedKey === item.viewKey}
                disabled={Boolean(item.disabled)}
                tooltip={item.menuLabel}
                onClick={() => {
                  if (!item.disabled) onSelect(item.viewKey);
                }}
              >
                <Icon />
                <span>{item.menuLabel}</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          );
        })}
      </SidebarMenu>
    </SidebarGroupContent>
  </SidebarGroup>
);

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const { tenantKey, jobId } = useDashboardParams();
  const selectedKey = useMemo(
    () => getViewKeyFromPath(location.pathname),
    [location.pathname],
  );
  const isReadonlyTenantAccess = isPlatformReadonlyTenantAccess({ user, tenantKey });
  const visibleMenuItems = useMemo(
    () => (isReadonlyTenantAccess
      ? MENU_ITEMS.filter((item) => item.viewKey !== 'accounts')
      : MENU_ITEMS),
    [isReadonlyTenantAccess],
  );

  const handleMenuSelect = (viewKey) => {
    const pathname = buildViewPath(viewKey, { tenantKey, jobId });
    const search = buildRouteSearch({
      search: location.search,
      nextViewKey: viewKey,
    });
    navigate(`${pathname}${search}`);
  };

  return (
    <UiSidebar collapsible="icon" className="border-sidebar-border">
      <SidebarHeader className="px-3 py-5">
        <div className="flex min-w-0 items-center gap-2 rounded-lg border border-sidebar-border bg-sidebar-accent/70 p-2 group-data-[collapsible=icon]:justify-center">
          <div className="grid size-8 shrink-0 place-items-center rounded-md bg-sidebar-primary text-sm font-medium text-sidebar-primary-foreground">
            明
          </div>
          <div className="flex min-w-0 flex-col gap-0.5 group-data-[collapsible=icon]:hidden">
            <div className="flex items-baseline gap-1.5 truncate">
              <span className="text-sm font-medium text-sidebar-foreground">明察</span>
              <span className="text-xs font-medium text-sidebar-primary">
                InsightFlow
              </span>
            </div>
            <span className="truncate text-xs text-sidebar-foreground/70">
              Monitor · Analyze · Report
            </span>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        {TASK_MENU_ITEMS.length ? (
          <>
            <SidebarMenuSection
              label="任务"
              items={TASK_MENU_ITEMS}
              selectedKey={selectedKey}
              onSelect={handleMenuSelect}
            />
            <SidebarSeparator />
          </>
        ) : null}
        <SidebarMenuSection
          label="工作台"
          items={visibleMenuItems}
          selectedKey={selectedKey}
          onSelect={handleMenuSelect}
        />
      </SidebarContent>
    </UiSidebar>
  );
};

export default React.memo(Sidebar);
