import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { normalizeMetricSnapshotMetadata } from '../metricSnapshotMetadata.js';

describe('metricSnapshotMetadata', () => {
  it('normalizes available snapshot freshness, coverage, and completeness', () => {
    const result = normalizeMetricSnapshotMetadata({
      data_source: 'metric_snapshot',
      snapshot_status: 'available',
      metric_generated_at: '2026-06-07T11:30:00+08:00',
      metric_coverage_rate: 0.8,
      metric_expected_task_count: 5,
      metric_succeeded_task_count: 4,
      metric_failed_task_count: 1,
      metric_analyzed_answer_count: 12,
    });

    assert.equal(result.hasSnapshot, true);
    assert.equal(result.sourceLabel, '指标快照');
    assert.equal(result.generatedAtLabel, '2026-06-07 11:30');
    assert.equal(result.coverageLabel, '80.00%');
    assert.equal(result.analysisCompletenessLabel, '成功 4 / 预期 5，失败 1');
    assert.equal(result.analyzedAnswerLabel, '12 条回答');
  });

  it('uses honest fallback labels when the snapshot is missing', () => {
    const result = normalizeMetricSnapshotMetadata({
      data_source: 'legacy_aggregation',
      snapshot_status: 'missing',
    });

    assert.equal(result.hasSnapshot, false);
    assert.equal(result.sourceLabel, '明细聚合');
    assert.equal(result.generatedAtLabel, '快照未生成');
    assert.equal(result.coverageLabel, '覆盖率待生成');
    assert.equal(result.analysisCompletenessLabel, '等待指标快照');
    assert.match(result.description, /当前数据来自历史明细聚合/);
  });
});
