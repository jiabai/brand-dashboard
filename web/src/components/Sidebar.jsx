import React, { useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  BarChart3,
  BookOpen,
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
import { getSidebarMenuRoutes, getTaskMenuRoutes } from '@/config/routes';
import { useDashboardParams } from '@/hooks/useDashboardParams';
import { buildRouteSearch, buildViewPath, getViewKeyFromPath } from '@/utils/routing';

const MENU_ICON_MAP = {
  BarChartOutlined: BarChart3,
  BookOutlined: BookOpen,
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
  const { tenantKey, jobId } = useDashboardParams();
  const selectedKey = useMemo(
    () => getViewKeyFromPath(location.pathname),
    [location.pathname],
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
    <UiSidebar collapsible="icon">
      <SidebarHeader className="px-3 py-4">
        <div className="flex min-w-0 flex-col gap-1 group-data-[collapsible=icon]:items-center">
          <div className="flex items-baseline gap-1.5">
            <span className="shrink-0 text-base font-bold text-sidebar-foreground">明察</span>
            <span className="truncate text-sm font-medium text-sidebar-primary group-data-[collapsible=icon]:hidden">
              InsightFlow
            </span>
          </div>
          <span className="truncate text-xs text-sidebar-foreground/60 group-data-[collapsible=icon]:hidden">
            监控 · 分析 · 报告
          </span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarMenuSection
          label="任务"
          items={TASK_MENU_ITEMS}
          selectedKey={selectedKey}
          onSelect={handleMenuSelect}
        />
        <SidebarSeparator />
        <SidebarMenuSection
          label="分析"
          items={MENU_ITEMS}
          selectedKey={selectedKey}
          onSelect={handleMenuSelect}
        />
      </SidebarContent>
    </UiSidebar>
  );
};

export default React.memo(Sidebar);
