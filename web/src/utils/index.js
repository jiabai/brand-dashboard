/**
 * 工具函数和常量定义
 */

import dayjs from 'dayjs';

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

// 平台颜色配置（与后端 api/v1/routes/dashboard.py 保持一致）
export const PLATFORM_COLORS = {
  chatgpt: '#10b981',
  gemini: '#3b82f6',
  claude: '#f59e0b',
  '通义千问': '#ef4444',
  qwen: '#ef4444',
  '豆包': '#8b5cf6',
  doubao: '#8b5cf6',
  deepseek: '#06b6d4',
  kimi: '#a855f7',
  '元宝': '#f97316',
  yuanbao: '#f97316',
  '夸克': '#ec4899',
  quark: '#ec4899',
  '文心一言': '#6b7280',
  ernie: '#6b7280',
  'ernie bot': '#6b7280',
};

/**
 * 获取平台的显示颜色
 * @param {string} name - 平台名称
 * @returns {string} 颜色十六进制值
 */
export const getPlatformColor = (name) => {
  const raw = String(name || '').trim();
  if (!raw) return '#6b7280';
  const keyLower = raw.toLowerCase();
  return PLATFORM_COLORS[keyLower] || PLATFORM_COLORS[raw] || '#6b7280';
};

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


export const toPercent = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return 0;
  return num <= 1 ? num * 100 : num;
};

export const toFraction = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return 0;
  if (num <= 1) return num;
  return num / 100;
};

export const clampPercent = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return 0;
  return Math.max(0, Math.min(100, num));
};

export const roundTwoDecimals = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return 0;
  return Math.round(num * 100) / 100;
};

export const buildQueryString = (params) => {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null) return;
    if (String(value).trim() === '') return;
    searchParams.set(key, String(value));
  });
  return searchParams.toString();
};

export const fetchJson = async (url, { signal, method = 'GET', body } = {}) => {
  const options = { method, signal };
  if (body) {
    options.headers = { 'Content-Type': 'application/json' };
    options.body = typeof body === 'string' ? body : JSON.stringify(body);
  }
  const response = await fetch(url, options);
  if (!response.ok) {
    let detail = '';
    try {
      const text = await response.text();
      if (text) {
        try {
          const parsed = JSON.parse(text);
          detail = parsed?.detail ? `: ${parsed.detail}` : `: ${text}`;
        } catch {
          detail = `: ${text}`;
        }
      }
    } catch {
      detail = '';
    }
    throw new Error(`请求失败(${response.status})${detail}`);
  }
  return response.json();
};

export const postJson = (url, body, { signal } = {}) =>
  fetchJson(url, { method: 'POST', body, signal });

export const normalizeListValue = (value) => {
  if (Array.isArray(value)) {
    return value.map((item) => String(item || '').trim()).filter(Boolean);
  }
  const text = String(value || '');
  if (!text) return [];
  return text.split(',').map((item) => item.trim()).filter(Boolean);
};

export const parseDateInput = (value) => {
  if (!value) return null;
  const text = String(value);
  if (/^\d{8}$/.test(text)) {
    const parsed = dayjs(text, 'YYYYMMDD');
    return parsed.isValid() ? parsed : null;
  }
  const parsed = dayjs(text);
  return parsed.isValid() ? parsed : null;
};

export const formatDateParam = (value) => {
  if (!value) return '';
  const parsed = dayjs.isDayjs(value) ? value : dayjs(value);
  if (!parsed.isValid()) return '';
  return parsed.format('YYYYMMDD');
};

export const formatDateDisplay = (value) => {
  if (!value) return '';
  const parsed = dayjs.isDayjs(value) ? value : dayjs(value);
  if (!parsed.isValid()) return '';
  return parsed.format('YYYY-MM-DD');
};

export const getRangeByTimeframe = (timeframe, dateParam) => {
  const today = dayjs();
  if (timeframe === 'yesterday') {
    const yesterday = today.subtract(1, 'day');
    return { startDate: yesterday, endDate: yesterday };
  }
  if (timeframe === 'specific_day') {
    const parsed = parseDateInput(dateParam);
    const day = parsed || today;
    return { startDate: day, endDate: day };
  }
  const days = timeframe === '30days' ? 30 : 7;
  return {
    startDate: today.subtract(days - 1, 'day'),
    endDate: today,
  };
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
