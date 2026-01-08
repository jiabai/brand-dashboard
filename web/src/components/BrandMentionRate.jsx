/**
 * Brand Mention Rate Component
 * Displays brand mention rate with circular progress chart and brand rankings
 *
 * @component
 * @example
 * return (
 *   <BrandMentionRate
 *     brandData={{ mentionRate: 85, rank: 1, change: 5 }}
 *     isLoading={false}
 *     error={null}
 *   />
 * );
 */

import React from 'react';
import { Card, Table, Typography, Statistic, Row, Col, Divider, Tag, Progress, Space, theme } from 'antd';
import { 
  TrophyOutlined, 
  RiseOutlined, 
  FileTextOutlined, 
  MessageOutlined, 
  LinkOutlined, 
  TagsOutlined 
} from '@ant-design/icons';

// Utilities
import { formatPercentage } from '@/utils';

// Components
import LoadingSpinner from './LoadingSpinner';
import EmptyState from './EmptyState';

// Mock data
const TARGET_BRAND_DATA = {
  name: "海尔",
  rank: 1,
  mentionRate: 85.5,
  firstMentionRate: 45.2,
  articleCitationRate: 30.5,
  promptValue: 95,
  citationSourceValue: 120,
  coveredKeywordsCount: 350
};

const OTHER_BRANDS_DATA = [
  { rank: 2, name: "美的", mentionRate: 78.3, firstMentionRate: 40.1 },
  { rank: 3, name: "格力", mentionRate: 72.1, firstMentionRate: 35.5 },
  { rank: 4, name: "西门子", mentionRate: 65.8, firstMentionRate: 32.0 },
  { rank: 5, name: "松下", mentionRate: 58.2, firstMentionRate: 28.5 },
];

/**
 * BrandMentionRate component
 */
const BrandMentionRate = ({ isLoading, error }) => {
  const { token } = theme.useToken();

  // Loading state
  if (isLoading) {
    return (
      <Card title="品牌提及排名">
        <LoadingSpinner text="正在加载品牌数据..." />
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card title="品牌提及排名">
        <EmptyState
          title="数据加载失败"
          description={error}
          actionText="重试"
          onAction={() => window.location.reload()}
        />
      </Card>
    );
  }

  const columns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 60,
      render: (rank) => (
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <Tag color={rank <= 3 ? 'blue' : 'default'} style={{ margin: 0 }}>{rank}</Tag>
        </div>
      ),
    },
    {
      title: '品牌',
      dataIndex: 'name',
      key: 'name',
      width: 80,
      render: (text) => <Typography.Text strong>{text}</Typography.Text>,
    },
    {
      title: '提及率',
      dataIndex: 'mentionRate',
      key: 'mentionRate',
      render: (val) => (
        <div style={{ width: 120 }}>
          <Progress percent={val} size="small" showInfo={false} strokeColor={token.colorPrimary} />
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>{formatPercentage(val)}</Typography.Text>
        </div>
      ),
      sorter: (a, b) => a.mentionRate - b.mentionRate,
    },
    {
      title: '首次提及率',
      dataIndex: 'firstMentionRate',
      key: 'firstMentionRate',
      render: (val) => (
        <div style={{ width: 120 }}>
          <Progress percent={val} size="small" showInfo={false} strokeColor={token.colorInfo} />
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>{formatPercentage(val)}</Typography.Text>
        </div>
      ),
      sorter: (a, b) => a.firstMentionRate - b.firstMentionRate,
    },
  ];

  return (
    <Card title="品牌提及排名" className="h-full">
      <div className="mb-6">
        <Row gutter={[24, 24]} align="middle">
          {/* Rank & Name */}
          <Col span={24}>
             <div style={{ 
               display: 'flex', 
               alignItems: 'center', 
               background: token.colorFillAlter, 
               padding: '16px', 
               borderRadius: token.borderRadiusLG,
               border: `1px solid ${token.colorBorderSecondary}`
             }}>
                <div style={{ 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  marginRight: 24,
                  minWidth: 80
                }}>
                  <TrophyOutlined style={{ fontSize: 32, color: token.colorWarning }} />
                  <Typography.Title level={2} style={{ margin: 0, color: token.colorWarning }}>
                    #{TARGET_BRAND_DATA.rank}
                  </Typography.Title>
                </div>
                <div>
                  <Typography.Title level={4} style={{ margin: 0 }}>
                    目标品牌: {TARGET_BRAND_DATA.name}
                  </Typography.Title>
                  <Space size="small" style={{ marginTop: 4 }}>
                    <Tag icon={<TagsOutlined />} color="processing">
                       {TARGET_BRAND_DATA.coveredKeywordsCount} 覆盖关键词
                    </Tag>
                  </Space>
                </div>
             </div>
          </Col>

          {/* Key Rates - Circular Progress */}
          <Col span={8} style={{ display: 'flex', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center' }}>
              <Progress type="circle" percent={TARGET_BRAND_DATA.mentionRate} width={80} strokeColor={token.colorPrimary} />
              <div style={{ marginTop: 8, fontWeight: 500 }}>提及率</div>
            </div>
          </Col>
          <Col span={8} style={{ display: 'flex', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center' }}>
              <Progress type="circle" percent={TARGET_BRAND_DATA.firstMentionRate} width={80} strokeColor={token.colorInfo} />
              <div style={{ marginTop: 8, fontWeight: 500 }}>首次提及率</div>
            </div>
          </Col>
          <Col span={8} style={{ display: 'flex', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center' }}>
              <Progress type="circle" percent={TARGET_BRAND_DATA.articleCitationRate} width={80} strokeColor={token.colorSuccess} />
              <div style={{ marginTop: 8, fontWeight: 500 }}>发文引用率</div>
            </div>
          </Col>

          {/* Other Metrics - Grid */}
          <Col span={24}>
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Card size="small" bordered={false} style={{ background: token.colorFillQuaternary }}>
                  <Statistic 
                    title="Prompt 数值" 
                    value={TARGET_BRAND_DATA.promptValue} 
                    prefix={<MessageOutlined />} 
                    valueStyle={{ fontSize: 18 }}
                  />
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small" bordered={false} style={{ background: token.colorFillQuaternary }}>
                  <Statistic 
                    title="引用信源数值" 
                    value={TARGET_BRAND_DATA.citationSourceValue} 
                    prefix={<LinkOutlined />} 
                    valueStyle={{ fontSize: 18 }}
                  />
                </Card>
              </Col>
            </Row>
          </Col>
        </Row>
      </div>
      
      <Divider orientation="left" style={{ margin: '12px 0' }}>其他品牌对比</Divider>
      
      <Table 
        dataSource={OTHER_BRANDS_DATA} 
        columns={columns} 
        pagination={false} 
        size="small"
        rowKey="name"
        scroll={{ x: 'max-content' }}
      />
    </Card>
  );
}

export default BrandMentionRate;
