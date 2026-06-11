export const hasPlatformAdminRole = (user) =>
  Array.isArray(user?.platformRoles) && user.platformRoles.includes('platform_admin');

export const hasTenantMembership = (user, tenantKey) => {
  const normalizedTenantKey = String(tenantKey || '').trim();
  if (!normalizedTenantKey) return false;
  return Array.isArray(user?.tenants) && user.tenants.some(
    (tenant) => tenant?.tenantKey === normalizedTenantKey,
  );
};

export const isPlatformReadonlyTenantAccess = ({ user, tenantKey } = {}) =>
  hasPlatformAdminRole(user) && Boolean(String(tenantKey || '').trim());

export const getPlatformAccessState = ({ isInitializing = false, isAuthenticated = false, user = null }) => {
  if (isInitializing) return 'loading';
  if (!isAuthenticated) return 'login';
  return hasPlatformAdminRole(user) ? 'allowed' : 'forbidden';
};
