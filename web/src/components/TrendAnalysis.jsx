import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Card, Space, Typography, DatePicker, Row, Col, Statistic, Tag, theme } from 'antd';
import { LineChartOutlined } from '@ant-design/icons';
import { Chart } from '@antv/g2';
import dayjs from 'dayjs';

import { CONFIG } from '@/config';
import { formatPercentage, getQueryParam, updateQueryParams } from '@/utils';

import LoadingSpinner from './LoadingSpinner';
import EmptyState from './EmptyState';

const { DEFAULT_TENANT_KEY, DEFAULT_JOB_ID, DEFAULT_BRAND } = CONFIG;

const buildQueryString = (params) => {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null) return;
    if (String(value).trim() === '') return;
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
  return num <= 1 ? num * 100 : num;
};

const toFraction = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return 0;
  if (num <= 1) return num;
  return num / 100;
};

const roundTwoDecimals = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return 0;
  return Math.round(num * 100) / 100;
};

const parseDateInput = (value) => {
  if (!value) return null;
  const text = String(value);
  if (/^\d{8}$/.test(text)) {
    const parsed = dayjs(text, 'YYYYMMDD');
    return parsed.isValid() ? parsed : null;
  }
  const parsed = dayjs(text);
  return parsed.isValid() ? parsed : null;
};

const formatDateParam = (value) => {
  if (!value) return '';
  const parsed = dayjs.isDayjs(value) ? value : dayjs(value);
  if (!parsed.isValid()) return '';
  return parsed.format('YYYYMMDD');
};

const formatDateDisplay = (value) => {
  if (!value) return '';
  const parsed = dayjs.isDayjs(value) ? value : dayjs(value);
  if (!parsed.isValid()) return '';
  return parsed.format('YYYY-MM-DD');
};

const getRangeByTimeframe = (timeframe, dateParam) => {
  const today = dayjs();
  if (timeframe === 'yesterday') {
    const yesterday = today.subtract(1, 'day');
    return { startDate: yesterday, endDate: yesterday };
  }
  if (timeframe === 'specific_day') {
    const parsed = parseDateInput(dateParam);
    const day = parsed || today;
    return { startDate: day, endDate: day };
  }
  const days = timeframe === '30days' ? 30 : 7;
  return {
    startDate: today.subtract(days - 1, 'day'),
    endDate: today,
  };
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

const TrendG2Chart = React.memo(function TrendG2Chart({ data, token }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    if (chartRef.current) {
      chartRef.current.destroy();
      chartRef.current = null;
    }

    if (!Array.isArray(data) || data.length === 0) {
      return;
    }

    const chart = new Chart({
      container: containerRef.current,
      autoFit: true,
    });
    chartRef.current = chart;

    chart.theme({ type: 'academy' });

    chart.data(data);

    chart
      .interval()
      .encode('x', 'dateStr')
      .encode('y', 'mention_rate')
      .axis('x', { 
        title: false, 
        labelFill: '#A6A6A6', 
        titleFill: '#A6A6A6' 
      })
      .axis('y', {
        title: '提及率 (Mention Rate)',
        titleFill: '#5B8FF9',
        labelFormatter: (d) => `${(Number(d) * 100).toFixed(1)}%`,
        labelFill: '#A6A6A6',
      })
      .tooltip({
        title: (d) => d.dateStr,
        items: [
          {
            field: 'mention_rate',
            name: '提及率',
            valueFormatter: (d) => `${(Number(d) * 100).toFixed(2)}%`,
          },
        ],
      });

    chart
      .line()
      .encode('x', 'dateStr')
      .encode('y', 'mention_rate')
      .encode('shape', 'smooth')
      .style('stroke', '#fdae6b')
      .style('lineWidth', 3)
      .tooltip(false);

    chart
      .point()
      .encode('x', 'dateStr')
      .encode('y', 'mention_rate')
      .encode('shape', 'point')
      .style('fill', '#fdae6b')
      .style('r', 5)
      .tooltip(false);

    chart.render();

    return () => {
      chart.destroy();
      chartRef.current = null;
    };
  }, [data, token]);

  return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />;
});

const TrendAnalysis = ({
  timeframe = '7days',
  date = '',
  tenantKey = DEFAULT_TENANT_KEY,
  jobId = DEFAULT_JOB_ID,
  brand = DEFAULT_BRAND,
}) => {
  const { token } = theme.useToken();
  const abortControllerRef = useRef(null);
  const metadataAbortRef = useRef(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [trendData, setTrendData] = useState([]);
  const [platform, setPlatform] = useState(() =>
    getQueryParam('trend_platform', '全部'),
  );
  const [keyword, setKeyword] = useState(() =>
    getQueryParam('trend_keyword', '全部'),
  );
  const [startDate, setStartDate] = useState(() => {
    const fromUrl = parseDateInput(getQueryParam('trend_start', ''));
    if (fromUrl) return fromUrl;
    return getRangeByTimeframe(timeframe, date).startDate;
  });
  const [endDate, setEndDate] = useState(() => {
    const fromUrl = parseDateInput(getQueryParam('trend_end', ''));
    if (fromUrl) return fromUrl;
    return getRangeByTimeframe(timeframe, date).endDate;
  });
  const [metadataLoading, setMetadataLoading] = useState(false);
  const [metadataError, setMetadataError] = useState('');
  const [platformOptions, setPlatformOptions] = useState([]);
  const [keywordOptions, setKeywordOptions] = useState([]);
  const [combinations, setCombinations] = useState([]);
  const [reloadKey, setReloadKey] = useState(0);

  const tenantKeyValue = useMemo(
    () => getQueryParam('tenant_key', tenantKey || DEFAULT_TENANT_KEY),
    [tenantKey],
  );
  const jobIdValue = useMemo(
    () => getQueryParam('job_id', jobId || DEFAULT_JOB_ID),
    [jobId],
  );
  const brandValue = useMemo(
    () => getQueryParam('brand', brand || DEFAULT_BRAND),
    [brand],
  );

  const startDateParam = useMemo(() => formatDateParam(startDate), [startDate]);
  const endDateParam = useMemo(() => formatDateParam(endDate), [endDate]);
  const displayStart = useMemo(() => formatDateDisplay(startDate), [startDate]);
  const displayEnd = useMemo(() => formatDateDisplay(endDate), [endDate]);

  useEffect(() => {
    updateQueryParams({
      trend_platform: platform,
      trend_keyword: keyword,
      trend_start: startDateParam,
      trend_end: endDateParam,
    });
  }, [platform, keyword, startDateParam, endDateParam]);

  useEffect(() => {
    if (!tenantKeyValue || !jobIdValue || !startDateParam || !endDateParam) {
      setPlatformOptions([]);
      setKeywordOptions([]);
      setCombinations([]);
      return;
    }

    if (metadataAbortRef.current) {
      metadataAbortRef.current.abort();
    }

    const controller = new AbortController();
    metadataAbortRef.current = controller;

    const run = async () => {
      try {
        setMetadataLoading(true);
        setMetadataError('');
        const result = await fetchJson(
          `/api/v1/dashboard/filter-metadata?${buildQueryString({
            tenant_key: tenantKeyValue,
            job_id: jobIdValue,
            start_date: startDateParam,
            end_date: endDateParam,
          })}`,
          { signal: controller.signal },
        );

        if (result?.code && result.code !== 200) {
          throw new Error(result?.message || '接口返回错误状态');
        }

        const payload = result?.data || {};
        const nextPlatforms = Array.isArray(payload.platforms) ? payload.platforms : [];
        const nextKeywords = Array.isArray(payload.keywords) ? payload.keywords : [];
        const nextCombinations = Array.isArray(payload.combinations) ? payload.combinations : [];
        setPlatformOptions(Array.from(new Set(nextPlatforms.filter(Boolean))));
        setKeywordOptions(Array.from(new Set(nextKeywords.filter(Boolean))));
        setCombinations(nextCombinations);
        setMetadataLoading(false);
      } catch (err) {
        if (controller.signal.aborted) return;
        if (err?.name === 'AbortError') return;
        setPlatformOptions([]);
        setKeywordOptions([]);
        setCombinations([]);
        setMetadataError(err?.message || '筛选项加载失败');
        setMetadataLoading(false);
      }
    };

    run();

    return () => {
      controller.abort();
    };
  }, [tenantKeyValue, jobIdValue, startDateParam, endDateParam]);

  useEffect(() => {
    // 只有当 URL 中没有具体日期参数时，才响应 props 的变化
    // 或者当 timeframe 变化时，重新同步日期范围
    if (!getQueryParam('trend_start') && !getQueryParam('trend_end')) {
      const range = getRangeByTimeframe(timeframe, date);
      setStartDate(range.startDate);
      setEndDate(range.endDate);
    }
  }, [timeframe, date]);

  const queryString = useMemo(
    () =>
      buildQueryString({
        tenant_key: tenantKeyValue,
        job_id: jobIdValue,
        brand: brandValue,
        platform,
        keyword,
        start_date: startDateParam,
        end_date: endDateParam,
      }),
    [
      tenantKeyValue,
      jobIdValue,
      brandValue,
      platform,
      keyword,
      startDateParam,
      endDateParam,
    ],
  );

  useEffect(() => {
    if (!platform || !keyword || !startDateParam || !endDateParam) {
      setTrendData([]);
      return;
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const run = async () => {
      try {
        setIsLoading(true);
        setError('');
        const result = await fetchJson(
          `/api/v1/dashboard/brand-mention-trend?${queryString}`,
          { signal: controller.signal },
        );

        if (result?.status && result.status !== 'success') {
          throw new Error('接口返回错误状态');
        }

        const list = Array.isArray(result?.data) ? result.data : [];
        const normalized = list
          .map((item) => {
            const dateRaw = String(item?.date || '').trim();
            if (!dateRaw) return null;
            return {
              date: dateRaw,
              mention_rate: toFraction(item?.mention_rate ?? 0),
            };
          })
          .filter(Boolean);

        setTrendData(normalized);
        setIsLoading(false);
      } catch (err) {
        if (controller.signal.aborted) return;
        if (err?.name === 'AbortError') return;
        setTrendData([]);
        setError(err?.message || '数据加载失败');
        setIsLoading(false);
      }
    };

    run();

    return () => {
      controller.abort();
    };
  }, [platform, keyword, startDateParam, endDateParam, queryString, reloadKey]);

  const chartData = useMemo(() => {
    if (!startDateParam || !endDateParam) return [];
    if (!dayjs(startDateParam, 'YYYYMMDD', true).isValid()) return [];
    if (!dayjs(endDateParam, 'YYYYMMDD', true).isValid()) return [];

    const start = dayjs(startDateParam, 'YYYYMMDD');
    const end = dayjs(endDateParam, 'YYYYMMDD');
    if (end.isBefore(start, 'day')) return [];

    const byDate = new Map(
      (Array.isArray(trendData) ? trendData : [])
        .filter((item) => item?.date)
        .map((item) => [String(item.date), Number(item.mention_rate) || 0]),
    );

    const fullData = [];
    let cursor = start;
    while (cursor.isBefore(end, 'day') || cursor.isSame(end, 'day')) {
      const dateRaw = cursor.format('YYYYMMDD');
      fullData.push({
        date: dateRaw,
        dateStr: cursor.format('YYYY-MM-DD'),
        mention_rate: byDate.get(dateRaw) ?? 0,
        brand: brandValue,
        platform,
        keyword,
      });
      cursor = cursor.add(1, 'day');
    }

    return fullData;
  }, [trendData, startDateParam, endDateParam, brandValue, platform, keyword]);

  const availablePlatforms = useMemo(() => {
    const options = ['全部', ...platformOptions];
    if (!combinations.length || keyword === '全部') return options;
    const allowed = new Set(
      combinations
        .filter((item) => item?.keyword === keyword)
        .map((item) => item?.platform)
        .filter(Boolean),
    );
    return options.filter((item) => item === '全部' || allowed.has(item));
  }, [platformOptions, combinations, keyword]);

  const availableKeywords = useMemo(() => {
    const options = ['全部', ...keywordOptions];
    if (!combinations.length || platform === '全部') return options;
    const allowed = new Set(
      combinations
        .filter((item) => item?.platform === platform)
        .map((item) => item?.keyword)
        .filter(Boolean),
    );
    return options.filter((item) => item === '全部' || allowed.has(item));
  }, [keywordOptions, combinations, platform]);

  useEffect(() => {
    if (!availablePlatforms.includes(platform)) {
      setPlatform(availablePlatforms[0] || '全部');
    }
  }, [availablePlatforms, platform]);

  useEffect(() => {
    if (!availableKeywords.includes(keyword)) {
      setKeyword(availableKeywords[0] || '全部');
    }
  }, [availableKeywords, keyword]);

  const stats = useMemo(() => {
    if (!chartData.length) {
      return {
        avg: 0,
        max: 0,
        min: 0,
        total: 0,
      };
    }
    const total = chartData.length;
    const values = chartData.map((item) => toPercent(item.mention_rate));
    const sum = values.reduce((acc, cur) => acc + cur, 0);
    const avg = roundTwoDecimals(sum / total);
    const max = roundTwoDecimals(Math.max(...values));
    const min = roundTwoDecimals(Math.min(...values));
    return { avg, max, min, total };
  }, [chartData]);

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card
        title={
          <Space direction="vertical" size={2}>
            <Space>
              <LineChartOutlined />
              <span>品牌提及率分析</span>
            </Space>
            <Typography.Text type="secondary">
              品牌: {brandValue} | 平台: {platform} | 关键词: {keyword}
            </Typography.Text>
          </Space>
        }
        extra={
          <Space wrap>
            <Tag color="geekblue">
              {displayStart || '--'} - {displayEnd || '--'}
            </Tag>
          </Space>
        }
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Row gutter={[16, 16]} align="middle">
            <Col flex="auto">
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <Space wrap align="center">
                  <Typography.Text type="secondary">日期范围</Typography.Text>
                  <DatePicker
                    value={startDate}
                    onChange={setStartDate}
                    format="YYYY-MM-DD"
                    allowClear
                  />
                  <Typography.Text type="secondary">至</Typography.Text>
                  <DatePicker
                    value={endDate}
                    onChange={setEndDate}
                    format="YYYY-MM-DD"
                    allowClear
                  />
                </Space>
                {metadataLoading ? (
                  <Typography.Text type="secondary">筛选项加载中...</Typography.Text>
                ) : metadataError ? (
                  <Typography.Text type="danger">{metadataError}</Typography.Text>
                ) : (
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <Space direction="vertical" size={4}>
                      <Typography.Text type="secondary">平台</Typography.Text>
                      <Space wrap>
                        {availablePlatforms.map((item) => {
                          const checked = platform === item;
                          const color = item === '全部' ? token.colorPrimary : getPlatformColor(item);
                          return (
                            <Tag.CheckableTag
                              key={`platform-${item}`}
                              checked={checked}
                              onChange={() => setPlatform(item)}
                              style={{
                                paddingInline: 12,
                                paddingBlock: 4,
                                borderRadius: 999,
                                border: `1px solid ${checked ? color : token.colorBorderSecondary}`,
                                color: checked ? token.colorText : color,
                                background: checked ? color : 'transparent',
                                marginInlineEnd: 0,
                              }}
                            >
                              {item}
                            </Tag.CheckableTag>
                          );
                        })}
                      </Space>
                    </Space>
                    <Space direction="vertical" size={4}>
                      <Typography.Text type="secondary">关键词</Typography.Text>
                      <Space wrap>
                        {availableKeywords.map((item) => {
                          const checked = keyword === item;
                          return (
                            <Tag.CheckableTag
                              key={`keyword-${item}`}
                              checked={checked}
                              onChange={() => setKeyword(item)}
                              style={{
                                paddingInline: 12,
                                paddingBlock: 4,
                                borderRadius: 8,
                                border: `1px solid ${checked ? token.colorPrimary : token.colorBorderSecondary}`,
                                color: checked ? token.colorText : token.colorTextSecondary,
                                background: checked ? token.colorPrimary : 'rgba(255, 255, 255, 0.08)',
                                marginInlineEnd: 0,
                              }}
                            >
                              {item}
                            </Tag.CheckableTag>
                          );
                        })}
                      </Space>
                    </Space>
                  </Space>
                )}
              </Space>
            </Col>
            <Col />
          </Row>
          <Row gutter={[16, 16]}>
            <Col xs={12} sm={12} md={6}>
              <Statistic title="平均提及率" value={formatPercentage(stats.avg)} />
            </Col>
            <Col xs={12} sm={12} md={6}>
              <Statistic title="最高提及率" value={formatPercentage(stats.max)} />
            </Col>
            <Col xs={12} sm={12} md={6}>
              <Statistic title="最低提及率" value={formatPercentage(stats.min)} />
            </Col>
            <Col xs={12} sm={12} md={6}>
              <Statistic
                title="点位数"
                value={stats.total || '--'}
              />
            </Col>
          </Row>
        </Space>
      </Card>

      <Card>
        {isLoading ? (
          <LoadingSpinner text="正在加载趋势数据..." />
        ) : error ? (
          <EmptyState
            title="数据加载失败"
            description={error}
            actionText="重试"
            onAction={() => setReloadKey((prev) => prev + 1)}
          />
        ) : !platform || !keyword || !startDateParam || !endDateParam ? (
          <EmptyState
            title="请输入筛选条件"
            description="选择平台、关键词与日期范围后即可查看趋势"
          />
        ) : (
          <div
            style={{
              height: 500,
              padding: 20,
              borderRadius: 8,
              background: token.colorBgElevated,
              boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
            }}
          >
            <TrendG2Chart data={chartData} token={token} />
          </div>
        )}
      </Card>
    </Space>
  );
};

export default React.memo(TrendAnalysis);
