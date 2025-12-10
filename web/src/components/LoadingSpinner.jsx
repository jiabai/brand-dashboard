/**
 * 加载状态组件
 * 显示数据加载时的动画效果
 */

import React from 'react';

const LoadingSpinner = ({ size = 'medium', text = '加载中...' }) => {
  const sizeMap = {
    small: 20,
    medium: 40,
    large: 60
  };

  const spinnerSize = sizeMap[size] || sizeMap.medium;

  return (
    <div className="loading-spinner">
      <div 
        className="spinner"
        style={{
          width: spinnerSize,
          height: spinnerSize,
          borderWidth: spinnerSize * 0.1
        }}
      />
      {text && <span className="loading-text">{text}</span>}
    </div>
  );
};


export default LoadingSpinner;
