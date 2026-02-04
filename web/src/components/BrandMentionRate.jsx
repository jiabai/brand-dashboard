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

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Card, Table, Typography, Statistic, Row, Col, Divider, Tag, Progress, Space, theme } from 'antd';
import { 
  TrophyOutlined, 
  MessageOutlined, 
  LinkOutlined, 
  TagsOutlined 
} from '@ant-design/icons';

// Utilities
import { formatPercentage } from '@/utils';
import { CONFIG } from '@/config';

// Components
import LoadingSpinner from './LoadingSpinner';
import EmptyState from './EmptyState';

const { DEFAULT_TENANT_KEY, DEFAULT_JOB_ID, DEFAULT_BRAND } = CONFIG;

const buildQueryString = (params) => {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null) return;
    searchParams.set(key, String(value));
  });
  return searchParams.toString();
};

const fetchJson = async (url, { signal } = {}) => {
  const response = await fetch(url, { method: 'GET', signal });
  if (!response.ok) {
    throw new Error(`请求失败(${response.status})`);
  }
  return response.json();
};

const toPercent = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return 0;
  // 统一处理：如果是小数形式（<=1）则乘以100，否则直接返回
  // 注意：1.0 也是 100%
  return num <= 1 ? num * 100 : num;
};

const clampPercent = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return 0;
  return Math.max(0, Math.min(100, num));
};

const roundTwoDecimals = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return 0;
  return Math.round(num * 100) / 100;
};

/**
 * BrandMentionRate component
 */
const BrandMentionRate = ({
  timeframe = '7days',
  date = '',
  tenantKey = DEFAULT_TENANT_KEY,
  jobId = DEFAULT_JOB_ID,
  brand = DEFAULT_BRAND,
}) => {
  const { token } = theme.useToken();
  const abortControllerRef = useRef(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortedInfo, setSortedInfo] = useState({
    columnKey: 'mentionRate',
    order: 'descend',
  });
  const [targetBrandData, setTargetBrandData] = useState(null);
  const [brandList, setBrandList] = useState([]);

  const brandMetricsQueryString = useMemo(
    () =>
      buildQueryString({
        tenant_key: tenantKey,
        job_id: jobId,
        timeframe,
        date,
      }),
    [tenantKey, jobId, timeframe, date],
  );

  const targetBrandQueryString = useMemo(
    () =>
      buildQueryString({
        tenant_key: tenantKey,
        job_id: jobId,
        timeframe,
        date,
        brand,
      }),
    [tenantKey, jobId, timeframe, date, brand],
  );

  const handleTableChange = (_, __, sorter) => {
    const nextSorter = Array.isArray(sorter) ? sorter[0] : sorter;
    if (!nextSorter || !nextSorter.columnKey) {
      return;
    }
    setSortedInfo({
      columnKey: nextSorter.columnKey,
      order: nextSorter.order || 'descend',
    });
  };

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
      title: '总提及率',
      dataIndex: 'mentionRate',
      key: 'mentionRate',
      render: (val) => (
        <div style={{ width: 120 }}>
          <Progress percent={val} size="small" showInfo={false} strokeColor={token.colorPrimary} />
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>{formatPercentage(val)}</Typography.Text>
        </div>
      ),
      sorter: (a, b) => a.mentionRate - b.mentionRate,
      defaultSortOrder: 'descend',
      sortOrder: sortedInfo.columnKey === 'mentionRate' ? sortedInfo.order : null,
    },
    {
      title: '首位提及率',
      dataIndex: 'firstMentionRate',
      key: 'firstMentionRate',
      render: (val) => (
        <div style={{ width: 120 }}>
          <Progress percent={val} size="small" showInfo={false} strokeColor={token.colorInfo} />
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>{formatPercentage(val)}</Typography.Text>
        </div>
      ),
      sorter: (a, b) => a.firstMentionRate - b.firstMentionRate,
      sortOrder: sortedInfo.columnKey === 'firstMentionRate' ? sortedInfo.order : null,
    },
    {
      title: '前3提及率',
      dataIndex: 'top3MentionRate',
      key: 'top3MentionRate',
      render: (val) => (
        <div style={{ width: 120 }}>
          <Progress percent={val} size="small" showInfo={false} strokeColor={token.colorWarning} />
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>{formatPercentage(val)}</Typography.Text>
        </div>
      ),
      sorter: (a, b) => a.top3MentionRate - b.top3MentionRate,
      sortOrder: sortedInfo.columnKey === 'top3MentionRate' ? sortedInfo.order : null,
    },
  ];

  const targetBrandName = targetBrandData?.name ?? brand;

  const { otherBrandsData, targetBrandRank } = useMemo(() => {
    if (!brandList.length) {
      return { otherBrandsData: [], targetBrandRank: null };
    }

    const metricKey =
      sortedInfo.columnKey === 'firstMentionRate' ? 'firstMentionRate' : 'mentionRate';
    const order = sortedInfo.order || 'descend';

    const listWithMetric = brandList.filter(
      (item) => typeof item[metricKey] === 'number',
    );

    const sorted = [...listWithMetric].sort((a, b) => {
      const diff = (a[metricKey] || 0) - (b[metricKey] || 0);
      return order === 'ascend' ? diff : -diff;
    });

    const ranked = sorted.map((item, index) => ({
      ...item,
      rank: index + 1,
    }));

    const targetIndex = ranked.findIndex((item) => item.name === targetBrandName);
    const rankValue = targetIndex === -1 ? null : ranked[targetIndex].rank;

    const others = ranked.filter((item) => item.name !== targetBrandName);

    return { otherBrandsData: others, targetBrandRank: rankValue };
  }, [brandList, sortedInfo, targetBrandName]);

  useEffect(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const run = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const [brandMetrics, postCitationRate] = await Promise.all([
          fetchJson(`/api/v1/dashboard/brand-metrics?${brandMetricsQueryString}`, {
            signal: controller.signal,
          }),
          fetchJson(`/api/v1/dashboard/post-citation-rate?${targetBrandQueryString}`, {
            signal: controller.signal,
          }),
        ]);

        if (brandMetrics?.status && brandMetrics.status !== 'success') {
          throw new Error('接口返回错误状态');
        }
        if (postCitationRate?.status && postCitationRate.status !== 'success') {
          throw new Error('接口返回错误状态');
        }

        const brandMetricsList = Array.isArray(brandMetrics?.data)
          ? brandMetrics.data
          : Array.isArray(brandMetrics)
          ? brandMetrics
          : [];
        const postCitationRateData = postCitationRate?.data?.[0] ?? postCitationRate;

        const normalizedBrandItems = brandMetricsList.map((item) => ({
          name: item?.brand,
          mentionRate: roundTwoDecimals(clampPercent(toPercent(item?.mention_rate ?? 0))),
          firstMentionRate: roundTwoDecimals(clampPercent(toPercent(item?.first_mention_rate ?? 0))),
          top3MentionRate: roundTwoDecimals(clampPercent(toPercent(item?.top3_mention_rate ?? 0))),
          promptValue: Number(item?.prompt_count ?? 0),
          coveredKeywordsCount: Number(item?.keyword_coverage ?? 0),
        }));

        setBrandList(normalizedBrandItems);

        const effectiveTargetName = brand || DEFAULT_BRAND;
        const targetItem =
          normalizedBrandItems.find((item) => item.name === effectiveTargetName) ??
          normalizedBrandItems[0];

        const nextTargetBrandData = targetItem
          ? {
              name: targetItem.name ?? effectiveTargetName,
              mentionRate: roundTwoDecimals(targetItem.mentionRate),
              firstMentionRate: roundTwoDecimals(targetItem.firstMentionRate),
              top3MentionRate: roundTwoDecimals(targetItem.top3MentionRate),
              articleCitationRate: roundTwoDecimals(clampPercent(
                toPercent(postCitationRateData?.citation_rate_by_post ?? 0),
              )),
              promptValue: targetItem.promptValue,
              citationSourceValue: Number(postCitationRateData?.citation_source_count ?? 0),
              coveredKeywordsCount: targetItem.coveredKeywordsCount,
            }
          : null;

        setTargetBrandData(nextTargetBrandData);
        setIsLoading(false);
      } catch (err) {
        if (controller.signal.aborted) return;
        if (err?.name === 'AbortError') return;
        setError(err?.message || '数据加载失败');
        setIsLoading(false);
      }
    };

    run();

    return () => {
      controller.abort();
    };
  }, [brandMetricsQueryString, targetBrandQueryString]);

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

  if (!targetBrandData) {
    return (
      <Card title="品牌提及排名">
        <EmptyState
          title="暂无数据"
          description="接口未返回可展示的数据"
          actionText="重试"
          onAction={() => window.location.reload()}
        />
      </Card>
    );
  }

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
                    {typeof targetBrandRank === 'number' ? `#${targetBrandRank}` : '--'}
                  </Typography.Title>
                </div>
                <div>
                  <Typography.Title level={4} style={{ margin: 0 }}>
                    目标品牌: {targetBrandData.name}
                  </Typography.Title>
                  <Space size="small" style={{ marginTop: 4 }}>
                    <Tag icon={<TagsOutlined />} color="processing">
                       {targetBrandData.coveredKeywordsCount} 覆盖关键词
                    </Tag>
                  </Space>
                </div>
             </div>
          </Col>

          {/* Key Rates - Circular Progress */}
          <Col span={6} style={{ display: 'flex', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center' }}>
              <Progress type="circle" percent={targetBrandData.mentionRate} size={80} strokeColor={token.colorPrimary} />
              <div style={{ marginTop: 8, fontWeight: 500 }}>总提及率</div>
            </div>
          </Col>
          <Col span={6} style={{ display: 'flex', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center' }}>
              <Progress type="circle" percent={targetBrandData.firstMentionRate} size={80} strokeColor={token.colorInfo} />
              <div style={{ marginTop: 8, fontWeight: 500 }}>首位提及率</div>
            </div>
          </Col>
          <Col span={6} style={{ display: 'flex', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center' }}>
              <Progress type="circle" percent={targetBrandData.top3MentionRate} size={80} strokeColor={token.colorWarning} />
              <div style={{ marginTop: 8, fontWeight: 500 }}>前3提及率</div>
            </div>
          </Col>
          <Col span={6} style={{ display: 'flex', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center' }}>
              <Progress type="circle" percent={targetBrandData.articleCitationRate} size={80} strokeColor={token.colorSuccess} />
              <div style={{ marginTop: 8, fontWeight: 500 }}>发文引用率</div>
            </div>
          </Col>

          {/* Other Metrics - Grid */}
          <Col span={24}>
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Card size="small" variant="borderless" style={{ background: token.colorFillQuaternary }}>
                  <Statistic 
                    title="问题总数" 
                    value={targetBrandData.promptValue} 
                    prefix={<MessageOutlined />} 
                    valueStyle={{ fontSize: 18 }}
                  />
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small" variant="borderless" style={{ background: token.colorFillQuaternary }}>
                  <Statistic 
                    title="引用信源数量" 
                    value={targetBrandData.citationSourceValue} 
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
        dataSource={otherBrandsData} 
        columns={columns} 
        pagination={false} 
        size="small"
        rowKey="name"
        scroll={{ x: 'max-content' }}
        onChange={handleTableChange}
      />
    </Card>
  );
}

export default React.memo(BrandMentionRate);
