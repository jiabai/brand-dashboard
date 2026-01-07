/**
 * 加载状态组件
 * 显示数据加载时的动画效果
 */

import React from 'react';
import { Spin } from 'antd';

const LoadingSpinner = ({ size = 'medium', text = '加载中...' }) => {
  const sizeMap = {
    small: 'small',
    medium: 'default',
    large: 'large'
  };

  const spinnerSize = sizeMap[size] || sizeMap.medium;

  return (
    <Spin size={spinnerSize} tip={text} />
  );
};


export default LoadingSpinner;
