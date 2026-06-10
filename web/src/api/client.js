import { readAuthSession } from '../auth/storage.js';

const parseTenantKeyFromUrl = (url) => {
  try {
    const parsed = new URL(String(url), 'http://localhost');
    return parsed.searchParams.get('tenant_key') || '';
  } catch {
    return '';
  }
};

const parseTenantKeyFromBody = (body) => {
  if (!body || typeof body === 'string') return '';
  return body.tenant_key || body.tenantKey || '';
};

const buildHeaders = ({ url, body, headers, authToken, tenantKey, skipTenantHeader = false }) => {
  const session = readAuthSession();
  const nextHeaders = { ...(headers || {}) };
  const token = authToken ?? session?.accessToken;
  const requestTenantKey = skipTenantHeader
    ? ''
    : tenantKey ||
      parseTenantKeyFromBody(body) ||
      parseTenantKeyFromUrl(url) ||
      session?.currentTenantKey ||
      '';

  if (body && !nextHeaders['Content-Type']) {
    nextHeaders['Content-Type'] = 'application/json';
  }
  if (token && !nextHeaders.Authorization) {
    nextHeaders.Authorization = `Bearer ${token}`;
  }
  if (requestTenantKey && !nextHeaders['X-Tenant-Key']) {
    nextHeaders['X-Tenant-Key'] = requestTenantKey;
  }

  return nextHeaders;
};

export const fetchJson = async (
  url,
  { signal, method = 'GET', body, headers, authToken, tenantKey, skipTenantHeader = false } = {},
) => {
  const options = {
    method,
    signal,
    headers: buildHeaders({ url, body, headers, authToken, tenantKey, skipTenantHeader }),
  };
  if (body) {
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
          const message = parsed?.message || parsed?.detail;
          detail = message ? `: ${message}` : `: ${text}`;
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

export const postJson = (url, body, options = {}) =>
  fetchJson(url, { ...options, method: 'POST', body });
