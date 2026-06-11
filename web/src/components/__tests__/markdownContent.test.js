import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(resolve(__dirname, '../MarkdownContent.jsx'), 'utf8');

describe('MarkdownContent rendering contract', () => {
  it('uses react-markdown with remark-gfm', () => {
    assert.match(source, /from ['"]react-markdown['"]/);
    assert.match(source, /from ['"]remark-gfm['"]/);
    assert.match(source, /remarkPlugins=\{\[remarkGfm\]\}/);
  });

  it('does NOT enable raw HTML rendering', () => {
    assert.doesNotMatch(source, /from ['"]rehype-raw['"]/);
    assert.doesNotMatch(source, /rehypePlugins/);
    assert.doesNotMatch(source, /dangerouslySetInnerHTML/);
  });

  it('opens links safely in a new tab', () => {
    assert.match(source, /target=['"]_blank['"]/);
    assert.match(source, /rel=['"]noreferrer['"]/);
  });
});
