import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  BookOpen,
  Filter,
  Link as LinkIcon,
  MessageSquareText,
  RotateCcw,
  Tags,
} from 'lucide-react';

import { fetchAnswerSnapshots, fetchBrandMetrics, fetchFilterMetadata } from '@/api';
import { useDashboardRequestParams } from '@/hooks/useDashboardParams';
import {
  ANSWER_SNAPSHOT_ALL_VALUE,
  ANSWER_SNAPSHOT_REFERENCE_OPTIONS,
  ANSWER_SNAPSHOT_SENTIMENT_OPTIONS,
  normalizeAnswerSnapshots,
} from '@/utils';

import DataTable from './DataTable.jsx';
import EmptyState from './EmptyState.jsx';
import LoadingSpinner from './LoadingSpinner.jsx';
import { Badge } from './ui/badge.jsx';
import { Button } from './ui/button.jsx';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card.jsx';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select.jsx';

const ALL_VALUE = ANSWER_SNAPSHOT_ALL_VALUE;

const uniqueOptions = (items = []) => (
  Array.from(new Set(items.filter(Boolean))).map((item) => ({
    label: item,
    value: item,
  }))
);

const toApiFilter = (value) => (value === ALL_VALUE ? undefined : value);

const toReferenceFilter = (value) => {
  if (value === 'referenced') return true;
  if (value === 'unreferenced') return false;
  return undefined;
};

const FilterSelect = ({ label, icon: Icon, value, options, onChange }) => (
  <label className="min-w-0 space-y-1.5">
    <span className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
      <Icon className="size-3.5" />
      {label}
    </span>
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-full">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          {options.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectGroup>
      </SelectContent>
    </Select>
  </label>
);

const ReferenceList = ({ references }) => {
  if (!references.length) {
    return <span className="text-muted-foreground">无引用</span>;
  }

  return (
    <div className="space-y-1.5">
      {references.slice(0, 2).map((reference) => (
        <a
          key={reference.url}
          href={reference.url}
          target="_blank"
          rel="noreferrer"
          className="block max-w-[16rem] truncate text-primary hover:underline"
        >
          {reference.domain || reference.url}
        </a>
      ))}
      {references.length > 2 ? (
        <span className="block text-xs text-muted-foreground">
          另有 {references.length - 2} 条引用
        </span>
      ) : null}
    </div>
  );
};

const AnswerText = ({ title, content }) => (
  <div className="max-w-[34rem] space-y-1">
    <div className="text-xs font-medium text-muted-foreground">{title}</div>
    <p className="max-h-24 overflow-hidden whitespace-normal break-words text-sm leading-relaxed text-foreground">
      {content || '--'}
    </p>
  </div>
);

const MobileAnswerSnapshotList = ({ rows }) => (
  <div className="space-y-3 md:hidden">
    {rows.map((record) => (
      <article key={record.id} className="space-y-3 rounded-md border bg-background p-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium text-foreground">{record.dateLabel}</span>
          <Badge variant="secondary" className="rounded-md">{record.platform}</Badge>
          <Badge variant="outline" className="rounded-md">{record.keyword}</Badge>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium text-foreground">{record.brand}</span>
          <Badge
            variant={record.sentimentStatus === 'negative' ? 'destructive' : 'secondary'}
            className="rounded-md"
          >
            {record.sentimentLabel}
          </Badge>
          <Badge variant={record.hasReference ? 'default' : 'outline'} className="rounded-md">
            {record.referenceLabel}
          </Badge>
        </div>
        <AnswerText title="Prompt" content={record.queryContent} />
        <AnswerText title="Answer" content={record.answerContent} />
        <div className="space-y-1">
          <div className="text-xs font-medium text-muted-foreground">引用</div>
          <ReferenceList references={record.references} />
        </div>
      </article>
    ))}
  </div>
);

const AnswerSnapshotsPage = () => {
  const { timeframe, date, endDate, tenantKey, jobId, brand } = useDashboardRequestParams();
  const abortControllerRef = useRef(null);

  const [filters, setFilters] = useState(() => ({
    brand: brand || ALL_VALUE,
    platform: ALL_VALUE,
    keyword: ALL_VALUE,
    sentiment: ALL_VALUE,
    reference: ALL_VALUE,
  }));
  const [brandOptions, setBrandOptions] = useState([]);
  const [platformOptions, setPlatformOptions] = useState([]);
  const [keywordOptions, setKeywordOptions] = useState([]);
  const [rows, setRows] = useState([]);
  const [summary, setSummary] = useState({ rowCount: 0, totalCount: 0 });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!brand) return;
    setFilters((previous) => (
      previous.brand === ALL_VALUE ? { ...previous, brand } : previous
    ));
  }, [brand]);

  const selectOptions = useMemo(() => ({
    brands: [
      { label: '全部品牌', value: ALL_VALUE },
      ...uniqueOptions([brand, ...brandOptions]),
    ],
    platforms: [
      { label: '全部平台', value: ALL_VALUE },
      ...uniqueOptions(platformOptions),
    ],
    keywords: [
      { label: '全部关键词', value: ALL_VALUE },
      ...uniqueOptions(keywordOptions),
    ],
  }), [brand, brandOptions, keywordOptions, platformOptions]);

  const updateFilter = (key) => (value) => {
    setFilters((previous) => ({ ...previous, [key]: value }));
  };

  const resetFilters = () => {
    setFilters({
      brand: brand || ALL_VALUE,
      platform: ALL_VALUE,
      keyword: ALL_VALUE,
      sentiment: ALL_VALUE,
      reference: ALL_VALUE,
    });
  };

  useEffect(() => {
    const controller = new AbortController();

    const loadOptions = async () => {
      try {
        const [brandMetrics, filterMetadata] = await Promise.all([
          fetchBrandMetrics(
            { tenantKey, jobId, timeframe, startDate: date, endDate: endDate || date },
            { signal: controller.signal },
          ),
          fetchFilterMetadata(
            { tenantKey, jobId, startDate: date, endDate: endDate || date },
            { signal: controller.signal },
          ),
        ]);

        const metricRows = Array.isArray(brandMetrics?.data) ? brandMetrics.data : [];
        setBrandOptions(metricRows.map((item) => item?.brand).filter(Boolean));
        setPlatformOptions(filterMetadata?.data?.platforms || []);
        setKeywordOptions(filterMetadata?.data?.keywords || []);
      } catch (err) {
        if (controller.signal.aborted || err?.name === 'AbortError') return;
        setBrandOptions([]);
        setPlatformOptions([]);
        setKeywordOptions([]);
      }
    };

    loadOptions();

    return () => {
      controller.abort();
    };
  }, [date, endDate, jobId, tenantKey, timeframe]);

  useEffect(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const loadRows = async () => {
      try {
        setIsLoading(true);
        setError('');
        const payload = await fetchAnswerSnapshots(
          {
            tenantKey,
            jobId,
            timeframe,
            startDate: date,
            endDate: endDate || date,
            brand: toApiFilter(filters.brand),
            platform: toApiFilter(filters.platform),
            keyword: toApiFilter(filters.keyword),
            sentiment: toApiFilter(filters.sentiment),
            hasReference: toReferenceFilter(filters.reference),
            limit: 50,
            offset: 0,
          },
          { signal: controller.signal },
        );

        if (payload?.status && payload.status !== 'success') {
          throw new Error('接口返回错误状态');
        }

        const normalized = normalizeAnswerSnapshots(payload);
        setRows(normalized.items);
        setSummary(normalized.summary);
        setIsLoading(false);
      } catch (err) {
        if (controller.signal.aborted || err?.name === 'AbortError') return;
        setRows([]);
        setSummary({ rowCount: 0, totalCount: 0 });
        setError(err?.message || '数据加载失败');
        setIsLoading(false);
      }
    };

    loadRows();

    return () => {
      controller.abort();
    };
  }, [date, endDate, filters, jobId, reloadKey, tenantKey, timeframe]);

  const columns = useMemo(
    () => [
      {
        title: '日期 / 维度',
        key: 'context',
        width: 180,
        render: (_, record) => (
          <div className="space-y-2">
            <span className="block font-medium text-foreground">{record.dateLabel}</span>
            <div className="flex flex-wrap gap-1.5">
              <Badge variant="secondary" className="rounded-md">{record.platform}</Badge>
              <Badge variant="outline" className="rounded-md">{record.keyword}</Badge>
            </div>
          </div>
        ),
      },
      {
        title: '品牌 / 情绪',
        key: 'brand',
        width: 160,
        render: (_, record) => (
          <div className="space-y-2">
            <span className="block font-medium text-foreground">{record.brand}</span>
            <Badge
              variant={record.sentimentStatus === 'negative' ? 'destructive' : 'secondary'}
              className="rounded-md"
            >
              {record.sentimentLabel}
            </Badge>
          </div>
        ),
      },
      {
        title: '问题',
        key: 'query',
        width: 260,
        render: (_, record) => <AnswerText title="Prompt" content={record.queryContent} />,
      },
      {
        title: '回答',
        key: 'answer',
        width: 360,
        render: (_, record) => <AnswerText title="Answer" content={record.answerContent} />,
      },
      {
        title: '引用状态',
        key: 'reference',
        width: 220,
        render: (_, record) => (
          <div className="space-y-2 text-sm">
            <Badge variant={record.hasReference ? 'default' : 'outline'} className="rounded-md">
              {record.referenceLabel}
            </Badge>
            <ReferenceList references={record.references} />
          </div>
        ),
      },
    ],
    [],
  );

  return (
    <div className="flex min-w-0 flex-col gap-5">
      <div className="flex flex-col gap-2 border-b border-border pb-4">
        <nav aria-label="面包屑导航" className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <span>仪表板</span>
          <span>/</span>
          <span className="font-medium text-foreground">问答快照</span>
        </nav>
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <h1 className="text-2xl font-medium text-foreground">问答快照</h1>
            <p className="max-w-[720px] text-sm text-muted-foreground">
              按品牌、平台、关键词、情绪和引用状态查看原始回答
            </p>
          </div>
          <div className="flex flex-wrap gap-2 text-sm text-muted-foreground">
            <Badge variant="secondary" className="rounded-md">
              当前 {summary.rowCount} 条
            </Badge>
            <Badge variant="outline" className="rounded-md">
              共 {summary.totalCount} 条
            </Badge>
          </div>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Filter className="size-5 text-primary" />
            <CardTitle>筛选条件</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-[1fr_1fr_1fr_1fr_1fr_auto]">
          <FilterSelect
            label="品牌"
            icon={BookOpen}
            value={filters.brand}
            options={selectOptions.brands}
            onChange={updateFilter('brand')}
          />
          <FilterSelect
            label="平台"
            icon={MessageSquareText}
            value={filters.platform}
            options={selectOptions.platforms}
            onChange={updateFilter('platform')}
          />
          <FilterSelect
            label="关键词"
            icon={Tags}
            value={filters.keyword}
            options={selectOptions.keywords}
            onChange={updateFilter('keyword')}
          />
          <FilterSelect
            label="情绪"
            icon={MessageSquareText}
            value={filters.sentiment}
            options={ANSWER_SNAPSHOT_SENTIMENT_OPTIONS}
            onChange={updateFilter('sentiment')}
          />
          <FilterSelect
            label="引用状态"
            icon={LinkIcon}
            value={filters.reference}
            options={ANSWER_SNAPSHOT_REFERENCE_OPTIONS}
            onChange={updateFilter('reference')}
          />
          <div className="flex items-end">
            <Button variant="outline" className="w-full gap-2" onClick={resetFilters}>
              <RotateCcw className="size-4" />
              重置
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <MessageSquareText className="size-5 text-primary" />
            <CardTitle>原始回答列表</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <LoadingSpinner text="正在加载问答快照..." />
          ) : error ? (
            <EmptyState
              title="数据加载失败"
              description={error}
              actionText="重试"
              onAction={() => setReloadKey((value) => value + 1)}
            />
          ) : rows.length ? (
            <>
              <div className="hidden md:block">
                <DataTable
                  data={rows}
                  columns={columns}
                  rowKey="id"
                  pagination={false}
                  emptyDescription="当前筛选下没有问答快照"
                />
              </div>
              <MobileAnswerSnapshotList rows={rows} />
            </>
          ) : (
            <EmptyState
              title="暂无问答快照"
              description="当前筛选下没有问答快照；可放宽品牌、平台、关键词、情绪或引用状态。"
              actionText="重置筛选"
              onAction={resetFilters}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default React.memo(AnswerSnapshotsPage);
