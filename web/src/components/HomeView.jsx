import React from 'react';
import { Spin } from 'antd';

import { useDashboardRequestParams } from '@/hooks/useDashboardParams';
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
    <Spin spinning={isLoading}>
      {selectedPlatform ? (
        <PlatformDetail
          platformName={selectedPlatform}
          onBack={onBackFromPlatform}
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'minmax(0, 1fr)',
            gap: 16,
          }}
        >
          <div style={{ minWidth: 0 }}>
            <BrandMentionRate />
          </div>
          <div style={{ minWidth: 0 }}>
            <PlatformMentionRates
              onPlatformClick={onPlatformClick}
            />
          </div>
          <div style={{ minWidth: 0 }}>
            <ReferencesTable />
          </div>
        </div>
      )}
    </Spin>
  );
};

export default React.memo(HomeView);
