import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  Gauge,
  RefreshCw,
  RotateCcw,
} from 'lucide-react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';

import { fetchProjectDataQuality, retryAnalysisRun } from '@/api';
import { useAuth } from '@/auth/AuthContext.jsx';
import { hasPlatformAdminRole, isPlatformReadonlyTenantAccess } from '@/auth/platformAccess.js';
import { useDashboardParams } from '@/hooks/useDashboardParams';
import EmptyState from '../EmptyState.jsx';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert.jsx';
import { Badge } from '../ui/badge.jsx';
import { Button } from '../ui/button.jsx';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../ui/card.jsx';
import { Progress } from '../ui/progress.jsx';
import {
  PROJECT_NAV_SOURCE_PLATFORM_TENANT_DETAIL,
  buildProjectDetailPath,
  normalizeProjectDataQualityResponse,
  readProjectNavigationSource,
} from './projectPresentation.js';

const formatDateTime = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const QualityStat = ({ label, value, helper }) => (
  <Card size="sm">
    <CardHeader>
      <CardDescription>{label}</CardDescription>
      <CardTitle>{value}</CardTitle>
      {helper ? <p className="text-xs text-muted-foreground">{helper}</p> : null}
    </CardHeader>
  </Card>
);

const ProjectDataQualityPage = () => {
  const navigate = useNavigate();
  const routeParams = useParams();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  const { tenantKey } = useDashboardParams();
  const projectId = routeParams.projectId || '';
  const [quality, setQuality] = useState(() => normalizeProjectDataQualityResponse({}));
  const [feedback, setFeedback] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [retryingRunId, setRetryingRunId] = useState('');

  const loadQuality = useCallback(async () => {
    if (!tenantKey || !projectId) return;
    setIsLoading(true);
    setFeedback('');
    try {
      const response = await fetchProjectDataQuality({ tenantKey, projectId });
      setQuality(normalizeProjectDataQualityResponse(response));
    } catch (error) {
      setQuality(normalizeProjectDataQualityResponse({}));
      setFeedback(error?.message || '数据质量加载失败');
    } finally {
      setIsLoading(false);
    }
  }, [tenantKey, projectId]);

  useEffect(() => {
    loadQuality();
  }, [loadQuality]);

  const metricCoverage = quality.metricCoverage;
  const isReadOnlyTenantAccess = isPlatformReadonlyTenantAccess({ user, tenantKey });
  const navigationSource = readProjectNavigationSource(searchParams);
  const shouldPreserveTenantOverviewSource =
    hasPlatformAdminRole(user)
    && navigationSource === PROJECT_NAV_SOURCE_PLATFORM_TENANT_DETAIL;
  const coverageValue = useMemo(() => {
    if (metricCoverage.coverageRate === null) return 0;
    return Math.max(0, Math.min(100, metricCoverage.coverageRate * 100));
  }, [metricCoverage.coverageRate]);

  const goBack = () => {
    const path = buildProjectDetailPath({
      tenantKey,
      projectId,
      source: shouldPreserveTenantOverviewSource ? navigationSource : '',
    });
    if (path) navigate(path);
  };

  const handleRetry = async (analysisRunId) => {
    if (!analysisRunId || retryingRunId) return;
    setRetryingRunId(analysisRunId);
    setFeedback('');
    try {
      await retryAnalysisRun({ tenantKey, analysisRunId });
      await loadQuality();
    } catch (error) {
      setFeedback(error?.message || '重新分析失败');
    } finally {
      setRetryingRunId('');
    }
  };

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border pb-4">
        <div className="min-w-0">
          <div className="mb-2 flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <Gauge className="size-3.5" aria-hidden="true" />
            <span>监测项目 / 数据质量</span>
          </div>
          <h1 className="text-2xl font-medium tracking-normal text-foreground">数据质量</h1>
          <p className="mt-1 max-w-2xl text-sm leading-relaxed text-muted-foreground">
            {projectId} 的采集失败、过期分析和分析事实覆盖状态。
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button type="button" variant="outline" onClick={goBack}>
            <ArrowLeft data-icon="inline-start" />
            返回项目
          </Button>
          <Button type="button" variant="outline" onClick={loadQuality} disabled={isLoading}>
            <RefreshCw data-icon="inline-start" className={isLoading ? 'animate-spin' : ''} />
            刷新
          </Button>
        </div>
      </div>

      {feedback ? (
        <Alert variant="destructive">
          <AlertTitle>操作失败</AlertTitle>
          <AlertDescription>{feedback}</AlertDescription>
        </Alert>
      ) : null}

      {isLoading ? (
        <div className="h-40 animate-pulse rounded-lg border border-border bg-muted/45" />
      ) : null}

      {!isLoading ? (
        <>
          <div className="grid gap-3 md:grid-cols-4">
            <QualityStat
              label="失败采集"
              value={quality.summary.failedCollectionTaskCount}
              helper={`${quality.summary.retryableFailedCollectionTaskCount} 个可重新领取`}
            />
            <QualityStat
              label="过期分析"
              value={quality.summary.staleAnalysisRunCount}
              helper={`${quality.summary.recomputableAnalysisRunCount} 个可重新分析`}
            />
            <QualityStat
              label="指标覆盖率"
              value={quality.summary.analysisCoverageLabel}
              helper={`${quality.summary.analysisFactCount} 条事实`}
            />
            <QualityStat
              label="指标维度"
              value={quality.summary.analysisDimensionCount}
              helper={metricCoverage.metricDefinitionVersion}
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="size-4" aria-hidden="true" />
                指标覆盖率
              </CardTitle>
              <CardDescription>
                当前项目分析事实覆盖了 {metricCoverage.succeededTaskCount} / {metricCoverage.expectedTaskCount} 个采集任务。
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <Progress value={coverageValue} />
              <div className="grid gap-3 text-sm sm:grid-cols-4">
                <div>
                  <div className="text-xs text-muted-foreground">覆盖率</div>
                  <div className="font-medium text-foreground">{metricCoverage.coverageLabel}</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">失败任务</div>
                  <div className="font-medium text-foreground">{metricCoverage.failedTaskCount}</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">分析回答</div>
                  <div className="font-medium text-foreground">{metricCoverage.analyzedAnswerCount}</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">分析完成</div>
                  <div className="font-medium text-foreground">{formatDateTime(metricCoverage.analysisFinishedAt)}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="size-4" aria-hidden="true" />
                  失败采集
                </CardTitle>
                <CardDescription>最近失败的 collection task 和错误原因。</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                {quality.failedCollectionTasks.length ? quality.failedCollectionTasks.map((task) => (
                  <div
                    key={task.collectionTaskId}
                    className="rounded-lg border border-border bg-muted/25 p-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="min-w-0">
                        <div className="truncate font-medium text-foreground">{task.collectionTaskId}</div>
                        <div className="text-xs text-muted-foreground">
                          {task.platform} / {task.keyword || '-'} / {task.collectionJobId}
                        </div>
                      </div>
                      <Badge variant={task.canRetry ? 'secondary' : 'outline'}>
                        {task.canRetry ? '可重试' : '已达上限'}
                      </Badge>
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">
                      {task.lastErrorCode || 'unknown'}: {task.lastErrorMessage || '无错误信息'}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      attempts {task.attemptCount} / {task.maxAttempts}
                    </p>
                  </div>
                )) : (
                  <EmptyState
                    icon={AlertTriangle}
                    title="暂无失败采集"
                    description="当前项目没有失败的采集任务。"
                  />
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <RotateCcw className="size-4" aria-hidden="true" />
                  过期分析
                </CardTitle>
                <CardDescription>需要重新分析的 stale analysis run。</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                {quality.staleAnalysisRuns.length ? quality.staleAnalysisRuns.map((run) => (
                  <div
                    key={run.analysisRunId}
                    className="rounded-lg border border-border bg-muted/25 p-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="min-w-0">
                        <div className="truncate font-medium text-foreground">{run.analysisRunId}</div>
                        <div className="text-xs text-muted-foreground">
                          {run.collectionJobId} / {formatDateTime(run.staleAt)}
                        </div>
                      </div>
                      {!isReadOnlyTenantAccess ? (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          disabled={!run.canRecompute || Boolean(retryingRunId)}
                          onClick={() => handleRetry(run.analysisRunId)}
                        >
                          <RotateCcw
                            data-icon="inline-start"
                            className={retryingRunId === run.analysisRunId ? 'animate-spin' : ''}
                          />
                          重新分析
                        </Button>
                      ) : null}
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">
                      {run.errorCode || 'stale'}: {run.errorMessage || '上游数据或配置已变化'}
                    </p>
                  </div>
                )) : (
                  <EmptyState
                    icon={RotateCcw}
                    title="暂无过期分析"
                    description="当前项目没有需要重算的分析运行。"
                  />
                )}
              </CardContent>
            </Card>
          </div>
        </>
      ) : null}
    </div>
  );
};

export default React.memo(ProjectDataQualityPage);
