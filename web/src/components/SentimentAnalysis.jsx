import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Minus, Smile, Tags, ThumbsDown, ThumbsUp } from 'lucide-react';
import { ReactWordcloud } from '@cp949/react-wordcloud';

import { fetchFilterMetadata, fetchSentimentAnalysis } from '@/api';
import { useDashboardRequestParams } from '@/hooks/useDashboardParams';
import {
  normalizeSentimentAnalysis,
  SENTIMENT_STATUS_META,
} from '@/utils';

import KeywordSection from './KeywordSection';
import EmptyState from './EmptyState.jsx';
import LoadingSpinner from './LoadingSpinner.jsx';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card.jsx';

const SENTIMENT_ICONS = {
  positive: ThumbsUp,
  negative: ThumbsDown,
  neutral: Minus,
  unknown: Tags,
};

const SentimentDonut = ({ distribution, sampleCount }) => {
  let cursor = 0;
  const segments = distribution.map((item) => {
    const start = cursor;
    const end = start + item.ratio * 100;
    cursor = end;
    return `${item.color} ${start}% ${end}%`;
  });

  const legendShapes = [
    <span key="shape" className="size-2.5 rounded-full" />,
    <span key="shape" className="size-2.5 rotate-45 rounded-sm" />,
    <span key="shape" className="size-0 border-x-[5px] border-b-[8px] border-x-transparent border-b-current" />,
    <span key="shape" className="size-2.5 rounded-sm" />,
  ];

  return (
    <div className="flex flex-col items-center gap-5">
      <div
        className="grid size-48 place-items-center rounded-full sm:size-56 lg:size-64"
        style={{ background: `conic-gradient(${segments.join(', ')})` }}
        role="img"
        aria-label={`情感分布: ${distribution.map((item) => `${item.chartLabel} ${item.percentLabel}`).join('，')}`}
      >
        <div className="grid size-28 place-items-center rounded-full bg-card text-center sm:size-32 lg:size-36">
          <div>
            <div className="text-2xl font-medium text-foreground">{sampleCount.toLocaleString()}</div>
            <div className="text-sm text-muted-foreground">分析样本</div>
          </div>
        </div>
      </div>
      <div className="flex flex-wrap justify-center gap-3">
        {distribution.map((item, index) => (
          <div key={item.sentimentStatus} className="flex items-center gap-2 rounded-md border px-3 py-1 text-sm">
            <span className="flex items-center justify-center" style={{ color: item.color }}>
              {legendShapes[index % legendShapes.length]}
            </span>
            <span className="font-medium text-foreground">{item.chartLabel}</span>
            <span className="text-muted-foreground">{item.percentLabel}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const WordCloud = ({ words }) => {
  const [activeWord, setActiveWord] = useState(null);

  const getWordColor = useCallback(
    (word) => {
      const meta = SENTIMENT_STATUS_META[word.sentiment] || SENTIMENT_STATUS_META.neutral;
      if (activeWord && activeWord !== word.text) {
        return '#94a3b8';
      }
      return meta.hexColor;
    },
    [activeWord],
  );

  const getWordTooltip = useCallback((word) => {
    const meta = SENTIMENT_STATUS_META[word.sentiment] || SENTIMENT_STATUS_META.neutral;
    return `${word.text} · ${meta.label} · ${word.value} 条 · ${word.percentLabel}`;
  }, []);

  const handleWordClick = useCallback((word) => {
    setActiveWord((previous) => (previous === word.text ? null : word.text));
  }, []);

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
      colors: Object.values(SENTIMENT_STATUS_META).map((item) => item.hexColor),
      deterministic: true,
      enableTooltip: true,
      fontFamily: 'system-ui, -apple-system, sans-serif',
      fontSizes: [14, 40],
      fontStyle: 'normal',
      fontWeight: '600',
      padding: 3,
      rotationAngles: [-35, 35],
      rotations: 3,
      scale: 'sqrt',
      spiral: 'archimedean',
      transitionDuration: 500,
    }),
    [],
  );

  if (!words.length) {
    return (
      <div className="grid min-h-72 place-items-center rounded-md bg-muted/25 p-4">
        <EmptyState
          title="暂无关键词情感数据"
          description="等待分析运行生成情感事实后，这里会展示关键词对应的情感倾向。"
          icon={Tags}
        />
      </div>
    );
  }

  return (
    <div
      className="relative min-h-72 overflow-hidden rounded-md bg-muted/25 p-4"
      role="img"
      aria-label={`热词云: ${words.map((word) => word.text).join('、')}`}
    >
      <ReactWordcloud words={words} callbacks={callbacks} options={options} />
      <div className="mt-3 flex flex-wrap justify-center gap-3">
        {Object.entries(SENTIMENT_STATUS_META).map(([key, meta]) => {
          const Icon = SENTIMENT_ICONS[key] || Tags;
          return (
            <div key={key} className="flex items-center gap-1.5 text-xs">
              <span className="inline-flex size-4 items-center justify-center rounded-full border bg-background">
                <Icon className="size-2.5" />
              </span>
              <span style={{ color: meta.hexColor }}>{meta.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default function SentimentAnalysis() {
  const {
    date,
    endDate,
    tenantKey,
    jobId,
    brand,
    timeframe,
    selectedPlatform,
  } = useDashboardRequestParams();
  const [keywords, setKeywords] = useState([]);
  const [selectedKeyword, setSelectedKeyword] = useState('');
  const [sentimentData, setSentimentData] = useState(() => normalizeSentimentAnalysis());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const stats = useMemo(
    () => [
      { label: '分析样本数', value: sentimentData.summary.sampleCountLabel },
      { label: '正面情感占比', value: sentimentData.summary.positivePercentLabel },
      { label: '负面情感占比', value: sentimentData.summary.negativePercentLabel },
      { label: '数据来源', value: sentimentData.summary.sourceLabel },
    ],
    [sentimentData],
  );

  useEffect(() => {
    const controller = new AbortController();

    const loadSentimentData = async () => {
      setIsLoading(true);
      setError('');
      try {
        const [metadataPayload, sentimentPayload] = await Promise.all([
          fetchFilterMetadata(
            { tenantKey, jobId, startDate: date, endDate },
            { signal: controller.signal },
          ),
          fetchSentimentAnalysis(
            {
              tenantKey,
              jobId,
              timeframe,
              startDate: date,
              endDate: endDate || date,
              brand: brand || undefined,
              platform: selectedPlatform || undefined,
              keyword: selectedKeyword || undefined,
            },
            { signal: controller.signal },
          ),
        ]);

        if (metadataPayload?.code === 200 && metadataPayload.data) {
          setKeywords(metadataPayload.data.keywords || []);
        } else {
          setKeywords([]);
        }

        if (sentimentPayload?.status && sentimentPayload.status !== 'success') {
          throw new Error('情感分析接口返回错误状态');
        }

        setSentimentData(normalizeSentimentAnalysis(sentimentPayload));
      } catch (err) {
        if (controller.signal.aborted || err?.name === 'AbortError') return;
        setKeywords([]);
        setSentimentData(normalizeSentimentAnalysis());
        setError(err?.message || '情感分析数据加载失败');
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    };

    loadSentimentData();

    return () => {
      controller.abort();
    };
  }, [
    brand,
    date,
    endDate,
    jobId,
    selectedKeyword,
    selectedPlatform,
    tenantKey,
    timeframe,
  ]);

  return (
    <div className="flex min-h-[calc(100vh-112px)] w-full flex-col gap-6">
      <KeywordSection
        keywords={keywords}
        loading={isLoading}
        selectedKeyword={selectedKeyword}
        onKeywordChange={setSelectedKeyword}
      />
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
            {sentimentData.summary.source === 'metric_snapshot' ? (
              <span className="text-muted-foreground">
                指标生成：
                <strong className="font-medium text-foreground">
                  {sentimentData.summary.generatedAtLabel}
                </strong>
              </span>
            ) : null}
          </div>
        </CardHeader>
        <CardContent className="grid flex-1 gap-6 lg:grid-cols-[1fr_0.8fr]">
          {isLoading ? (
            <div className="grid min-h-80 place-items-center lg:col-span-2">
              <LoadingSpinner text="正在加载情感分析数据..." />
            </div>
          ) : sentimentData.hasData ? (
            <>
              <div className="flex min-h-80 items-center justify-center">
                <SentimentDonut
                  distribution={sentimentData.distribution}
                  sampleCount={sentimentData.summary.sampleCount}
                />
              </div>
              <WordCloud words={sentimentData.wordCloud} />
            </>
          ) : (
            <div className="grid min-h-80 place-items-center lg:col-span-2">
              <EmptyState
                title="暂无真实情感数据"
                description="等待分析运行生成情感事实，或调整品牌、平台、关键词和时间范围后重试。"
                icon={Smile}
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
