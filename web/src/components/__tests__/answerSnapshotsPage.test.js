import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const sourcePath = resolve(__dirname, '../AnswerSnapshotsPage.jsx');
const source = readFileSync(sourcePath, 'utf8');

describe('AnswerSnapshotsPage presentation contract', () => {
  it('renders the expected answer snapshot filters', () => {
    assert.match(source, /问答快照/);
    assert.match(source, /品牌/);
    assert.match(source, /平台/);
    assert.match(source, /关键词/);
    assert.match(source, /情绪/);
    assert.match(source, /引用状态/);
  });

  it('uses a non-misleading empty state', () => {
    assert.match(source, /当前筛选下没有问答快照/);
  });
});
