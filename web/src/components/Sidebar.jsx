import React, { useMemo } from 'react';
import { Layout, Menu, Typography, theme } from 'antd';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  BarChartOutlined,
  BookOutlined,
  HomeOutlined,
  LineChartOutlined,
  MessageOutlined,
  PictureOutlined,
  PlusOutlined,
  SmileOutlined,
  SettingOutlined,
  UnorderedListOutlined,
  UserOutlined
} from '@ant-design/icons';
import { getSidebarMenuRoutes, getTaskMenuRoutes } from '@/config/routes';
import { useDashboardParams } from '@/hooks/useDashboardParams';
import { buildRouteSearch, buildViewPath, getViewKeyFromPath } from '@/utils/routing';

const MENU_ICON_MAP = {
  BarChartOutlined: <BarChartOutlined />,
  BookOutlined: <BookOutlined />,
  HomeOutlined: <HomeOutlined />,
  LineChartOutlined: <LineChartOutlined />,
  MessageOutlined: <MessageOutlined />,
  PictureOutlined: <PictureOutlined />,
  PlusOutlined: <PlusOutlined />,
  SettingOutlined: <SettingOutlined />,
  SmileOutlined: <SmileOutlined />,
  UnorderedListOutlined: <UnorderedListOutlined />,
  UserOutlined: <UserOutlined />,
};

const toMenuItem = (route) => ({
  key: route.viewKey,
  icon: MENU_ICON_MAP[route.menuIcon],
  label: route.menuLabel,
  disabled: Boolean(route.disabled),
});

const MENU_ITEMS = getSidebarMenuRoutes().map(toMenuItem);
const TASK_MENU_ITEMS = getTaskMenuRoutes().map(toMenuItem);

const Sidebar = ({ collapsed, onCollapse }) => {
  const { token } = theme.useToken();
  const navigate = useNavigate();
  const location = useLocation();
  const { tenantKey, jobId } = useDashboardParams();
  const selectedKey = useMemo(
    () => getViewKeyFromPath(location.pathname),
    [location.pathname],
  );

  const handleMenuClick = ({ key }) => {
    const pathname = buildViewPath(key, { tenantKey, jobId });
    const search = buildRouteSearch({
      search: location.search,
      nextViewKey: key,
    });
    navigate(`${pathname}${search}`);
  };

  return (
    <Layout.Sider
      width={240}
      collapsible
      collapsed={collapsed}
      onCollapse={onCollapse}
      style={{
        borderRight: `1px solid ${token.colorBorderSecondary}`,
        position: 'sticky',
        top: 0,
        height: '100vh',
        background: token.colorBgContainer
      }}
    >
      <div style={{ 
        padding: collapsed ? `${token.padding}px 0` : token.padding,
        display: 'flex',
        justifyContent: 'center'
      }}>
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          gap: 4,
          alignItems: collapsed ? 'center' : 'flex-start',
          width: '100%'
        }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'baseline', 
            gap: 6,
            justifyContent: collapsed ? 'center' : 'flex-start'
          }}>
            <Typography.Text style={{ 
              fontSize: 16, 
              fontWeight: 700, 
              color: token.colorText,
              flexShrink: 0
            }}>
              明察
            </Typography.Text>
            {!collapsed && (
              <Typography.Text style={{ 
                fontSize: 15, 
                fontWeight: 500, 
                color: token.colorPrimary,
                whiteSpace: 'nowrap'
              }}>
                InsightFlow
              </Typography.Text>
            )}
          </div>
          {!collapsed ? (
            <Typography.Text type="secondary" style={{ fontSize: 12, whiteSpace: 'nowrap' }}>
              监控 · 分析 · 报告
            </Typography.Text>
          ) : null}
        </div>
      </div>

      <div style={{ paddingInline: token.paddingSM, paddingBottom: token.paddingSM }}>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          onClick={handleMenuClick}
          items={TASK_MENU_ITEMS}
          style={{ border: 'none' }}
        />
      </div>

      <Menu
        mode="inline"
        selectedKeys={[selectedKey]}
        onClick={handleMenuClick}
        items={MENU_ITEMS}
        style={{ border: 'none' }}
      />
    </Layout.Sider>
  );
};

export default React.memo(Sidebar);
