import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const sourcePath = resolve(__dirname, '../SentimentAnalysis.jsx');
const source = readFileSync(sourcePath, 'utf8');

describe('SentimentAnalysis real-data contract', () => {
  it('loads sentiment data through the dashboard API adapter', () => {
    assert.match(source, /fetchSentimentAnalysis/);
    assert.match(source, /normalizeSentimentAnalysis/);
    assert.doesNotMatch(source, /MOCK_SENTIMENT/);
    assert.doesNotMatch(source, /WORD_CLOUD_DATA/);
  });

  it('uses an explicit empty state when real sentiment data is unavailable', () => {
    assert.match(source, /暂无真实情感数据/);
    assert.match(source, /等待分析运行生成情感事实/);
  });
});
