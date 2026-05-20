export const hasPlatformAdminRole = (user) =>
  Array.isArray(user?.platformRoles) && user.platformRoles.includes('platform_admin');

export const getPlatformAccessState = ({ isInitializing = false, isAuthenticated = false, user = null }) => {
  if (isInitializing) return 'loading';
  if (!isAuthenticated) return 'login';
  return hasPlatformAdminRole(user) ? 'allowed' : 'forbidden';
};
