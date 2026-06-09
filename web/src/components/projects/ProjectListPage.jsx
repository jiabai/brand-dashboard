import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ArrowLeft, ArrowRight, FolderKanban, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { fetchProjects } from '@/api';
import { useAuth } from '@/auth/AuthContext.jsx';
import { hasPlatformAdminRole } from '@/auth/platformAccess.js';
import { useDashboardParams } from '@/hooks/useDashboardParams';
import EmptyState from '../EmptyState.jsx';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert.jsx';
import { Badge } from '../ui/badge.jsx';
import { Button } from '../ui/button.jsx';
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../ui/card.jsx';
import { buildPlatformTenantDetailPath } from '../platform/tenantPresentation.js';
import {
  buildProjectDetailPath,
  getProjectStatusMeta,
  normalizeProjectListResponse,
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

const ProjectListPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { tenantKey } = useDashboardParams();
  const [projects, setProjects] = useState([]);
  const [feedback, setFeedback] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const loadProjects = useCallback(async () => {
    if (!tenantKey) return;
    setIsLoading(true);
    setFeedback('');
    try {
      const response = await fetchProjects({ tenantKey });
      const normalized = normalizeProjectListResponse(response);
      setProjects(normalized.projects);
    } catch (error) {
      setFeedback(error?.message || '项目列表加载失败');
    } finally {
      setIsLoading(false);
    }
  }, [tenantKey]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const stats = useMemo(() => {
    const active = projects.filter((project) => project.status === 'active').length;
    const draft = projects.filter((project) => project.status === 'draft').length;
    return { total: projects.length, active, draft };
  }, [projects]);
  const isPlatformAdmin = hasPlatformAdminRole(user);
  const platformTenantDetailPath = buildPlatformTenantDetailPath(tenantKey);

  const openProject = (projectId) => {
    const path = buildProjectDetailPath({ tenantKey, projectId });
    if (path) navigate(path);
  };

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-4">
        <div className="min-w-0">
          <div className="mb-2 flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <FolderKanban className="size-3.5" aria-hidden="true" />
            <span>工作台 / 项目工作台</span>
          </div>
          <h1 className="text-2xl font-medium tracking-normal text-foreground">项目工作台</h1>
          <p className="mt-1 max-w-2xl text-sm leading-relaxed text-muted-foreground">
            查看这个租户的监测项目、目标品牌、竞品和消费者问题集配置。
          </p>
        </div>
        <div className="flex flex-wrap items-center justify-end gap-2">
          {isPlatformAdmin && platformTenantDetailPath ? (
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate(platformTenantDetailPath)}
            >
              <ArrowLeft data-icon="inline-start" />
              返回租户详情
            </Button>
          ) : null}
          <Button variant="outline" onClick={loadProjects} disabled={isLoading}>
            <RefreshCw data-icon="inline-start" className={isLoading ? 'animate-spin' : ''} />
            刷新
          </Button>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-border bg-card px-4 py-3 shadow-[var(--shadow-sm)]">
          <div className="text-xs text-muted-foreground">项目总数</div>
          <div className="mt-1 text-2xl font-medium text-foreground">{stats.total}</div>
        </div>
        <div className="rounded-lg border border-border bg-card px-4 py-3 shadow-[var(--shadow-sm)]">
          <div className="text-xs text-muted-foreground">运行中</div>
          <div className="mt-1 text-2xl font-medium text-foreground">{stats.active}</div>
        </div>
        <div className="rounded-lg border border-border bg-card px-4 py-3 shadow-[var(--shadow-sm)]">
          <div className="text-xs text-muted-foreground">配置中</div>
          <div className="mt-1 text-2xl font-medium text-foreground">{stats.draft}</div>
        </div>
      </div>

      {feedback ? (
        <Alert variant="destructive">
          <AlertTitle>加载失败</AlertTitle>
          <AlertDescription>{feedback}</AlertDescription>
        </Alert>
      ) : null}

      {isLoading && projects.length === 0 ? (
        <div className="grid gap-3">
          {[0, 1, 2].map((item) => (
            <div
              key={item}
              className="h-28 animate-pulse rounded-lg border border-border bg-muted/45"
            />
          ))}
        </div>
      ) : null}

      {!isLoading && !feedback && projects.length === 0 ? (
        <EmptyState
          icon={FolderKanban}
          title="暂无监测项目"
          description="当前租户还没有可查看的监测项目。"
        />
      ) : null}

      {projects.length ? (
        <div className="grid gap-3">
          {projects.map((project) => {
            const status = getProjectStatusMeta(project.status);
            return (
              <Card key={project.project_id} size="sm" className="transition-colors hover:border-primary/35">
                <CardHeader className="gap-2">
                  <div className="min-w-0">
                    <CardTitle className="truncate">{project.name || project.project_id}</CardTitle>
                    <CardDescription className="mt-1 flex flex-wrap gap-2">
                      <span>{project.category || '未设置品类'}</span>
                      <span>更新于 {formatDateTime(project.updated_at)}</span>
                    </CardDescription>
                  </div>
                  <CardAction className="flex items-center gap-2">
                    <Badge variant={status.variant}>{status.label}</Badge>
                    <Button
                      type="button"
                      size="sm"
                      onClick={() => openProject(project.project_id)}
                    >
                      打开
                      <ArrowRight data-icon="inline-end" />
                    </Button>
                  </CardAction>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-2 text-sm text-muted-foreground sm:grid-cols-3">
                    <div>
                      <span className="block text-xs text-muted-foreground">Project ID</span>
                      <span className="font-mono text-foreground">{project.project_id}</span>
                    </div>
                    <div>
                      <span className="block text-xs text-muted-foreground">行业</span>
                      <span className="text-foreground">{project.industry || '-'}</span>
                    </div>
                    <div>
                      <span className="block text-xs text-muted-foreground">租户</span>
                      <span className="font-mono text-foreground">{project.tenant_key}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : null}
    </div>
  );
};

export default React.memo(ProjectListPage);
