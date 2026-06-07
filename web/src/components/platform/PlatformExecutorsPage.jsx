import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Activity, AlertTriangle, Clock, ListTree, RefreshCw, ServerCog } from 'lucide-react';

import { fetchPlatformCollectionHealth } from '../../api/platform.js';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert.jsx';
import { Badge } from '../ui/badge.jsx';
import { Button } from '../ui/button.jsx';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table.jsx';
import {
  formatCount,
  formatDateTime,
  getExecutorHealthMeta,
  normalizeCollectionHealthResponse,
} from './executorHealthPresentation.js';

const summaryItems = [
  { key: 'executorCount', label: '执行器', icon: ServerCog },
  { key: 'pendingTaskCount', label: '待领取', icon: ListTree },
  { key: 'runningTaskCount', label: '运行中', icon: Activity },
  { key: 'failedTaskCount', label: '失败任务', icon: AlertTriangle },
  { key: 'retryableFailedTaskCount', label: '可重试', icon: RefreshCw },
  { key: 'expiredLeaseTaskCount', label: '租约过期', icon: Clock },
];

const PlatformExecutorsPage = () => {
  const [health, setHealth] = useState(() => normalizeCollectionHealthResponse({}));
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshToken, setRefreshToken] = useState(0);

  const loadHealth = useCallback(async (signal) => {
    setIsLoading(true);
    setError('');
    try {
      const response = await fetchPlatformCollectionHealth({ failedTaskLimit: 20 }, { signal });
      setHealth(normalizeCollectionHealthResponse(response));
    } catch (loadError) {
      if (loadError.name !== 'AbortError') {
        setError(loadError.message || '采集健康度加载失败');
      }
    } finally {
      if (!signal?.aborted) setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    loadHealth(controller.signal);
    return () => controller.abort();
  }, [loadHealth, refreshToken]);

  const summary = health.summary;
  const orderedQueues = useMemo(
    () =>
      [...health.queues].sort(
        (a, b) =>
          (b.failedTaskCount || 0) - (a.failedTaskCount || 0) ||
          (b.pendingTaskCount || 0) - (a.pendingTaskCount || 0),
      ),
    [health.queues],
  );

  return (
    <div className="grid gap-5">
      <section className="flex flex-col gap-4 border-b border-border pb-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0">
          <h1 className="text-2xl font-medium text-foreground">执行器健康</h1>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <span>{formatCount(summary.activeExecutorCount)} 个启用</span>
            <span className="text-border">/</span>
            <span>{formatCount(summary.inactiveExecutorCount)} 个停用</span>
          </div>
        </div>
        <Button
          type="button"
          variant="outline"
          onClick={() => setRefreshToken((current) => current + 1)}
          disabled={isLoading}
        >
          <RefreshCw className="size-4" />
          刷新
        </Button>
      </section>

      {error ? (
        <Alert variant="destructive">
          <AlertTitle>采集健康度加载失败</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
        {summaryItems.map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.key} className="rounded-md border border-border bg-card p-3">
              <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
                <span>{item.label}</span>
                <Icon className="size-4" />
              </div>
              <div className="mt-3 text-2xl font-medium text-foreground">
                {formatCount(summary[item.key])}
              </div>
            </div>
          );
        })}
      </section>

      <section className="grid gap-3">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-medium text-foreground">执行器</h2>
          <Badge variant="secondary" className="rounded-md">
            {formatCount(health.executors.length)}
          </Badge>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>执行器</TableHead>
              <TableHead>健康</TableHead>
              <TableHead>活跃租约</TableHead>
              <TableHead>运行 Attempt</TableHead>
              <TableHead>失败 Attempt</TableHead>
              <TableHead>最近 Attempt</TableHead>
              <TableHead>更新时间</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                  正在加载执行器...
                </TableCell>
              </TableRow>
            ) : health.executors.length ? (
              health.executors.map((executor) => {
                const meta = getExecutorHealthMeta(executor.healthStatus);
                return (
                  <TableRow key={executor.executorId}>
                    <TableCell>
                      <div className="grid gap-1">
                        <span className="font-medium text-foreground">{executor.name || executor.executorId}</span>
                        <span className="font-mono text-xs text-muted-foreground">{executor.executorId}</span>
                        <span className="text-xs text-muted-foreground">{executor.ipAddress || '未记录 IP'}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={meta.variant} className="rounded-md">{meta.label}</Badge>
                    </TableCell>
                    <TableCell>{formatCount(executor.activeLeaseCount)}</TableCell>
                    <TableCell>{formatCount(executor.runningAttemptCount)}</TableCell>
                    <TableCell>{formatCount(executor.failedAttemptCount)}</TableCell>
                    <TableCell>{formatDateTime(executor.latestAttemptAt)}</TableCell>
                    <TableCell>{formatDateTime(executor.updatedAt)}</TableCell>
                  </TableRow>
                );
              })
            ) : (
              <TableRow>
                <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                  暂无执行器
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </section>

      <section className="grid gap-3">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-medium text-foreground">队列</h2>
          <Badge variant="secondary" className="rounded-md">
            {formatCount(orderedQueues.length)}
          </Badge>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>租户 / 项目</TableHead>
              <TableHead>批次</TableHead>
              <TableHead>待领取</TableHead>
              <TableHead>已预约</TableHead>
              <TableHead>运行中</TableHead>
              <TableHead>成功</TableHead>
              <TableHead>失败</TableHead>
              <TableHead>租约过期</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={8} className="h-24 text-center text-muted-foreground">
                  正在加载队列...
                </TableCell>
              </TableRow>
            ) : orderedQueues.length ? (
              orderedQueues.map((queue) => (
                <TableRow key={`${queue.tenantKey}:${queue.collectionJobId}`}>
                  <TableCell>
                    <div className="grid gap-1">
                      <span className="font-medium text-foreground">{queue.tenantName || queue.tenantKey}</span>
                      <span className="text-xs text-muted-foreground">
                        {[queue.projectName, queue.projectId].filter(Boolean).join(' / ') || '未绑定项目'}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="grid gap-1">
                      <span className="font-mono text-xs text-foreground">{queue.collectionJobId}</span>
                      <span className="text-xs text-muted-foreground">{queue.collectionJobStatus || '未知'}</span>
                    </div>
                  </TableCell>
                  <TableCell>{formatCount(queue.pendingTaskCount)}</TableCell>
                  <TableCell>{formatCount(queue.reservedTaskCount)}</TableCell>
                  <TableCell>{formatCount(queue.runningTaskCount)}</TableCell>
                  <TableCell>{formatCount(queue.succeededTaskCount)}</TableCell>
                  <TableCell>{formatCount(queue.failedTaskCount)}</TableCell>
                  <TableCell>{formatCount(queue.expiredLeaseTaskCount)}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={8} className="h-24 text-center text-muted-foreground">
                  暂无采集队列
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </section>

      <section className="grid gap-3">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-medium text-foreground">失败任务</h2>
          <Badge variant="destructive" className="rounded-md">
            {formatCount(health.failedTasks.length)}
          </Badge>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>任务</TableHead>
              <TableHead>租户 / 项目</TableHead>
              <TableHead>平台</TableHead>
              <TableHead>尝试</TableHead>
              <TableHead>错误</TableHead>
              <TableHead>更新时间</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                  正在加载失败任务...
                </TableCell>
              </TableRow>
            ) : health.failedTasks.length ? (
              health.failedTasks.map((task) => (
                <TableRow key={`${task.tenantKey}:${task.collectionTaskId}`}>
                  <TableCell>
                    <div className="grid max-w-80 gap-1">
                      <span className="font-mono text-xs text-foreground">{task.collectionTaskId}</span>
                      <span className="truncate text-xs text-muted-foreground" title={task.queryContent}>
                        {task.queryContent || '未记录问题'}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="grid gap-1">
                      <span>{task.tenantName || task.tenantKey}</span>
                      <span className="text-xs text-muted-foreground">{task.projectName || task.projectId}</span>
                    </div>
                  </TableCell>
                  <TableCell>{task.platform || '未记录'}</TableCell>
                  <TableCell>
                    {formatCount(task.attemptCount)} / {formatCount(task.maxAttempts)}
                  </TableCell>
                  <TableCell>
                    <div className="grid max-w-80 gap-1">
                      <span className="text-sm text-foreground">{task.lastErrorCode || 'unknown'}</span>
                      <span className="truncate text-xs text-muted-foreground" title={task.lastErrorMessage}>
                        {task.lastErrorMessage || '未记录错误信息'}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>{formatDateTime(task.updatedAt)}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                  暂无失败任务
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </section>
    </div>
  );
};

export default PlatformExecutorsPage;
