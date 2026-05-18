import React, { useEffect, useMemo, useRef, useState } from 'react';
import dayjs from 'dayjs';
import {
  Download,
  ExternalLink,
  FileText,
  Filter,
  Globe,
  Hash,
  Info,
  TrendingUp,
} from 'lucide-react';

import { fetchCitationDomainStats, fetchCitationTypeStats, fetchFilterMetadata } from '@/api';
import { useDashboardRequestParams } from '@/hooks/useDashboardParams';
import { normalizeCitationTypeStats } from '@/utils/sourceAnalysis';
import {
  clampPercent,
  roundTwoDecimals,
  normalizeListValue,
  parseDateInput,
  formatDateParam,
  formatDateDisplay,
  getRangeByTimeframe,
} from '@/utils';

import DataTable from './DataTable.jsx';
import KeywordSection from './KeywordSection';
import { Button } from './ui/button.jsx';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card.jsx';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from './ui/popover.jsx';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select.jsx';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from './ui/tooltip.jsx';

const buildSourceUrl = (domain) => {
  if (!domain) return '';
  const text = String(domain).trim();
  if (!text) return '';
  if (/^https?:\/\//i.test(text)) {
    return text;
  }
  return `https://${text}`;
};

const InlineTags = ({ value, variant = 'secondary', icon = false }) => {
  const items = normalizeListValue(value);
  if (!items.length) {
    return <span className="text-muted-foreground">--</span>;
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item) => (
        <span
          key={item}
          className="inline-flex items-center gap-1 rounded-md border bg-muted px-2 py-0.5 text-xs text-muted-foreground"
          data-variant={variant}
        >
          {icon ? <Hash className="size-3" /> : null}
          {item}
        </span>
      ))}
    </div>
  );
};

const SourceAnalysisChart = ({
  displayDate,
  timeframeLabel = '按天',
  summary,
  stats,
  loading,
}) => {
  const safeStats = Array.isArray(stats) ? stats : [];

  return (
    <Card>
      <CardHeader className="space-y-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="size-5 text-primary" />
          <CardTitle>信源分析</CardTitle>
          <Tooltip>
            <TooltipTrigger asChild>
              <Info className="size-4 cursor-help text-muted-foreground" />
            </TooltipTrigger>
            <TooltipContent>基于大模型引用的信源分布比例</TooltipContent>
          </Tooltip>
        </div>
        <div className="flex flex-wrap gap-x-6 gap-y-2 pl-7 text-sm">
          {[
            { label: timeframeLabel, value: displayDate },
            { label: 'Prompt 总数', value: summary?.conversations ?? 0 },
            { label: '引用信源数', value: summary?.totalRows ?? 0 },
          ].map((item) => (
            <span key={item.label} className="text-muted-foreground">
              {item.label}：
              <strong className="font-semibold text-foreground">
                {loading ? '加载中' : item.value}
              </strong>
            </span>
          ))}
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* 屏幕阅读器摘要 */}
        <p className="sr-only">
          {safeStats.length
            ? `信源分布: ${safeStats.map((s) => `${s.type} ${s.value}%`).join('，')}`
            : '暂无信源数据'}
        </p>

        {/* Y轴刻度参考线 */}
        <div className="relative ml-0 sm:ml-7">
          <div className="flex h-4 overflow-hidden rounded-full bg-muted">
            {safeStats.length ? (
              <div className="flex h-full w-full">
                {safeStats.map((item) => (
                  <div
                    key={item.type}
                    className="h-full"
                    style={{
                      width: `${clampPercent(item.value)}%`,
                      background: item.color,
                    }}
                    title={`${item.type}: ${item.value}%`}
                    role="graphics-symbol"
                    aria-label={`${item.type}: ${item.value}%`}
                  />
                ))}
              </div>
            ) : null}
          </div>
          {/* 百分比刻度标注 */}
          <div className="mt-1.5 flex justify-between text-[10px] text-muted-foreground">
            <span>0%</span>
            <span>25%</span>
            <span>50%</span>
            <span>75%</span>
            <span>100%</span>
          </div>
        </div>

        {/* 图例 — 使用不同形状辅助色盲区分 */}
        <div className="flex flex-wrap justify-center gap-4">
          {safeStats.map((item, idx) => {
            const shapes = [
              <span key="shape" className="size-2.5 rounded-full" style={{ background: item.color }} />,
              <span key="shape" className="size-2.5 rounded-sm" style={{ background: item.color }} />,
              <span key="shape" className="size-0 border-x-[5px] border-b-[8px] border-x-transparent border-b-current" style={{ color: item.color }} />,
              <span key="shape" className="size-2.5 rotate-45 rounded-sm" style={{ background: item.color }} />,
              <span key="shape" className="size-2.5 rounded-full border-2" style={{ borderColor: item.color }} />,
            ];
            return (
              <div key={item.type} className="flex items-center gap-2 rounded-md px-3 py-1 text-sm hover:bg-muted">
                {shapes[idx % shapes.length]}
                <span className="font-semibold text-foreground">{item.type}</span>
                <span className="text-muted-foreground">{item.value}%</span>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

const MediaListTable = ({
  rows = [],
  loading = false,
  error = '',
  platformOptions = [],
  selectedPlatform,
  onPlatformChange,
}) => {
  const normalizedPlatformOptions = useMemo(() => {
    const fallback = ['deepseek', '千问', '豆包', '元宝'];
    const base = platformOptions.length ? platformOptions : fallback;
    return Array.from(new Set(base.filter(Boolean))).map((item) => ({
      label: item,
      value: item,
    }));
  }, [platformOptions]);

  const columns = useMemo(
    () => [
      {
        title: '引用来源',
        key: 'source',
        width: 280,
        render: (_, record) => (
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Globe className="size-4 text-muted-foreground" />
              <span className="font-semibold text-foreground">{record.sourceName}</span>
            </div>
            <span className="block text-xs text-muted-foreground">{record.domain}</span>
          </div>
        ),
      },
      {
        title: '品牌关键词',
        dataIndex: 'keyword',
        key: 'keyword',
        width: 180,
        render: (text) => <InlineTags value={text} icon />,
      },
      {
        title: '内容类型',
        dataIndex: 'contentType',
        key: 'contentType',
        width: 160,
        render: (text) => <InlineTags value={text} />,
      },
      {
        title: '大模型平台',
        dataIndex: 'platform',
        key: 'platform',
        width: 160,
        render: (text) => <InlineTags value={text} variant="platform" />,
      },
      {
        title: '引用率',
        dataIndex: 'citationRate',
        key: 'citationRate',
        width: 140,
        sorter: (a, b) => a.citationRate - b.citationRate,
        defaultSortOrder: 'descend',
        render: (value) => {
          const tone = value > 70 ? 'var(--chart-4)' : value < 30 ? 'var(--muted-foreground)' : 'var(--chart-3)';
          return (
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-16 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full"
                  style={{ width: `${clampPercent(value)}%`, background: tone }}
                />
              </div>
              <span className="min-w-10 text-sm font-semibold" style={{ color: tone }}>
                {value}%
              </span>
            </div>
          );
        },
      },
      {
        title: '操作',
        key: 'action',
        width: 80,
        render: (_, record) => (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" disabled={!record.sourceUrl} asChild={Boolean(record.sourceUrl)}>
                {record.sourceUrl ? (
                  <a href={record.sourceUrl} target="_blank" rel="noreferrer">
                    <ExternalLink className="size-4" />
                  </a>
                ) : (
                  <span>
                    <ExternalLink className="size-4" />
                  </span>
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent>查看原文</TooltipContent>
          </Tooltip>
        ),
      },
    ],
    [],
  );

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex flex-col gap-3 border-b sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <FileText className="size-5 text-primary" />
          <CardTitle>引用媒介列表</CardTitle>
        </div>
        <div className="flex flex-wrap gap-2">
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline">
                <Filter className="size-4" />
                高级筛选
              </Button>
            </PopoverTrigger>
            <PopoverContent align="end" className="w-64 space-y-2">
              <div className="text-sm text-muted-foreground">大模型平台</div>
              <Select
                value={selectedPlatform || '__all__'}
                onValueChange={(value) => onPlatformChange?.(value === '__all__' ? '' : value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="全部平台" />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectItem value="__all__">全部平台</SelectItem>
                    {normalizedPlatformOptions.map((item) => (
                      <SelectItem key={item.value} value={item.value}>
                        {item.label}
                      </SelectItem>
                    ))}
                  </SelectGroup>
                </SelectContent>
              </Select>
            </PopoverContent>
          </Popover>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button disabled>
                <Download className="size-4" />
                导出报告
              </Button>
            </TooltipTrigger>
            <TooltipContent>功能开发中，即将上线</TooltipContent>
          </Tooltip>
        </div>
      </CardHeader>
      <CardContent>
        {error ? <p className="mb-3 text-sm text-destructive">{error}</p> : null}
        <DataTable
          columns={columns}
          data={rows}
          rowKey={(record) => record.key || record.domain || record.sourceUrl}
          pagination={{ pageSize: 10 }}
          loading={loading}
          error={error}
          emptyDescription={error ? '加载失败，请稍后再试' : '暂无数据'}
        />
      </CardContent>
    </Card>
  );
};

export default function SourceAnalysis() {
  const { timeframe, date, endDate, tenantKey, jobId, brand } = useDashboardRequestParams();
  const [keywords, setKeywords] = useState([]);
  const [selectedKeyword, setSelectedKeyword] = useState('');
  const [selectedPlatform, setSelectedPlatform] = useState('');
  const [platformOptions, setPlatformOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [citationSummary, setCitationSummary] = useState({ totalRows: 0, conversations: 0 });
  const [citationStats, setCitationStats] = useState([]);
  const [citationLoading, setCitationLoading] = useState(false);
  const [citationError, setCitationError] = useState('');
  const citationAbortRef = useRef(null);
  const mediaAbortRef = useRef(null);
  const [mediaRows, setMediaRows] = useState([]);
  const [mediaLoading, setMediaLoading] = useState(false);
  const [mediaError, setMediaError] = useState('');

  const dateRange = useMemo(() => {
    if (timeframe === 'specific_day') {
      const start = parseDateInput(date) || dayjs();
      const end = parseDateInput(endDate) || start;
      const normalizedEnd = end.isBefore(start, 'day') ? start : end;
      return { startDate: start, endDate: normalizedEnd };
    }
    return getRangeByTimeframe(timeframe, date);
  }, [timeframe, date, endDate]);

  const displayDate = useMemo(() => {
    const start = formatDateDisplay(dateRange.startDate);
    const end = formatDateDisplay(dateRange.endDate);
    return start === end ? start : `${start} ~ ${end}`;
  }, [dateRange]);

  const startDateParam = useMemo(
    () => formatDateParam(dateRange.startDate),
    [dateRange.startDate],
  );
  const endDateParam = useMemo(
    () => formatDateParam(dateRange.endDate),
    [dateRange.endDate],
  );

  const timeframeLabel = useMemo(() => {
    if (timeframe === 'yesterday') return '昨天';
    if (timeframe === '7days') return '最近7天';
    if (timeframe === '30days') return '最近30天';
    return '指定日期';
  }, [timeframe]);

  useEffect(() => {
    const controller = new AbortController();

    const fetchMetadata = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchFilterMetadata(
          { tenantKey, jobId, startDate: startDateParam, endDate: endDateParam },
          { signal: controller.signal },
        );

        if (result?.code === 200 && result.data) {
          setKeywords(result.data.keywords || []);
          setPlatformOptions(result.data.platforms || []);
        } else {
          throw new Error(result?.message || '获取元数据失败');
        }
      } catch (err) {
        if (err.name === 'AbortError') return;
        console.error('Fetch filter metadata error:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchMetadata();

    return () => {
      controller.abort();
    };
  }, [tenantKey, jobId, startDateParam, endDateParam]);

  useEffect(() => {
    if (selectedKeyword && !keywords.includes(selectedKeyword)) {
      setSelectedKeyword('');
    }
  }, [keywords, selectedKeyword]);

  useEffect(() => {
    if (!tenantKey || !jobId) {
      setCitationSummary({ totalRows: 0, conversations: 0 });
      setCitationStats([]);
      return;
    }

    if (citationAbortRef.current) {
      citationAbortRef.current.abort();
    }

    const controller = new AbortController();
    citationAbortRef.current = controller;

    const run = async () => {
      setCitationLoading(true);
      setCitationError('');
      try {
        const result = await fetchCitationTypeStats(
          {
            tenantKey,
            jobId,
            brand,
            timeframe,
            startDate: startDateParam,
            endDate: endDateParam,
          },
          { signal: controller.signal },
        );

        if (result?.status && result.status !== 'success') {
          throw new Error('接口返回错误状态');
        }

        const normalized = normalizeCitationTypeStats(result, { maxItems: 5 });
        setCitationSummary(normalized.summary);
        setCitationStats(normalized.stats);
        setCitationLoading(false);
      } catch (err) {
        if (controller.signal.aborted) return;
        if (err?.name === 'AbortError') return;
        setCitationSummary({ totalRows: 0, conversations: 0 });
        setCitationStats([]);
        setCitationError(err?.message || '数据加载失败');
        setCitationLoading(false);
      }
    };

    run();

    return () => {
      controller.abort();
    };
  }, [tenantKey, jobId, brand, timeframe, startDateParam, endDateParam]);

  useEffect(() => {
    if (!tenantKey || !jobId || !brand) {
      setMediaRows([]);
      setMediaError('');
      return;
    }

    if (mediaAbortRef.current) {
      mediaAbortRef.current.abort();
    }

    const controller = new AbortController();
    mediaAbortRef.current = controller;

    const run = async () => {
      setMediaLoading(true);
      setMediaError('');
      try {
        const result = await fetchCitationDomainStats(
          {
            tenantKey,
            jobId,
            brand,
            timeframe,
            startDate: startDateParam,
            endDate: endDateParam,
            keyword: selectedKeyword || undefined,
            platform: selectedPlatform || undefined,
          },
          { signal: controller.signal },
        );

        if (result?.status && result.status !== 'success') {
          throw new Error('接口返回错误状态');
        }

        const list = Array.isArray(result?.domain_distribution) ? result.domain_distribution : [];
        const normalized = list
          .map((item, index) => {
            const domain = item?.domain ?? '';
            const chineseName = item?.chinese_name ?? item?.chineseName ?? '';
            const keywordValue = item?.keywords ?? item?.keyword ?? '';
            const contentTypeValue = item?.content_types ?? item?.contentTypes ?? '';
            const platformValue = item?.platforms ?? item?.platform ?? '';
            const rawRate =
              item?.['domain-citation-rate'] ??
              item?.domain_citation_rate ??
              item?.domainCitationRate ??
              0;
            const citationRate = roundTwoDecimals(clampPercent(rawRate));
            return {
              key: `${domain || 'row'}-${index}`,
              domain,
              sourceName: chineseName || domain || '--',
              sourceUrl: buildSourceUrl(domain),
              keyword: keywordValue,
              contentType: contentTypeValue,
              platform: platformValue,
              citationRate,
            };
          })
          .filter((item) => item.domain);

        setMediaRows(normalized);
        setMediaLoading(false);
      } catch (err) {
        if (controller.signal.aborted) return;
        if (err?.name === 'AbortError') return;
        setMediaRows([]);
        setMediaError(err?.message || '数据加载失败');
        setMediaLoading(false);
      }
    };

    run();

    return () => {
      controller.abort();
    };
  }, [
    tenantKey,
    jobId,
    brand,
    timeframe,
    startDateParam,
    endDateParam,
    selectedKeyword,
    selectedPlatform,
  ]);

  return (
    <div className="flex w-full flex-col gap-6">
      <KeywordSection
        keywords={keywords}
        loading={loading}
        selectedKeyword={selectedKeyword}
        onKeywordChange={setSelectedKeyword}
      />
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      {citationError ? <p className="text-sm text-destructive">{citationError}</p> : null}
      <SourceAnalysisChart
        displayDate={displayDate}
        timeframeLabel={timeframeLabel}
        summary={citationSummary}
        stats={citationStats}
        loading={citationLoading}
      />
      <MediaListTable
        rows={mediaRows}
        loading={mediaLoading}
        error={mediaError}
        platformOptions={platformOptions}
        selectedPlatform={selectedPlatform}
        onPlatformChange={setSelectedPlatform}
      />
    </div>
  );
}
