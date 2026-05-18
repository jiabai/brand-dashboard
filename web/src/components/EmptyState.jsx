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
  <div className="flex min-h-32 flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-border bg-muted/35 p-5 text-center">
    <div className="flex size-9 items-center justify-center rounded-full bg-background text-lg text-muted-foreground ring-1 ring-border" aria-hidden="true">
      {icon}
    </div>
    <div className="flex flex-col gap-1">
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
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
