import React, { useEffect, useRef, useState } from 'react';
import { Card, List, Progress, Typography, Statistic, Tag, theme } from 'antd';
import { TrophyOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { fetchPlatformMetricsByBrand } from '@/api';
import { useDashboardRequestParams } from '@/hooks/useDashboardParams';
import { getPlatformColor, toPercent, clampPercent, roundTwoDecimals } from '@/utils';

const PlatformMentionRates = ({
  onPlatformClick,
}) => {
  const { timeframe, date, endDate, tenantKey, jobId, brand } = useDashboardRequestParams();
  const { token } = theme.useToken();
  const abortControllerRef = useRef(null);
  const [platforms, setPlatforms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const fetchPlatformData = async () => {
      try {
        setLoading(true);
        setError(null);

        const data = await fetchPlatformMetricsByBrand(
          { tenantKey, jobId, brand, timeframe, startDate: date, endDate: endDate || date },
          { signal: controller.signal },
        );

        if (data?.status && data.status !== 'success') {
          throw new Error('接口返回错误状态');
        }

        const list = Array.isArray(data?.data?.platforms) ? data.data.platforms : [];

        const nextPlatforms = list
          .map((item) => {
            const name = item?.platform;
            const rate = roundTwoDecimals(clampPercent(toPercent(item?.mention_rate ?? 0)));
            return {
              name,
              rate,
              color: getPlatformColor(name) || token.colorPrimary,
              change: 0,
            };
          })
          .filter((item) => item.name)
          .sort((a, b) => (b.rate || 0) - (a.rate || 0));

        setPlatforms(nextPlatforms);
        setLoading(false);
      } catch (err) {
        if (controller.signal.aborted) return;
        if (err?.name === 'AbortError') return;
        setError(err?.message || '数据加载失败');
        setLoading(false);
      }
    };

    fetchPlatformData();
    return () => {
      controller.abort();
    };
  }, [brand, date, endDate, jobId, tenantKey, timeframe, token.colorPrimary]);

  if (loading) {
    return (
      <Card title={`各平台提及率 (${brand})`} loading />
    );
  }

  if (error) {
    return (
      <Card title={`各平台提及率 (${brand})`}>
        <Typography.Text type="danger">{error}</Typography.Text>
      </Card>
    );
  }

  if (platforms.length === 0) {
    return (
      <Card title={`各平台提及率 (${brand})`}>
        <Typography.Text type="secondary">暂无平台数据</Typography.Text>
      </Card>
    );
  }

  return (
    <Card title={`各平台提及率 (${brand})`}>
      <List
        dataSource={platforms}
        renderItem={(platform, index) => (
          <List.Item
            style={{
              padding: token.padding,
              marginBottom: token.marginSM,
              borderRadius: token.borderRadiusLG,
              background: index < 3 ? token.colorFillAlter : 'transparent',
              border: index < 3 ? `1px solid ${token.colorBorderSecondary}` : 'none',
              transition: 'all 0.3s ease',
              cursor: 'pointer'
            }}
            onClick={() => {
              if (onPlatformClick) {
                onPlatformClick(platform);
              }
            }}
          >
            <div style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: token.marginXS }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: token.marginSM }}>
                  {index < 3 && (
                    <Tag color={platform.color} icon={<TrophyOutlined />}>
                      {index + 1}
                    </Tag>
                  )}
                  <Typography.Text strong style={{ fontSize: index < 3 ? token.fontSizeLG : token.fontSize }}>
                    {platform.name}
                  </Typography.Text>
                </div>
                <Statistic
                  value={platform.rate}
                  suffix="%"
                  precision={2}
                  valueStyle={{ color: platform.color, fontSize: token.fontSizeXL, fontWeight: 'bold' }}
                />
              </div>
              <Progress
                percent={platform.rate}
                showInfo={false}
                strokeColor={platform.color}
                size={['100%', 8]}
              />
              {platform.change !== 0 && (
                <div style={{ marginTop: token.marginXS, display: 'flex', alignItems: 'center', gap: '4px' }}>
                  {platform.change > 0 ? (
                    <ArrowUpOutlined style={{ color: token.colorSuccess, fontSize: token.fontSizeSM }} />
                  ) : (
                    <ArrowDownOutlined style={{ color: token.colorError, fontSize: token.fontSizeSM }} />
                  )}
                  <Typography.Text type={platform.change > 0 ? 'success' : 'danger'} style={{ fontSize: token.fontSizeSM }}>
                    {Math.abs(platform.change)}%
                  </Typography.Text>
                </div>
              )}
            </div>
          </List.Item>
        )}
      />
    </Card>
  );
};

export default React.memo(PlatformMentionRates);
