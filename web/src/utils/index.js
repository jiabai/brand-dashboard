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

export const DEFAULT_MODEL_DATA = [
  { model: 'GPT-4', rate: 22.5 },
  { model: 'Claude', rate: 18.3 },
  { model: 'Gemini', rate: 15.7 },
  { model: 'Ernie Bot', rate: 12.8 },
  { model: 'Qwen', rate: 10.2 },
  { model: 'LLaMA', rate: 8.9 }
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
  return `${value}%`;
};


// 数据验证函数
export const validateBrandData = (data) => {
  return data && 
    typeof data.mentionRate === 'number' &&
    typeof data.rank === 'number' &&
    typeof data.change === 'number';
};

export const validateModelData = (data) => {
  return Array.isArray(data) && data.every(item => 
    item.model && typeof item.rate === 'number'
  );
};

export const validateReferencesData = (data) => {
  return Array.isArray(data) && data.every(item => 
    item.rank && item.domain && typeof item.visibility === 'number'
  );
};
