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
  chatgpt: 'var(--chart-4)',
  gemini: 'var(--chart-2)',
  claude: 'var(--chart-1)',
  '通义千问': 'var(--chart-5)',
  qwen: 'var(--chart-5)',
  '豆包': 'var(--chart-3)',
  doubao: 'var(--chart-3)',
  deepseek: 'var(--chart-2)',
  kimi: 'var(--chart-8)',
  '元宝': 'var(--chart-3)',
  yuanbao: 'var(--chart-3)',
  '夸克': 'var(--chart-1)',
  quark: 'var(--chart-1)',
  '文心一言': 'var(--chart-10)',
  ernie: 'var(--chart-10)',
  'ernie bot': 'var(--chart-10)',
};

export const getPlatformColor = (name) => {
  const raw = String(name || '').trim();
  if (!raw) return 'var(--chart-10)';
  const keyLower = raw.toLowerCase();
  return PLATFORM_COLORS[keyLower] || PLATFORM_COLORS[raw] || 'var(--chart-10)';
};
