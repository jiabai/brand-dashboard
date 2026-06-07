import assert from 'node:assert/strict';
import test from 'node:test';

import { normalizeSentimentAnalysis } from '../sentimentAnalysis.js';

test('normalizeSentimentAnalysis maps backend sentiment rows for presentation', () => {
  const result = normalizeSentimentAnalysis({
    data: {
      distribution: [
        { sentiment_status: 'positive', answer_count: 7, ratio: 0.4667 },
        { sentiment_status: 'negative', answer_count: 5, ratio: 0.3333 },
      ],
      keywords: [
        {
          keyword: 'math',
          platform: 'deepseek',
          brand: 'Brand A',
          sentiment_status: 'positive',
          answer_count: 6,
          ratio: 0.6,
        },
      ],
    },
    metadata: {
      data_source: 'metric_snapshot',
      sample_count: 15,
      metric_generated_at: '2026-06-07T11:30:00+08:00',
    },
  });

  assert.equal(result.hasData, true);
  assert.equal(result.summary.sampleCount, 15);
  assert.equal(result.summary.sourceLabel, '指标快照');
  assert.equal(result.distribution[0].sentimentStatus, 'positive');
  assert.equal(result.distribution[0].label, '正向');
  assert.equal(result.distribution[0].percentLabel, '46.67%');
  assert.equal(result.wordCloud[0].text, 'math');
  assert.equal(result.wordCloud[0].sentiment, 'positive');
  assert.equal(result.wordCloud[0].value, 6);
});

test('normalizeSentimentAnalysis returns an honest empty state for missing data', () => {
  const result = normalizeSentimentAnalysis({
    data: { distribution: [], keywords: [] },
    metadata: { data_source: 'empty', sample_count: 0 },
  });

  assert.equal(result.hasData, false);
  assert.equal(result.summary.sampleCount, 0);
  assert.equal(result.summary.sourceLabel, '暂无真实数据');
  assert.deepEqual(result.distribution, []);
  assert.deepEqual(result.wordCloud, []);
});
