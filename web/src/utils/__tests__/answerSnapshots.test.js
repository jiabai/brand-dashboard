import test from 'node:test';
import assert from 'node:assert/strict';

import { normalizeAnswerSnapshots } from '../answerSnapshots.js';

test('normalizeAnswerSnapshots maps backend rows for table presentation', () => {
  const result = normalizeAnswerSnapshots({
    data: [
      {
        conversation_id: 'conv_ref',
        date: '20260607',
        platform: 'deepseek',
        brand: 'Brand A',
        keyword: 'math',
        query_content: '数学培训怎么选？',
        answer_content: 'Brand A 被正向推荐。',
        sentiment_status: 'positive',
        has_reference: true,
        reference_count: 2,
        references: [{ url: 'https://example.com/ref', domain: 'example.com' }],
      },
    ],
    metadata: { total_count: 1, row_count: 1 },
  });

  assert.equal(result.items.length, 1);
  assert.equal(result.items[0].id, 'conv_ref');
  assert.equal(result.items[0].dateLabel, '2026-06-07');
  assert.equal(result.items[0].sentimentLabel, '正向');
  assert.equal(result.items[0].referenceLabel, '2 条引用');
  assert.equal(result.items[0].hasReference, true);
  assert.equal(result.summary.totalCount, 1);
});

test('normalizeAnswerSnapshots keeps honest defaults for empty payloads', () => {
  const result = normalizeAnswerSnapshots(null);

  assert.deepEqual(result.items, []);
  assert.equal(result.summary.totalCount, 0);
  assert.equal(result.summary.rowCount, 0);
});
