import React, { useMemo } from 'react';
import { Card, Table, Typography, Button, Tag, Progress, theme } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { formatPercentage } from '../utils';

const PlatformDetail = ({ platformName, onBack }) => {
  const { token } = theme.useToken();

  const data = useMemo(() => {
    return [
      { rank: 1, name: "海尔", mentionRate: 85.5, firstMentionRate: 45.2 },
      { rank: 2, name: "美的", mentionRate: 78.3, firstMentionRate: 40.1 },
      { rank: 3, name: "格力", mentionRate: 72.1, firstMentionRate: 35.5 },
      { rank: 4, name: "西门子", mentionRate: 65.8, firstMentionRate: 32.0 },
      { rank: 5, name: "松下", mentionRate: 58.2, firstMentionRate: 28.5 },
      { rank: 6, name: "小米", mentionRate: 45.0, firstMentionRate: 20.1 },
      { rank: 7, name: "TCL", mentionRate: 32.5, firstMentionRate: 15.3 },
    ];
  }, [platformName]);

  const columns = useMemo(() => {
    return [
      {
        title: '排名',
        dataIndex: 'rank',
        key: 'rank',
        width: 80,
        render: (rank) => (
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <Tag color={rank <= 3 ? 'gold' : 'default'} style={{ margin: 0, minWidth: 24, textAlign: 'center' }}>{rank}</Tag>
          </div>
        ),
      },
      {
        title: '品牌',
        dataIndex: 'name',
        key: 'name',
        width: 120,
        render: (text) => <Typography.Text strong>{text}</Typography.Text>,
      },
      {
        title: '提及率',
        dataIndex: 'mentionRate',
        key: 'mentionRate',
        render: (val) => (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Progress percent={val} size="small" showInfo={false} strokeColor={token.colorPrimary} style={{ width: 120 }} />
            <Typography.Text>{formatPercentage(val)}</Typography.Text>
          </div>
        ),
        sorter: (a, b) => a.mentionRate - b.mentionRate,
      },
      {
        title: '首位提及率',
        dataIndex: 'firstMentionRate',
        key: 'firstMentionRate',
        render: (val) => (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Progress percent={val} size="small" showInfo={false} strokeColor={token.colorInfo} style={{ width: 120 }} />
            <Typography.Text type="secondary">{formatPercentage(val)}</Typography.Text>
          </div>
        ),
        sorter: (a, b) => a.firstMentionRate - b.firstMentionRate,
      },
    ];
  }, [token.colorInfo, token.colorPrimary]);

  return (
    <Card 
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Button 
            type="text" 
            icon={<ArrowLeftOutlined />} 
            onClick={onBack}
          />
          <span>{platformName} - 品牌提及率排名</span>
        </div>
      }
      style={{ height: '100%' }}
    >
      <Table 
        dataSource={data} 
        columns={columns} 
        pagination={false} 
        rowKey="name"
      />
    </Card>
  );
};

export default React.memo(PlatformDetail);
