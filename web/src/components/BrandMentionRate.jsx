/**
 * Brand Mention Rate Component
 * Displays brand mention rate with circular progress chart and brand rankings
 *
 * @component
 * @example
 * return (
 *   <BrandMentionRate
 *     brandData={{ mentionRate: 85, rank: 1, change: 5 }}
 *     isLoading={false}
 *     error={null}
 *   />
 * );
 */

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Activity, Clock, Database, Gauge, Link, MessageCircle, Tags, Trophy } from 'lucide-react';

// Utilities
import { fetchBrandMetrics, fetchPostCitationRate } from '@/api';
import { useDashboardRequestParams } from '@/hooks/useDashboardParams';
import {
  clampPercent,
  formatPercentage,
  normalizeMetricSnapshotMetadata,
  roundTwoDecimals,
  toPercent,
} from '@/utils';

// Components
import DataTable from './DataTable.jsx';
import EmptyState from './EmptyState';
import LoadingSpinner from './LoadingSpinner';
import { Badge } from './ui/badge.jsx';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card.jsx';
import { Progress } from './ui/progress.jsx';

const metricTones = {
  primary: 'var(--primary)',
  info: 'var(--chart-2)',
  warning: 'var(--chart-4)',
  success: 'var(--chart-3)',
};

const MetricCircle = ({ label, value, tone = 'primary' }) => {
  const safeValue = clampPercent(Number(value) || 0);
  const color = metricTones[tone] || metricTones.primary;

  return (
    <div className="flex min-w-0 flex-col items-center gap-2 text-center">
      <div
        className="grid size-24 place-items-center rounded-full"
        style={{
          background: `conic-gradient(${color} ${safeValue * 3.6}deg, var(--muted) 0deg)`,
        }}
      >
        <div className="grid size-16 place-items-center rounded-full bg-card text-sm font-medium text-foreground ring-1 ring-border">
          {formatPercentage(safeValue)}
        </div>
      </div>
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
    </div>
  );
};

const StatTile = ({ icon: Icon, label, value }) => (
  <div className="rounded-md bg-muted/45 px-3 py-2.5">
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <Icon className="size-4" />
      {label}
    </div>
    <div className="mt-1 text-lg font-medium leading-snug text-foreground">{value}</div>
  </div>
);

const SnapshotMetadataTile = ({ icon: Icon, label, value }) => (
  <div className="min-w-0 rounded-md bg-muted/45 px-3 py-2.5">
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <Icon className="size-4 shrink-0" />
      <span className="truncate">{label}</span>
    </div>
    <div className="mt-1 break-words text-sm font-medium leading-snug text-foreground">{value}</div>
  </div>
);

const SnapshotQualityPanel = ({ metadata }) => {
  if (!metadata) return null;

  const generatedAtLabel = metadata.generatedAtLabel || '快照未生成';

  return (
    <section className="space-y-3 rounded-md border border-border bg-background/80 p-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 items-center gap-2">
          <Database className="size-4 shrink-0 text-muted-foreground" />
          <span className="truncate text-sm font-medium text-foreground">数据来源: {metadata.sourceLabel}</span>
        </div>
        <Badge variant={metadata.hasSnapshot ? 'default' : 'secondary'} className="w-fit rounded-md">
          {metadata.snapshotStatus === 'available' ? '快照可用' : '快照未生成'}
        </Badge>
      </div>
      <p className="text-xs leading-relaxed text-muted-foreground">{metadata.description}</p>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <SnapshotMetadataTile icon={Clock} label="指标生成" value={generatedAtLabel} />
        <SnapshotMetadataTile icon={Gauge} label="采集覆盖" value={metadata.coverageLabel} />
        <SnapshotMetadataTile icon={Activity} label="分析完整性" value={metadata.analysisCompletenessLabel} />
        <SnapshotMetadataTile icon={MessageCircle} label="分析回答" value={metadata.analyzedAnswerLabel} />
      </div>
    </section>
  );
};

const RateCell = ({ value, tone = 'primary' }) => (
  <div className="w-[7.5rem] space-y-1">
    <Progress
      value={value}
      className={{
        primary: '[&_[data-slot=progress-indicator]]:bg-primary',
        info: '[&_[data-slot=progress-indicator]]:bg-chart-2',
        warning: '[&_[data-slot=progress-indicator]]:bg-chart-4',
      }[tone]}
    />
    <span className="text-xs text-muted-foreground">{formatPercentage(value)}</span>
  </div>
);

const BrandMentionRate = () => {
  const { timeframe, date, endDate, tenantKey, jobId, brand } = useDashboardRequestParams();
  const abortControllerRef = useRef(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [targetBrandData, setTargetBrandData] = useState(null);
  const [brandList, setBrandList] = useState([]);
  const [metricSnapshotMetadata, setMetricSnapshotMetadata] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  const targetBrandName = targetBrandData?.name ?? brand;

  const { otherBrandsData, targetBrandRank } = useMemo(() => {
    if (!brandList.length) {
      return { otherBrandsData: [], targetBrandRank: null };
    }

    const ranked = [...brandList]
      .filter((item) => typeof item.mentionRate === 'number')
      .sort((a, b) => (b.mentionRate || 0) - (a.mentionRate || 0))
      .map((item, index) => ({
        ...item,
        rank: index + 1,
      }));

    const targetIndex = ranked.findIndex((item) => item.name === targetBrandName);
    const rankValue = targetIndex === -1 ? null : ranked[targetIndex].rank;
    const others = ranked.filter((item) => item.name !== targetBrandName);

    return { otherBrandsData: others, targetBrandRank: rankValue };
  }, [brandList, targetBrandName]);

  const columns = useMemo(
    () => [
      {
        title: '排名',
        dataIndex: 'rank',
        key: 'rank',
        width: 72,
        render: (rank) => (
          <div className="flex justify-center">
            <Badge variant={rank <= 3 ? 'default' : 'secondary'}>{rank}</Badge>
          </div>
        ),
        sorter: (a, b) => a.rank - b.rank,
      },
      {
        title: '品牌',
        dataIndex: 'name',
        key: 'name',
        width: 120,
        render: (text) => <span className="font-medium text-foreground">{text}</span>,
      },
      {
        title: '总提及率',
        dataIndex: 'mentionRate',
        key: 'mentionRate',
        width: 160,
        render: (val) => <RateCell value={val} />,
        sorter: (a, b) => a.mentionRate - b.mentionRate,
        defaultSortOrder: 'descend',
      },
      {
        title: '首位提及率',
        dataIndex: 'firstMentionRate',
        key: 'firstMentionRate',
        width: 160,
        render: (val) => <RateCell value={val} tone="info" />,
        sorter: (a, b) => a.firstMentionRate - b.firstMentionRate,
      },
      {
        title: '前3提及率',
        dataIndex: 'top3MentionRate',
        key: 'top3MentionRate',
        width: 160,
        render: (val) => <RateCell value={val} tone="warning" />,
        sorter: (a, b) => a.top3MentionRate - b.top3MentionRate,
      },
    ],
    [],
  );

  useEffect(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const run = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const brandMetrics = await fetchBrandMetrics(
          { tenantKey, jobId, timeframe, startDate: date, endDate: endDate || date },
          { signal: controller.signal },
        );

        if (brandMetrics?.status && brandMetrics.status !== 'success') {
          throw new Error('接口返回错误状态');
        }

        setMetricSnapshotMetadata(normalizeMetricSnapshotMetadata(brandMetrics?.metadata));

        const brandMetricsList = Array.isArray(brandMetrics?.data)
          ? brandMetrics.data
          : Array.isArray(brandMetrics)
            ? brandMetrics
            : [];

        const normalizedBrandItems = brandMetricsList.map((item) => ({
          name: item?.brand,
          mentionRate: roundTwoDecimals(clampPercent(toPercent(item?.mention_rate ?? 0))),
          firstMentionRate: roundTwoDecimals(clampPercent(toPercent(item?.first_mention_rate ?? 0))),
          top3MentionRate: roundTwoDecimals(clampPercent(toPercent(item?.top3_mention_rate ?? 0))),
          promptValue: Number(item?.prompt_count ?? 0),
          coveredKeywordsCount: Number(item?.keyword_coverage ?? 0),
        }));

        setBrandList(normalizedBrandItems);

        const effectiveTargetName = brand || normalizedBrandItems[0]?.name || '';
        const targetItem =
          normalizedBrandItems.find((item) => item.name === effectiveTargetName) ??
          normalizedBrandItems[0];

        let postCitationRateData = null;
        if (effectiveTargetName) {
          const postCitationRate = await fetchPostCitationRate(
            { tenantKey, jobId, timeframe, startDate: date, endDate: endDate || date, brand: effectiveTargetName },
            { signal: controller.signal },
          );
          if (postCitationRate?.status && postCitationRate.status !== 'success') {
            throw new Error('接口返回错误状态');
          }
          postCitationRateData = postCitationRate?.data?.[0] ?? postCitationRate;
        }

        const nextTargetBrandData = targetItem
          ? {
              name: targetItem.name ?? effectiveTargetName,
              mentionRate: roundTwoDecimals(targetItem.mentionRate),
              firstMentionRate: roundTwoDecimals(targetItem.firstMentionRate),
              top3MentionRate: roundTwoDecimals(targetItem.top3MentionRate),
              articleCitationRate: roundTwoDecimals(clampPercent(
                toPercent(postCitationRateData?.citation_rate_by_post ?? 0),
              )),
              promptValue: targetItem.promptValue,
              citationSourceValue: Number(postCitationRateData?.citation_source_count ?? 0),
              coveredKeywordsCount: targetItem.coveredKeywordsCount,
            }
          : null;

        setTargetBrandData(nextTargetBrandData);
        setIsLoading(false);
      } catch (err) {
        if (controller.signal.aborted) return;
        if (err?.name === 'AbortError') return;
        setMetricSnapshotMetadata(null);
        setError(err?.message || '数据加载失败');
        setIsLoading(false);
      }
    };

    run();

    return () => {
      controller.abort();
    };
  }, [brand, date, endDate, jobId, tenantKey, timeframe, reloadKey]);

  if (isLoading) {
    return (
      <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Trophy className="size-5 text-primary" />
          <CardTitle>品牌提及排名</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <LoadingSpinner text="正在加载品牌数据..." />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Trophy className="size-5 text-primary" />
            <CardTitle>品牌提及排名</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <EmptyState
            title="数据加载失败"
            description={error}
            actionText="重试"
            onAction={() => setReloadKey((prev) => prev + 1)}
          />
        </CardContent>
      </Card>
    );
  }

  if (!targetBrandData) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Trophy className="size-5 text-primary" />
            <CardTitle>品牌提及排名</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <EmptyState
            title="暂无数据"
            description="当前筛选下没有可展示的品牌指标；若刚完成采集，请等待分析和指标快照生成。"
            actionText="重试"
            onAction={() => setReloadKey((prev) => prev + 1)}
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
      <Card className="h-full">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Trophy className="size-5 text-primary" />
            <CardTitle>目标品牌核心指标</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <section className="flex flex-col gap-3 rounded-md bg-muted/35 p-4 sm:flex-row sm:items-center">
            <div className="flex min-w-14 flex-row items-center gap-2 sm:flex-col sm:gap-0">
                <Trophy className="size-5 text-foreground" />
                <span className="text-xl font-medium leading-none text-foreground">
                  {typeof targetBrandRank === 'number' ? `#${targetBrandRank}` : '--'}
                </span>
            </div>
            <div className="min-w-0 space-y-2">
                <h3 className="truncate text-base font-medium leading-snug text-foreground">
                  目标品牌: {targetBrandData.name}
                </h3>
                <Badge variant="secondary" className="gap-1 rounded-md">
                  <Tags className="size-3" />
                  {targetBrandData.coveredKeywordsCount} 覆盖关键词
                </Badge>
            </div>
          </section>

          <SnapshotQualityPanel metadata={metricSnapshotMetadata} />

          <section className="grid grid-cols-2 gap-3 xl:grid-cols-4">
            <MetricCircle label="总提及率" value={targetBrandData.mentionRate} />
            <MetricCircle label="首位提及率" value={targetBrandData.firstMentionRate} tone="info" />
            <MetricCircle label="前3提及率" value={targetBrandData.top3MentionRate} tone="warning" />
            <MetricCircle label="发文引用率" value={targetBrandData.articleCitationRate} tone="success" />
          </section>

          <section className="grid grid-cols-2 gap-3">
            <StatTile icon={MessageCircle} label="问题总数" value={targetBrandData.promptValue} />
            <StatTile icon={Link} label="引用信源数量" value={targetBrandData.citationSourceValue} />
          </section>
        </CardContent>
      </Card>

      <Card className="h-full">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Trophy className="size-5 text-muted-foreground" />
            <CardTitle>竞品品牌对比</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <DataTable
            data={otherBrandsData}
            columns={columns}
            pagination={false}
            rowKey="name"
            emptyDescription="暂无其他品牌数据"
          />
        </CardContent>
      </Card>
    </div>
  );
};

export default React.memo(BrandMentionRate);
