import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import dayjs from 'dayjs';

import { fetchAvailableDates } from '../api/index.js';
import { formatDateDisplay, formatDateParam, parseDateInput } from '../utils/index.js';

export const TIME_OPTIONS = [
  { label: '昨天', value: 'yesterday' },
  { label: '过去7天', value: '7days' },
  { label: '过去30天', value: '30days' },
  { label: '指定日期', value: 'specific_day' },
];

export const getNormalizedDateRange = (startDateParam, endDateParam, fallbackDate = dayjs()) => {
  const fallback = dayjs.isDayjs(fallbackDate) ? fallbackDate : dayjs(fallbackDate);
  const safeFallback = fallback.isValid() ? fallback : dayjs();
  const start = parseDateInput(startDateParam) || safeFallback;
  const rawEnd = parseDateInput(endDateParam) || start;
  const end = rawEnd.isBefore(start, 'day') ? start : rawEnd;
  return { start, end };
};

export const getSelectedDateParams = (timeframe, { start, end }) => {
  if (timeframe !== 'specific_day') {
    return {
      selectedDateParam: '',
      selectedEndDateParam: '',
    };
  }

  return {
    selectedDateParam: formatDateParam(start),
    selectedEndDateParam: formatDateParam(end),
  };
};

export const normalizeAvailableDates = (dates) =>
  (Array.isArray(dates) ? dates : [])
    .map((item) => formatDateDisplay(item))
    .filter(Boolean);

export const getLatestAvailableDate = (availableDates) => {
  if (!Array.isArray(availableDates) || !availableDates.length) return '';
  return availableDates.reduce((latest, current) => {
    if (!latest) return current;
    return dayjs(current).isAfter(dayjs(latest), 'day') ? current : latest;
  }, '');
};

export const getLatestAvailableDateParams = (latestAvailableDate) => {
  const latest = parseDateInput(latestAvailableDate);
  if (!latest) return null;

  const dateParam = formatDateParam(latest);
  return {
    timeframe: 'specific_day',
    start_date: dateParam,
    end_date: dateParam,
  };
};

export const shouldDisableCalendarDate = (
  current,
  availableDates,
  { restrictToAvailableDates = false } = {},
) => {
  if (!current || !restrictToAvailableDates) return false;
  if (!Array.isArray(availableDates) || availableDates.length === 0) return false;

  const normalized = dayjs.isDayjs(current)
    ? current.format('YYYY-MM-DD')
    : formatDateDisplay(current);
  if (!normalized) return false;

  return !new Set(availableDates).has(normalized);
};

export const useTimeframeManager = ({
  tenantKey,
  jobId,
  timeframe,
  startDateParam,
  endDateParam,
  updateParams,
  searchParams,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [availableDates, setAvailableDates] = useState([]);
  const loadingTimerRef = useRef(null);

  const { start, end } = useMemo(
    () => getNormalizedDateRange(startDateParam, endDateParam),
    [startDateParam, endDateParam],
  );

  const { selectedDateParam, selectedEndDateParam } = useMemo(
    () => getSelectedDateParams(timeframe, { start, end }),
    [end, start, timeframe],
  );

  const availableDateSet = useMemo(() => new Set(availableDates), [availableDates]);
  const latestAvailableDate = useMemo(
    () => getLatestAvailableDate(availableDates),
    [availableDates],
  );
  const hasExplicitTimeframe = searchParams?.has?.('timeframe') ?? false;

  const isDateDisabled = useCallback(
    (current) => {
      return shouldDisableCalendarDate(current, availableDates);
    },
    [availableDates],
  );

  useEffect(() => {
    if (!tenantKey) {
      setAvailableDates([]);
      return;
    }

    const controller = new AbortController();
    const run = async () => {
      const result = await fetchAvailableDates(
        { tenantKey, jobId },
        { signal: controller.signal },
      );
      setAvailableDates(normalizeAvailableDates(result?.data));
    };

    run().catch(() => {
      if (controller.signal.aborted) return;
      setAvailableDates([]);
    });

    return () => {
      controller.abort();
    };
  }, [tenantKey, jobId]);

  useEffect(() => {
    return () => {
      if (loadingTimerRef.current) {
        clearTimeout(loadingTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (timeframe !== 'specific_day') return;
    if (startDateParam && endDateParam && !end.isBefore(start, 'day')) return;
    updateParams(
      {
        start_date: selectedDateParam,
        end_date: selectedEndDateParam,
      },
      { replace: true },
    );
  }, [
    end,
    endDateParam,
    selectedDateParam,
    selectedEndDateParam,
    start,
    startDateParam,
    timeframe,
    updateParams,
  ]);

  useEffect(() => {
    if (hasExplicitTimeframe) return;
    if (timeframe === 'specific_day') return;
    const latestParams = getLatestAvailableDateParams(latestAvailableDate);
    if (!latestParams) return;

    updateParams(latestParams, { replace: true });
  }, [hasExplicitTimeframe, latestAvailableDate, timeframe, updateParams]);

  useEffect(() => {
    if (timeframe !== 'specific_day') return;
    if (!latestAvailableDate) return;
    const latest = dayjs(latestAvailableDate, 'YYYY-MM-DD');
    if (!latest.isValid()) return;

    const startKey = start.format('YYYY-MM-DD');
    const endKey = end.format('YYYY-MM-DD');
    const hasValidStart = availableDateSet.has(startKey);
    const hasValidEnd = availableDateSet.has(endKey);

    if (hasValidStart && hasValidEnd) return;

    updateParams(
      {
        start_date: formatDateParam(latest),
        end_date: formatDateParam(latest),
      },
      { replace: true },
    );
  }, [availableDateSet, end, latestAvailableDate, start, timeframe, updateParams]);

  const handleFilterChange = useCallback(
    (filter) => {
      if (loadingTimerRef.current) {
        clearTimeout(loadingTimerRef.current);
      }

      setIsLoading(true);
      loadingTimerRef.current = setTimeout(() => setIsLoading(false), 800);

      if (filter === 'specific_day') {
        const nextStart = parseDateInput(startDateParam) || parseDateInput(latestAvailableDate) || dayjs();
        const nextEnd = parseDateInput(endDateParam) || nextStart;
        const normalizedEnd = nextEnd.isBefore(nextStart, 'day') ? nextStart : nextEnd;
        updateParams({
          timeframe: filter,
          start_date: formatDateParam(nextStart),
          end_date: formatDateParam(normalizedEnd),
        });
        return;
      }

      updateParams({
        timeframe: filter,
        start_date: null,
        end_date: null,
      });
    },
    [endDateParam, latestAvailableDate, startDateParam, updateParams],
  );

  const handleStartDateChange = useCallback(
    (nextValue) => {
      const nextStart = nextValue || end || dayjs();
      const nextEnd = end && !end.isBefore(nextStart, 'day') ? end : nextStart;
      updateParams({
        timeframe: 'specific_day',
        start_date: formatDateParam(nextStart),
        end_date: formatDateParam(nextEnd),
      });
    },
    [end, updateParams],
  );

  const handleEndDateChange = useCallback(
    (nextValue) => {
      const nextEnd = nextValue || start || dayjs();
      const nextStart = start && !nextEnd.isBefore(start, 'day') ? start : nextEnd;
      updateParams({
        timeframe: 'specific_day',
        start_date: formatDateParam(nextStart),
        end_date: formatDateParam(nextEnd),
      });
    },
    [start, updateParams],
  );

  return {
    availableDates,
    end,
    handleEndDateChange,
    handleFilterChange,
    handleStartDateChange,
    isDateDisabled,
    isLoading,
    latestAvailableDate,
    selectedDateParam,
    selectedEndDateParam,
    start,
  };
};

export default useTimeframeManager;
