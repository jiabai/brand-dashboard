import React, { useMemo } from 'react';
import { Table, Progress, Card, Tag, Space, Typography, Tooltip } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';

const { Text, Title } = Typography;

const MOCK_DATA = [
  { keyword: '三角洲陪玩', platform: 'deepseek', brand: '五九电竞', mention_rate: 0.6935, first_mention_rate: 0.0323 },
  { keyword: '三角洲陪玩', platform: 'deepseek', brand: '知悦电竞', mention_rate: 0.5161, first_mention_rate: 0.0000 },
  { keyword: '三角洲陪玩', platform: 'deepseek', brand: '河马电竞', mention_rate: 0.3871, first_mention_rate: 0.0000 },
  { keyword: '三角洲陪玩', platform: 'deepseek', brand: '哈基桃电竞', mention_rate: 0.1613, first_mention_rate: 0.0000 },
  { keyword: '三角洲陪玩', platform: 'deepseek', brand: '黛玉电竞', mention_rate: 0.0484, first_mention_rate: 0.0000 },
  { keyword: '三角洲陪玩俱乐部', platform: 'deepseek', brand: '河马电竞', mention_rate: 0.7321, first_mention_rate: 0.0000 },
  { keyword: '三角洲陪玩俱乐部', platform: 'deepseek', brand: '五九电竞', mention_rate: 0.4286, first_mention_rate: 0.0179 },
  { keyword: '三角洲陪玩俱乐部', platform: 'deepseek', brand: '知悦电竞', mention_rate: 0.2500, first_mention_rate: 0.0000 },
  { keyword: '三角洲陪玩俱乐部', platform: 'deepseek', brand: '黛玉电竞', mention_rate: 0.0714, first_mention_rate: 0.0000 },
  { keyword: '三角洲陪玩俱乐部', platform: 'deepseek', brand: '哈基桃电竞', mention_rate: 0.0536, first_mention_rate: 0.0000 },
];

const BrandShareOfVoiceTable = () => {
  const keywordFilters = useMemo(() => {
    const keywords = [...new Set(MOCK_DATA.map(item => item.keyword))];
    return keywords.map(k => ({ text: k, value: k }));
  }, []);

  const platformFilters = useMemo(() => {
    const platforms = [...new Set(MOCK_DATA.map(item => item.platform))];
    return platforms.map(p => ({ text: p, value: p }));
  }, []);

  const columns = [
    {
      title: 'Keyword',
      dataIndex: 'keyword',
      key: 'keyword',
      filters: keywordFilters,
      onFilter: (value, record) => record.keyword === value,
      render: (text) => <Text strong>{text}</Text>,
    },
    {
      title: 'Platform',
      dataIndex: 'platform',
      key: 'platform',
      filters: platformFilters,
      onFilter: (value, record) => record.platform === value,
      render: (text) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: 'Brand',
      dataIndex: 'brand',
      key: 'brand',
      render: (text) => <Text>{text}</Text>,
    },
    {
      title: (
        <Space>
          Mention Rate
          <Tooltip title="Percentage of conversations where the brand was mentioned">
            <InfoCircleOutlined style={{ color: 'rgba(0,0,0,0.45)' }} />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'mention_rate',
      key: 'mention_rate',
      sorter: (a, b) => a.mention_rate - b.mention_rate,
      defaultSortOrder: 'descend',
      render: (value) => (
        <Space direction="vertical" style={{ width: '100%' }} size={0}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>{(value * 100).toFixed(2)}%</Text>
          </div>
          <Progress 
            percent={value * 100} 
            showInfo={false} 
            size="small" 
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
        </Space>
      ),
      width: 200,
    },
    {
      title: (
        <Space>
          First Mention Rate
          <Tooltip title="Percentage of conversations where the brand was mentioned first">
            <InfoCircleOutlined style={{ color: 'rgba(0,0,0,0.45)' }} />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'first_mention_rate',
      key: 'first_mention_rate',
      sorter: (a, b) => a.first_mention_rate - b.first_mention_rate,
      render: (value) => (
        <Space direction="vertical" style={{ width: '100%' }} size={0}>
           <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>{(value * 100).toFixed(2)}%</Text>
          </div>
          <Progress 
            percent={value * 100} 
            showInfo={false} 
            size="small" 
            strokeColor="#faad14"
          />
        </Space>
      ),
      width: 200,
    },
  ];

  return (
    <Card 
      title={<Title level={4} style={{ margin: 0 }}>Brand Share of Voice</Title>}
      bordered={false}
      style={{ margin: 24, borderRadius: 8 }}
    >
      <Table 
        columns={columns} 
        dataSource={MOCK_DATA} 
        rowKey={(record) => `${record.keyword}-${record.platform}-${record.brand}`}
        pagination={{ pageSize: 10 }}
      />
    </Card>
  );
};

export default BrandShareOfVoiceTable;
