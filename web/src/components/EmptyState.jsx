/**
 * 空状态组件
 * 当没有数据时显示的占位符
 */

import React from 'react';
import { Button, Empty } from 'antd';

const EmptyState = ({ 
  title = '暂无数据', 
  description = '当前没有可用的数据', 
  icon = '📊',
  actionText,
  onAction 
}) => {
  return (
    <Empty
      image={Empty.PRESENTED_IMAGE_SIMPLE}
      description={
        <div>
          <div style={{ fontWeight: 600 }}>{title}</div>
          <div style={{ color: 'rgba(0, 0, 0, 0.45)' }}>{description}</div>
        </div>
      }
    >
      {actionText && onAction ? <Button onClick={onAction}>{actionText}</Button> : null}
    </Empty>
  );
};


export default EmptyState;
