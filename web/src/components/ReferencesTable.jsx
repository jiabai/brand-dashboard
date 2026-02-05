/**
 * 引用列表组件
 * 显示文章引用信息和引用率
 */

import React, { useEffect, useMemo, useState } from 'react';
import { Button, Card, Empty, Table, Typography } from 'antd';
import { CONFIG } from '@/config';
import { buildDomainCitationQueryString } from '@/utils/domainCitationQuery';

const { DEFAULT_TENANT_KEY, DEFAULT_JOB_ID, DEFAULT_BRAND } = CONFIG;

const MIN_COLUMN_WIDTH = 80;

const fetchJson = async (url, { signal } = {}) => {
  const response = await fetch(url, { method: 'GET', signal });
  if (!response.ok) {
    throw new Error(`请求失败(${response.status})`);
  }
  return response.json();
};

const clampPercent = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return 0;
  return Math.max(0, Math.min(100, num));
};

const roundTwoDecimals = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return 0;
  return Math.round(num * 100) / 100;
};

const ResizableHeaderCell = ({ onResize, width, children, ...restProps }) => {
  if (!width) {
    return <th {...restProps}>{children}</th>;
  }

  return (
    <th {...restProps} style={{ ...(restProps.style ?? {}), width, position: 'relative' }}>
      {children}
      <div
        onMouseDown={onResize}
        role="separator"
        tabIndex={-1}
        style={{
          position: 'absolute',
          top: 0,
          right: -6,
          width: 12,
          height: '100%',
          cursor: 'col-resize',
          userSelect: 'none',
        }}
      />
    </th>
  );
};

const ReferencesTable = ({
  timeframe = '7days',
  date = '',
  endDate = '',
  tenantKey = DEFAULT_TENANT_KEY,
  jobId = DEFAULT_JOB_ID,
  brand = DEFAULT_BRAND,
  referencesData,
  isLoading,
  error,
}) => {
  const hasExternalData = Array.isArray(referencesData);
  const [data, setData] = useState([]);
  const [internalLoading, setInternalLoading] = useState(!hasExternalData);
  const [internalError, setInternalError] = useState(null);

  useEffect(() => {
    if (hasExternalData) return;

    const controller = new AbortController();
    const run = async () => {
      try {
        setInternalLoading(true);
        setInternalError(null);

        const queryString = buildDomainCitationQueryString({
          tenantKey,
          jobId,
          brand,
          timeframe,
          startDate: date,
          endDate,
        });

        const result = await fetchJson(
          `/api/v1/dashboard/citation-domain-stats?${queryString}`,
          { signal: controller.signal },
        );

        if (result?.status && result.status !== 'success') {
          throw new Error('接口返回错误状态');
        }

        const list = Array.isArray(result?.domain_distribution) ? result.domain_distribution : [];

        const normalized = list
          .map((item, index) => {
            const domain = item?.domain;
            const chineseName = item?.chinese_name ?? item?.chineseName ?? '';
            const rawRate =
              item?.['domain-citation-rate'] ??
              item?.domain_citation_rate ??
              item?.domainCitationRate ??
              0;
            const rate = roundTwoDecimals(clampPercent(rawRate));
            return { rank: index + 1, domain, chineseName, rate };
          })
          .filter((item) => item.domain);

        setData(normalized);
        setInternalLoading(false);
      } catch (err) {
        if (controller.signal.aborted) return;
        if (err?.name === 'AbortError') return;
        setInternalError(err?.message || '数据加载失败');
        setInternalLoading(false);
      }
    };

    run();

    return () => {
      controller.abort();
    };
  }, [hasExternalData, tenantKey, jobId, brand, timeframe, date, endDate]);

  const displayData = hasExternalData ? referencesData : data;
  const loading = isLoading ?? internalLoading;
  const errorMsg = error ?? internalError ?? null;

  const baseColumns = useMemo(() => {
    return [
      {
        title: '排名',
        dataIndex: 'rank',
        key: 'rank',
        width: 80
      },
      {
        title: '链接域名',
        dataIndex: 'domain',
        key: 'domain',
        width: 260,
        render: (domain) => (
          <Typography.Link href={`https://${domain}`} target="_blank" rel="noopener noreferrer">
            {domain}
          </Typography.Link>
        )
      },
      {
        title: '中文名称',
        dataIndex: 'chineseName',
        key: 'chineseName',
        width: 160,
        render: (value, record) => value ?? record?.chinese_name ?? ''
      },
      {
        title: '域名引用率',
        dataIndex: 'rate',
        key: 'rate',
        width: 120,
        render: (rate) => `${roundTwoDecimals(rate)}%`
      }
    ];
  }, []);

  const [columns, setColumns] = useState(() => baseColumns);

  useEffect(() => {
    setColumns(baseColumns);
  }, [baseColumns]);

  const resizableColumns = useMemo(() => {
    const startResize = (columnIndex) => (event) => {
      event.preventDefault();
      event.stopPropagation();

      const startX = event.clientX;
      const startWidth = Number(columns[columnIndex]?.width) || MIN_COLUMN_WIDTH;

      const onMouseMove = (moveEvent) => {
        const delta = moveEvent.clientX - startX;
        const nextWidth = Math.max(MIN_COLUMN_WIDTH, startWidth + delta);

        setColumns((prev) => {
          if (!Array.isArray(prev) || !prev[columnIndex]) return prev;
          const next = prev.slice();
          const current = next[columnIndex];
          next[columnIndex] = { ...current, width: nextWidth };
          return next;
        });
      };

      const onMouseUp = () => {
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
      };

      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    };

    return columns.map((col, index) => ({
      ...col,
      onHeaderCell: () => ({
        width: col.width,
        onResize: startResize(index),
      }),
    }));
  }, [columns]);

  // 加载状态
  if (loading) {
    return (
      <Card title="引用媒介详情" loading />
    );
  }

  // 错误状态
  if (errorMsg) {
    return (
      <Card title="引用媒介详情">
        <Typography.Paragraph type="danger">{errorMsg}</Typography.Paragraph>
        <Button type="primary" onClick={() => window.location.reload()}>
          重试
        </Button>
      </Card>
    );
  }

  // 空状态
  if (!displayData || displayData.length === 0) {
    return (
      <Card title="引用媒介详情">
        <Empty description="当前时间范围内没有可用的引用链接数据" />
      </Card>
    );
  }

  return (
    <Card title="引用媒介详情">
      <Table
        rowKey={(record) => record.domain ?? String(record.rank)}
        size="middle"
        tableLayout="fixed"
        scroll={{ x: 'max-content' }}
        components={{
          header: {
            cell: ResizableHeaderCell,
          },
        }}
        columns={resizableColumns}
        dataSource={displayData}
        pagination={
          displayData.length > 20
            ? { pageSize: 20, showSizeChanger: true, showQuickJumper: true }
            : false
        }
        loading={Boolean(loading)}
      />
    </Card>
  );
};

export default React.memo(ReferencesTable);
