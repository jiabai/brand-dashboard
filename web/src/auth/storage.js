const AUTH_STORAGE_KEY = 'brand-dashboard.auth.v1';

const getStorage = () => {
  try {
    return globalThis.localStorage || null;
  } catch {
    return null;
  }
};

const getActiveTenantKey = (tenants = []) => {
  const activeTenant = tenants.find((tenant) => tenant?.status === 'active') || tenants[0];
  return activeTenant?.tenantKey || '';
};

export const normalizeAuthSession = (payload = {}, preferredTenantKey = '') => {
  const user = payload.user || {};
  const tenants = Array.isArray(user.tenants) ? user.tenants : [];
  const tenantKeys = new Set(tenants.map((tenant) => tenant?.tenantKey).filter(Boolean));
  const currentTenantKey = tenantKeys.has(preferredTenantKey)
    ? preferredTenantKey
    : tenantKeys.has(payload.currentTenantKey)
      ? payload.currentTenantKey
      : getActiveTenantKey(tenants);

  return {
    accessToken: payload.accessToken || '',
    tokenType: payload.tokenType || 'Bearer',
    expiresIn: payload.expiresIn || null,
    user: {
      ...user,
      tenants,
      platformRoles: Array.isArray(user.platformRoles) ? user.platformRoles : [],
    },
    currentTenantKey,
  };
};

export const readAuthSession = () => {
  const storage = getStorage();
  if (!storage) return null;

  try {
    const raw = storage.getItem(AUTH_STORAGE_KEY);
    return raw ? normalizeAuthSession(JSON.parse(raw)) : null;
  } catch {
    return null;
  }
};

export const writeAuthSession = (session) => {
  const storage = getStorage();
  if (!storage) return normalizeAuthSession(session);

  const normalized = normalizeAuthSession(session, session?.currentTenantKey);
  storage.setItem(AUTH_STORAGE_KEY, JSON.stringify(normalized));
  return normalized;
};

export const updateCurrentTenantKey = (tenantKey) => {
  const current = readAuthSession();
  if (!current) return null;
  return writeAuthSession({ ...current, currentTenantKey: tenantKey });
};

export const clearAuthSession = () => {
  const storage = getStorage();
  if (storage) storage.removeItem(AUTH_STORAGE_KEY);
};
