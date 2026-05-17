import { useCallback, useMemo } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';

import { CONFIG } from '@/config';

const DEFAULT_TIMEFRAME = '30days';

export const useDashboardParams = () => {
  const routeParams = useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  const tenantKey =
    routeParams.tenantKey ||
    searchParams.get('tenant_key') ||
    CONFIG.DEFAULT_TENANT_KEY;
  const jobId =
    routeParams.jobId ||
    searchParams.get('job_id') ||
    CONFIG.DEFAULT_JOB_ID;
  const brand = searchParams.get('brand') || CONFIG.DEFAULT_BRAND;
  const timeframe = searchParams.get('timeframe') || DEFAULT_TIMEFRAME;
  const startDateParam = searchParams.get('start_date') || '';
  const endDateParam = searchParams.get('end_date') || '';
  const selectedPlatform = searchParams.get('platform') || '';
  const executorId = searchParams.get('executor_id') || CONFIG.DEFAULT_EXECUTOR_ID;
  const includeDeleted = searchParams.get('include_deleted') || CONFIG.DEFAULT_INCLUDE_DELETED;

  const updateParams = useCallback(
    (updates, options = {}) => {
      const { replace = false } = options;
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.delete('view');
        next.delete('tenant_key');
        next.delete('date');

        Object.entries(updates).forEach(([key, value]) => {
          if (value === null || value === undefined || value === '') {
            next.delete(key);
          } else {
            next.set(key, String(value));
          }
        });

        return next;
      }, { replace });
    },
    [setSearchParams],
  );

  return useMemo(
    () => ({
      tenantKey,
      jobId,
      brand,
      timeframe,
      startDateParam,
      endDateParam,
      selectedPlatform,
      executorId,
      includeDeleted,
      searchParams,
      updateParams,
    }),
    [
      tenantKey,
      jobId,
      brand,
      timeframe,
      startDateParam,
      endDateParam,
      selectedPlatform,
      executorId,
      includeDeleted,
      searchParams,
      updateParams,
    ],
  );
};

export default useDashboardParams;
