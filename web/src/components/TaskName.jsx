import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button, Space, Spin, Tag, Tooltip, Typography } from 'antd';

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
    <Space size="small" align="center">
      <Tag color="blue">当前任务</Tag>
      {loading ? (
        <Space size="small" align="center">
          <Spin size="small" />
          <Typography.Text type="secondary">加载中...</Typography.Text>
        </Space>
      ) : error ? (
        <Tooltip title={error}>
          <Button type="link" danger onClick={handleRetry} style={{ paddingInline: 0 }}>
            任务加载失败，点击重试
          </Button>
        </Tooltip>
      ) : (
        <Typography.Text strong ellipsis style={{ maxWidth: 320 }}>
          {taskName}
        </Typography.Text>
      )}
    </Space>
  );
};

export default React.memo(TaskName);
