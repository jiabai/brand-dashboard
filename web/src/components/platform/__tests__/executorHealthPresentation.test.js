import test from 'node:test';
import assert from 'node:assert/strict';

import {
  getExecutorHealthMeta,
  normalizeCollectionHealthResponse,
} from '../executorHealthPresentation.js';

test('normalizes platform collection health response with stable defaults', () => {
  const response = {
    data: {
      summary: {
        executorCount: 2,
        activeExecutorCount: 1,
        failedTaskCount: 3,
      },
      executors: [{ executorId: 'exec_a', healthStatus: 'active' }],
      queues: [{ tenantKey: 'tn_a', pendingTaskCount: 2 }],
      failedTasks: [{ collectionTaskId: 'task_1', lastErrorMessage: 'timeout' }],
    },
  };

  assert.deepEqual(normalizeCollectionHealthResponse(response), {
    summary: {
      executorCount: 2,
      activeExecutorCount: 1,
      inactiveExecutorCount: 0,
      pendingTaskCount: 0,
      reservedTaskCount: 0,
      runningTaskCount: 0,
      failedTaskCount: 3,
      retryableFailedTaskCount: 0,
      expiredLeaseTaskCount: 0,
    },
    executors: [{ executorId: 'exec_a', healthStatus: 'active' }],
    queues: [{ tenantKey: 'tn_a', pendingTaskCount: 2 }],
    failedTasks: [{ collectionTaskId: 'task_1', lastErrorMessage: 'timeout' }],
  });

  assert.deepEqual(normalizeCollectionHealthResponse({}), {
    summary: {
      executorCount: 0,
      activeExecutorCount: 0,
      inactiveExecutorCount: 0,
      pendingTaskCount: 0,
      reservedTaskCount: 0,
      runningTaskCount: 0,
      failedTaskCount: 0,
      retryableFailedTaskCount: 0,
      expiredLeaseTaskCount: 0,
    },
    executors: [],
    queues: [],
    failedTasks: [],
  });
});

test('maps executor health status labels', () => {
  assert.deepEqual(getExecutorHealthMeta('active'), { label: '正常', variant: 'default' });
  assert.deepEqual(getExecutorHealthMeta('idle'), { label: '空闲', variant: 'secondary' });
  assert.deepEqual(getExecutorHealthMeta('inactive'), { label: '停用', variant: 'outline' });
  assert.deepEqual(getExecutorHealthMeta('error'), { label: '异常', variant: 'destructive' });
  assert.deepEqual(getExecutorHealthMeta('unknown'), { label: '未知', variant: 'outline' });
});
