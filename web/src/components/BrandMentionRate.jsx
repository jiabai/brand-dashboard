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
import { Link, MessageCircle, Tags, Trophy } from 'lucide-react';

// Utilities
import { fetchBrandMetrics, fetchPostCitationRate } from '@/api';
import { useDashboardRequestParams } from '@/hooks/useDashboardParams';
import { formatPercentage, toPercent, clampPercent, roundTwoDecimals } from '@/utils';
import { CONFIG } from '@/config';

// Components
import DataTable from './DataTable.jsx';
import EmptyState from './EmptyState';
import LoadingSpinner from './LoadingSpinner';
import { Badge } from './ui/badge.jsx';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card.jsx';
import { Progress } from './ui/progress.jsx';
import { Separator } from './ui/separator.jsx';

const { DEFAULT_BRAND } = CONFIG;

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
        className="grid size-14 place-items-center rounded-full"
        style={{
          background: `conic-gradient(${color} ${safeValue * 3.6}deg, var(--muted) 0deg)`,
        }}
      >
        <div className="grid size-10 place-items-center rounded-full bg-card text-[11px] font-semibold text-foreground ring-1 ring-border">
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
    <div className="mt-1 text-lg font-semibold leading-none text-foreground">{value}</div>
  </div>
);

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

        const [brandMetrics, postCitationRate] = await Promise.all([
          fetchBrandMetrics(
            { tenantKey, jobId, timeframe, startDate: date, endDate: endDate || date },
            { signal: controller.signal },
          ),
          fetchPostCitationRate(
            { tenantKey, jobId, timeframe, startDate: date, endDate: endDate || date, brand },
            { signal: controller.signal },
          ),
        ]);

        if (brandMetrics?.status && brandMetrics.status !== 'success') {
          throw new Error('接口返回错误状态');
        }
        if (postCitationRate?.status && postCitationRate.status !== 'success') {
          throw new Error('接口返回错误状态');
        }

        const brandMetricsList = Array.isArray(brandMetrics?.data)
          ? brandMetrics.data
          : Array.isArray(brandMetrics)
            ? brandMetrics
            : [];
        const postCitationRateData = postCitationRate?.data?.[0] ?? postCitationRate;

        const normalizedBrandItems = brandMetricsList.map((item) => ({
          name: item?.brand,
          mentionRate: roundTwoDecimals(clampPercent(toPercent(item?.mention_rate ?? 0))),
          firstMentionRate: roundTwoDecimals(clampPercent(toPercent(item?.first_mention_rate ?? 0))),
          top3MentionRate: roundTwoDecimals(clampPercent(toPercent(item?.top3_mention_rate ?? 0))),
          promptValue: Number(item?.prompt_count ?? 0),
          coveredKeywordsCount: Number(item?.keyword_coverage ?? 0),
        }));

        setBrandList(normalizedBrandItems);

        const effectiveTargetName = brand || DEFAULT_BRAND;
        const targetItem =
          normalizedBrandItems.find((item) => item.name === effectiveTargetName) ??
          normalizedBrandItems[0];

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
        setError(err?.message || '数据加载失败');
        setIsLoading(false);
      }
    };

    run();

    return () => {
      controller.abort();
    };
  }, [brand, date, endDate, jobId, tenantKey, timeframe]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>品牌提及排名</CardTitle>
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
          <CardTitle>品牌提及排名</CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            title="数据加载失败"
            description={error}
            actionText="重试"
            onAction={() => window.location.reload()}
          />
        </CardContent>
      </Card>
    );
  }

  if (!targetBrandData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>品牌提及排名</CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            title="暂无数据"
            description="接口未返回可展示的数据"
            actionText="重试"
            onAction={() => window.location.reload()}
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>品牌提及排名</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <section className="flex flex-col gap-3 rounded-md bg-muted/35 p-4 sm:flex-row sm:items-center">
          <div className="flex min-w-14 flex-row items-center gap-2 sm:flex-col sm:gap-0">
              <Trophy className="size-5 text-chart-3" />
              <span className="text-xl font-semibold leading-none text-chart-3">
                {typeof targetBrandRank === 'number' ? `#${targetBrandRank}` : '--'}
              </span>
          </div>
          <div className="min-w-0 space-y-2">
              <h3 className="truncate text-base font-semibold leading-tight text-foreground">
                目标品牌: {targetBrandData.name}
              </h3>
              <Badge variant="secondary" className="gap-1 rounded-md">
                <Tags className="size-3" />
                {targetBrandData.coveredKeywordsCount} 覆盖关键词
              </Badge>
          </div>
        </section>

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

        <Separator />

        <section className="space-y-3">
          <h3 className="text-[15px] font-semibold leading-tight text-foreground">其他品牌对比</h3>
          <DataTable
            data={otherBrandsData}
            columns={columns}
            pagination={false}
            rowKey="name"
            emptyDescription="暂无其他品牌数据"
          />
        </section>
      </CardContent>
    </Card>
  );
};

export default React.memo(BrandMentionRate);
