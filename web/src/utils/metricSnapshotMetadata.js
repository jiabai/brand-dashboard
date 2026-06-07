const toFiniteNumber = (value) => {
  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : null;
};

const toCount = (value) => {
  const numericValue = toFiniteNumber(value);
  return numericValue === null ? null : Math.max(0, Math.trunc(numericValue));
};

export const formatMetricGeneratedAt = (value) => {
  const text = String(value ?? '').trim();
  if (!text) return '快照未生成';

  return text
    .replace('T', ' ')
    .replace(/\.\d+/, '')
    .replace(/(?:Z|[+-]\d{2}:?\d{2})$/, '')
    .trim()
    .slice(0, 16);
};

export const formatMetricCoverageRate = (value) => {
  const numericValue = toFiniteNumber(value);
  if (numericValue === null) return '覆盖率待生成';

  const percentValue = numericValue <= 1 ? numericValue * 100 : numericValue;
  return `${percentValue.toFixed(2)}%`;
};

const formatAnalysisCompleteness = ({ expected, succeeded, failed }) => {
  if (expected === null && succeeded === null && failed === null) {
    return '等待指标快照';
  }

  if (expected !== null && succeeded !== null) {
    const failedLabel = failed === null ? 0 : failed;
    return `成功 ${succeeded} / 预期 ${expected}，失败 ${failedLabel}`;
  }

  if (succeeded !== null) return `成功 ${succeeded}`;
  if (expected !== null) return `预期 ${expected}`;
  return `失败 ${failed ?? 0}`;
};

const formatAnalyzedAnswerCount = (value) => {
  const count = toCount(value);
  return count === null ? '回答数待生成' : `${count} 条回答`;
};

export const normalizeMetricSnapshotMetadata = (metadata = {}) => {
  const source = metadata?.data_source ?? 'legacy_aggregation';
  const snapshotStatus = metadata?.snapshot_status ?? 'missing';
  const hasSnapshot = source === 'metric_snapshot' && snapshotStatus !== 'missing';
  const expected = toCount(metadata?.metric_expected_task_count);
  const succeeded = toCount(metadata?.metric_succeeded_task_count);
  const failed = toCount(metadata?.metric_failed_task_count);

  return {
    hasSnapshot,
    source,
    snapshotStatus,
    sourceLabel: hasSnapshot ? '指标快照' : '明细聚合',
    generatedAtLabel: formatMetricGeneratedAt(metadata?.metric_generated_at),
    coverageLabel: formatMetricCoverageRate(metadata?.metric_coverage_rate),
    analysisCompletenessLabel: formatAnalysisCompleteness({ expected, succeeded, failed }),
    analyzedAnswerLabel: formatAnalyzedAnswerCount(metadata?.metric_analyzed_answer_count),
    description: hasSnapshot
      ? '指标来自最新分析快照，展示生成时间、采集覆盖率和分析完成情况。'
      : '当前数据来自历史明细聚合；指标快照生成后会补充覆盖率和新鲜度。',
  };
};
