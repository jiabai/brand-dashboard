import { buildViewPath } from '../utils/routing.js';
import { hasPlatformAdminRole } from './platformAccess.js';

export const getLoginRedirectTarget = ({
  location,
  session,
  tenantKey,
} = {}) => {
  const from = location?.state?.from;
  if (from?.pathname && from.pathname !== '/login') {
    return `${from.pathname}${from.search || ''}`;
  }

  if (hasPlatformAdminRole(session?.user)) {
    return '/platform/tenants';
  }

  if (!tenantKey) return '/login';

  return buildViewPath('projects', { tenantKey });
};
