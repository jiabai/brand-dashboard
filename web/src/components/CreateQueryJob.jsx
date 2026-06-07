import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { MinusCircle, Plus, Sparkles, Upload } from 'lucide-react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import dayjs from 'dayjs';

import { CONFIG } from '../config';
import { fetchProjects, loadQueryJob } from '@/api';
import { useDashboardParams } from '@/hooks/useDashboardParams';
import {
  LEGACY_PROJECT_VALUE,
  createInitialQueryJobForm,
  normalizeProjectOptions,
  validateQueryJobForm,
} from './query-jobs/queryJobForm.js';
import { buildRouteSearch, buildViewPath } from '@/utils/routing';

import SubmissionSuccess from './SubmissionSuccess';
import { Alert, AlertDescription, AlertTitle } from './ui/alert.jsx';
import { Button } from './ui/button.jsx';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card.jsx';
import { Input } from './ui/input.jsx';
import { Separator } from './ui/separator.jsx';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select.jsx';
import { Textarea } from './ui/textarea.jsx';

const Field = ({ label, required = false, children, error }) => (
  <label className="block space-y-1.5">
    <span className="text-sm font-medium text-foreground">
      {label}
      {required ? <span className="text-destructive"> *</span> : null}
    </span>
    {children}
    {error ? <span className="block text-xs text-destructive">{error}</span> : null}
  </label>
);

const SectionTitle = ({ children }) => (
  <div className="flex items-center gap-3 py-2">
    <Separator className="flex-1" />
    <span className="text-sm font-medium text-muted-foreground">{children}</span>
    <Separator className="flex-1" />
  </div>
);

const CreateQueryJob = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { tenantKey, jobId } = useDashboardParams();
  const navigate = useNavigate();
  const location = useLocation();
  const executorId = searchParams.get('executor_id') || CONFIG.DEFAULT_EXECUTOR_ID;
  const [loading, setLoading] = useState(false);
  const [isLoadingProjects, setIsLoadingProjects] = useState(false);
  const [result, setResult] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [projectFeedback, setProjectFeedback] = useState('');
  const [projectOptions, setProjectOptions] = useState([]);
  const [formValues, setFormValues] = useState(() =>
    createInitialQueryJobForm({ tenantKey, executorId }),
  );

  useEffect(() => {
    setFormValues((current) => ({
      ...current,
      tenant_key: tenantKey || '',
      executor_id: executorId || '',
    }));
  }, [executorId, tenantKey]);

  useEffect(() => {
    if (!tenantKey) {
      setProjectOptions([]);
      return undefined;
    }

    const controller = new AbortController();
    setIsLoadingProjects(true);
    setProjectFeedback('');

    fetchProjects({ tenantKey }, { signal: controller.signal })
      .then((response) => {
        setProjectOptions(normalizeProjectOptions(response));
      })
      .catch((error) => {
        if (controller.signal.aborted) return;
        setProjectOptions([]);
        setProjectFeedback(error?.message || '项目列表加载失败');
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoadingProjects(false);
      });

    return () => {
      controller.abort();
    };
  }, [tenantKey]);

  const handleNavigate = useCallback(
    (viewKey) => {
      const pathname = buildViewPath(viewKey, { tenantKey, jobId });
      const search = buildRouteSearch({
        search: location.search,
        nextViewKey: viewKey,
      });
      navigate(`${pathname}${search}`);
    },
    [jobId, location.search, navigate, tenantKey],
  );

  useEffect(() => {
    if (searchParams.get('executor_id')) return;
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('executor_id', executorId);
      return next;
    }, { replace: true });
  }, [executorId, searchParams, setSearchParams]);

  const setField = (field, value) => {
    setFormValues((current) => ({ ...current, [field]: value }));
  };

  const setDataField = (field, value) => {
    setFormValues((current) => ({
      ...current,
      data: {
        ...current.data,
        [field]: value,
      },
    }));
  };

  const setCompetitor = (index, value) => {
    setFormValues((current) => ({
      ...current,
      data: {
        ...current.data,
        competitor: current.data.competitor.map((item, itemIndex) => (itemIndex === index ? value : item)),
      },
    }));
  };

  const addCompetitor = () => {
    setFormValues((current) => ({
      ...current,
      data: {
        ...current.data,
        competitor: [...current.data.competitor, ''],
      },
    }));
  };

  const removeCompetitor = (index) => {
    setFormValues((current) => ({
      ...current,
      data: {
        ...current.data,
        competitor: current.data.competitor.filter((_, itemIndex) => itemIndex !== index),
      },
    }));
  };

  const updateContent = (index, updater) => {
    setFormValues((current) => ({
      ...current,
      data: {
        ...current.data,
        content: current.data.content.map((item, itemIndex) =>
          itemIndex === index ? updater(item) : item,
        ),
      },
    }));
  };

  const addContent = () => {
    setFormValues((current) => ({
      ...current,
      data: {
        ...current.data,
        content: [...current.data.content, { keyword: '', query_content: [''] }],
      },
    }));
  };

  const removeContent = (index) => {
    setFormValues((current) => ({
      ...current,
      data: {
        ...current.data,
        content: current.data.content.filter((_, itemIndex) => itemIndex !== index),
      },
    }));
  };

  const generateRandomIds = useCallback(() => {
    const randomHex = (len) => {
      if (globalThis.crypto?.getRandomValues) {
        const bytes = new Uint8Array(Math.ceil(len / 2));
        globalThis.crypto.getRandomValues(bytes);
        return Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('').slice(0, len);
      }

      return Date.now().toString(16).padEnd(len, '0').slice(0, len);
    };
    const today = dayjs().format('YYYYMMDD_HHmmss');

    setFormValues((current) => ({
      ...current,
      job_id: `job_${today}_${randomHex(8)}`,
    }));
  }, []);

  const onSubmit = async (event) => {
    event.preventDefault();
    setFeedback(null);
    setResult(null);

    const { errors, payload } = validateQueryJobForm(formValues);
    if (errors.length) {
      setFeedback({
        type: 'error',
        title: '请先修正表单',
        message: errors.join('；'),
      });
      return;
    }

    setLoading(true);
    try {
      let data;
      try {
        data = await loadQueryJob(payload);
      } catch (err) {
        data = { success: false, message: err.message };
      }

      if (data.success) {
        setFeedback({ type: 'success', title: '任务加载成功', message: data.message || '任务加载成功' });
        setResult({ ...data, job_id: payload.job_id });
        setFormValues(createInitialQueryJobForm({
          tenantKey,
          executorId,
          projectId: formValues.project_id,
        }));
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else {
        let errorMessage = data.message || '任务加载失败';
        if (data.detail) {
          if (typeof data.detail === 'string') {
            errorMessage = data.detail;
          } else if (Array.isArray(data.detail)) {
            errorMessage = data.detail
              .map((err) => `${err.loc ? err.loc.join('.') : ''}: ${err.msg}`)
              .join('; ');
          }
        }
        setFeedback({ type: 'error', title: '任务加载失败', message: errorMessage });
      }
    } catch (error) {
      console.error('Error submitting form:', error);
      setFeedback({ type: 'error', title: '请求发生错误', message: error.message });
    } finally {
      setLoading(false);
    }
  };

  const contentItems = useMemo(() => formValues.data.content, [formValues.data.content]);

  if (result) {
    return (
      <div className="mx-auto max-w-5xl p-4">
        <SubmissionSuccess
          result={result}
          onReset={() => {
            setResult(null);
            generateRandomIds();
          }}
          onViewStatus={() => handleNavigate('task-status')}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl p-4">
      <Card>
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle>LLM 查询任务加载</CardTitle>
          <Button variant="outline" type="button" onClick={generateRandomIds}>
            <Sparkles className="size-4" />
            生成示例 ID
          </Button>
        </CardHeader>
        <CardContent>
          {feedback ? (
            <Alert variant={feedback.type === 'error' ? 'destructive' : 'default'} className="mb-4">
              <AlertTitle>{feedback.title}</AlertTitle>
              <AlertDescription>{feedback.message}</AlertDescription>
            </Alert>
          ) : null}

          <form className="space-y-6" autoComplete="off" onSubmit={onSubmit}>
            <SectionTitle>基本信息</SectionTitle>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Field label="租户标识 Key" required>
                <Input value={formValues.tenant_key} disabled placeholder="tn_..." />
              </Field>
              <Field label="关联监测项目">
                <Select
                  value={formValues.project_id || LEGACY_PROJECT_VALUE}
                  onValueChange={(value) => setField('project_id', value)}
                  disabled={isLoadingProjects}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder={isLoadingProjects ? '正在加载项目' : '选择项目'} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      <SelectItem value={LEGACY_PROJECT_VALUE}>暂不关联项目</SelectItem>
                      {projectOptions.map((project) => (
                        <SelectItem key={project.value} value={project.value}>
                          {project.label}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  </SelectContent>
                </Select>
                {projectFeedback ? (
                  <span className="block text-xs text-muted-foreground">{projectFeedback}</span>
                ) : null}
              </Field>
              <Field label="任务 ID" required>
                <Input
                  value={formValues.job_id}
                  onChange={(event) => setField('job_id', event.target.value)}
                  placeholder="job_..."
                />
              </Field>
              <Field label="执行器 ID" required>
                <Input value={formValues.executor_id} disabled placeholder="exec_..." />
              </Field>
              <Field label="最近执行日期" required>
                <Input
                  type="date"
                  value={formValues.last_executed_date}
                  onChange={(event) => setField('last_executed_date', event.target.value)}
                />
              </Field>
              <Field label="生效开始时间" required>
                <Input
                  type="datetime-local"
                  value={formValues.effective_from}
                  onChange={(event) => setField('effective_from', event.target.value)}
                />
              </Field>
              <Field label="生效结束时间">
                <Input
                  type="datetime-local"
                  value={formValues.effective_to}
                  onChange={(event) => setField('effective_to', event.target.value)}
                />
              </Field>
              <Field label="总执行次数" required>
                <Input
                  type="number"
                  min="1"
                  value={formValues.total_runs}
                  onChange={(event) => setField('total_runs', Number(event.target.value))}
                />
              </Field>
              <Field label="已执行次数">
                <Input
                  type="number"
                  min="0"
                  value={formValues.executed_runs}
                  onChange={(event) => setField('executed_runs', Number(event.target.value))}
                />
              </Field>
            </div>

            <SectionTitle>数据配置 (Data)</SectionTitle>
            <Field label="分类名称" required>
              <Input
                value={formValues.data.category}
                onChange={(event) => setDataField('category', event.target.value)}
                placeholder="例如：游戏"
              />
            </Field>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Field label="品牌名称" required>
                <Input
                  value={formValues.data.brand}
                  onChange={(event) => setDataField('brand', event.target.value)}
                  placeholder="例如：哈基桃电竞"
                />
              </Field>
            </div>

            <div className="space-y-2">
              <div className="text-sm font-medium text-foreground">竞品名称列表 *</div>
              {formValues.data.competitor.map((item, index) => (
                <div key={`competitor-${index}`} className="flex gap-2">
                  <Input
                    value={item}
                    onChange={(event) => setCompetitor(index, event.target.value)}
                    placeholder="竞品名称"
                  />
                  <Button
                    type="button"
                    variant="destructive"
                    size="icon"
                    onClick={() => removeCompetitor(index)}
                    disabled={formValues.data.competitor.length <= 1}
                    aria-label="删除竞品"
                  >
                    <MinusCircle className="size-4" />
                  </Button>
                </div>
              ))}
              <Button type="button" variant="outline" className="w-full" onClick={addCompetitor}>
                <Plus className="size-4" />
                添加竞品
              </Button>
            </div>

            <SectionTitle>查询内容 (Content)</SectionTitle>
            <div className="space-y-4">
              {contentItems.map((item, contentIndex) => (
                <Card key={`content-${contentIndex}`} className="bg-muted/20">
                  <CardHeader className="flex flex-row items-center justify-between gap-3">
                    <CardTitle className="text-base">内容项 #{contentIndex + 1}</CardTitle>
                    <Button
                      type="button"
                      variant="destructive"
                      size="icon"
                      onClick={() => removeContent(contentIndex)}
                      disabled={contentItems.length <= 1}
                      aria-label="删除内容项"
                    >
                      <MinusCircle className="size-4" />
                    </Button>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Field label="关键词" required>
                      <Input
                        value={item.keyword}
                        onChange={(event) =>
                          updateContent(contentIndex, (current) => ({
                            ...current,
                            keyword: event.target.value,
                          }))
                        }
                        placeholder="例如：三角洲陪玩"
                      />
                    </Field>

                    <div className="space-y-2">
                      <div className="text-sm text-muted-foreground">查询语句列表</div>
                      {item.query_content.map((query, queryIndex) => (
                        <div key={`query-${contentIndex}-${queryIndex}`} className="flex gap-2">
                          <Textarea
                            value={query}
                            rows={2}
                            onChange={(event) =>
                              updateContent(contentIndex, (current) => ({
                                ...current,
                                query_content: current.query_content.map((value, valueIndex) =>
                                  valueIndex === queryIndex ? event.target.value : value,
                                ),
                              }))
                            }
                            placeholder="例如：三角洲陪玩哪家好？"
                          />
                          <Button
                            type="button"
                            variant="destructive"
                            size="icon"
                            onClick={() =>
                              updateContent(contentIndex, (current) => ({
                                ...current,
                                query_content: current.query_content.filter((_, valueIndex) => valueIndex !== queryIndex),
                              }))
                            }
                            disabled={item.query_content.length <= 1}
                            aria-label="删除查询语句"
                          >
                            <MinusCircle className="size-4" />
                          </Button>
                        </div>
                      ))}
                      <Button
                        type="button"
                        variant="outline"
                        className="w-full"
                        onClick={() =>
                          updateContent(contentIndex, (current) => ({
                            ...current,
                            query_content: [...current.query_content, ''],
                          }))
                        }
                      >
                        <Plus className="size-4" />
                        添加查询语句
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
              <Button type="button" variant="outline" className="w-full" onClick={addContent}>
                <Plus className="size-4" />
                添加内容项
              </Button>
            </div>

            <div className="sticky bottom-0 z-10 border-t bg-background/90 py-4 backdrop-blur-sm">
              <Button type="submit" disabled={loading} className="w-full" size="lg">
                <Upload className="size-4" />
                {loading ? '提交中...' : '提交任务'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default CreateQueryJob;
