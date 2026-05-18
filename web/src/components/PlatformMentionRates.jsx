import React, { useEffect, useRef, useState } from 'react';
import { ArrowDown, ArrowUp, Trophy } from 'lucide-react';
import { fetchPlatformMetricsByBrand } from '@/api';
import { useDashboardRequestParams } from '@/hooks/useDashboardParams';
import { getPlatformColor, toPercent, clampPercent, roundTwoDecimals } from '@/utils';
import EmptyState from './EmptyState.jsx';
import LoadingSpinner from './LoadingSpinner.jsx';
import { Alert, AlertDescription, AlertTitle } from './ui/alert.jsx';
import { Badge } from './ui/badge.jsx';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card.jsx';
import { Progress } from './ui/progress.jsx';

const PlatformMentionRates = ({
  onPlatformClick,
}) => {
  const { timeframe, date, endDate, tenantKey, jobId, brand } = useDashboardRequestParams();
  const abortControllerRef = useRef(null);
  const [platforms, setPlatforms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const fetchPlatformData = async () => {
      try {
        setLoading(true);
        setError(null);

        const data = await fetchPlatformMetricsByBrand(
          { tenantKey, jobId, brand, timeframe, startDate: date, endDate: endDate || date },
          { signal: controller.signal },
        );

        if (data?.status && data.status !== 'success') {
          throw new Error('接口返回错误状态');
        }

        const list = Array.isArray(data?.data?.platforms) ? data.data.platforms : [];

        const nextPlatforms = list
          .map((item) => {
            const name = item?.platform;
            const rate = roundTwoDecimals(clampPercent(toPercent(item?.mention_rate ?? 0)));
            return {
              name,
              rate,
              color: getPlatformColor(name) || 'var(--primary)',
              change: 0,
            };
          })
          .filter((item) => item.name)
          .sort((a, b) => (b.rate || 0) - (a.rate || 0));

        setPlatforms(nextPlatforms);
        setLoading(false);
      } catch (err) {
        if (controller.signal.aborted) return;
        if (err?.name === 'AbortError') return;
        setError(err?.message || '数据加载失败');
        setLoading(false);
      }
    };

    fetchPlatformData();
    return () => {
      controller.abort();
    };
  }, [brand, date, endDate, jobId, tenantKey, timeframe]);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>各平台提及率 ({brand})</CardTitle>
        </CardHeader>
        <CardContent>
          <LoadingSpinner text="正在加载平台数据..." />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>各平台提及率 ({brand})</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertTitle>平台数据加载失败</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (platforms.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>各平台提及率 ({brand})</CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState title="暂无平台数据" description="当前筛选条件下没有平台提及率数据" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="min-h-[220px]">
      <CardHeader>
        <CardTitle>各平台提及率 ({brand})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-3">
          {platforms.map((platform, index) => (
            <button
              key={platform.name}
              type="button"
              className="w-full rounded-md border border-border/80 bg-muted/25 p-3 text-left transition-colors hover:border-primary/35 hover:bg-muted/55 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:outline-none data-[featured=true]:bg-muted/40"
              data-featured={index < 3}
              onClick={() => onPlatformClick?.(platform)}
            >
              <div className="flex w-full flex-col gap-2.5">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex min-w-0 items-center gap-2">
                  {index < 3 && (
                      <Badge variant="secondary" className="h-6 gap-1 rounded-md px-2">
                        <Trophy data-icon="inline-start" />
                      {index + 1}
                      </Badge>
                  )}
                    <span className="truncate text-sm font-semibold text-foreground">
                    {platform.name}
                    </span>
                </div>
                  <span className="shrink-0 text-xl font-semibold leading-none" style={{ color: platform.color }}>
                    {platform.rate.toFixed(2)}%
                  </span>
              </div>
              <Progress
                  value={platform.rate}
                  className="h-2.5 [&_[data-slot=progress-indicator]]:bg-[var(--platform-color)]"
                  style={{ '--platform-color': platform.color }}
              />
              {platform.change !== 0 && (
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  {platform.change > 0 ? (
                      <ArrowUp data-icon="inline-start" className="text-chart-3" />
                  ) : (
                      <ArrowDown data-icon="inline-start" className="text-destructive" />
                  )}
                    {Math.abs(platform.change)}%
                </div>
              )}
            </div>
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default React.memo(PlatformMentionRates);
