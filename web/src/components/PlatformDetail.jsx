import React, { useEffect, useMemo, useState } from 'react';
import { Card, Table, Typography, Button, Tag, Progress, Spin, theme } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { fetchBrandMetrics } from '@/api';
import { useDashboardRequestParams } from '@/hooks/useDashboardParams';
import { formatPercentage } from '../utils';

const PlatformDetail = ({
  platformName,
  onBack,
}) => {
  const { tenantKey, jobId, brand, timeframe, startDate, endDate } = useDashboardRequestParams();
  const { token } = theme.useToken();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState([]);

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();

    const fetchData = async () => {
      setLoading(true);
      try {
        const result = await fetchBrandMetrics(
          {
            tenantKey,
            jobId,
            timeframe,
            startDate,
            endDate,
            platform: platformName,
            brand,
          },
          { signal: controller.signal },
        );
        if (cancelled) return;
        const list = Array.isArray(result?.data) ? result.data : [];
        const sorted = [...list]
          .sort((a, b) => (b.mention_rate || 0) - (a.mention_rate || 0))
          .map((item, index) => ({
            rank: index + 1,
            name: item.brand,
            mentionRate: item.mention_rate,
            firstMentionRate: item.first_mention_rate,
          }));
        setData(sorted);
      } catch (err) {
        if (cancelled || err.name === 'AbortError') return;
        setData([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchData();
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [platformName, tenantKey, jobId, brand, timeframe, startDate, endDate]);

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
      <Spin spinning={loading}>
        <Table
          dataSource={data}
          columns={columns}
          pagination={false}
          rowKey="name"
        />
      </Spin>
    </Card>
  );
};

export default React.memo(PlatformDetail);
