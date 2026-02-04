import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Card, List, Progress, Typography, Statistic, Tag, theme } from 'antd';
import { TrophyOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { CONFIG } from '@/config';

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
  if (num > 0 && num <= 1) return num * 100;
  return num;
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

const PLATFORM_COLORS = {
  chatgpt: '#10b981',
  gemini: '#3b82f6',
  claude: '#f59e0b',
  '通义千问': '#ef4444',
  qwen: '#ef4444',
  豆包: '#8b5cf6',
  deepseek: '#06b6d4',
  kimi: '#a855f7',
  元宝: '#f97316',
  夸克: '#ec4899',
  文心一言: '#6b7280',
};

const getPlatformColor = (name) => {
  const raw = String(name || '').trim();
  if (!raw) return '#6b7280';
  const keyLower = raw.toLowerCase();
  return PLATFORM_COLORS[keyLower] || PLATFORM_COLORS[raw] || '#6b7280';
};

const PlatformMentionRates = ({
  onPlatformClick,
  timeframe = '7days',
  date = '',
  endDate = '',
  tenantKey = DEFAULT_TENANT_KEY,
  jobId = DEFAULT_JOB_ID,
  brand = DEFAULT_BRAND,
}) => {
  const { token } = theme.useToken();
  const abortControllerRef = useRef(null);
  const [platforms, setPlatforms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const queryString = useMemo(
    () =>
      buildQueryString({
        tenant_key: tenantKey,
        job_id: jobId,
        brand,
        timeframe,
        start_date: timeframe === 'specific_day' ? date : undefined,
        end_date: timeframe === 'specific_day' ? endDate || date : undefined,
      }),
    [tenantKey, jobId, brand, timeframe, date, endDate],
  );

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

        const data = await fetchJson(
          `/api/v1/dashboard/platform-metrics-by-brand?${queryString}`,
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
  }, [queryString, token.colorPrimary]);

  if (loading) {
    return (
      <Card title="各平台提及率" loading />
    );
  }

  if (error) {
    return (
      <Card title="各平台提及率">
        <Typography.Text type="danger">{error}</Typography.Text>
      </Card>
    );
  }

  if (platforms.length === 0) {
    return (
      <Card title="各平台提及率">
        <Typography.Text type="secondary">暂无平台数据</Typography.Text>
      </Card>
    );
  }

  return (
    <Card title="各平台提及率">
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
