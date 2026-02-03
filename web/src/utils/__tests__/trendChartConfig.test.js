import assert from 'node:assert/strict';
import { buildTrendChartConfig } from '../trendChartConfig.js';

const trendData = [
  { dateLabel: '01-01', mentionRatePct: 10, deltaPct: 1 },
];

const token = {
  colorPrimary: '#111111',
  colorSuccess: '#22c55e',
  colorError: '#ef4444',
  colorTextSecondary: '#6b7280',
};

const config = buildTrendChartConfig(trendData, token);

assert.ok(config);
assert.ok(Array.isArray(config.children));
assert.equal(config.children.length, 2);
assert.equal(config.children[0].type, 'line');
assert.equal(config.children[1].type, 'interval');
assert.equal(config.xField, 'dateLabel');
