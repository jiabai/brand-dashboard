import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Card, Space, Typography, Row, Col, Statistic, Tag, theme } from 'antd';
import { LineChartOutlined } from '@ant-design/icons';
import { useSearchParams } from 'react-router-dom';
import dayjs from 'dayjs';

import { fetchBrandMentionTrend, fetchFilterMetadata } from '@/api';
import { useDashboardRequestParams } from '@/hooks/useDashboardParams';
import {
  formatPercentage,
  getPlatformColor,
  toPercent,
  toFraction,
  roundTwoDecimals,
  parseDateInput,
  formatDateParam,
  formatDateDisplay,
  getRangeByTimeframe,
} from '@/utils';
import { loadG2Chart } from '@/utils/loadG2Chart';

import LoadingSpinner from './LoadingSpinner';
import EmptyState from './EmptyState';

const TrendG2Chart = React.memo(function TrendG2Chart({ data, token }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    let disposed = false;

    if (chartRef.current) {
      chartRef.current.destroy();
      chartRef.current = null;
    }

    if (!Array.isArray(data) || data.length === 0) {
      return () => {
        disposed = true;
      };
    }

    const container = containerRef.current;

    const run = async () => {
      const Chart = await loadG2Chart();
      if (disposed) return;

      const chart = new Chart({
        container,
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
          titleFill: '#A6A6A6',
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
    };

    run().catch(() => {});

    return () => {
      disposed = true;
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, [data, token]);

  return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />;
});

const TrendAnalysis = () => {
  const { timeframe, date, endDate, tenantKey, jobId, brand } = useDashboardRequestParams();
  const { token } = theme.useToken();
  const [searchParams, setSearchParams] = useSearchParams();
  const abortControllerRef = useRef(null);
  const metadataAbortRef = useRef(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [trendData, setTrendData] = useState([]);
  const [platform, setPlatform] = useState(() =>
    searchParams.get('trend_platform') || '全部',
  );
  const [keyword, setKeyword] = useState(() =>
    searchParams.get('trend_keyword') || '全部',
  );
  const [metadataLoading, setMetadataLoading] = useState(false);
  const [metadataError, setMetadataError] = useState('');
  const [platformOptions, setPlatformOptions] = useState([]);
  const [keywordOptions, setKeywordOptions] = useState([]);
  const [combinations, setCombinations] = useState([]);
  const [reloadKey, setReloadKey] = useState(0);

  const tenantKeyValue = tenantKey;
  const jobIdValue = jobId;
  const brandValue = brand;

  const dateRange = useMemo(() => {
    if (timeframe === 'specific_day') {
      const start = parseDateInput(date) || dayjs();
      const end = parseDateInput(endDate) || start;
      const normalizedEnd = end.isBefore(start, 'day') ? start : end;
      return { startDate: start, endDate: normalizedEnd };
    }
    return getRangeByTimeframe(timeframe, date);
  }, [timeframe, date, endDate]);

  const startDateParam = useMemo(
    () => formatDateParam(dateRange.startDate),
    [dateRange.startDate],
  );
  const endDateParam = useMemo(
    () => formatDateParam(dateRange.endDate),
    [dateRange.endDate],
  );
  const displayStart = useMemo(
    () => formatDateDisplay(dateRange.startDate),
    [dateRange.startDate],
  );
  const displayEnd = useMemo(
    () => formatDateDisplay(dateRange.endDate),
    [dateRange.endDate],
  );

  useEffect(() => {
    const nextPlatform = searchParams.get('trend_platform') || '全部';
    const nextKeyword = searchParams.get('trend_keyword') || '全部';
    setPlatform((current) => (current === nextPlatform ? current : nextPlatform));
    setKeyword((current) => (current === nextKeyword ? current : nextKeyword));
  }, [searchParams]);

  useEffect(() => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('trend_platform', platform);
      next.set('trend_keyword', keyword);
      return next;
    }, { replace: true });
  }, [keyword, platform, setSearchParams]);

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
        const result = await fetchFilterMetadata(
          {
            tenantKey: tenantKeyValue,
            jobId: jobIdValue,
            startDate: startDateParam,
            endDate: endDateParam,
          },
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
        const result = await fetchBrandMentionTrend(
          {
            tenantKey: tenantKeyValue,
            jobId: jobIdValue,
            brand: brandValue,
            platform,
            keyword,
            timeframe,
            startDate: startDateParam,
            endDate: endDateParam,
          },
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
  }, [
    brandValue,
    endDateParam,
    jobIdValue,
    keyword,
    platform,
    reloadKey,
    startDateParam,
    tenantKeyValue,
    timeframe,
  ]);

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
            description="选择平台与关键词后即可查看趋势"
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
