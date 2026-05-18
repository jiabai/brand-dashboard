import React, { useEffect, useMemo, useState } from 'react';
import { Smile } from 'lucide-react';

import { fetchFilterMetadata } from '@/api';
import { useDashboardRequestParams } from '@/hooks/useDashboardParams';

import KeywordSection from './KeywordSection';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card.jsx';

const MOCK_SENTIMENT = [
  { name: '正面', value: 600, color: 'var(--chart-2)' },
  { name: '负面', value: 200, color: 'var(--destructive)' },
  { name: '中性', value: 200, color: 'var(--chart-4)' },
];

const WORD_CLOUD_DATA = [
  { text: '品牌声量', value: 88 },
  { text: '正面反馈', value: 72 },
  { text: '体验', value: 66 },
  { text: '信任', value: 58 },
  { text: '价格', value: 52 },
  { text: '服务', value: 46 },
  { text: '质量', value: 44 },
  { text: '推荐', value: 40 },
  { text: '社媒讨论', value: 36 },
  { text: '复购', value: 32 },
  { text: '物流', value: 28 },
  { text: '客服', value: 24 },
];

const SentimentDonut = () => {
  const total = MOCK_SENTIMENT.reduce((sum, item) => sum + item.value, 0);
  let cursor = 0;
  const segments = MOCK_SENTIMENT.map((item) => {
    const start = cursor;
    const end = start + (item.value / total) * 100;
    cursor = end;
    return `${item.color} ${start}% ${end}%`;
  });

  // 形状图标辅助色盲区分
  const legendShapes = [
    <span key="shape" className="size-2.5 rounded-full" />,
    <span key="shape" className="size-2.5 rotate-45 rounded-sm" />,
    <span key="shape" className="size-0 border-x-[5px] border-b-[8px] border-x-transparent border-b-current" />,
  ];

  return (
    <div className="flex flex-col items-center gap-5">
      <div
        className="grid size-48 place-items-center rounded-full sm:size-56 lg:size-64"
        style={{ background: `conic-gradient(${segments.join(', ')})` }}
        role="img"
        aria-label={`情感分布: ${MOCK_SENTIMENT.map((s) => `${s.name} ${Math.round((s.value / total) * 100)}%`).join('，')}`}
      >
        <div className="grid size-28 place-items-center rounded-full bg-card text-center sm:size-32 lg:size-36">
          <div>
            <div className="text-2xl font-medium text-foreground">{total.toLocaleString()}</div>
            <div className="text-sm text-muted-foreground">分析样本</div>
          </div>
        </div>
      </div>
      <div className="flex flex-wrap justify-center gap-3">
        {MOCK_SENTIMENT.map((item, idx) => (
          <div key={item.name} className="flex items-center gap-2 rounded-md border px-3 py-1 text-sm">
            <span className="flex items-center justify-center" style={{ color: item.color }}>
              {legendShapes[idx % legendShapes.length]}
            </span>
            <span className="font-medium text-foreground">{item.name}</span>
            <span className="text-muted-foreground">{Math.round((item.value / total) * 100)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const WordCloud = () => {
  const max = Math.max(...WORD_CLOUD_DATA.map((item) => item.value));
  const min = Math.min(...WORD_CLOUD_DATA.map((item) => item.value));

  return (
    <div
      className="flex min-h-72 flex-wrap items-center justify-center gap-x-5 gap-y-4 rounded-md bg-muted/25 p-6"
      role="img"
      aria-label={`热词云: ${WORD_CLOUD_DATA.map((w) => w.text).join('、')}`}
    >
      {WORD_CLOUD_DATA.map((item) => {
        const ratio = (item.value - min) / Math.max(1, max - min);
        const fontSize = 14 + ratio * 26;
        // 基于权重大小使用语义色彩：高权重=primary强调，低权重=柔和
        const tone = ratio > 0.6 ? 'text-primary' : ratio > 0.3 ? 'text-foreground' : 'text-muted-foreground';
        return (
          <span
            key={item.text}
            className={`font-medium ${tone} transition-opacity hover:opacity-70`}
            style={{ fontSize }}
          >
            {item.text}
          </span>
        );
      })}
    </div>
  );
};

export default function SentimentAnalysis() {
  const { date, endDate, tenantKey, jobId } = useDashboardRequestParams();
  const [keywords, setKeywords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const stats = useMemo(() => {
    const total = MOCK_SENTIMENT.reduce((sum, item) => sum + item.value, 0);
    const positive = MOCK_SENTIMENT.find((item) => item.name === '正面')?.value ?? 0;
    const negative = MOCK_SENTIMENT.find((item) => item.name === '负面')?.value ?? 0;

    return [
      { label: '分析样本数', value: total.toLocaleString() },
      { label: '正面情感占比', value: `${Math.round((positive / total) * 100)}%` },
      { label: '负面情感占比', value: `${Math.round((negative / total) * 100)}%` },
    ];
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    const fetchMetadata = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchFilterMetadata(
          { tenantKey, jobId, startDate: date, endDate },
          { signal: controller.signal },
        );

        if (result?.code === 200 && result.data) {
          setKeywords(result.data.keywords || []);
        } else {
          throw new Error(result?.message || '获取元数据失败');
        }
      } catch (err) {
        if (err.name === 'AbortError') return;
        console.error('Fetch filter metadata error:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchMetadata();

    return () => {
      controller.abort();
    };
  }, [tenantKey, jobId, date, endDate]);

  return (
    <div className="flex min-h-[calc(100vh-112px)] w-full flex-col gap-6">
      <KeywordSection keywords={keywords} loading={loading} />
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      <Card className="flex flex-1 flex-col">
        <CardHeader className="space-y-3">
          <div className="flex items-center gap-2">
            <Smile className="size-5 text-primary" />
            <CardTitle>情感分析</CardTitle>
          </div>
          <div className="flex flex-wrap gap-x-6 gap-y-2 pl-0 text-sm sm:pl-7">
            {stats.map((item) => (
              <span key={item.label} className="text-muted-foreground">
                {item.label}：
                <strong className="font-medium text-foreground">{item.value}</strong>
              </span>
            ))}
          </div>
        </CardHeader>
        <CardContent className="grid flex-1 gap-6 lg:grid-cols-[1fr_0.8fr]">
          <div className="flex min-h-80 items-center justify-center">
            <SentimentDonut />
          </div>
          <WordCloud />
        </CardContent>
      </Card>
    </div>
  );
}
