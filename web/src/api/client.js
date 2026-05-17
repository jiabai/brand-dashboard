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
