import test from 'node:test';
import assert from 'node:assert/strict';

import { filterRows, paginateRows, sortRows } from '../DataTable.js';

const rows = [
  { id: 1, platform: 'Doubao', rate: 0.3 },
  { id: 2, platform: 'DeepSeek', rate: 0.8 },
  { id: 3, platform: 'Doubao', rate: 0.5 },
];

test('filterRows applies column filter predicates', () => {
  const result = filterRows(rows, {
    platform: {
      value: 'Doubao',
      onFilter: (value, record) => record.platform === value,
    },
  });

  assert.deepEqual(result.map((row) => row.id), [1, 3]);
});

test('sortRows toggles ascending and descending sort order', () => {
  const sorter = (a, b) => a.rate - b.rate;

  assert.deepEqual(sortRows(rows, { sorter, order: 'asc' }).map((row) => row.id), [1, 3, 2]);
  assert.deepEqual(sortRows(rows, { sorter, order: 'desc' }).map((row) => row.id), [2, 3, 1]);
});

test('paginateRows returns the requested page slice and page count', () => {
  const result = paginateRows(rows, { page: 2, pageSize: 2 });

  assert.deepEqual(result.rows.map((row) => row.id), [3]);
  assert.equal(result.pageCount, 2);
  assert.equal(result.page, 2);
});
