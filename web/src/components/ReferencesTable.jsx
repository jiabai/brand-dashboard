/**
 * 引用列表组件
 * 显示文章引用信息和引用率
 */

import React, { useEffect, useMemo, useState } from 'react';
import { Button, Card, Empty, Table, Typography } from 'antd';
import { CONFIG } from '@/config';

const { DEFAULT_TENANT_KEY, DEFAULT_JOB_ID, DEFAULT_BRAND } = CONFIG;

const buildQueryString = (params) => {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null) return;
    searchParams.set(key, String(value));
  });
  return searchParams.toString();
};

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

const ReferencesTable = ({
  timeframe = '7days',
  date = '',
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

        const queryString = buildQueryString({
          tenant_key: tenantKey,
          job_id: jobId,
          brand,
          timeframe,
          date,
        });

        const result = await fetchJson(
          `/api/v1/dashboard/domain-citation-rate?${queryString}`,
          { signal: controller.signal },
        );

        if (result?.status && result.status !== 'success') {
          throw new Error('接口返回错误状态');
        }

        const list = Array.isArray(result?.domain_distribution) ? result.domain_distribution : [];

        const normalized = list
          .map((item, index) => {
            const domain = item?.domain;
            const rawRate =
              item?.['domain-citation-rate'] ??
              item?.domain_citation_rate ??
              item?.domainCitationRate ??
              0;
            const rate = roundTwoDecimals(clampPercent(rawRate));
            return { rank: index + 1, domain, rate };
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
  }, [hasExternalData, tenantKey, jobId, brand, timeframe, date]);

  const displayData = hasExternalData ? referencesData : data;
  const loading = isLoading ?? internalLoading;
  const errorMsg = error ?? internalError ?? null;

  const columns = useMemo(() => {
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
        render: (domain) => (
          <Typography.Link href={`https://${domain}`} target="_blank" rel="noopener noreferrer">
            {domain}
          </Typography.Link>
        )
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
        columns={columns}
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
