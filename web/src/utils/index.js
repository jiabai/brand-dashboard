/**
 * 工具函数和常量定义
 */

// 默认数据
export const DEFAULT_BRAND_DATA = {
  mentionRate: 69.1,
  rank: 2,
  change: 2.3,
  totalBrands: 10
};

export const DEFAULT_PLATFORM_DATA = [
  { name: 'GPT-4', rate: 22.5 },
  { name: 'Claude', rate: 18.3 },
  { name: 'Gemini', rate: 15.7 },
  { name: 'Ernie Bot', rate: 12.8 },
  { name: 'Qwen', rate: 10.2 },
  { name: 'LLaMA', rate: 8.9 }
];

export const DEFAULT_REFERENCES_DATA = [
  { rank: 1, domain: 'openai.com', visibility: 85.5 },
  { rank: 2, domain: 'wikipedia.org', visibility: 72.3 },
  { rank: 3, domain: 'github.com', visibility: 68.7 },
  { rank: 4, domain: 'stackoverflow.com', visibility: 55.2 },
  { rank: 5, domain: 'medium.com', visibility: 48.9 },
  { rank: 6, domain: 'reddit.com', visibility: 42.1 },
  { rank: 7, domain: 'arxiv.org', visibility: 38.5 },
  { rank: 8, domain: 'huggingface.co', visibility: 35.2 }
];

// 工具函数
export const formatPercentage = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return '0%';
  // 处理浮点数精度问题并保留两位小数
  const rounded = Math.round(num * 100) / 100;
  return `${rounded.toFixed(2)}%`;
};

/**
 * 从 URL 参数中获取指定 key 的值
 * @param {string} key - 参数名
 * @param {string} defaultValue - 默认值
 * @returns {string} 参数值
 */
export const getQueryParam = (key, defaultValue = '') => {
  const params = new URLSearchParams(window.location.search);
  return params.get(key) || defaultValue;
};

export const updateQueryParams = (params) => {
  const url = new URL(window.location.href);
  Object.entries(params).forEach(([key, value]) => {
    if (value === null || value === undefined || value === '') {
      url.searchParams.delete(key);
    } else {
      url.searchParams.set(key, String(value));
    }
  });
  window.history.pushState({}, '', url);
};


// 数据验证函数
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
