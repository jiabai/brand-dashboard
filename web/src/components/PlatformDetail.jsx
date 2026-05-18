import React, { useEffect, useMemo, useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { fetchBrandMetrics } from '@/api';
import { useDashboardRequestParams } from '@/hooks/useDashboardParams';
import { formatPercentage } from '../utils';
import DataTable from './DataTable.jsx';
import LoadingSpinner from './LoadingSpinner.jsx';
import { Badge } from './ui/badge.jsx';
import { Button } from './ui/button.jsx';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card.jsx';
import { Progress } from './ui/progress.jsx';

const PlatformDetail = ({
  platformName,
  onBack,
}) => {
  const { tenantKey, jobId, brand, timeframe, startDate, endDate } = useDashboardRequestParams();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState([]);

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();

    const fetchData = async () => {
      setLoading(true);
      try {
        const result = await fetchBrandMetrics(
          {
            tenantKey,
            jobId,
            timeframe,
            startDate,
            endDate,
            platform: platformName,
            brand,
          },
          { signal: controller.signal },
        );
        if (cancelled) return;
        const list = Array.isArray(result?.data) ? result.data : [];
        const sorted = [...list]
          .sort((a, b) => (b.mention_rate || 0) - (a.mention_rate || 0))
          .map((item, index) => ({
            rank: index + 1,
            name: item.brand,
            mentionRate: item.mention_rate,
            firstMentionRate: item.first_mention_rate,
          }));
        setData(sorted);
      } catch (err) {
        if (cancelled || err.name === 'AbortError') return;
        setData([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchData();
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [platformName, tenantKey, jobId, brand, timeframe, startDate, endDate]);

  const columns = useMemo(() => {
    return [
      {
        title: '排名',
        dataIndex: 'rank',
        key: 'rank',
        width: 80,
        render: (rank) => (
          <div className="flex justify-center">
            <Badge variant={rank <= 3 ? 'default' : 'secondary'}>{rank}</Badge>
          </div>
        ),
      },
      {
        title: '品牌',
        dataIndex: 'name',
        key: 'name',
        width: 120,
        render: (text) => <span className="font-medium text-foreground">{text}</span>,
      },
      {
        title: '提及率',
        dataIndex: 'mentionRate',
        key: 'mentionRate',
        render: (val) => (
          <div className="flex min-w-40 items-center gap-2">
            <Progress value={val} className="h-2 w-28" />
            <span>{formatPercentage(val)}</span>
          </div>
        ),
        sorter: (a, b) => a.mentionRate - b.mentionRate,
      },
      {
        title: '首位提及率',
        dataIndex: 'firstMentionRate',
        key: 'firstMentionRate',
        render: (val) => (
          <div className="flex min-w-40 items-center gap-2">
            <Progress value={val} className="h-2 w-28 [&_[data-slot=progress-indicator]]:bg-chart-2" />
            <span className="text-muted-foreground">{formatPercentage(val)}</span>
          </div>
        ),
        sorter: (a, b) => a.firstMentionRate - b.firstMentionRate,
      },
    ];
  }, []);

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={onBack} aria-label="返回平台列表">
            <ArrowLeft />
          </Button>
          <CardTitle>{platformName} - 品牌提及率排名</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
      {loading ? (
        <LoadingSpinner text="正在加载平台详情..." />
      ) : (
        <DataTable
          data={data}
          columns={columns}
          rowKey="name"
          pagination={false}
          emptyDescription="暂无平台详情数据"
        />
      )}
      </CardContent>
    </Card>
  );
};

export default React.memo(PlatformDetail);
