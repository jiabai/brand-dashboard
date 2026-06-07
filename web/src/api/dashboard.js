import { fetchJson as fetch } from './client.js';
import { buildQueryString } from '../utils/url.js';

export const fetchAvailableDates = ({ tenantKey, jobId }, options) => {
  const params = buildQueryString({ tenant_key: tenantKey, job_id: jobId });
  return fetch(`/api/v1/dashboard/available-dates?${params}`, options);
};

export const fetchBrandMetrics = ({ tenantKey, jobId, timeframe, startDate, endDate, platform }, options) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId,
    timeframe,
    start_date: timeframe === 'specific_day' ? startDate : undefined,
    end_date: timeframe === 'specific_day' ? endDate : undefined,
    platform,
  });
  return fetch(`/api/v1/dashboard/brand-metrics?${params}`, options);
};

export const fetchAnswerSnapshots = (
  {
    tenantKey,
    jobId,
    timeframe,
    startDate,
    endDate,
    brand,
    platform,
    keyword,
    sentiment,
    hasReference,
    limit,
    offset,
  },
  options,
) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId,
    timeframe,
    start_date: timeframe === 'specific_day' ? startDate : undefined,
    end_date: timeframe === 'specific_day' ? endDate : undefined,
    brand,
    platform,
    keyword,
    sentiment,
    has_reference: typeof hasReference === 'boolean' ? hasReference : undefined,
    limit,
    offset,
  });
  return fetch(`/api/v1/dashboard/answer-snapshots?${params}`, options);
};

export const fetchPostCitationRate = ({ tenantKey, jobId, timeframe, startDate, endDate, brand }, options) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId,
    timeframe,
    start_date: timeframe === 'specific_day' ? startDate : undefined,
    end_date: timeframe === 'specific_day' ? endDate : undefined,
    brand,
  });
  return fetch(`/api/v1/dashboard/post-citation-rate?${params}`, options);
};

export const fetchPlatformMetricsByBrand = ({ tenantKey, jobId, timeframe, startDate, endDate, brand }, options) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId,
    timeframe,
    start_date: timeframe === 'specific_day' ? startDate : undefined,
    end_date: timeframe === 'specific_day' ? endDate : undefined,
    brand,
  });
  return fetch(`/api/v1/dashboard/platform-metrics-by-brand?${params}`, options);
};

export const fetchKeywordPlatformBrandRates = ({ tenantKey, jobId, timeframe, startDate, endDate }, options) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId,
    timeframe,
    start_date: timeframe === 'specific_day' ? startDate : undefined,
    end_date: timeframe === 'specific_day' ? endDate : undefined,
  });
  return fetch(`/api/v1/dashboard/keyword-platform-brand-rates?${params}`, options);
};

export const fetchCitationDomainSummary = ({ tenantKey, jobId, brand, timeframe, startDate, endDate }, options) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId,
    brand,
    timeframe,
    start_date: timeframe === 'specific_day' ? startDate : undefined,
    end_date: timeframe === 'specific_day' ? endDate : undefined,
  });
  return fetch(`/api/v1/dashboard/citation-domain-summary?${params}`, options);
};

export const fetchFilterMetadata = ({ tenantKey, jobId, startDate, endDate }, options) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId,
    start_date: startDate,
    end_date: endDate,
  });
  return fetch(`/api/v1/dashboard/filter-metadata?${params}`, options);
};

export const fetchBrandMentionTrend = ({ tenantKey, jobId, brand, platform, keyword, timeframe, startDate, endDate }, options) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId,
    brand,
    platform,
    keyword,
    timeframe,
    start_date: startDate,
    end_date: endDate,
  });
  return fetch(`/api/v1/dashboard/brand-mention-trend?${params}`, options);
};

export const fetchCitationTypeStats = ({ tenantKey, jobId, brand, timeframe, startDate, endDate }, options) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId,
    brand,
    timeframe,
    start_date: timeframe === 'specific_day' ? startDate : undefined,
    end_date: timeframe === 'specific_day' ? endDate : undefined,
  });
  return fetch(`/api/v1/dashboard/citation-type-stats?${params}`, options);
};

export const fetchCitationDomainStats = (
  { tenantKey, jobId, brand, timeframe, startDate, endDate, keyword, platform },
  options,
) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId,
    brand,
    timeframe,
    start_date: timeframe === 'specific_day' ? startDate : undefined,
    end_date: timeframe === 'specific_day' ? endDate : undefined,
    keyword,
    platform,
  });
  return fetch(`/api/v1/dashboard/citation-domain-stats?${params}`, options);
};
