import React, { useState, useEffect, useRef, useCallback } from 'react';

import { Badge } from './ui/badge.jsx';
import { Button } from './ui/button.jsx';
import { Spinner } from './ui/spinner.jsx';
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip.jsx';

/**
 * TaskName component - 显示用户自定义的任务名称
 * @returns {JSX.Element} 任务名称组件
 */
const TaskName = () => {
  const [taskName, setTaskName] = useState('加载中...');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hasStopped, setHasStopped] = useState(false);
  const timeoutRef = useRef(null);
  const abortControllerRef = useRef(null);

  const fetchTaskName = useCallback(async (isRetry = false) => {
    // 取消之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // 创建新的 AbortController
    abortControllerRef.current = new AbortController();

    try {
      if (!isRetry) {
        setLoading(true);
      }

      // 使用模拟数据代替API请求
      const data = { success: true, taskName: '品牌仪表板任务' };

      if (data.success && data.taskName) {
        setTaskName(data.taskName);
        setError(null);
        setHasStopped(false);
      } else {
        // 如果没有任务名称，显示默认值
        setTaskName('未命名任务');
      }
    } catch (err) {
      console.error('获取任务名称失败:', err);
      setError(err.message);
      setTaskName('获取失败');
      setHasStopped(true);
      setLoading(false);
    } finally {
      if (!isRetry) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    // 初始加载
    fetchTaskName();

    // 清理函数
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // 手动重试函数
  const handleRetry = () => {
    setHasStopped(false);
    setError(null);
    fetchTaskName();
  };

  return (
    <div className="flex min-w-0 items-center gap-2">
      <Badge variant="secondary" className="shrink-0">当前任务</Badge>
      {loading ? (
        <span className="inline-flex items-center gap-1.5 text-sm text-muted-foreground">
          <Spinner />
          加载中...
        </span>
      ) : error ? (
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="link" onClick={handleRetry} className="h-auto px-0 text-destructive">
              任务加载失败，点击重试
            </Button>
          </TooltipTrigger>
          <TooltipContent>{error}</TooltipContent>
        </Tooltip>
      ) : (
        <span className="max-w-80 truncate text-sm font-semibold text-foreground">
          {taskName}
        </span>
      )}
    </div>
  );
};

export default React.memo(TaskName);
