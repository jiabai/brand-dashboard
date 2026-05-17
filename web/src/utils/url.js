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

export const buildQueryString = (params) => {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null) return;
    if (String(value).trim() === '') return;
    searchParams.set(key, String(value));
  });
  return searchParams.toString();
};
