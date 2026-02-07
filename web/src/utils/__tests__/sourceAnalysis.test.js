import test from 'node:test';
import assert from 'node:assert/strict';

const loadModule = async () => {
  try {
    return await import('../sourceAnalysis.js');
  } catch (error) {
    assert.fail(`无法加载 sourceAnalysis.js: ${error.message}`);
  }
};

test('normalizeCitationTypeStats 返回汇总与前五条类型占比', async () => {
  const { normalizeCitationTypeStats } = await loadModule();

  const payload = {
    summary: { total_rows: 1240, conversations: 356 },
    citation_type_stats: [
      { content_type: 'news', type_pct: 42.35 },
      { content_type: 'tech_review', type_pct: 28.19 },
      { content_type: 'gov_report', type_pct: 12.58 },
      { content_type: 'social_media', type_pct: 0.93 },
      { content_type: 'forum', type_pct: 5 },
      { content_type: 'blog', type_pct: 2.3 },
    ],
  };

  const result = normalizeCitationTypeStats(payload, { maxItems: 5 });

  assert.equal(result.summary.totalRows, 1240);
  assert.equal(result.summary.conversations, 356);
  assert.equal(result.stats.length, 5);
  assert.equal(result.stats[0].type, '新闻');
  assert.equal(result.stats[1].type, '科技评测');
  assert.equal(result.stats[2].type, '政府报告');
  assert.equal(result.stats[3].value, 0.93);
  assert.equal(result.stats[4].type, '论坛');
});
