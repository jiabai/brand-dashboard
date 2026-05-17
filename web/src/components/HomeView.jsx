import React from 'react';
import { Spin } from 'antd';
import { useOutletContext } from 'react-router-dom';

import PlatformDetail from './PlatformDetail.jsx';

const BrandMentionRate = React.lazy(() => import('./BrandMentionRate.jsx'));
const PlatformMentionRates = React.lazy(() => import('./PlatformMentionRates.jsx'));
const ReferencesTable = React.lazy(() => import('./ReferencesTable.jsx'));

const HomeView = () => {
  const {
    tenantKey,
    jobId,
    brand,
    timeframe,
    selectedDateParam,
    selectedEndDateParam,
    selectedPlatform,
    isLoading,
    onPlatformClick,
    onBackFromPlatform,
  } = useOutletContext();

  return (
    <Spin spinning={isLoading}>
      {selectedPlatform ? (
        <PlatformDetail
          platformName={selectedPlatform}
          tenantKey={tenantKey}
          jobId={jobId}
          brand={brand}
          timeframe={timeframe}
          startDate={selectedDateParam}
          endDate={selectedEndDateParam}
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
            <BrandMentionRate
              timeframe={timeframe}
              date={selectedDateParam}
              endDate={selectedEndDateParam}
              tenantKey={tenantKey}
              jobId={jobId}
              brand={brand}
            />
          </div>
          <div style={{ minWidth: 0 }}>
            <PlatformMentionRates
              timeframe={timeframe}
              date={selectedDateParam}
              endDate={selectedEndDateParam}
              tenantKey={tenantKey}
              jobId={jobId}
              brand={brand}
              onPlatformClick={onPlatformClick}
            />
          </div>
          <div style={{ minWidth: 0 }}>
            <ReferencesTable
              timeframe={timeframe}
              date={selectedDateParam}
              endDate={selectedEndDateParam}
              tenantKey={tenantKey}
              jobId={jobId}
              brand={brand}
            />
          </div>
        </div>
      )}
    </Spin>
  );
};

export default React.memo(HomeView);
