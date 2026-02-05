const buildQueryString = (params) => {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null) return;
    searchParams.set(key, String(value));
  });
  return searchParams.toString();
};

export const buildDomainCitationQueryString = ({
  tenantKey,
  jobId,
  brand,
  timeframe,
  startDate,
  endDate,
}) =>
  buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId,
    brand,
    timeframe,
    start_date: timeframe === 'specific_day' ? startDate : undefined,
    end_date: timeframe === 'specific_day' ? endDate || startDate : undefined,
  });
