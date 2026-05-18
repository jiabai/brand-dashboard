import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Info } from 'lucide-react';
import { fetchKeywordPlatformBrandRates } from '@/api';
import { useDashboardRequestParams } from '@/hooks/useDashboardParams';
import DataTable from './DataTable.jsx';
import { Alert, AlertDescription, AlertTitle } from './ui/alert.jsx';
import { Badge } from './ui/badge.jsx';
import { Card, CardContent } from './ui/card.jsx';
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
        <Info className="text-muted-foreground" />
      </TooltipTrigger>
      <TooltipContent>{description}</TooltipContent>
    </Tooltip>
  </span>
);

const RateCell = ({ value, className = '[&_[data-slot=progress-indicator]]:bg-primary' }) => (
  <div className="flex min-w-32 flex-col gap-1">
    <span className="text-xs text-muted-foreground">{(value * 100).toFixed(2)}%</span>
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
        title: 'Platform',
        dataIndex: 'platform',
        key: 'platform',
        filters: platformFilters,
        onFilter: (value, record) => record.platform === value,
        render: (text) => <Badge variant="secondary">{text}</Badge>,
        width: columnWidths.platform ?? 140,
      },
      {
        title: 'Keyword',
        dataIndex: 'keyword',
        key: 'keyword',
        filters: keywordFilters,
        onFilter: (value, record) => record.keyword === value,
        render: (text) => <span className="font-semibold text-foreground">{text}</span>,
        width: columnWidths.keyword ?? 240,
      },
      {
        title: 'Brand',
        dataIndex: 'brand',
        key: 'brand',
        render: (text) => <span className="text-foreground">{text}</span>,
        width: columnWidths.brand ?? 200,
      },
      {
        title: <RateHeader label="Mention Rate" description="Percentage of conversations where the brand was mentioned" />,
        dataIndex: 'mention_rate',
        key: 'mention_rate',
        sorter: (a, b) => a.mention_rate - b.mention_rate,
        defaultSortOrder: 'descend',
        render: (value) => <RateCell value={value} />,
        width: columnWidths.mention_rate ?? 200,
      },
      {
        title: <RateHeader label="First Mention Rate" description="Percentage of conversations where the brand was mentioned first" />,
        dataIndex: 'first_mention_rate',
        key: 'first_mention_rate',
        sorter: (a, b) => a.first_mention_rate - b.first_mention_rate,
        render: (value) => <RateCell value={value} className="[&_[data-slot=progress-indicator]]:bg-chart-4" />,
        width: columnWidths.first_mention_rate ?? 200,
      },
      {
        title: <RateHeader label="Top 3 Mention Rate" description="Percentage of conversations where the brand was mentioned in the top 3 positions" />,
        dataIndex: 'top3_mention_rate',
        key: 'top3_mention_rate',
        sorter: (a, b) => a.top3_mention_rate - b.top3_mention_rate,
        render: (value) => <RateCell value={value} className="[&_[data-slot=progress-indicator]]:bg-chart-2" />,
        width: columnWidths.top3_mention_rate ?? 200,
      },
    ];

    return defs.map((col) => ({
      ...col,
      onResize: handleResize(col.key),
    }));
  }, [columnWidths, handleResize, keywordFilters, platformFilters]);

  return (
    <Card className="m-6">
      <CardContent className="pt-4">
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
        pagination={{ pageSize: 10 }}
        emptyDescription={error ? '加载失败，请检查URL参数或稍后重试' : '暂无数据'}
      />
      </CardContent>
    </Card>
  );
};

export default BrandShareOfVoiceTable;
