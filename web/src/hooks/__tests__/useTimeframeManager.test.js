import test from 'node:test';
import assert from 'node:assert/strict';

import {
  getLatestAvailableDate,
  getLatestAvailableDateParams,
  getNormalizedDateRange,
  getSelectedDateParams,
  normalizeAvailableDates,
  shouldDisableCalendarDate,
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

test('manual calendar selection is not locked to available dates by default', () => {
  const availableDates = ['2026-02-12'];

  assert.equal(shouldDisableCalendarDate('2026-05-18', availableDates), false);
  assert.equal(
    shouldDisableCalendarDate('2026-05-18', availableDates, { restrictToAvailableDates: true }),
    true,
  );
});

test('latest available date seeds default specific-day params when timeframe is not explicit', () => {
  assert.deepEqual(getLatestAvailableDateParams('2026-02-12'), {
    timeframe: 'specific_day',
    start_date: '20260212',
    end_date: '20260212',
  });
  assert.equal(getLatestAvailableDateParams(''), null);
});
