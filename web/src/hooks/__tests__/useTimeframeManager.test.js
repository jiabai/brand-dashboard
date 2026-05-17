import test from 'node:test';
import assert from 'node:assert/strict';

import {
  getLatestAvailableDate,
  getNormalizedDateRange,
  getSelectedDateParams,
  normalizeAvailableDates,
} from '../useTimeframeManager.js';

test('getNormalizedDateRange clamps an end date before the start date', () => {
  const { start, end } = getNormalizedDateRange('20260510', '20260508');

  assert.equal(start.format('YYYYMMDD'), '20260510');
  assert.equal(end.format('YYYYMMDD'), '20260510');
});

test('getSelectedDateParams only exposes dates for specific_day timeframe', () => {
  const range = getNormalizedDateRange('20260510', '20260512');

  assert.deepEqual(getSelectedDateParams('7days', range), {
    selectedDateParam: '',
    selectedEndDateParam: '',
  });
  assert.deepEqual(getSelectedDateParams('specific_day', range), {
    selectedDateParam: '20260510',
    selectedEndDateParam: '20260512',
  });
});

test('available dates are normalized and newest date is selected', () => {
  const dates = normalizeAvailableDates(['2026-05-10', '', '20260512', 'bad']);

  assert.deepEqual(dates, ['2026-05-10', '2026-05-12']);
  assert.equal(getLatestAvailableDate(dates), '2026-05-12');
});
