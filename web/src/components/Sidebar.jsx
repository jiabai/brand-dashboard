import React from 'react';
import { Layout, Menu, Typography } from 'antd';
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

const Sidebar = ({ collapsed, onCollapse }) => {
  const menuItems = [
    { key: 'home', icon: <HomeOutlined />, label: '首页' },
    { key: 'trend', icon: <LineChartOutlined />, label: '趋势分析' },
    { key: 'models', icon: <BarChartOutlined />, label: '分模型分析' },
    { key: 'sources', icon: <MessageOutlined />, label: '信源分析' },
    { key: 'snapshots', icon: <PictureOutlined />, label: '问答快照' },
    { key: 'settings', icon: <SettingOutlined />, label: '品牌设置' },
    { key: 'subscribe', icon: <BookOutlined />, label: '订阅' }
  ];

  return (
    <Layout.Sider
      theme="light"
      width={240}
      collapsible
      collapsed={collapsed}
      onCollapse={onCollapse}
      style={{
        borderRight: '1px solid rgba(5, 5, 5, 0.06)',
        position: 'sticky',
        top: 0,
        height: '100vh'
      }}
    >
      <div style={{ padding: 16 }}>
        <Typography.Title level={5} style={{ margin: 0 }}>
          Brand Dashboard
        </Typography.Title>
        {!collapsed ? (
          <Typography.Text type="secondary">监控 · 分析 · 报告</Typography.Text>
        ) : null}
      </div>

      <div style={{ paddingInline: 12, paddingBottom: 12 }}>
        <Menu
          mode="inline"
          defaultSelectedKeys={['home']}
          items={[
            {
              key: 'task',
              icon: <PlusOutlined />,
              label: '任务'
            }
          ]}
        />
      </div>

      <Menu mode="inline" defaultSelectedKeys={['home']} items={menuItems} />
    </Layout.Sider>
  );
};

export default Sidebar;
