import React from 'react';

import { useDashboardRequestParams } from '@/hooks/useDashboardParams';
import LoadingSpinner from './LoadingSpinner.jsx';
import PlatformDetail from './PlatformDetail.jsx';

const BrandMentionRate = React.lazy(() => import('./BrandMentionRate.jsx'));
const PlatformMentionRates = React.lazy(() => import('./PlatformMentionRates.jsx'));
const ReferencesTable = React.lazy(() => import('./ReferencesTable.jsx'));

const HomeView = () => {
  const {
    selectedPlatform,
    isLoading,
    onPlatformClick,
    onBackFromPlatform,
  } = useDashboardRequestParams();

  return (
    <>
      {isLoading ? (
        <div className="app-shell-loading">
          <LoadingSpinner text="正在加载首页数据..." />
        </div>
      ) : null}
      {selectedPlatform ? (
        <PlatformDetail
          platformName={selectedPlatform}
          onBack={onBackFromPlatform}
        />
      ) : (
        <div className="grid min-w-0 grid-cols-1 items-start gap-5 xl:grid-cols-[minmax(0,1.5fr)_minmax(340px,0.9fr)]">
          <div className="min-w-0">
            <BrandMentionRate />
          </div>
          <div className="min-w-0">
            <PlatformMentionRates
              onPlatformClick={onPlatformClick}
            />
          </div>
          <div className="min-w-0 xl:col-span-2">
            <ReferencesTable />
          </div>
        </div>
      )}
    </>
  );
};

export default React.memo(HomeView);
