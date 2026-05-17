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

export const getPlatformColor = (name) => {
  const raw = String(name || '').trim();
  if (!raw) return '#6b7280';
  const keyLower = raw.toLowerCase();
  return PLATFORM_COLORS[keyLower] || PLATFORM_COLORS[raw] || '#6b7280';
};
