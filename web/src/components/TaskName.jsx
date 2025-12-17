import React, { useState, useEffect, useRef, useCallback } from 'react';
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
  const [hasStopped, setHasStopped] = useState(false);
  const timeoutRef = useRef(null);
  const abortControllerRef = useRef(null);

  const MAX_RETRIES = 3;
  const RETRY_DELAY = 1000; // 1秒

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

      // TODO: 替换为实际的API端点
      const response = await fetch('/api/task/current', {
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.success && data.taskName) {
        setTaskName(data.taskName);
        setError(null);
        setRetryCount(0);
        setHasStopped(false);
      } else {
        // 如果没有任务名称，显示默认值
        setTaskName('未命名任务');
      }
    } catch (err) {
      // 忽略被取消的请求
      if (err.name === 'AbortError') {
        return;
      }

      console.error('获取任务名称失败:', err);
      setError(err.message);

      const newRetryCount = retryCount + 1;
      setRetryCount(newRetryCount);

      // 如果重试次数未达到上限，1秒后重试
      if (newRetryCount < MAX_RETRIES) {
        timeoutRef.current = setTimeout(() => {
          fetchTaskName(true);
        }, RETRY_DELAY);
      } else {
        // 达到最大重试次数，停止并显示失败状态
        setTaskName('获取失败');
        setHasStopped(true);
        setLoading(false);
      }
    } finally {
      if (!isRetry) {
        setLoading(false);
      }
    }
  }, [retryCount]);

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
    setRetryCount(0);
    setHasStopped(false);
    setError(null);
    fetchTaskName();
  };

  return (
    <div className="task-name-container flex items-center h-full">
      <div className="flex relative">
        <ul className="flex gap-8 list-none p-0 px-4 m-0 relative z-[3] text-slate-500">
          <li className="rounded-full relative cursor-default transition-[background-color_color_box-shadow] duration-300 ease shadow-[0_0_0.5px_1.5px_transparent] font-semibold text-white">
            <div className="outline-none py-[0.6em] px-[1em] inline-flex items-center gap-3">
              <span className="uppercase tracking-wider text-white/70 text-sm whitespace-nowrap">当前任务</span>
              <div className="h-4 w-px bg-white/20"></div>
              {loading ? (
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 border-2 border-white/30 border-t-white/80 rounded-full animate-spin"></div>
                  <span className="text-white/80 font-medium whitespace-nowrap">加载中...</span>
                </div>
              ) : error ? (
                <div 
                  className="flex items-center group cursor-pointer text-rose-300 hover:text-rose-200 transition-colors"
                  onClick={handleRetry}
                  title={error}
                >
                  <svg className="w-3.5 h-3.5 mr-1.5 opacity-70 group-hover:opacity-100" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <span className="whitespace-nowrap">{hasStopped ? '任务加载失败' : taskName}</span>
                </div>
              ) : (
                <span className="bg-gradient-to-r from-white to-white/90 bg-clip-text text-transparent max-w-xs truncate">
                  {taskName}
                </span>
              )}
            </div>
            {/* 静态的背景效果，模仿 GooeyNav 的激活状态 */}
            <div className="absolute inset-0 rounded-full bg-[#7c3aed] opacity-100 transform scale-100 -z-10 shadow-[0_0_0.5px_1.5px_transparent]"></div>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default TaskName;
