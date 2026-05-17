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
import { useDashboardParams } from '@/hooks/useDashboardParams';
import { buildRouteSearch, buildViewPath, getViewKeyFromPath } from '@/utils/routing';

const MENU_ITEMS = [
  { key: 'home', icon: <HomeOutlined />, label: '首页' },
  { key: 'trend', icon: <LineChartOutlined />, label: '趋势分析' },
  { key: 'platforms', icon: <BarChartOutlined />, label: '分平台分析' },
  { key: 'sources', icon: <MessageOutlined />, label: '信源分析' },
  { key: 'sentiment', icon: <SmileOutlined />, label: '情感分析' },
  { key: 'snapshots', icon: <PictureOutlined />, label: '问答快照', disabled: true },
  { key: 'settings', icon: <SettingOutlined />, label: '品牌设置', disabled: true },
  { key: 'accounts', icon: <UserOutlined />, label: '账户管理' },
  { key: 'subscribe', icon: <BookOutlined />, label: '订阅', disabled: true }
];

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
    // 禁用这些特定键的跳转
    if (['snapshots', 'settings', 'subscribe'].includes(key)) {
      return;
    }
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
          items={[
            {
              key: 'task-load',
              icon: <PlusOutlined />,
              label: '新建任务'
            },
            {
              key: 'task-status',
              icon: <UnorderedListOutlined />,
              label: '任务状态'
            }
          ]}
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
