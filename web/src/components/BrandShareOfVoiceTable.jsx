import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Info } from 'lucide-react';
import { fetchKeywordPlatformBrandRates } from '@/api';
import { useDashboardRequestParams } from '@/hooks/useDashboardParams';
import DataTable from './DataTable.jsx';
import { Alert, AlertDescription, AlertTitle } from './ui/alert.jsx';
import { Badge } from './ui/badge.jsx';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card.jsx';
import { Progress } from './ui/progress.jsx';
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip.jsx';

const COLUMN_WIDTH_STORAGE_KEY = 'BrandShareOfVoiceTable:columnWidths';
const MIN_COLUMN_WIDTH = 96;
const MAX_COLUMN_WIDTH = 720;

const RateHeader = ({ label, description }) => (
  <span className="inline-flex items-center gap-1">
    {label}
    <Tooltip>
      <TooltipTrigger asChild>
        <Info className="size-4 text-muted-foreground" />
      </TooltipTrigger>
      <TooltipContent>{description}</TooltipContent>
    </Tooltip>
  </span>
);

const RateCell = ({ value, className = '[&_[data-slot=progress-indicator]]:bg-primary' }) => (
  <div className="flex min-w-40 flex-col gap-1.5">
    <span className="text-sm font-medium text-muted-foreground">{(value * 100).toFixed(2)}%</span>
    <Progress value={value * 100} className={className} />
  </div>
);

const BrandShareOfVoiceTable = () => {
  const { timeframe, startDate, endDate, tenantKey, jobId } = useDashboardRequestParams();
  const abortControllerRef = useRef(null);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [columnWidths, setColumnWidths] = useState(() => {
    try {
      const raw = window.localStorage.getItem(COLUMN_WIDTH_STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (_) {
      return {};
    }
  });

  useEffect(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const run = async () => {
      try {
        setLoading(true);
        setError('');
        const result = await fetchKeywordPlatformBrandRates(
          { tenantKey, jobId, timeframe, startDate, endDate },
          { signal: controller.signal },
        );

        if (result?.status && result.status !== 'success') {
          throw new Error('接口返回错误状态');
        }

        const list = Array.isArray(result?.data) ? result.data : [];

        const normalized = list
          .map((item) => {
            const keyword = item?.keyword;
            const platform = item?.platform;
            const brand = item?.brand;
            const mentionRate = Number(item?.mention_rate ?? 0);
            const firstMentionRate = Number(item?.first_mention_rate ?? 0);
            const top3MentionRate = Number(item?.top3_mention_rate ?? 0);
            return {
              keyword,
              platform,
              brand,
              mention_rate: Number.isFinite(mentionRate) ? mentionRate : 0,
              first_mention_rate: Number.isFinite(firstMentionRate) ? firstMentionRate : 0,
              top3_mention_rate: Number.isFinite(top3MentionRate) ? top3MentionRate : 0,
            };
          })
          .filter((item) => item.keyword && item.platform && item.brand);

        setRows(normalized);
        setLoading(false);
      } catch (err) {
        if (controller.signal.aborted) return;
        if (err?.name === 'AbortError') return;
        setRows([]);
        setError(err?.message || '数据加载失败');
        setLoading(false);
      }
    };

    run();

    return () => {
      controller.abort();
    };
  }, [endDate, jobId, startDate, tenantKey, timeframe]);

  const keywordFilters = useMemo(() => {
    const keywords = [...new Set(rows.map((item) => item.keyword).filter(Boolean))];
    return keywords.map((k) => ({ text: k, value: k }));
  }, [rows]);

  const platformFilters = useMemo(() => {
    const platforms = [...new Set(rows.map((item) => item.platform).filter(Boolean))];
    return platforms.map((p) => ({ text: p, value: p }));
  }, [rows]);

  const setColumnWidth = useCallback((key, nextWidth) => {
    const width = Math.max(MIN_COLUMN_WIDTH, Math.min(MAX_COLUMN_WIDTH, Math.round(nextWidth)));
    setColumnWidths((prev) => {
      const next = { ...prev, [key]: width };
      try {
        window.localStorage.setItem(COLUMN_WIDTH_STORAGE_KEY, JSON.stringify(next));
      } catch (_) {
        // ignore
      }
      return next;
    });
  }, []);

  const handleResize = useCallback(
    (key) => (nextWidth) => {
      setColumnWidth(key, nextWidth);
    },
    [setColumnWidth],
  );

  const columns = useMemo(() => {
    const defs = [
      {
        title: '平台',
        dataIndex: 'platform',
        key: 'platform',
        filters: platformFilters,
        onFilter: (value, record) => record.platform === value,
        render: (text) => <Badge variant="secondary">{text}</Badge>,
        width: columnWidths.platform ?? 160,
      },
      {
        title: '关键词',
        dataIndex: 'keyword',
        key: 'keyword',
        filters: keywordFilters,
        onFilter: (value, record) => record.keyword === value,
        render: (text) => <span className="font-medium text-foreground">{text}</span>,
        width: columnWidths.keyword ?? 300,
      },
      {
        title: '品牌',
        dataIndex: 'brand',
        key: 'brand',
        render: (text) => <span className="text-foreground">{text}</span>,
        width: columnWidths.brand ?? 240,
      },
      {
        title: <RateHeader label="提及率" description="品牌被提及的对话占比" />,
        dataIndex: 'mention_rate',
        key: 'mention_rate',
        sorter: (a, b) => a.mention_rate - b.mention_rate,
        defaultSortOrder: 'descend',
        render: (value) => <RateCell value={value} />,
        width: columnWidths.mention_rate ?? 280,
      },
      {
        title: <RateHeader label="首提率" description="品牌被首先提及的对话占比" />,
        dataIndex: 'first_mention_rate',
        key: 'first_mention_rate',
        sorter: (a, b) => a.first_mention_rate - b.first_mention_rate,
        render: (value) => <RateCell value={value} className="[&_[data-slot=progress-indicator]]:bg-chart-4" />,
        width: columnWidths.first_mention_rate ?? 280,
      },
      {
        title: <RateHeader label="前三提及率" description="品牌在前三位置被提及的对话占比" />,
        dataIndex: 'top3_mention_rate',
        key: 'top3_mention_rate',
        sorter: (a, b) => a.top3_mention_rate - b.top3_mention_rate,
        render: (value) => <RateCell value={value} className="[&_[data-slot=progress-indicator]]:bg-chart-2" />,
        width: columnWidths.top3_mention_rate ?? 280,
      },
    ];

    return defs.map((col) => ({
      ...col,
      onResize: handleResize(col.key),
    }));
  }, [columnWidths, handleResize, keywordFilters, platformFilters]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>品牌声量份额</CardTitle>
      </CardHeader>
      <CardContent className="p-8">
      {!!error && (
        <Alert variant="destructive" className="mb-3">
          <AlertTitle>数据加载失败</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      <DataTable
        columns={columns}
        data={rows}
        rowKey={(record) => `${record.keyword}-${record.platform}-${record.brand}`}
        loading={loading}
        error=""
        className="[&_table]:min-w-[1280px]"
        pagination={{ pageSize: 10 }}
        emptyDescription={error ? '加载失败，请检查URL参数或稍后重试' : '暂无数据'}
      />
      </CardContent>
    </Card>
  );
};

export default BrandShareOfVoiceTable;
