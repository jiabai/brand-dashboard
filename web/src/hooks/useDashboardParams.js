import { useCallback, useMemo } from 'react';
import { useOutletContext, useParams, useSearchParams } from 'react-router-dom';

import { CONFIG } from '../config.js';

export const DEFAULT_TIMEFRAME = '30days';

export const resolveRouteParam = (value, fallback, placeholderValues = []) => {
  const normalized = String(value || '').trim();
  if (!normalized) return fallback;
  return placeholderValues.includes(normalized) ? fallback : normalized;
};

/**
 * @returns {{
 *   tenantKey: string,
 *   jobId: string,
 *   brand: string,
 *   timeframe: string,
 *   startDateParam: string,
 *   endDateParam: string,
 *   selectedPlatform: string,
 *   executorId: string,
 *   includeDeleted: string,
 *   searchParams: URLSearchParams,
 *   updateParams: (updates: Record<string, unknown>, options?: { replace?: boolean }) => void
 * }}
 */
export const useDashboardParams = () => {
  const routeParams = useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  const tenantKey = resolveRouteParam(
    routeParams.tenantKey,
    '',
    ['default'],
  );
  const jobId = resolveRouteParam(
    routeParams.jobId,
    '',
    ['latest'],
  );
  const brand = searchParams.get('brand') || '';
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

export const useDashboardRequestParams = (overrides = {}) => {
  const dashboardParams = useDashboardParams();
  const outletContext = useOutletContext() || {};

  const timeframe = overrides.timeframe ?? outletContext.timeframe ?? dashboardParams.timeframe;
  const startDate =
    overrides.startDate ??
    overrides.date ??
    outletContext.selectedDateParam ??
    (timeframe === 'specific_day' ? dashboardParams.startDateParam : '');
  const endDate =
    overrides.endDate ??
    outletContext.selectedEndDateParam ??
    (timeframe === 'specific_day'
      ? dashboardParams.endDateParam || dashboardParams.startDateParam
      : '');

  return {
    ...dashboardParams,
    ...outletContext,
    tenantKey: overrides.tenantKey ?? outletContext.tenantKey ?? dashboardParams.tenantKey,
    jobId: overrides.jobId ?? outletContext.jobId ?? dashboardParams.jobId,
    brand: overrides.brand ?? outletContext.brand ?? dashboardParams.brand,
    timeframe,
    date: startDate,
    startDate,
    endDate,
    selectedDateParam: startDate,
    selectedEndDateParam: endDate,
    selectedPlatform: overrides.selectedPlatform ?? outletContext.selectedPlatform ?? dashboardParams.selectedPlatform,
  };
};

export default useDashboardParams;
