import { fetchJson as fetch, postJson as post } from './client.js';
import { buildQueryString } from '../utils/url.js';

export const fetchAvailableDates = ({ tenantKey, jobId }) => {
  const params = buildQueryString({ tenant_key: tenantKey, job_id: jobId });
  return fetch(`/api/v1/dashboard/available-dates?${params}`);
};

export const fetchBrandMetrics = ({ tenantKey, jobId, timeframe, startDate, endDate }) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId,
    timeframe,
    start_date: timeframe === 'specific_day' ? startDate : undefined,
    end_date: timeframe === 'specific_day' ? endDate : undefined,
  });
  return fetch(`/api/v1/dashboard/brand-metrics?${params}`);
};

export const fetchPostCitationRate = ({ tenantKey, jobId, timeframe, startDate, endDate, brand }) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId,
    timeframe,
    start_date: timeframe === 'specific_day' ? startDate : undefined,
    end_date: timeframe === 'specific_day' ? endDate : undefined,
    brand,
  });
  return fetch(`/api/v1/dashboard/post-citation-rate?${params}`);
};

export const fetchPlatformMetricsByBrand = ({ tenantKey, jobId, timeframe, startDate, endDate, brand }) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId,
    timeframe,
    start_date: timeframe === 'specific_day' ? startDate : undefined,
    end_date: timeframe === 'specific_day' ? endDate : undefined,
    brand,
  });
  return fetch(`/api/v1/dashboard/platform-metrics-by-brand?${params}`);
};

export const fetchKeywordPlatformBrandRates = ({ tenantKey, jobId, timeframe, startDate, endDate }) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId,
    timeframe,
    start_date: timeframe === 'specific_day' ? startDate : undefined,
    end_date: timeframe === 'specific_day' ? endDate : undefined,
  });
  return fetch(`/api/v1/dashboard/keyword-platform-brand-rates?${params}`);
};

export const fetchCitationDomainSummary = ({ tenantKey, jobId, brand, timeframe, startDate, endDate }) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId,
    brand,
    timeframe,
    start_date: timeframe === 'specific_day' ? startDate : undefined,
    end_date: timeframe === 'specific_day' ? endDate : undefined,
  });
  return fetch(`/api/v1/dashboard/citation-domain-summary?${params}`);
};

export const fetchFilterMetadata = ({ tenantKey, jobId, startDate, endDate }) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId,
    start_date: startDate,
    end_date: endDate,
  });
  return fetch(`/api/v1/dashboard/filter-metadata?${params}`);
};

export const fetchBrandMentionTrend = ({ tenantKey, jobId, brand, platform, keyword, timeframe, startDate, endDate }) => {
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
  return fetch(`/api/v1/dashboard/brand-mention-trend?${params}`);
};

export const fetchCitationTypeStats = ({ tenantKey, jobId, brand, timeframe, startDate, endDate }) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId,
    brand,
    timeframe,
    start_date: timeframe === 'specific_day' ? startDate : undefined,
    end_date: timeframe === 'specific_day' ? endDate : undefined,
  });
  return fetch(`/api/v1/dashboard/citation-type-stats?${params}`);
};

export const fetchCitationDomainStats = ({ tenantKey, jobId, brand, timeframe, startDate, endDate }) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId,
    brand,
    timeframe,
    start_date: timeframe === 'specific_day' ? startDate : undefined,
    end_date: timeframe === 'specific_day' ? endDate : undefined,
  });
  return fetch(`/api/v1/dashboard/citation-domain-stats?${params}`);
};
