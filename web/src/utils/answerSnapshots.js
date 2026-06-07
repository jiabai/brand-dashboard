export const ANSWER_SNAPSHOT_ALL_VALUE = '__all__';

export const ANSWER_SNAPSHOT_SENTIMENT_OPTIONS = [
  { label: '全部情绪', value: ANSWER_SNAPSHOT_ALL_VALUE },
  { label: '正向', value: 'positive' },
  { label: '中性', value: 'neutral' },
  { label: '负向', value: 'negative' },
  { label: '未知', value: 'unknown' },
];

export const ANSWER_SNAPSHOT_REFERENCE_OPTIONS = [
  { label: '全部引用状态', value: ANSWER_SNAPSHOT_ALL_VALUE },
  { label: '有引用', value: 'referenced' },
  { label: '无引用', value: 'unreferenced' },
];

const sentimentLabelMap = Object.fromEntries(
  ANSWER_SNAPSHOT_SENTIMENT_OPTIONS
    .filter((option) => option.value !== ANSWER_SNAPSHOT_ALL_VALUE)
    .map((option) => [option.value, option.label]),
);

export const getAnswerSnapshotSentimentLabel = (value) => (
  sentimentLabelMap[value] || '未知'
);

export const getAnswerSnapshotReferenceLabel = (count) => {
  const referenceCount = Number(count) || 0;
  return referenceCount > 0 ? `${referenceCount} 条引用` : '无引用';
};

export const formatAnswerSnapshotDate = (value) => {
  const text = String(value ?? '').trim();
  if (!text) return '--';
  if (/^\d{8}$/.test(text)) {
    return `${text.slice(0, 4)}-${text.slice(4, 6)}-${text.slice(6, 8)}`;
  }
  return text.slice(0, 10);
};

export const normalizeAnswerSnapshots = (payload) => {
  const rows = Array.isArray(payload?.data) ? payload.data : [];
  const metadata = payload?.metadata || {};

  return {
    items: rows.map((item, index) => {
      const referenceCount = Number(item?.reference_count ?? 0);
      return {
        id: item?.conversation_id || `answer-snapshot-${index}`,
        conversationId: item?.conversation_id || '',
        date: item?.date || '',
        dateLabel: formatAnswerSnapshotDate(item?.date),
        platform: item?.platform || '--',
        brand: item?.brand || '--',
        keyword: item?.keyword || '--',
        queryContent: item?.query_content || '',
        answerContent: item?.answer_content || '',
        sentimentStatus: item?.sentiment_status || 'unknown',
        sentimentLabel: getAnswerSnapshotSentimentLabel(item?.sentiment_status),
        isMentioned: Boolean(item?.is_mentioned),
        hasReference: Boolean(item?.has_reference),
        referenceCount,
        referenceLabel: getAnswerSnapshotReferenceLabel(referenceCount),
        references: Array.isArray(item?.references) ? item.references : [],
      };
    }),
    summary: {
      rowCount: Number(metadata?.row_count ?? rows.length) || 0,
      totalCount: Number(metadata?.total_count ?? rows.length) || 0,
      limit: Number(metadata?.limit ?? rows.length) || rows.length,
      offset: Number(metadata?.offset ?? 0) || 0,
    },
  };
};
