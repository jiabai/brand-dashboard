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

export const formatPercentage = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return '0%';
  const rounded = Math.round(num * 100) / 100;
  return `${rounded.toFixed(2)}%`;
};
