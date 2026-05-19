/**
 * 加载状态组件
 * 显示数据加载时的动画效果
 */

import React from 'react';

import { Spinner } from './ui/spinner.jsx';
import { cn } from '@/lib/cn';

const LoadingSpinner = ({ size = 'medium', text = '加载中...' }) => {
  const sizeMap = {
    small: 'size-4',
    medium: 'size-5',
    large: 'size-7'
  };

  return (
    <div className="inline-flex items-center gap-2 text-sm text-muted-foreground">
      <Spinner className={cn(sizeMap[size] || sizeMap.medium)} />
      <span>{text}</span>
    </div>
  );
};


export default LoadingSpinner;
