import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { Smile, ThumbsUp, ThumbsDown, Minus } from 'lucide-react';
import { ReactWordcloud } from '@cp949/react-wordcloud';

import { fetchFilterMetadata } from '@/api';
import { useDashboardRequestParams } from '@/hooks/useDashboardParams';

import KeywordSection from './KeywordSection';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card.jsx';

const MOCK_SENTIMENT = [
  { name: '正面', value: 600, color: 'var(--chart-2)' },
  { name: '负面', value: 200, color: 'var(--destructive)' },
  { name: '中性', value: 200, color: 'var(--chart-4)' },
];

const SENTIMENT = {
  POSITIVE: 'positive',
  NEGATIVE: 'negative',
  NEUTRAL: 'neutral',
};

const WORD_CLOUD_DATA = [
  { text: '品牌声量', value: 88, sentiment: SENTIMENT.POSITIVE },
  { text: '正面反馈', value: 72, sentiment: SENTIMENT.POSITIVE },
  { text: '体验', value: 66, sentiment: SENTIMENT.POSITIVE },
  { text: '信任', value: 58, sentiment: SENTIMENT.POSITIVE },
  { text: '价格', value: 52, sentiment: SENTIMENT.NEGATIVE },
  { text: '服务', value: 46, sentiment: SENTIMENT.NEGATIVE },
  { text: '质量', value: 44, sentiment: SENTIMENT.POSITIVE },
  { text: '推荐', value: 40, sentiment: SENTIMENT.POSITIVE },
  { text: '社媒讨论', value: 36, sentiment: SENTIMENT.NEUTRAL },
  { text: '复购', value: 32, sentiment: SENTIMENT.POSITIVE },
  { text: '物流', value: 28, sentiment: SENTIMENT.NEGATIVE },
  { text: '客服', value: 24, sentiment: SENTIMENT.NEGATIVE },
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

const SENTIMENT_META = {
  [SENTIMENT.POSITIVE]: {
    label: '正面',
    tone: 'text-emerald-600',
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    icon: ThumbsUp,
  },
  [SENTIMENT.NEGATIVE]: {
    label: '负面',
    tone: 'text-red-600',
    bg: 'bg-red-50',
    border: 'border-red-200',
    icon: ThumbsDown,
  },
  [SENTIMENT.NEUTRAL]: {
    label: '中性',
    tone: 'text-slate-600',
    bg: 'bg-slate-50',
    border: 'border-slate-200',
    icon: Minus,
  },
};

const SENTIMENT_COLORS = {
  [SENTIMENT.POSITIVE]: '#059669', // emerald-600
  [SENTIMENT.NEGATIVE]: '#dc2626', // red-600
  [SENTIMENT.NEUTRAL]: '#475569', // slate-600
};

const WordCloud = () => {
  const [activeWord, setActiveWord] = useState(null);

  const words = useMemo(
    () =>
      WORD_CLOUD_DATA.map((item) => ({
        text: item.text,
        value: item.value,
        sentiment: item.sentiment,
      })),
    [],
  );

  const getWordColor = useCallback(
    (word) => {
      const meta = SENTIMENT_META[word.sentiment] || SENTIMENT_META[SENTIMENT.NEUTRAL];
      // 如果词语被激活，使用对应情感颜色；否则使用 muted 颜色
      if (activeWord && activeWord !== word.text) {
        return '#94a3b8'; // slate-400 for inactive
      }
      return SENTIMENT_COLORS[word.sentiment] || '#475569';
    },
    [activeWord],
  );

  const getWordTooltip = useCallback((word) => {
    const meta = SENTIMENT_META[word.sentiment] || SENTIMENT_META[SENTIMENT.NEUTRAL];
    return `${word.text} · ${meta.label} · 权重: ${word.value}`;
  }, []);

  const handleWordClick = useCallback(
    (word) => {
      setActiveWord((prev) => (prev === word.text ? null : word.text));
    },
    [],
  );

  const callbacks = useMemo(
    () => ({
      getWordColor,
      getWordTooltip,
      onWordClick: handleWordClick,
    }),
    [getWordColor, getWordTooltip, handleWordClick],
  );

  const options = useMemo(
    () => ({
      colors: Object.values(SENTIMENT_COLORS),
      deterministic: true,
      enableTooltip: true,
      fontFamily: 'system-ui, -apple-system, sans-serif',
      fontSizes: [14, 40],
      fontStyle: 'normal',
      fontWeight: '600',
      padding: 3,
      rotationAngles: [-45, 45],
      rotations: 3,
      scale: 'sqrt',
      spiral: 'archimedean',
      transitionDuration: 500,
    }),
    [],
  );

  return (
    <div
      className="relative min-h-72 overflow-hidden rounded-md bg-muted/25 p-4"
      role="img"
      aria-label={`热词云: ${words.map((w) => w.text).join('、')}`}
    >
      <ReactWordcloud words={words} callbacks={callbacks} options={options} />
      {/* 图例 */}
      <div className="mt-3 flex flex-wrap justify-center gap-3">
        {Object.entries(SENTIMENT_META).map(([key, meta]) => {
          const Icon = meta.icon;
          return (
            <div key={key} className="flex items-center gap-1.5 text-xs">
              <span className={`inline-flex size-4 items-center justify-center rounded-full ${meta.bg} ${meta.border} border`}>
                <Icon className="size-2.5" />
              </span>
              <span className={meta.tone}>{meta.label}</span>
            </div>
          );
        })}
      </div>
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
