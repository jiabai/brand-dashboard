/**
 * 空状态组件
 * 当没有数据时显示的占位符
 */

import React from 'react';
import { Button } from './ui/button';

const EmptyState = ({ 
  title = '暂无数据', 
  description = '当前没有可用的数据', 
  icon = '📊',
  actionText,
  onAction 
}) => {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">{icon}</div>
      <h3 className="empty-state-title">{title}</h3>
      <p className="empty-state-description">{description}</p>
      {actionText && onAction && (
        <Button
          className="empty-state-action"
          size="sm"
          onClick={onAction}
        >
          {actionText}
        </Button>
      )}
    </div>
  );
};


export default EmptyState;
