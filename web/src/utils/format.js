import dayjs from 'dayjs';

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
