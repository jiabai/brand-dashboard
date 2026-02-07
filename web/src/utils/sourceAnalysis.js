const DEFAULT_TYPE_LABELS = {
  news: '新闻',
  tech_review: '科技评测',
  gov_report: '政府报告',
  ecommerce: '电商',
  qa: '问答百科',
  official_site: '官网',
  social_media: '社交媒体',
  forum: '论坛',
  blog: '博客',
  review: '评论',
};

const DEFAULT_TYPE_COLORS = {
  ecommerce: '#2582a1',
  news: '#f88c24',
  qa: '#c52125',
  official_site: '#87f4d0',
  social_media: '#a062d4',
  tech_review: '#2582a1',
  gov_report: '#87f4d0',
  forum: '#c52125',
  blog: '#f88c24',
  review: '#a062d4',
};

const FALLBACK_COLORS = ['#2582a1', '#f88c24', '#c52125', '#87f4d0', '#a062d4'];

const toPercent = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return 0;
  return num;
};

const roundTwoDecimals = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return 0;
  return Math.round(num * 100) / 100;
};

const resolveTypeLabel = (type) => {
  const key = String(type || '').trim();
  if (!key) return '未知';
  return DEFAULT_TYPE_LABELS[key] || key;
};

const resolveTypeColor = (type, index) => {
  const key = String(type || '').trim();
  if (DEFAULT_TYPE_COLORS[key]) return DEFAULT_TYPE_COLORS[key];
  return FALLBACK_COLORS[index % FALLBACK_COLORS.length];
};

export const normalizeCitationTypeStats = (payload, { maxItems = 5 } = {}) => {
  const summary = payload?.summary || {};
  const totalRows = Number(summary.total_rows ?? summary.totalRows ?? 0);
  const conversations = Number(summary.conversations ?? 0);
  const rawStats = Array.isArray(payload?.citation_type_stats)
    ? payload.citation_type_stats
    : [];

  const stats = rawStats.slice(0, maxItems).map((item, index) => {
    const rawType = item?.content_type ?? item?.contentType ?? '';
    const type = resolveTypeLabel(rawType);
    const value = roundTwoDecimals(toPercent(item?.type_pct ?? item?.typePct ?? 0));
    const color = resolveTypeColor(rawType, index);
    return { type, value, color };
  });

  return {
    summary: {
      totalRows: Number.isFinite(totalRows) ? totalRows : 0,
      conversations: Number.isFinite(conversations) ? conversations : 0,
    },
    stats,
  };
};
