import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Card, Space, Typography, Input, Button, Row, Col, Statistic, Tag, theme } from 'antd';
import { LineChartOutlined } from '@ant-design/icons';
import { DualAxes } from '@ant-design/charts';

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

const formatDateToParam = (value) => {
  if (!value) return '';
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}${month}${day}`;
};

const parseDateParam = (value) => {
  if (!value) return null;
  const text = String(value);
  if (/^\d{8}$/.test(text)) {
    const year = Number(text.slice(0, 4));
    const month = Number(text.slice(4, 6)) - 1;
    const day = Number(text.slice(6, 8));
    return new Date(year, month, day);
  }
  const date = new Date(text);
  return Number.isNaN(date.getTime()) ? null : date;
};

const getRangeByTimeframe = (timeframe, dateParam) => {
  const today = new Date();
  if (timeframe === 'yesterday') {
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);
    const dayStr = formatDateToParam(yesterday);
    return { startDate: dayStr, endDate: dayStr };
  }
  if (timeframe === 'specific_day') {
    const parsed = parseDateParam(dateParam);
    const dayStr = formatDateToParam(parsed || today);
    return { startDate: dayStr, endDate: dayStr };
  }
  const days = timeframe === '30days' ? 30 : 7;
  const start = new Date(today);
  start.setDate(today.getDate() - (days - 1));
  return {
    startDate: formatDateToParam(start),
    endDate: formatDateToParam(today),
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

const TrendAnalysis = ({
  timeframe = '7days',
  date = '',
  tenantKey = DEFAULT_TENANT_KEY,
  jobId = DEFAULT_JOB_ID,
  brand = DEFAULT_BRAND,
}) => {
  const { token } = theme.useToken();
  const abortControllerRef = useRef(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [trendData, setTrendData] = useState([]);
  const [platformInput, setPlatformInput] = useState(() =>
    getQueryParam('trend_platform', 'deepseek'),
  );
  const [keywordInput, setKeywordInput] = useState(() =>
    getQueryParam('trend_keyword', ''),
  );
  const [platform, setPlatform] = useState(() =>
    getQueryParam('trend_platform', 'deepseek'),
  );
  const [keyword, setKeyword] = useState(() =>
    getQueryParam('trend_keyword', ''),
  );

  const dateRange = useMemo(() => getRangeByTimeframe(timeframe, date), [timeframe, date]);

  useEffect(() => {
    updateQueryParams({
      trend_platform: platform,
      trend_keyword: keyword,
      trend_start: dateRange.startDate,
      trend_end: dateRange.endDate,
    });
  }, [platform, keyword, dateRange.startDate, dateRange.endDate]);

  const queryString = useMemo(
    () =>
      buildQueryString({
        tenant_key: tenantKey,
        job_id: jobId,
        brand,
        platform,
        keyword,
        start_date: dateRange.startDate,
        end_date: dateRange.endDate,
      }),
    [tenantKey, jobId, brand, platform, keyword, dateRange.startDate, dateRange.endDate],
  );

  const applyFilters = () => {
    const nextPlatform = String(platformInput || '').trim();
    const nextKeyword = String(keywordInput || '').trim();
    setPlatform(nextPlatform);
    setKeyword(nextKeyword);
  };

  useEffect(() => {
    if (!platform || !keyword || !dateRange.startDate || !dateRange.endDate) {
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
  }, [platform, keyword, dateRange.startDate, dateRange.endDate, queryString]);

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
            <Tag color="processing">{brand}</Tag>
            <Tag color="geekblue">
              {dateRange.startDate} - {dateRange.endDate}
            </Tag>
          </Space>
        }
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Row gutter={[16, 16]} align="middle">
            <Col flex="auto">
              <Space wrap>
                <Input
                  value={platformInput}
                  onChange={(event) => setPlatformInput(event.target.value)}
                  placeholder="平台名称，例如 deepseek"
                  style={{ width: 240 }}
                />
                <Input
                  value={keywordInput}
                  onChange={(event) => setKeywordInput(event.target.value)}
                  placeholder="关键词"
                  style={{ width: 240 }}
                />
                <Button type="primary" onClick={applyFilters}>
                  应用
                </Button>
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
            onAction={() => applyFilters()}
          />
        ) : !platform || !keyword ? (
          <EmptyState
            title="请输入平台与关键词"
            description="填写平台名称与关键词后即可查看趋势"
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
