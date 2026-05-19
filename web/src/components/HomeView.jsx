import React from 'react';
import { ChevronRight } from 'lucide-react';

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
        <div className="flex min-w-0 flex-col gap-6">
          <div className="flex flex-col gap-2 border-b border-border pb-4">
            <nav aria-label="面包屑导航" className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span>仪表板</span>
              <ChevronRight className="size-3" aria-hidden="true" />
              <span className="font-medium text-foreground">首页概览</span>
            </nav>
            <h1 className="text-2xl font-medium text-foreground">首页概览</h1>
            <p className="max-w-[720px] text-sm text-muted-foreground">
              品牌声量、平台分布和信源引用数据的综合概览
            </p>
          </div>
          <div className="min-w-0">
            <BrandMentionRate />
          </div>
          <div className="min-w-0">
            <PlatformMentionRates
              onPlatformClick={onPlatformClick}
            />
          </div>
          <div className="min-w-0">
            <ReferencesTable />
          </div>
        </div>
      )}
    </>
  );
};

export default React.memo(HomeView);
