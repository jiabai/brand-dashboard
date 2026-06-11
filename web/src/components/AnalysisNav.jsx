import React, { useMemo } from 'react';
import { NavLink, useLocation } from 'react-router-dom';

import { useDashboardParams } from '@/hooks/useDashboardParams';
import {
  buildRouteSearch,
  buildViewPath,
  getAnalysisNavRoutes,
  getViewKeyFromPath,
} from '@/utils/routing';

const ANALYSIS_NAV_ITEMS = getAnalysisNavRoutes();

const AnalysisNav = () => {
  const location = useLocation();
  const { tenantKey, jobId } = useDashboardParams();
  const selectedKey = useMemo(
    () => getViewKeyFromPath(location.pathname),
    [location.pathname],
  );

  return (
    <nav
      aria-label="分析看板导航"
      className="flex items-center gap-1 overflow-x-auto border-b border-border pb-2"
    >
      {ANALYSIS_NAV_ITEMS.map((item) => {
        const pathname = buildViewPath(item.viewKey, { tenantKey, jobId });
        const search = buildRouteSearch({
          search: location.search,
          nextViewKey: item.viewKey,
        });
        const isActive = selectedKey === item.viewKey;
        return (
          <NavLink
            key={item.viewKey}
            to={`${pathname}${search}`}
            className={[
              'inline-flex shrink-0 items-center rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              isActive
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground',
            ].join(' ')}
          >
            {item.menuLabel}
          </NavLink>
        );
      })}
    </nav>
  );
};

export default React.memo(AnalysisNav);
