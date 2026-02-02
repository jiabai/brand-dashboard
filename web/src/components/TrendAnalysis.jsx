import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Card, Space, Typography, DatePicker, Row, Col, Statistic, Tag, theme } from 'antd';
import { LineChartOutlined } from '@ant-design/icons';
import { DualAxes } from '@ant-design/charts';
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

const formatDateLabel = (value) => {
  if (!value) return '';
  const text = String(value);
  if (/^\d{8}$/.test(text)) {
    return `${text.slice(4, 6)}-${text.slice(6, 8)}`;
  }
  return text;
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
        let previousRate = null;
        const normalized = list.map((item) => {
          const mentionRateRaw = Number(item?.mention_rate ?? 0);
          const mentionRatePct = roundTwoDecimals(toPercent(mentionRateRaw));
          const deltaPct =
            previousRate === null ? 0 : roundTwoDecimals(mentionRatePct - previousRate);
          previousRate = mentionRatePct;
          return {
            dateLabel: formatDateLabel(item?.date),
            dateRaw: String(item?.date || ''),
            mentionRatePct,
            deltaPct,
            isFilled: Boolean(item?.is_filled),
          };
        });

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
    if (!trendData.length) {
      return {
        avg: 0,
        max: 0,
        min: 0,
        filledCount: 0,
        total: 0,
      };
    }
    const total = trendData.length;
    const filledCount = trendData.filter((item) => item.isFilled).length;
    const values = trendData.map((item) => item.mentionRatePct);
    const sum = values.reduce((acc, cur) => acc + cur, 0);
    const avg = roundTwoDecimals(sum / total);
    const max = roundTwoDecimals(Math.max(...values));
    const min = roundTwoDecimals(Math.min(...values));
    return { avg, max, min, filledCount, total };
  }, [trendData]);

  const chartConfig = useMemo(() => {
    if (!trendData.length) return null;

    const lineColor = token.colorPrimary;
    return {
      data: [trendData, trendData],
      xField: 'dateLabel',
      yField: ['mentionRatePct', 'deltaPct'],
      legend: false,
      tooltip: {
        shared: true,
      },
      xAxis: {
        tickLine: null,
        label: {
          style: { fill: token.colorTextSecondary },
        },
      },
      yAxis: {
        mentionRatePct: {
          label: {
            formatter: (value) => `${value}%`,
            style: { fill: token.colorTextSecondary },
          },
        },
        deltaPct: {
          label: {
            formatter: (value) => `${value}%`,
            style: { fill: token.colorTextSecondary },
          },
        },
      },
      meta: {
        mentionRatePct: {
          alias: '提及率',
          formatter: (value) => `${Number(value).toFixed(2)}%`,
        },
        deltaPct: {
          alias: '日变化',
          formatter: (value) => `${Number(value) >= 0 ? '+' : ''}${Number(value).toFixed(2)}%`,
        },
      },
      geometryOptions: [
        {
          geometry: 'line',
          color: lineColor,
          lineStyle: { lineWidth: 2 },
          point: {
            size: 4,
            shape: 'circle',
            style: (datum) =>
              datum.isFilled
                ? { fill: 'transparent', stroke: lineColor, lineWidth: 2 }
                : { fill: lineColor, stroke: lineColor },
          },
        },
        {
          geometry: 'column',
          color: (datum) =>
            datum.deltaPct >= 0 ? token.colorSuccess : token.colorError,
          columnStyle: (datum) => ({
            fillOpacity: datum.isFilled ? 0.35 : 0.75,
            radius: [3, 3, 0, 0],
          }),
        },
      ],
      slider: {
        start: 0.55,
        end: 1,
        height: 16,
      },
    };
  }, [trendData, token.colorPrimary, token.colorSuccess, token.colorError, token.colorTextSecondary]);

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card
        title={
          <Space>
            <LineChartOutlined />
            <span>品牌提及率趋势</span>
          </Space>
        }
        extra={
          <Space wrap>
            <Tag color="processing">{brandValue}</Tag>
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
            <Col>
              <Space>
                <Tag color="default">实心点=原始</Tag>
                <Tag color="default">空心点=补齐</Tag>
              </Space>
            </Col>
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
                title="补齐点占比"
                value={stats.total ? `${roundTwoDecimals((stats.filledCount / stats.total) * 100)}%` : '--'}
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
        ) : !trendData.length ? (
          <EmptyState
            title="暂无趋势数据"
            description="当前筛选条件下未返回可展示的数据"
          />
        ) : (
          <div style={{ height: 420 }}>
            <DualAxes {...chartConfig} />
          </div>
        )}
      </Card>
    </Space>
  );
};

export default React.memo(TrendAnalysis);
