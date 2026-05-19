import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  CheckCircle,
  Clock,
  RefreshCw,
  Search,
  XCircle,
} from 'lucide-react';
import dayjs from 'dayjs';
import { CONFIG } from '../config';
import { fetchQueryJobStatus } from '@/api';
import { useDashboardParams } from '@/hooks/useDashboardParams';
import {
  buildQueryJobStatusRowKey,
} from '../utils';
import DataTable from './DataTable.jsx';
import { Alert, AlertDescription, AlertTitle } from './ui/alert.jsx';
import { Badge } from './ui/badge.jsx';
import { Button } from './ui/button.jsx';
import { Card, CardContent } from './ui/card.jsx';
import { Checkbox } from './ui/checkbox.jsx';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select.jsx';
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip.jsx';

// Mapping status codes to visual elements
// Assuming 1 is active/effective based on context, adjusting as needed
const STATUS_MAP = {
  0: { text: '未生效', variant: 'secondary', Icon: Clock },
  1: { text: '生效中', variant: 'default', Icon: RefreshCw, iconClassName: 'animate-spin' },
  2: { text: '已完成', variant: 'secondary', Icon: CheckCircle },
  3: { text: '已失效', variant: 'destructive', Icon: XCircle },
};

const formatDateTime = (value) => {
  if (!value) return '-';
  const parsed = dayjs(value);
  return parsed.isValid() ? parsed.format('YYYY-MM-DD HH:mm') : '-';
};

const QueryJobStatus = () => {
  const {
    tenantKey,
    includeDeleted: includeDeletedParam,
    searchParams,
    updateParams,
  } = useDashboardParams();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState([]);
  const [jobIdOptions, setJobIdOptions] = useState([]);
  const [feedback, setFeedback] = useState('');
  const selectedJobId = searchParams.get('job_id') || '';
  const includeDeleted = useMemo(() => {
    const raw = includeDeletedParam || CONFIG.DEFAULT_INCLUDE_DELETED || 'false';
    return raw === 'true' || raw === '1';
  }, [includeDeletedParam]);

  const updateSearchParams = useCallback(
    (updates) => {
      updateParams(updates);
    },
    [updateParams],
  );

  const fetchData = useCallback(async () => {
    if (!tenantKey) {
      return;
    }
    setLoading(true);
    try {
      let result;
      try {
        result = await fetchQueryJobStatus({
          tenantKey,
          jobId: selectedJobId,
          includeDeleted,
        });
      } catch {
        setFeedback('查询失败');
        return;
      }

      if (result?.success) {
        setFeedback('');
        const jobs = Array.isArray(result.jobs) ? result.jobs : [];
        setData(jobs);
        const nextJobIds = jobs.map((job) => job?.job_id).filter(Boolean);
        setJobIdOptions((prev) => {
          if (selectedJobId) {
            return Array.from(new Set([...prev, ...nextJobIds]));
          }
          return Array.from(new Set(nextJobIds));
        });
      } else {
        setFeedback(result?.message || '查询失败');
      }
    } catch (error) {
      console.error('Fetch error:', error);
      setFeedback('网络请求错误');
    } finally {
      setLoading(false);
    }
  }, [tenantKey, includeDeleted, selectedJobId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const columns = [
    {
      title: '品牌 / 竞品',
      key: 'brand_info',
      width: 250,
      render: (_, record) => (
        <div className="flex min-w-52 flex-col gap-1">
          <span className="text-base font-medium text-foreground">{record.brand}</span>
          <div className="flex flex-wrap gap-1">
            {record.competitor?.map((comp, idx) => (
              <Badge key={idx} variant="secondary">
                {comp}
              </Badge>
            ))}
          </div>
        </div>
      ),
    },
    {
      title: '查询内容',
      dataIndex: 'query_content',
      key: 'query_content',
      render: (text) => (
        <Tooltip>
          <TooltipTrigger asChild>
            <span className="block max-w-md truncate font-mono text-sm text-foreground">
              {text}
            </span>
          </TooltipTrigger>
          <TooltipContent className="max-w-lg">{text}</TooltipContent>
        </Tooltip>
      ),
    },
    {
      title: '生效时间',
      key: 'time',
      width: 200,
      render: (_, record) => (
        <div className="flex min-w-44 flex-col text-xs text-muted-foreground">
          <span>
            From: {formatDateTime(record.effective_from)}
          </span>
          {record.effective_to && (
            <span>
              To: &nbsp;&nbsp;&nbsp;{formatDateTime(record.effective_to)}
            </span>
          )}
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'query_status',
      key: 'query_status',
      width: 120,
      render: (status) => {
        const statusConfig = STATUS_MAP[status] || { text: '未知', variant: 'secondary', Icon: Clock };
        const Icon = statusConfig.Icon;
        return (
          <Badge variant={statusConfig.variant} className="gap-1">
            <Icon data-icon="inline-start" className={statusConfig.iconClassName} />
            {statusConfig.text}
          </Badge>
        );
      },
    },
  ];

  return (
    <div className="max-w-6xl mx-auto p-4 fade-in-up">
      <style>{`
        .fade-in-up {
          animation: fadeInUp 0.6s ease-out;
        }
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .glass-card {
          background: color-mix(in srgb, var(--foreground) 2%, transparent);
          backdrop-filter: blur(10px);
          border: 1px solid color-mix(in srgb, var(--foreground) 6%, transparent);
        }
      `}</style>
      
      <div className="flex w-full flex-col gap-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="mb-1 text-2xl font-medium text-foreground">任务状态监控</h2>
            <p className="m-0 text-sm text-muted-foreground">实时追踪 LLM 查询任务的执行与生效情况</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
             <Select
                value={selectedJobId || '__all__'}
                onValueChange={(value) => updateSearchParams({ job_id: value === '__all__' ? null : value })}
             >
               <SelectTrigger className="w-72">
                 <Search data-icon="inline-start" />
                 <SelectValue placeholder="选择任务 ID" />
               </SelectTrigger>
               <SelectContent>
                 <SelectGroup>
                   <SelectItem value="__all__">全部任务</SelectItem>
                   {jobIdOptions.map((jobId) => (
                     <SelectItem key={jobId} value={jobId}>{jobId}</SelectItem>
                   ))}
                 </SelectGroup>
               </SelectContent>
             </Select>
             <label className="flex items-center gap-2 text-sm text-muted-foreground">
                <Checkbox
                  checked={includeDeleted}
                  onCheckedChange={(checked) => updateSearchParams({ include_deleted: checked ? 'true' : 'false' })}
                />
                包含已删除
             </label>
             <Button onClick={fetchData} disabled={loading}>
                <RefreshCw data-icon="inline-start" className={loading ? 'animate-spin' : ''} />
                查询
             </Button>
          </div>
        </div>

        {feedback ? (
          <Alert variant="destructive">
            <AlertTitle>查询失败</AlertTitle>
            <AlertDescription>{feedback}</AlertDescription>
          </Alert>
        ) : null}

        <Card className="glass-card">
          <CardContent className="p-0">
          <DataTable
            data={data}
            columns={columns}
            rowKey={buildQueryJobStatusRowKey}
            loading={loading}
            pagination={{ pageSize: 10 }}
            emptyDescription="暂无数据，请尝试查询"
          />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default QueryJobStatus;
