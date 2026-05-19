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

test('dashboard theme uses warm canvas and coral tokens instead of temporary purple/orange theme', () => {
  const css = readFileSync(join(webRoot, 'src', 'index.css'), 'utf8');

  assert.match(css, /--background:\s*#faf9f5;/);
  assert.match(css, /--primary:\s*#cc785c;/);
  assert.doesNotMatch(css, /#150c24|#0a0512|#241835|#312044|#722ED1|#722ed1|#fa8c16/i);
});

test('empty states stay compact for dashboard density', () => {
  const emptyState = readFileSync(join(webRoot, 'src', 'components', 'EmptyState.jsx'), 'utf8');

  assert.match(emptyState, /min-h-32/);
  assert.doesNotMatch(emptyState, /min-h-48|p-8|size-12/);
});

test('app does not force dark mode for the warm dashboard theme', () => {
  const app = readFileSync(join(webRoot, 'src', 'App.jsx'), 'utf8');

  assert.doesNotMatch(app, /document\.documentElement\.classList\.add\(['"]dark['"]\)/);
});

test('global CSS does not override component typography utilities', () => {
  const css = readFileSync(join(webRoot, 'src', 'index.css'), 'utf8');

  assert.doesNotMatch(css, /h[1-6]\s*\{[^}]*font-size/s);
  assert.doesNotMatch(css, /\*\s*,\s*\*::before\s*,\s*\*::after\s*\{[^}]*padding:\s*0/s);
  assert.doesNotMatch(css, /\.px-5\s*\{|\.flex\s*\{/);
});

test('specific day controls use native date inputs instead of offscreen calendar popovers', () => {
  const layout = readFileSync(join(webRoot, 'src', 'components', 'DashboardLayout.jsx'), 'utf8');

  assert.match(layout, /type="date"/);
  assert.doesNotMatch(layout, /<Calendar/);
  assert.doesNotMatch(layout, /PopoverTrigger|PopoverContent/);
});

test('dashboard content is not capped on wide desktop viewports', () => {
  const shellCss = readFileSync(join(webRoot, 'src', 'styles', 'app-shell.css'), 'utf8');

  assert.match(shellCss, /\.app-shell-content\s*\{[^}]*max-width:\s*none;/s);
  assert.doesNotMatch(shellCss, /\.app-shell-content\s*\{[^}]*max-width:\s*1[0-9]{3}px/s);
});

test('wide dashboard charts keep a bounded height instead of scaling by width', () => {
  const trend = readFileSync(join(webRoot, 'src', 'components', 'TrendAnalysis.jsx'), 'utf8');

  assert.match(trend, /h-\[360px\]/);
  assert.match(trend, /2xl:h-\[400px\]/);
  assert.doesNotMatch(trend, /min-w-\[720px\]/);
});

test('data tables keep readable density for desktop dashboards', () => {
  const table = readFileSync(join(webRoot, 'src', 'components', 'ui', 'table.jsx'), 'utf8');

  assert.match(table, /caption-bottom text-sm/);
  assert.match(table, /min-h-12/);
  assert.match(table, /px-4 py-2\.5/);
});
