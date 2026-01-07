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
import { Card, Col, List, Progress, Row, Space, Tag, Typography } from 'antd';

// Utilities
import { DEFAULT_BRAND_DATA, formatPercentage } from '@/utils';

// Components
import LoadingSpinner from './LoadingSpinner';
import EmptyState from './EmptyState';

// Mock brand ranking data for demonstration
const BRAND_RANKINGS = [
  { rank: 1, text: "海尔", percent: 85.5, change: "up" },
  { rank: 2, text: "美的", percent: 78.3, change: "stable" },
  { rank: 3, text: "格力", percent: 72.1, change: "down" },
  { rank: 4, text: "西门子", percent: 65.8, change: "up" },
  { rank: 5, text: "松下", percent: 58.2, change: "up" },
  { rank: 6, text: "三星", percent: 52.7, change: "stable" },
  { rank: 7, text: "LG", percent: 48.3, change: "down" },
  { rank: 8, text: "TCL", percent: 42.1, change: "up" },
  { rank: 9, text: "海信", percent: 38.6, change: "stable" },
  { rank: 10, text: "小米", percent: 35.2, change: "down" }
];

/**
 * BrandMentionRate component displays circular progress and keyword rankings
 *
 * @param {Object} props - Component props
 * @param {Object} props.brandData - Brand mention data
 * @param {boolean} props.isLoading - Loading state
 * @param {string} props.error - Error message
 * @returns {JSX.Element} Brand mention rate UI
 */
const BrandMentionRate = ({ brandData, isLoading, error }) => {
  // Data validation and default value handling
  const data = brandData && typeof brandData === 'object'
    ? { ...DEFAULT_BRAND_DATA, ...brandData }
    : DEFAULT_BRAND_DATA;

  // Loading state
  if (isLoading) {
    return (
      <Card title="品牌总提及率">
        <LoadingSpinner text="正在加载品牌数据..." />
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card title="品牌总提及率">
        <EmptyState
          title="数据加载失败"
          description={error}
          actionText="重试"
          onAction={() => window.location.reload()}
        />
      </Card>
    );
  }

  // Empty state
  if (!data.mentionRate && data.mentionRate !== 0) {
    return (
      <Card title="品牌总提及率">
        <EmptyState
          title="暂无品牌数据"
          description="当前时间范围内没有可用的品牌提及数据"
        />
      </Card>
    );
  }

  // Split brand rankings into two columns
  const leftBrands = BRAND_RANKINGS.slice(0, 5);
  const rightBrands = BRAND_RANKINGS.slice(5, 10);

  const renderBrand = (item) => {
    const rankColor =
      item.rank === 1 ? 'gold' : item.rank === 2 ? 'blue' : item.rank === 3 ? 'geekblue' : 'default';

    return (
      <List.Item style={{ paddingInline: 0 }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space size="small">
            <Tag color={rankColor} style={{ marginInlineEnd: 0 }}>
              {item.rank}
            </Tag>
            <Typography.Text strong>{item.text}</Typography.Text>
          </Space>
          <Typography.Text>{formatPercentage(item.percent)}</Typography.Text>
        </Space>
      </List.Item>
    );
  };

  return (
    <Card title="品牌总提及率">
      <Row gutter={[16, 16]} align="middle">
        <Col xs={24} sm={10} style={{ display: 'flex', justifyContent: 'center' }}>
          <Space direction="vertical" align="center" size="small">
            <Progress type="circle" percent={Number(data.mentionRate)} />
            <Typography.Text type="secondary">变化: +{formatPercentage(data.change)}</Typography.Text>
          </Space>
        </Col>
        <Col xs={24} sm={14}>
          <Row gutter={16}>
            <Col span={12}>
              <List size="small" dataSource={leftBrands} renderItem={renderBrand} />
            </Col>
            <Col span={12}>
              <List size="small" dataSource={rightBrands} renderItem={renderBrand} />
            </Col>
          </Row>
        </Col>
      </Row>
    </Card>
  );
}

export default BrandMentionRate;
