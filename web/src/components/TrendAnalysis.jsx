import React, { useEffect, useMemo, useRef, useState } from 'react';
import { LineChart, RefreshCw } from 'lucide-react';
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
import { cn } from '@/lib/cn';

import EmptyState from './EmptyState';
import LoadingSpinner from './LoadingSpinner';
import { Badge } from './ui/badge.jsx';
import { Button } from './ui/button.jsx';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card.jsx';

const FilterChips = ({ label, options, value, onChange, getColor }) => (
  <div className="space-y-2">
    <div className="text-sm text-muted-foreground">{label}</div>
    <div className="flex flex-wrap gap-2">
      {options.map((item) => {
        const checked = value === item;
        const color = getColor?.(item) || 'var(--primary)';
        return (
          <button
            key={`${label}-${item}`}
            type="button"
            className={cn(
              'rounded-md border px-3 py-1 text-sm transition-colors',
              checked ? 'text-primary-foreground' : 'bg-background text-muted-foreground hover:bg-muted',
            )}
            style={checked ? { borderColor: color, background: color } : undefined}
            onClick={() => onChange(item)}
          >
            {item}
          </button>
        );
      })}
    </div>
  </div>
);

const StatCard = ({ label, value }) => (
  <div className="rounded-md border bg-muted/35 p-4">
    <div className="text-sm text-muted-foreground">{label}</div>
    <div className="mt-2 text-2xl font-semibold text-foreground">{value}</div>
  </div>
);

const TrendSvgChart = ({ data }) => {
  const width = 900;
  const height = 360;
  const padding = { top: 28, right: 28, bottom: 54, left: 64 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;

  const values = data.map((item) => toPercent(item.mention_rate));
  const maxValue = Math.max(1, ...values);
  const minValue = Math.min(0, ...values);
  const range = Math.max(1, maxValue - minValue);
  const xStep = data.length > 1 ? innerWidth / (data.length - 1) : innerWidth;

  const points = data.map((item, index) => {
    const value = toPercent(item.mention_rate);
    const x = padding.left + index * xStep;
    const y = padding.top + innerHeight - ((value - minValue) / range) * innerHeight;
    return { ...item, value, x, y };
  });

  const line = points.map((point) => `${point.x},${point.y}`).join(' ');
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
    const value = minValue + ratio * range;
    return {
      value,
      y: padding.top + innerHeight - ratio * innerHeight,
    };
  });
  const labelStep = Math.max(1, Math.ceil(points.length / 7));

  return (
    <div className="w-full overflow-x-auto rounded-md border bg-card p-3">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="品牌提及率趋势图" className="min-w-[720px]">
        <defs>
          <linearGradient id="trend-fill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.22" />
            <stop offset="100%" stopColor="var(--primary)" stopOpacity="0" />
          </linearGradient>
        </defs>

        {yTicks.map((tick) => (
          <g key={tick.value}>
            <line
              x1={padding.left}
              x2={width - padding.right}
              y1={tick.y}
              y2={tick.y}
              stroke="var(--border)"
              strokeDasharray="4 4"
            />
            <text x={padding.left - 12} y={tick.y + 4} textAnchor="end" className="fill-muted-foreground text-xs">
              {formatPercentage(roundTwoDecimals(tick.value))}
            </text>
          </g>
        ))}

        <polyline
          points={[
            `${padding.left},${padding.top + innerHeight}`,
            line,
            `${width - padding.right},${padding.top + innerHeight}`,
          ].join(' ')}
          fill="url(#trend-fill)"
          stroke="none"
        />
        <polyline points={line} fill="none" stroke="var(--primary)" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" />

        {points.map((point, index) => (
          <g key={point.date}>
            <circle cx={point.x} cy={point.y} r="4.5" fill="var(--card)" stroke="var(--primary)" strokeWidth="2" />
            <title>{`${point.dateStr}: ${formatPercentage(roundTwoDecimals(point.value))}`}</title>
            {index % labelStep === 0 || index === points.length - 1 ? (
              <text
                x={point.x}
                y={height - 18}
                textAnchor="middle"
                className="fill-muted-foreground text-xs"
              >
                {point.dateStr.slice(5)}
              </text>
            ) : null}
          </g>
        ))}
      </svg>
    </div>
  );
};

const TrendAnalysis = () => {
  const { timeframe, date, endDate, tenantKey, jobId, brand } = useDashboardRequestParams();
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
    <div className="flex w-full flex-col gap-6">
      <Card>
        <CardHeader className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <LineChart className="size-5 text-primary" />
              <CardTitle>品牌提及率分析</CardTitle>
            </div>
            <p className="text-sm text-muted-foreground">
              品牌: {brandValue} | 平台: {platform} | 关键词: {keyword}
            </p>
          </div>
          <Badge variant="secondary">
            {displayStart || '--'} - {displayEnd || '--'}
          </Badge>
        </CardHeader>
        <CardContent className="space-y-5">
          {metadataLoading ? (
            <p className="text-sm text-muted-foreground">筛选项加载中...</p>
          ) : metadataError ? (
            <p className="text-sm text-destructive">{metadataError}</p>
          ) : (
            <div className="space-y-4">
              <FilterChips
                label="平台"
                options={availablePlatforms}
                value={platform}
                onChange={setPlatform}
                getColor={(item) => (item === '全部' ? 'var(--primary)' : getPlatformColor(item))}
              />
              <FilterChips
                label="关键词"
                options={availableKeywords}
                value={keyword}
                onChange={setKeyword}
              />
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="平均提及率" value={formatPercentage(stats.avg)} />
            <StatCard label="最高提及率" value={formatPercentage(stats.max)} />
            <StatCard label="最低提及率" value={formatPercentage(stats.min)} />
            <StatCard label="点位数" value={stats.total || '--'} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
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
          ) : chartData.length ? (
            <TrendSvgChart data={chartData} />
          ) : (
            <EmptyState
              title="暂无趋势数据"
              description="当前筛选条件下没有可展示的数据"
              actionText="刷新"
              onAction={() => setReloadKey((prev) => prev + 1)}
              icon={<RefreshCw className="size-6" />}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default React.memo(TrendAnalysis);
