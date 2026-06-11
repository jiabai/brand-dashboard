import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  BarChart3,
  Building2,
  Check,
  Copy,
  FolderKanban,
  Gauge,
  ListChecks,
  MailPlus,
  RefreshCw,
  ShieldCheck,
  UserRound,
  Users,
} from 'lucide-react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';

import {
  fetchPlatformTenantDetail,
  fetchPlatformTenantMembers,
  resendPlatformTenantActivation,
  updatePlatformTenantMember,
} from '../../api/platform.js';
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
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select.jsx';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from '../ui/sheet.jsx';
import { Spinner } from '../ui/spinner.jsx';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table.jsx';
import { Textarea } from '../ui/textarea.jsx';
import {
  PROJECT_NAV_SOURCE_PLATFORM_TENANT_DETAIL,
  buildProjectDataQualityPath,
  buildProjectDetailPath,
  buildProjectListPath,
  getProjectStatusMeta,
} from '../projects/projectPresentation.js';
import { formatDateTime } from './executorHealthPresentation.js';
import {
  buildTenantDashboardPath,
  buildTenantTaskStatusPath,
  formatDate,
  getAdminStatusLabel,
  getBillingCycleLabel,
  getEmailDeliveryMeta,
  getPlanTypeLabel,
  getQueryJobStatusMeta,
  getTenantStatusMeta,
  normalizeTenantDetailResponse,
} from './tenantPresentation.js';

const formatCount = (value) => Number(value || 0).toLocaleString('zh-CN');

const DetailField = ({ label, value }) => (
  <div className="grid gap-1">
    <span className="text-xs text-muted-foreground">{label}</span>
    <span className="break-words text-sm font-medium text-foreground">{value || '未设置'}</span>
  </div>
);

const PlatformTenantDetailPage = () => {
  const { tenantKey = '' } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const projectOverviewRef = useRef(null);
  const tenantAdminRef = useRef(null);
  const [tenant, setTenant] = useState(null);
  const [projects, setProjects] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshToken, setRefreshToken] = useState(0);
  const [memberSheetOpen, setMemberSheetOpen] = useState(false);
  const [members, setMembers] = useState([]);
  const [isLoadingMembers, setIsLoadingMembers] = useState(false);
  const [membersError, setMembersError] = useState('');
  const [selectedMemberId, setSelectedMemberId] = useState('');
  const [reason, setReason] = useState('');
  const [isSubmittingMember, setIsSubmittingMember] = useState(false);
  const [memberActionError, setMemberActionError] = useState('');
  const [memberActionMessage, setMemberActionMessage] = useState('');
  const [isResendingActivation, setIsResendingActivation] = useState(false);
  const [resendError, setResendError] = useState('');
  const [resendResult, setResendResult] = useState(null);
  const [copiedActivation, setCopiedActivation] = useState(false);

  const loadTenant = useCallback(
    async (signal) => {
      if (!tenantKey) return;
      setIsLoading(true);
      setError('');
      try {
        const response = await fetchPlatformTenantDetail(tenantKey, { signal });
        const normalized = normalizeTenantDetailResponse(response);
        setTenant(normalized.tenant);
        setProjects(normalized.projects);
      } catch (loadError) {
        if (loadError.name !== 'AbortError') {
          setTenant(null);
          setProjects([]);
          setError(loadError.message || '租户详情加载失败');
        }
      } finally {
        if (!signal?.aborted) setIsLoading(false);
      }
    },
    [tenantKey],
  );

  useEffect(() => {
    const controller = new AbortController();
    loadTenant(controller.signal);
    return () => controller.abort();
  }, [loadTenant, refreshToken]);

  const loadTenantMembers = useCallback(
    async (signal) => {
      if (!tenantKey) return;
      setIsLoadingMembers(true);
      setMembersError('');
      try {
        const response = await fetchPlatformTenantMembers(tenantKey, { signal });
        const nextMembers = Array.isArray(response?.data?.members) ? response.data.members : [];
        setMembers(nextMembers);
        setSelectedMemberId((current) => {
          const hasCurrentActiveMember = nextMembers.some(
            (member) =>
              String(member.userId) === current &&
              member.status === 'active' &&
              member.userStatus === 'active',
          );
          if (hasCurrentActiveMember) return current;
          const firstActiveMember = nextMembers.find(
            (member) => member.status === 'active' && member.userStatus === 'active',
          );
          return firstActiveMember ? String(firstActiveMember.userId) : '';
        });
      } catch (loadError) {
        if (loadError.name !== 'AbortError') {
          setMembers([]);
          setSelectedMemberId('');
          setMembersError(loadError.message || '成员列表加载失败');
        }
      } finally {
        if (!signal?.aborted) setIsLoadingMembers(false);
      }
    },
    [tenantKey],
  );

  useEffect(() => {
    if (!memberSheetOpen) return undefined;
    const controller = new AbortController();
    loadTenantMembers(controller.signal);
    return () => controller.abort();
  }, [loadTenantMembers, memberSheetOpen]);

  useEffect(() => {
    if (!tenant) return undefined;
    const target =
      location.hash === '#project-overview'
        ? projectOverviewRef.current
        : location.hash === '#tenant-admin'
          ? tenantAdminRef.current
          : null;
    if (!target) return undefined;
    const frameId = window.requestAnimationFrame(() => {
      target.scrollIntoView({ block: 'start' });
    });
    return () => window.cancelAnimationFrame(frameId);
  }, [location.hash, tenant]);

  const status = getTenantStatusMeta(tenant?.status);
  const latestJob = tenant?.latestJob;
  const latestJobStatus = getQueryJobStatusMeta(latestJob?.queryStatus);
  const dashboardPath = buildTenantDashboardPath(tenant);
  const taskStatusPath = buildTenantTaskStatusPath(tenant?.tenantKey || tenantKey);
  const projectWorkspacePath = buildProjectListPath({ tenantKey: tenant?.tenantKey || tenantKey });
  const canOpenTenantTools = tenant?.status === 'active';

  const projectStats = useMemo(() => {
    const active = projects.filter((project) => project.status === 'active').length;
    const draft = projects.filter((project) => project.status === 'draft').length;
    return { total: projects.length, active, draft };
  }, [projects]);

  const summaryCards = [
    {
      key: 'status',
      label: '租户状态',
      value: status.label,
      icon: ShieldCheck,
      badge: status,
    },
    {
      key: 'members',
      label: '成员',
      value: `${formatCount(tenant?.memberCount)} / ${tenant?.maxUsers || '不限'}`,
      icon: Users,
    },
    {
      key: 'projects',
      label: '项目数',
      value: formatCount(projectStats.total),
      icon: FolderKanban,
    },
    {
      key: 'jobs',
      label: '任务',
      value: `${formatCount(tenant?.activeJobCount)} 生效 / ${formatCount(tenant?.jobCount)} 总计`,
      icon: ListChecks,
    },
  ];

  const activeMembers = useMemo(
    () => members.filter((member) => member.status === 'active' && member.userStatus === 'active'),
    [members],
  );
  const selectedMember = useMemo(
    () => activeMembers.find((member) => String(member.userId) === selectedMemberId),
    [activeMembers, selectedMemberId],
  );
  const adminActionLabel = tenant?.adminEmail || tenant?.adminName ? '应急设置' : '设置管理员';
  const canSubmitMemberUpdate = Boolean(selectedMemberId && reason.trim()) && !isSubmittingMember;

  const handleOpenMemberSheet = () => {
    setMemberActionError('');
    setMemberActionMessage('');
    setReason('');
    setMemberSheetOpen(true);
  };

  const handleSubmitMemberUpdate = async (event) => {
    event.preventDefault();
    const normalizedReason = reason.trim();
    if (!selectedMemberId || !normalizedReason) {
      setMemberActionError('请选择成员并填写应急原因');
      return;
    }

    setIsSubmittingMember(true);
    setMemberActionError('');
    setMemberActionMessage('');
    try {
      const response = await updatePlatformTenantMember(
        tenant?.tenantKey || tenantKey,
        selectedMemberId,
        {
          role: 'admin',
          status: 'active',
          reason: normalizedReason,
        },
      );
      const updatedMember = response?.data?.member;
      if (updatedMember?.userId) {
        setMembers((current) =>
          current.map((member) => (member.userId === updatedMember.userId ? updatedMember : member)),
        );
      }
      setMemberActionMessage(
        `${selectedMember?.email || '选中成员'} 已设置为租户管理员`,
      );
      setReason('');
      setRefreshToken((current) => current + 1);
    } catch (submitError) {
      setMemberActionError(submitError.message || '租户管理员设置失败');
    } finally {
      setIsSubmittingMember(false);
    }
  };

  const resendDeliveryMeta = resendResult
    ? getEmailDeliveryMeta(resendResult.emailDelivery)
    : null;

  const handleResendActivation = async () => {
    setIsResendingActivation(true);
    setResendError('');
    try {
      const response = await resendPlatformTenantActivation(tenantKey);
      setResendResult(response?.data || response || null);
    } catch (submitError) {
      setResendResult(null);
      setResendError(submitError.message || '激活邮件重发失败');
    } finally {
      setIsResendingActivation(false);
    }
  };

  const handleCopyActivationUrl = async () => {
    if (!navigator?.clipboard || !resendResult?.activationUrl) return;
    await navigator.clipboard.writeText(resendResult.activationUrl);
    setCopiedActivation(true);
    window.setTimeout(() => setCopiedActivation(false), 1600);
  };

  return (
    <div className="grid gap-5">
      <section className="flex flex-col gap-4 border-b border-border pb-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="mb-2 flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <Building2 className="size-3.5" aria-hidden="true" />
            <span>平台后台 / 租户详情</span>
          </div>
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <h1 className="truncate text-2xl font-medium text-foreground">
              {tenant?.tenantName || tenantKey}
            </h1>
            {tenant ? <Badge variant={status.variant} className="rounded-md">{status.label}</Badge> : null}
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <span className="font-mono">{tenant?.tenantKey || tenantKey}</span>
            {tenant?.companyLegalName ? (
              <>
                <span className="text-border">/</span>
                <span>{tenant.companyLegalName}</span>
              </>
            ) : null}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button type="button" variant="outline" onClick={() => navigate('/platform/tenants')}>
            <ArrowLeft className="size-4" />
            返回列表
          </Button>
          <Button
            type="button"
            disabled={!canOpenTenantTools || !projectWorkspacePath}
            onClick={() => navigate(projectWorkspacePath)}
          >
            <FolderKanban className="size-4" />
            进入项目工作台
            <ArrowRight className="size-4" />
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => setRefreshToken((current) => current + 1)}
            disabled={isLoading}
          >
            <RefreshCw className={isLoading ? 'size-4 animate-spin' : 'size-4'} />
            刷新
          </Button>
        </div>
      </section>

      {error ? (
        <Alert variant="destructive">
          <AlertTitle>租户详情加载失败</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {isLoading && !tenant ? (
        <div className="h-72 animate-pulse rounded-md border border-border bg-muted/45" />
      ) : null}

      {!isLoading && !error && !tenant ? (
        <EmptyState
          icon={Building2}
          title="租户不存在"
          description="没有找到这个平台租户。"
        />
      ) : null}

      {tenant ? (
        <>
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {summaryCards.map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.key} className="rounded-md border border-border bg-card p-3">
                  <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
                    <span>{item.label}</span>
                    <Icon className="size-4" />
                  </div>
                  <div className="mt-3 flex items-center gap-2 text-2xl font-medium text-foreground">
                    <span>{item.value}</span>
                    {item.badge ? (
                      <Badge variant={item.badge.variant} className="rounded-md text-xs">
                        {item.badge.label}
                      </Badge>
                    ) : null}
                  </div>
                </div>
              );
            })}
          </section>

          <section className="grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="size-4" aria-hidden="true" />
                  排障入口
                </CardTitle>
                <CardDescription>
                  {latestJob ? `${latestJob.jobId} / ${latestJob.brand || '未设置品牌'}` : '暂无最近任务'}
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3">
                {latestJob ? (
                  <div className="grid gap-2 rounded-md border border-border bg-muted/25 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="font-mono text-sm text-foreground">{latestJob.jobId}</span>
                      <Badge variant={latestJobStatus.variant} className="rounded-md">
                        {latestJobStatus.label}
                      </Badge>
                    </div>
                    <div className="grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
                      <DetailField label="品牌" value={latestJob.brand} />
                      <DetailField label="品类" value={latestJob.category} />
                      <DetailField label="生效开始" value={formatDateTime(latestJob.effectiveFrom)} />
                      <DetailField label="创建时间" value={formatDateTime(latestJob.createdAt)} />
                    </div>
                  </div>
                ) : (
                  <EmptyState
                    icon={ListChecks}
                    title="暂无最近任务"
                    description="当前租户还没有可直达的最新任务看板。"
                  />
                )}
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    disabled={!canOpenTenantTools || !dashboardPath}
                    onClick={() => navigate(dashboardPath)}
                  >
                    <BarChart3 className="size-4" />
                    最新任务看板
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    disabled={!canOpenTenantTools}
                    onClick={() => navigate(taskStatusPath)}
                  >
                    <ListChecks className="size-4" />
                    任务状态
                  </Button>
                </div>
              </CardContent>
            </Card>

            <div className="grid gap-4">
              <div id="tenant-admin" ref={tenantAdminRef}>
                <Card>
                  <CardHeader className="gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div className="grid gap-1">
                      <CardTitle className="flex items-center gap-2">
                        <UserRound className="size-4" aria-hidden="true" />
                        租户管理员
                      </CardTitle>
                      <CardDescription>平台只读查看，用于客户识别、联络和排障交接。</CardDescription>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      {tenant.adminStatus === 'pending_activation' ? (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          disabled={isResendingActivation}
                          onClick={handleResendActivation}
                        >
                          <MailPlus className="size-3.5" />
                          {isResendingActivation ? '重发中...' : '重发激活邮件'}
                        </Button>
                      ) : null}
                      <Button
                        type="button"
                        size="sm"
                        disabled={!canOpenTenantTools}
                        onClick={handleOpenMemberSheet}
                      >
                        <ShieldCheck className="size-3.5" />
                        {adminActionLabel}
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="grid gap-4 sm:grid-cols-2">
                    <DetailField label="管理员姓名" value={tenant.adminName} />
                    <DetailField label="管理员邮箱" value={tenant.adminEmail} />
                    <DetailField label="管理员手机号" value={tenant.adminPhone} />
                    <DetailField label="管理员状态" value={getAdminStatusLabel(tenant.adminStatus)} />
                    {resendError ? (
                      <Alert variant="destructive" className="sm:col-span-2">
                        <AlertTitle>激活邮件重发失败</AlertTitle>
                        <AlertDescription>{resendError}</AlertDescription>
                      </Alert>
                    ) : null}
                    {resendResult ? (
                      <div className="grid gap-3 sm:col-span-2">
                        {resendDeliveryMeta ? (
                          <Alert variant={resendDeliveryMeta.variant}>
                            <AlertTitle>{resendDeliveryMeta.title}</AlertTitle>
                            <AlertDescription>{resendDeliveryMeta.description}</AlertDescription>
                          </Alert>
                        ) : null}
                        <div className="grid gap-1">
                          <span className="text-xs font-medium text-muted-foreground">新激活链接</span>
                          <div className="flex min-w-0 items-center gap-2">
                            <code className="min-w-0 flex-1 truncate text-xs text-foreground">
                              {resendResult.activationUrl || '未返回'}
                            </code>
                            {resendResult.activationUrl ? (
                              <Button
                                type="button"
                                variant="outline"
                                size="icon-sm"
                                onClick={handleCopyActivationUrl}
                                title="复制激活链接"
                              >
                                {copiedActivation ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
                              </Button>
                            ) : null}
                          </div>
                        </div>
                      </div>
                    ) : null}
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Building2 className="size-4" aria-hidden="true" />
                    客户资料
                  </CardTitle>
                  <CardDescription>{getPlanTypeLabel(tenant.planType)} / {getBillingCycleLabel(tenant.billingCycle)}</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-4 sm:grid-cols-2">
                  <DetailField label="行业" value={tenant.industry} />
                  <DetailField label="合同开始" value={formatDate(tenant.contractStartDate)} />
                  <DetailField label="合同到期" value={formatDate(tenant.contractEndDate)} />
                  <DetailField label="创建时间" value={formatDateTime(tenant.createdAt)} />
                </CardContent>
              </Card>
            </div>
          </section>

          <div id="project-overview" ref={projectOverviewRef}>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FolderKanban className="size-4" aria-hidden="true" />
                  项目概览
                </CardTitle>
                <CardDescription>
                  只读摘要，{projectStats.active} 个运行中，{projectStats.draft} 个配置中
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table className="min-w-[900px]">
                <TableHeader>
                  <TableRow>
                    <TableHead>项目</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead>行业</TableHead>
                    <TableHead>品类</TableHead>
                    <TableHead>更新时间</TableHead>
                    <TableHead className="text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {projects.length ? (
                    projects.map((project) => {
                      const projectStatus = getProjectStatusMeta(project.status);
                      const projectPath = buildProjectDetailPath({
                        tenantKey: tenant?.tenantKey || tenantKey,
                        projectId: project.project_id,
                        source: PROJECT_NAV_SOURCE_PLATFORM_TENANT_DETAIL,
                      });
                      const qualityPath = buildProjectDataQualityPath({
                        tenantKey: tenant?.tenantKey || tenantKey,
                        projectId: project.project_id,
                        source: PROJECT_NAV_SOURCE_PLATFORM_TENANT_DETAIL,
                      });
                      return (
                        <TableRow key={project.project_id}>
                          <TableCell>
                            <div className="grid gap-1">
                              <span className="font-medium text-foreground">
                                {project.name || project.project_id}
                              </span>
                              <span className="font-mono text-xs text-muted-foreground">
                                {project.project_id}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant={projectStatus.variant} className="rounded-md">
                              {projectStatus.label}
                            </Badge>
                          </TableCell>
                          <TableCell>{project.industry || '-'}</TableCell>
                          <TableCell>{project.category || '-'}</TableCell>
                          <TableCell>{formatDateTime(project.updated_at)}</TableCell>
                          <TableCell>
                            <div className="flex flex-wrap justify-end gap-2">
                              <Button
                                type="button"
                                size="sm"
                                variant="outline"
                                disabled={!canOpenTenantTools || !projectPath}
                                onClick={() => navigate(projectPath)}
                              >
                                <FolderKanban className="size-3.5" />
                                打开项目
                              </Button>
                              <Button
                                type="button"
                                size="sm"
                                variant="ghost"
                                disabled={!canOpenTenantTools || !qualityPath}
                                onClick={() => navigate(qualityPath)}
                              >
                                <Gauge className="size-3.5" />
                                数据质量
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })
                  ) : (
                    <TableRow>
                      <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                        暂无监测项目
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </>
      ) : null}

      <Sheet open={memberSheetOpen} onOpenChange={setMemberSheetOpen}>
        <SheetContent className="w-full sm:max-w-md">
          <SheetHeader>
            <SheetTitle>设置租户管理员</SheetTitle>
            <SheetDescription>
              {tenant?.tenantName || tenantKey} / {tenant?.tenantKey || tenantKey}
            </SheetDescription>
          </SheetHeader>
          <form className="flex min-h-0 flex-1 flex-col" onSubmit={handleSubmitMemberUpdate}>
            <div className="grid flex-1 content-start gap-4 overflow-y-auto px-4">
              {membersError ? (
                <Alert variant="destructive">
                  <AlertTitle>成员列表加载失败</AlertTitle>
                  <AlertDescription>{membersError}</AlertDescription>
                </Alert>
              ) : null}
              {memberActionError ? (
                <Alert variant="destructive">
                  <AlertTitle>设置失败</AlertTitle>
                  <AlertDescription>{memberActionError}</AlertDescription>
                </Alert>
              ) : null}
              {memberActionMessage ? (
                <Alert>
                  <AlertTitle>设置成功</AlertTitle>
                  <AlertDescription>{memberActionMessage}</AlertDescription>
                </Alert>
              ) : null}

              <label className="grid gap-1.5">
                <span className="text-xs font-medium text-muted-foreground">成员</span>
                {isLoadingMembers ? (
                  <div className="flex h-10 items-center gap-2 rounded-md border border-border bg-muted/35 px-3 text-sm text-muted-foreground">
                    <Spinner />
                    正在加载成员
                  </div>
                ) : activeMembers.length ? (
                  <Select value={selectedMemberId || undefined} onValueChange={setSelectedMemberId}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="选择成员" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        {activeMembers.map((member) => (
                          <SelectItem key={member.userId} value={String(member.userId)}>
                            {member.email}
                          </SelectItem>
                        ))}
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                ) : (
                  <div className="rounded-md border border-dashed border-border bg-muted/25 p-3 text-sm text-muted-foreground">
                    暂无可设置的 active 成员
                  </div>
                )}
              </label>

              {selectedMember ? (
                <div className="grid gap-2 rounded-md border border-border bg-muted/25 p-3 text-sm">
                  <div className="font-medium text-foreground">{selectedMember.email}</div>
                  <div className="grid gap-1 text-muted-foreground">
                    <span>当前角色：{selectedMember.role}</span>
                    <span>成员状态：{selectedMember.status}</span>
                  </div>
                </div>
              ) : null}

              <label className="grid gap-1.5">
                <span className="text-xs font-medium text-muted-foreground">应急原因</span>
                <Textarea
                  value={reason}
                  onChange={(event) => setReason(event.target.value)}
                  rows={4}
                  placeholder="填写客户支持工单、授权来源或处理背景"
                  required
                />
              </label>
            </div>
            <SheetFooter className="border-t border-border">
              <Button type="button" variant="outline" onClick={() => setMemberSheetOpen(false)}>
                取消
              </Button>
              <Button type="submit" disabled={!canSubmitMemberUpdate}>
                {isSubmittingMember ? <Spinner /> : <ShieldCheck className="size-4" />}
                设置管理员
              </Button>
            </SheetFooter>
          </form>
        </SheetContent>
      </Sheet>
    </div>
  );
};

export default PlatformTenantDetailPage;
