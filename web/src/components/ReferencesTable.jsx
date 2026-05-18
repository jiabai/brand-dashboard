/**
 * 引用列表组件
 * 显示文章引用信息和引用率
 */

import React, { useEffect, useMemo, useState } from 'react';
import { fetchCitationDomainSummary } from '@/api';
import { useDashboardRequestParams } from '@/hooks/useDashboardParams';
import { clampPercent, roundTwoDecimals } from '@/utils';
import DataTable from './DataTable.jsx';
import EmptyState from './EmptyState.jsx';
import LoadingSpinner from './LoadingSpinner.jsx';
import { Button } from './ui/button.jsx';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card.jsx';

const ReferencesTable = ({
  referencesData,
  isLoading,
  error,
}) => {
  const { timeframe, date, endDate, tenantKey, jobId, brand } = useDashboardRequestParams();
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

        const result = await fetchCitationDomainSummary(
          { tenantKey, jobId, brand, timeframe, startDate: date, endDate },
          { signal: controller.signal },
        );

        if (result?.status && result.status !== 'success') {
          throw new Error('接口返回错误状态');
        }

        const list = Array.isArray(result?.data) ? result.data : Array.isArray(result?.domain_distribution) ? result.domain_distribution : [];

        const normalized = list
          .map((item, index) => {
            const domain = item?.domain;
            const chineseName = item?.chinese_name ?? item?.chineseName ?? '';
            const citationCount = item?.citation_count ?? item?.citationCount ?? 0;
            const keywordCoverage = item?.keyword_coverage ?? item?.keywordCoverage ?? 0;
            const platformCoverage = item?.platform_coverage ?? item?.platformCoverage ?? 0;
            const rawRate =
              item?.['domain-citation-rate'] ??
              item?.domain_citation_rate ??
              item?.domainCitationRate ??
              0;
            const rate = roundTwoDecimals(clampPercent(rawRate));
            return {
              rank: index + 1,
              domain,
              chineseName,
              citationCount,
              keywordCoverage,
              platformCoverage,
              rate,
            };
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
        width: 80,
      },
      {
        title: '链接域名',
        dataIndex: 'domain',
        key: 'domain',
        width: 260,
        render: (domain) => (
          <a className="text-primary hover:underline" href={`https://${domain}`} target="_blank" rel="noopener noreferrer">
            {domain}
          </a>
        ),
      },
      {
        title: '中文名称',
        dataIndex: 'chineseName',
        key: 'chineseName',
        width: 160,
        render: (value, record) => value ?? record?.chinese_name ?? '',
      },
      {
        title: '引用次数',
        dataIndex: 'citationCount',
        key: 'citationCount',
        width: 120,
      },
      {
        title: '关键词覆盖数',
        dataIndex: 'keywordCoverage',
        key: 'keywordCoverage',
        width: 140,
      },
      {
        title: '平台覆盖数',
        dataIndex: 'platformCoverage',
        key: 'platformCoverage',
        width: 120,
      },
      {
        title: '域名引用率',
        dataIndex: 'rate',
        key: 'rate',
        width: 120,
        render: (rate) => `${roundTwoDecimals(rate)}%`,
      },
    ];
  }, []);

  // 加载状态
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>引用媒介详情</CardTitle>
        </CardHeader>
        <CardContent>
          <LoadingSpinner text="正在加载引用媒介..." />
        </CardContent>
      </Card>
    );
  }

  // 错误状态
  if (errorMsg) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>引用媒介详情</CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            title="数据加载失败"
            description={errorMsg}
            icon="!"
            actionText="重试"
            onAction={() => window.location.reload()}
          />
        </CardContent>
      </Card>
    );
  }

  // 空状态
  if (!displayData || displayData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>引用媒介详情</CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState title="暂无引用媒介" description="当前时间范围内没有可用的引用链接数据" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>引用媒介详情</CardTitle>
      </CardHeader>
      <CardContent>
      <DataTable
        rowKey={(record) => record.domain ?? String(record.rank)}
        columns={baseColumns}
        data={displayData}
        pagination={
          displayData.length > 20
            ? { pageSize: 20 }
            : false
        }
        loading={Boolean(loading)}
      />
      </CardContent>
    </Card>
  );
};

export default React.memo(ReferencesTable);
