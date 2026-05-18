/**
 * 空状态组件
 * 当没有数据时显示的占位符
 */

import React from 'react';

import { Button } from './ui/button.jsx';

const EmptyState = ({ 
  title = '暂无数据', 
  description = '当前没有可用的数据', 
  icon = '📊',
  actionText,
  onAction 
}) => (
  <div className="flex min-h-48 flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border bg-card/60 p-8 text-center">
    <div className="flex size-12 items-center justify-center rounded-full bg-muted text-2xl" aria-hidden="true">
      {icon}
    </div>
    <div className="flex flex-col gap-1">
      <h3 className="text-base font-semibold text-foreground">{title}</h3>
      <p className="m-0 text-sm text-muted-foreground">{description}</p>
    </div>
    {actionText && onAction ? (
      <Button variant="outline" onClick={onAction}>
        {actionText}
      </Button>
    ) : null}
  </div>
);


export default EmptyState;
