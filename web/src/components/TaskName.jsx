import React, { useState, useEffect, useRef } from 'react';
import { Card } from './ui/card';

/**
 * TaskName component - 显示用户自定义的任务名称
 * @returns {JSX.Element} 任务名称组件
 */
const TaskName = () => {
  const [taskName, setTaskName] = useState('加载中...');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const intervalRef = useRef(null);

  const MAX_RETRIES = 3;

  useEffect(() => {
    // 获取任务名称的函数
    const fetchTaskName = async () => {
      try {
        setLoading(true);
        // TODO: 替换为实际的API端点
        const response = await fetch('/api/task/current');

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.taskName) {
          setTaskName(data.taskName);
          setError(null);
          setRetryCount(0); // 成功后重置重试计数
        } else {
          // 如果没有任务名称，显示默认值
          setTaskName('未命名任务');
        }
      } catch (err) {
        console.error('获取任务名称失败:', err);
        setError(err.message);
        setTaskName('获取失败');

        // 失败后增加重试计数
        setRetryCount(prev => prev + 1);
      } finally {
        setLoading(false);
      }
    };

    fetchTaskName();

    // 只有在重试次数未超限时才设置定期刷新
    if (retryCount < MAX_RETRIES) {
      intervalRef.current = setInterval(fetchTaskName, 30000); // 30秒刷新一次
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [retryCount]);

  // 手动重试函数
  const handleRetry = () => {
    setRetryCount(0); // 重置重试计数，触发重新获取
  };

  return (
    <div className="task-name-container flex items-center">
      <Card className="px-4 py-2 bg-background/50 backdrop-blur-sm">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-muted-foreground">当前任务:</span>
          {loading ? (
            <div className="w-20 h-4 bg-gray-200 animate-pulse rounded"></div>
          ) : error ? (
            <span
              className="text-sm text-red-500 cursor-pointer hover:underline"
              title={`${error} - 点击重试`}
              onClick={handleRetry}
            >
              {taskName}
            </span>
          ) : (
            <span className="text-sm font-semibold text-foreground">
              {taskName}
            </span>
          )}
        </div>
      </Card>
    </div>
  );
};

export default TaskName;