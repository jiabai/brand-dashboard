import dayjs from 'dayjs';

export const normalizeListValue = (value) => {
  if (Array.isArray(value)) {
    return value.map((item) => String(item || '').trim()).filter(Boolean);
  }
  const text = String(value || '');
  if (!text) return [];
  return text.split(',').map((item) => item.trim()).filter(Boolean);
};

export const buildQueryJobStatusRowKey = (record = {}, index = 0) => {
  const parts = [
    record.tenant_key,
    record.id,
    record.query_job_id,
    record.job_id,
    record.brand,
    record.query_content,
    record.effective_from,
    record.effective_to,
  ]
    .map((value) => String(value ?? '').trim())
    .filter(Boolean);

  return parts.length ? parts.join('::') : `query-job-${index}`;
};

export const getRangeByTimeframe = (timeframe, dateParam) => {
  const today = dayjs();
  if (timeframe === 'yesterday') {
    const yesterday = today.subtract(1, 'day');
    return { startDate: yesterday, endDate: yesterday };
  }
  if (timeframe === 'specific_day') {
    const parsed = dayjs(dateParam);
    const day = parsed && parsed.isValid() ? parsed : today;
    return { startDate: day, endDate: day };
  }
  const days = timeframe === '30days' ? 30 : 7;
  return {
    startDate: today.subtract(days - 1, 'day'),
    endDate: today,
  };
};

export const validateBrandData = (data) => {
  return data && 
    typeof data.mentionRate === 'number' &&
    typeof data.rank === 'number' &&
    typeof data.change === 'number';
};

export const validatePlatformData = (data) => {
  return Array.isArray(data) && data.every(item => 
    item.name && typeof item.rate === 'number'
  );
};

export const validateReferencesData = (data) => {
  return Array.isArray(data) && data.every(item => 
    item.rank && item.domain && typeof item.visibility === 'number'
  );
};
