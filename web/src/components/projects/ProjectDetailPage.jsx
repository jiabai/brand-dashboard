import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ArrowLeft, Boxes, FileQuestion, FolderKanban, Gauge, RefreshCw } from 'lucide-react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';

import { fetchProjectDetail } from '@/api';
import { useAuth } from '@/auth/AuthContext.jsx';
import { hasPlatformAdminRole } from '@/auth/platformAccess.js';
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
import { Separator } from '../ui/separator.jsx';
import { buildPlatformTenantProjectOverviewPath } from '../platform/tenantPresentation.js';
import {
  PROJECT_NAV_SOURCE_PLATFORM_TENANT_DETAIL,
  buildProjectListPath,
  buildProjectDataQualityPath,
  countProjectBrandsByRole,
  getProjectStatusMeta,
  normalizeProjectDetailResponse,
  readProjectNavigationSource,
} from './projectPresentation.js';

const ProjectDetailPage = () => {
  const navigate = useNavigate();
  const routeParams = useParams();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  const { tenantKey } = useDashboardParams();
  const projectId = routeParams.projectId || '';
  const [project, setProject] = useState(null);
  const [feedback, setFeedback] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const loadProject = useCallback(async () => {
    if (!tenantKey || !projectId) return;
    setIsLoading(true);
    setFeedback('');
    try {
      const response = await fetchProjectDetail({ tenantKey, projectId });
      setProject(normalizeProjectDetailResponse(response));
    } catch (error) {
      setProject(null);
      setFeedback(error?.message || '项目详情加载失败');
    } finally {
      setIsLoading(false);
    }
  }, [tenantKey, projectId]);

  useEffect(() => {
    loadProject();
  }, [loadProject]);

  const status = getProjectStatusMeta(project?.status);
  const brandCounts = useMemo(
    () => countProjectBrandsByRole(project?.brands),
    [project?.brands],
  );
  const navigationSource = readProjectNavigationSource(searchParams);
  const isFromTenantProjectOverview =
    hasPlatformAdminRole(user)
    && navigationSource === PROJECT_NAV_SOURCE_PLATFORM_TENANT_DETAIL;

  const goBack = () => {
    const path = isFromTenantProjectOverview
      ? buildPlatformTenantProjectOverviewPath(tenantKey)
      : buildProjectListPath({ tenantKey });
    if (path) navigate(path);
  };

  const openDataQuality = () => {
    const path = buildProjectDataQualityPath({
      tenantKey,
      projectId,
      source: isFromTenantProjectOverview ? navigationSource : '',
    });
    if (path) navigate(path);
  };

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border pb-4">
        <div className="min-w-0">
          <div className="mb-2 flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <FolderKanban className="size-3.5" aria-hidden="true" />
            <span>监测项目 / 项目详情</span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-medium tracking-normal text-foreground">
              {project?.name || projectId}
            </h1>
            {project ? <Badge variant={status.variant}>{status.label}</Badge> : null}
          </div>
          <p className="mt-1 max-w-2xl text-sm leading-relaxed text-muted-foreground">
            {project?.category || '未设置品类'} · {project?.industry || '未设置行业'} · {projectId}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button type="button" variant="outline" onClick={goBack}>
            <ArrowLeft data-icon="inline-start" />
            {isFromTenantProjectOverview ? '返回项目概览' : '返回项目工作台'}
          </Button>
          <Button type="button" variant="outline" onClick={openDataQuality}>
            <Gauge data-icon="inline-start" />
            数据质量
          </Button>
          <Button type="button" variant="outline" onClick={loadProject} disabled={isLoading}>
            <RefreshCw data-icon="inline-start" className={isLoading ? 'animate-spin' : ''} />
            刷新
          </Button>
        </div>
      </div>

      {feedback ? (
        <Alert variant="destructive">
          <AlertTitle>加载失败</AlertTitle>
          <AlertDescription>{feedback}</AlertDescription>
        </Alert>
      ) : null}

      {isLoading && !project ? (
        <div className="h-72 animate-pulse rounded-lg border border-border bg-muted/45" />
      ) : null}

      {!isLoading && !feedback && !project ? (
        <EmptyState
          icon={FolderKanban}
          title="项目不存在"
          description="当前租户下没有找到这个监测项目。"
        />
      ) : null}

      {project ? (
        <>
          <div className="grid gap-3 md:grid-cols-4">
            <Card size="sm">
              <CardHeader>
                <CardDescription>目标品牌</CardDescription>
                <CardTitle>{brandCounts.target}</CardTitle>
              </CardHeader>
            </Card>
            <Card size="sm">
              <CardHeader>
                <CardDescription>竞品品牌</CardDescription>
                <CardTitle>{brandCounts.competitor}</CardTitle>
              </CardHeader>
            </Card>
            <Card size="sm">
              <CardHeader>
                <CardDescription>问题集版本</CardDescription>
                <CardTitle>{project.prompt_sets.length}</CardTitle>
              </CardHeader>
            </Card>
            <Card size="sm">
              <CardHeader>
                <CardDescription>Project ID</CardDescription>
                <CardTitle className="truncate font-mono text-base">{project.project_id}</CardTitle>
              </CardHeader>
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Boxes className="size-4" aria-hidden="true" />
                  品牌配置
                </CardTitle>
                <CardDescription>目标品牌、竞品和观察品牌</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                {project.brands.length ? project.brands.map((brand) => (
                  <div
                    key={`${brand.role}-${brand.brand_id}`}
                    className="rounded-lg border border-border bg-muted/25 p-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="font-medium text-foreground">{brand.brand_name}</div>
                      <Badge variant={brand.role === 'target' ? 'default' : 'secondary'}>
                        {brand.role}
                      </Badge>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {(brand.aliases || []).map((alias) => (
                        <Badge key={alias} variant="outline">{alias}</Badge>
                      ))}
                    </div>
                  </div>
                )) : (
                  <EmptyState
                    icon={Boxes}
                    title="暂无品牌配置"
                    description="当前项目还没有品牌配置。"
                  />
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileQuestion className="size-4" aria-hidden="true" />
                  问题集
                </CardTitle>
                <CardDescription>项目内消费者问题版本</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-4">
                {project.prompt_sets.length ? project.prompt_sets.map((promptSet) => (
                  <div
                    key={promptSet.prompt_set_id}
                    className="rounded-lg border border-border bg-muted/25 p-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <div className="font-medium text-foreground">
                          {promptSet.name || promptSet.prompt_set_id}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          v{promptSet.version} · {promptSet.prompt_set_id}
                        </div>
                      </div>
                      <Badge variant={promptSet.status === 'active' ? 'default' : 'secondary'}>
                        {promptSet.status}
                      </Badge>
                    </div>
                    {promptSet.items.length ? (
                      <>
                        <Separator className="my-3" />
                        <div className="flex flex-col gap-2">
                          {promptSet.items.map((item) => (
                            <div
                              key={item.prompt_item_id}
                              className="rounded-md bg-background px-3 py-2 text-sm"
                            >
                              <div className="flex flex-wrap items-center gap-2">
                                <Badge variant="outline">{item.keyword}</Badge>
                                <span className="font-mono text-xs text-muted-foreground">
                                  {item.prompt_item_id}
                                </span>
                              </div>
                              <p className="mt-2 text-foreground">{item.query_content}</p>
                            </div>
                          ))}
                        </div>
                      </>
                    ) : null}
                  </div>
                )) : (
                  <EmptyState
                    icon={FileQuestion}
                    title="暂无问题集"
                    description="当前项目还没有问题集。"
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

export default React.memo(ProjectDetailPage);
