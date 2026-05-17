import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

import { CONFIG } from '@/config';
import { buildLegacyRedirectUrl } from '@/utils/routing';

const LegacyRedirect = () => {
  const location = useLocation();
  const redirectTo = buildLegacyRedirectUrl({
    search: location.search,
    defaults: {
      tenantKey: CONFIG.DEFAULT_TENANT_KEY,
      jobId: CONFIG.DEFAULT_JOB_ID,
    },
  });

  return <Navigate to={redirectTo} replace />;
};

export default React.memo(LegacyRedirect);
