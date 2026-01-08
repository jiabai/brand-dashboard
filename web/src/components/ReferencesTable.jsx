/**
 * 引用列表组件
 * 显示文章引用信息和引用率
 */

import React, { useState, useEffect } from 'react';
import { Button, Card, Empty, Table, Typography } from 'antd';

// 模拟数据 - 移到组件外部避免每次渲染重新创建
const MOCK_REFERENCES_DATA = [
  { rank: 1, domain: 'techcrunch.com', rate: 95 },
  { rank: 2, domain: 'reddit.com', rate: 88 },
  { rank: 3, domain: 'twitter.com', rate: 82 },
  { rank: 4, domain: 'youtube.com', rate: 76 },
  { rank: 5, domain: 'medium.com', rate: 71 }
];

const ReferencesTable = ({ referencesData, isLoading, error }) => {
  // 内部状态管理
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);

  // 模拟数据加载
  useEffect(() => {
    if (isLoading !== undefined) {
      setLoading(isLoading);
    } else {
      setLoading(true);
      const timer = setTimeout(() => {
        setData(MOCK_REFERENCES_DATA);
        setLoading(false);
      }, 1000);
      // 清理函数防止内存泄漏
      return () => clearTimeout(timer);
    }

    if (error) {
      setErrorMsg(error);
    }
  }, [isLoading, error, referencesData]);

  // 使用传入数据或模拟数据
  const displayData = referencesData || data;

  const columns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 80
    },
    {
      title: '链接域名',
      dataIndex: 'domain',
      key: 'domain',
      render: (domain) => (
        <Typography.Link href={`https://${domain}`} target="_blank" rel="noopener noreferrer">
          {domain}
        </Typography.Link>
      )
    },
    {
      title: '引用率',
      dataIndex: 'rate',
      key: 'rate',
      width: 120,
      render: (rate) => `${rate}%`
    }
  ];

  // 加载状态
  if (loading) {
    return (
      <Card title="引用链接详情" loading />
    );
  }

  // 错误状态
  if (errorMsg) {
    return (
      <Card title="引用链接详情">
        <Typography.Paragraph type="danger">{errorMsg}</Typography.Paragraph>
        <Button type="primary" onClick={() => window.location.reload()}>
          重试
        </Button>
      </Card>
    );
  }

  // 空状态
  if (!displayData || displayData.length === 0) {
    return (
      <Card title="引用链接详情">
        <Empty description="当前时间范围内没有可用的引用链接数据" />
      </Card>
    );
  }

  return (
    <Card title="引用链接详情">
      <Table
        rowKey="rank"
        size="middle"
        columns={columns}
        dataSource={displayData}
        pagination={false}
        loading={Boolean(isLoading)}
      />
    </Card>
  );
};

export default ReferencesTable;
