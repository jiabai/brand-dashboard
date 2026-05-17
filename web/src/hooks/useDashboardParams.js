import { useCallback, useMemo } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';

import { CONFIG } from '@/config';

const DEFAULT_TIMEFRAME = '30days';

export const useDashboardParams = () => {
  const routeParams = useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  const tenantKey = routeParams.tenantKey || CONFIG.DEFAULT_TENANT_KEY;
  const jobId = routeParams.jobId || CONFIG.DEFAULT_JOB_ID;
  const brand = searchParams.get('brand') || CONFIG.DEFAULT_BRAND;
  const timeframe = searchParams.get('timeframe') || DEFAULT_TIMEFRAME;
  const startDateParam = searchParams.get('start_date') || '';
  const endDateParam = searchParams.get('end_date') || '';
  const selectedPlatform = searchParams.get('platform') || '';
  const updateParams = useCallback(
    (updates, options = {}) => {
      const { replace = false } = options;
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.delete('view');
        next.delete('tenant_key');
        next.delete('job_id');
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
      searchParams,
      updateParams,
    ],
  );
};

export default useDashboardParams;
