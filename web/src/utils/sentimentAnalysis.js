import { formatMetricGeneratedAt } from './metricSnapshotMetadata.js';

export const SENTIMENT_STATUS_ORDER = ['positive', 'negative', 'neutral', 'unknown'];

export const SENTIMENT_STATUS_META = {
  positive: {
    label: '正向',
    chartLabel: '正面',
    color: 'var(--chart-2)',
    hexColor: '#059669',
  },
  negative: {
    label: '负向',
    chartLabel: '负面',
    color: 'var(--destructive)',
    hexColor: '#dc2626',
  },
  neutral: {
    label: '中性',
    chartLabel: '中性',
    color: 'var(--chart-4)',
    hexColor: '#475569',
  },
  unknown: {
    label: '未知',
    chartLabel: '未知',
    color: 'var(--muted-foreground)',
    hexColor: '#64748b',
  },
};

const SOURCE_LABELS = {
  metric_snapshot: '指标快照',
  legacy_fact: '分析明细',
  empty: '暂无真实数据',
};

const toNumber = (value, fallback = 0) => {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
};

const toCount = (value) => Math.max(0, Math.trunc(toNumber(value, 0)));

export const formatSentimentPercent = (value) => `${(toNumber(value, 0) * 100).toFixed(2)}%`;

const normalizeStatus = (value) => {
  const status = String(value || '').toLowerCase();
  return SENTIMENT_STATUS_META[status] ? status : 'unknown';
};

const sortBySentimentOrder = (items) => (
  [...items].sort((a, b) => (
    SENTIMENT_STATUS_ORDER.indexOf(a.sentimentStatus)
      - SENTIMENT_STATUS_ORDER.indexOf(b.sentimentStatus)
  ))
);

export const normalizeSentimentAnalysis = (payload = {}) => {
  const data = payload?.data || {};
  const metadata = payload?.metadata || {};
  const distributionRows = Array.isArray(data?.distribution) ? data.distribution : [];
  const keywordRows = Array.isArray(data?.keywords) ? data.keywords : [];
  const sampleCount = toCount(metadata?.sample_count);
  const source = metadata?.data_source || (sampleCount > 0 ? 'legacy_fact' : 'empty');

  const distribution = sortBySentimentOrder(
    distributionRows
      .map((item) => {
        const sentimentStatus = normalizeStatus(item?.sentiment_status);
        const meta = SENTIMENT_STATUS_META[sentimentStatus];
        const ratio = toNumber(item?.ratio, 0);
        return {
          sentimentStatus,
          label: meta.label,
          chartLabel: meta.chartLabel,
          answerCount: toCount(item?.answer_count),
          ratio,
          percentLabel: formatSentimentPercent(ratio),
          color: meta.color,
          hexColor: meta.hexColor,
        };
      })
      .filter((item) => item.answerCount > 0),
  );

  const wordCloud = keywordRows
    .map((item) => {
      const sentiment = normalizeStatus(item?.sentiment_status);
      const answerCount = toCount(item?.answer_count);
      return {
        text: item?.keyword || '--',
        value: answerCount,
        sentiment,
        platform: item?.platform || '--',
        brand: item?.brand || '--',
        ratio: toNumber(item?.ratio, 0),
        percentLabel: formatSentimentPercent(item?.ratio),
      };
    })
    .filter((item) => item.value > 0)
    .sort((a, b) => b.value - a.value || a.text.localeCompare(b.text));

  const positive = distribution.find((item) => item.sentimentStatus === 'positive');
  const negative = distribution.find((item) => item.sentimentStatus === 'negative');

  return {
    hasData: sampleCount > 0 && distribution.length > 0,
    distribution,
    wordCloud,
    summary: {
      sampleCount,
      sampleCountLabel: sampleCount.toLocaleString(),
      source,
      sourceLabel: SOURCE_LABELS[source] || '分析明细',
      generatedAtLabel: formatMetricGeneratedAt(metadata?.metric_generated_at),
      positivePercentLabel: positive?.percentLabel || '0.00%',
      negativePercentLabel: negative?.percentLabel || '0.00%',
      rowCount: toCount(metadata?.row_count),
    },
  };
};
