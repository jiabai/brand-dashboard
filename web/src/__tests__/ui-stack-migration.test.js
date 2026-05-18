import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import test from 'node:test';
import assert from 'node:assert/strict';

const repoRoot = join(import.meta.dirname, '..', '..', '..');
const webRoot = join(repoRoot, 'web');
const legacyUi = ['a', 'n', 't', 'd'].join('');
const legacyIcons = ['@ant', '-design', '/icons'].join('');
const legacyReset = [legacyUi, 'dist', 'reset.css'].join('/');
const legacyChart = ['@antv', 'g2'].join('/');
const legacyProvider = ['Config', 'Provider'].join('');
const legacyMessage = ['message', 'useMessage'].join('.');

const bannedPatterns = [
  new RegExp(`from\\s+['"]${legacyUi}['"]`),
  new RegExp(`from\\s+['"]${legacyIcons.replace('/', '\\/')}['"]`),
  new RegExp(`import\\s+['"]${legacyReset.replaceAll('/', '\\/')}['"]`),
  new RegExp(legacyChart.replace('/', '\\/')),
  /theme\.useToken/,
  new RegExp(legacyProvider),
  new RegExp(legacyMessage.replace('.', '\\.')),
];

const scanTargets = [
  join(webRoot, 'src'),
  join(webRoot, 'package.json'),
  join(webRoot, 'vite.config.js'),
];

const ignoredDirs = new Set(['dist', 'node_modules']);
const ignoredFiles = new Set([join(webRoot, 'src', '__tests__', 'ui-stack-migration.test.js')]);

function collectFiles(path) {
  const stat = statSync(path);

  if (stat.isFile()) {
    if (ignoredFiles.has(path)) return [];
    return [path];
  }

  return readdirSync(path).flatMap((entry) => {
    if (ignoredDirs.has(entry)) return [];
    return collectFiles(join(path, entry));
  });
}

test('web UI stack no longer imports legacy UI or chart runtime dependencies', () => {
  const matches = scanTargets
    .flatMap(collectFiles)
    .flatMap((filePath) => {
      const content = readFileSync(filePath, 'utf8');
      return bannedPatterns
        .filter((pattern) => pattern.test(content))
        .map((pattern) => `${relative(repoRoot, filePath)} matches ${pattern}`);
    });

  assert.deepEqual(matches, []);
});

test('tailwind v4 entrypoint is used so responsive shadcn classes are generated', () => {
  const css = readFileSync(join(webRoot, 'src', 'index.css'), 'utf8');

  assert.match(css, /@import\s+["']tailwindcss["'];/);
  assert.doesNotMatch(css, /@tailwind\s+(base|components|utilities)\s*;/);
});
