import React from 'react';
import { Layout, Menu, Typography, theme } from 'antd';
import {
  BarChartOutlined,
  BookOutlined,
  HomeOutlined,
  LineChartOutlined,
  MessageOutlined,
  PictureOutlined,
  PlusOutlined,
  SettingOutlined
} from '@ant-design/icons';

const MENU_ITEMS = [
  { key: 'home', icon: <HomeOutlined />, label: '首页' },
  { key: 'trend', icon: <LineChartOutlined />, label: '趋势分析' },
  { key: 'platforms', icon: <BarChartOutlined />, label: '分平台分析' },
  { key: 'sources', icon: <MessageOutlined />, label: '信源分析' },
  { key: 'snapshots', icon: <PictureOutlined />, label: '问答快照' },
  { key: 'settings', icon: <SettingOutlined />, label: '品牌设置' },
  { key: 'subscribe', icon: <BookOutlined />, label: '订阅' }
];

const Sidebar = ({ collapsed, onCollapse, onMenuClick, selectedKey }) => {
  const { token } = theme.useToken();

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
      <div style={{ padding: token.padding }}>
        <Typography.Title level={5} style={{ margin: 0 }}>
          Brand Dashboard
        </Typography.Title>
        {!collapsed ? (
          <Typography.Text type="secondary">监控 · 分析 · 报告</Typography.Text>
        ) : null}
      </div>

      <div style={{ paddingInline: token.paddingSM, paddingBottom: token.paddingSM }}>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          onClick={({ key }) => onMenuClick && onMenuClick(key)}
          items={[
            {
              key: 'task-load',
              icon: <PlusOutlined />,
              label: '加载任务'
            }
          ]}
          style={{ border: 'none' }}
        />
      </div>

      <Menu
        mode="inline"
        selectedKeys={[selectedKey]}
        onClick={({ key }) => onMenuClick && onMenuClick(key)}
        items={MENU_ITEMS}
        style={{ border: 'none' }}
      />
    </Layout.Sider>
  );
};

export default React.memo(Sidebar);
