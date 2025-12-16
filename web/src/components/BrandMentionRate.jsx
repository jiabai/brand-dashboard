/**
 * Brand Mention Rate Component
 * Displays brand mention rate with circular progress chart and brand rankings
 *
 * @component
 * @example
 * return (
 *   <BrandMentionRate
 *     brandData={{ mentionRate: 85, rank: 1, change: 5 }}
 *     isLoading={false}
 *     error={null}
 *   />
 * );
 */

import React from 'react';

// Styles
import '../styles/brand-mention-rate.css';

// Utilities
import { DEFAULT_BRAND_DATA, formatPercentage } from '@/utils';

// Components
import LoadingSpinner from './LoadingSpinner';
import EmptyState from './EmptyState';

// Mock brand ranking data for demonstration
const BRAND_RANKINGS = [
  { rank: 1, text: "海尔", percent: 85.5, change: "up" },
  { rank: 2, text: "美的", percent: 78.3, change: "stable" },
  { rank: 3, text: "格力", percent: 72.1, change: "down" },
  { rank: 4, text: "西门子", percent: 65.8, change: "up" },
  { rank: 5, text: "松下", percent: 58.2, change: "up" },
  { rank: 6, text: "三星", percent: 52.7, change: "stable" },
  { rank: 7, text: "LG", percent: 48.3, change: "down" },
  { rank: 8, text: "TCL", percent: 42.1, change: "up" },
  { rank: 9, text: "海信", percent: 38.6, change: "stable" },
  { rank: 10, text: "小米", percent: 35.2, change: "down" }
];

/**
 * BrandMentionRate component displays circular progress and keyword rankings
 *
 * @param {Object} props - Component props
 * @param {Object} props.brandData - Brand mention data
 * @param {boolean} props.isLoading - Loading state
 * @param {string} props.error - Error message
 * @returns {JSX.Element} Brand mention rate UI
 */
const BrandMentionRate = ({ brandData, isLoading, error }) => {
  // Data validation and default value handling
  const data = brandData && typeof brandData === 'object'
    ? { ...DEFAULT_BRAND_DATA, ...brandData }
    : DEFAULT_BRAND_DATA;

  // Loading state
  if (isLoading) {
    return (
      <div className="brand-mention-rate">
        <h2>品牌总提及率</h2>
        <LoadingSpinner text="正在加载品牌数据..." />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="brand-mention-rate">
        <h2>品牌总提及率</h2>
        <EmptyState
          title="数据加载失败"
          description={error}
          icon="❌"
          actionText="重试"
          onAction={() => window.location.reload()}
        />
      </div>
    );
  }

  // Empty state
  if (!data.mentionRate && data.mentionRate !== 0) {
    return (
      <div className="brand-mention-rate">
        <h2>品牌总提及率</h2>
        <EmptyState
          title="暂无品牌数据"
          description="当前时间范围内没有可用的品牌提及数据"
          icon="📊"
        />
      </div>
    );
  }

  // Circular progress calculation
  const radius = 100;
  const strokeWidth = 14;
  const normalizedRadius = radius - strokeWidth * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDasharray = `${circumference} ${circumference}`;
  const strokeDashoffset = circumference - (data.mentionRate / 100) * circumference;

  // Split brand rankings into two columns
  const leftBrands = BRAND_RANKINGS.slice(0, 5);
  const rightBrands = BRAND_RANKINGS.slice(5, 10);

  /**
   * Render individual brand ranking item
   * @param {Object} item - Brand ranking data
   * @returns {JSX.Element} Brand ranking item UI
   */
  const renderBrand = (item) => (
    <div
      key={item.rank}
      className={`brand-item flex items-center justify-between p-2.5 rounded-md text-sm transition-colors bg-white/5 hover:bg-white/10 border border-white/5`}
    >
      <span className={`brand-rank ${
        item.rank === 1 ? 'rank-1' : 
        item.rank === 2 ? 'rank-2' : 
        item.rank === 3 ? 'rank-3' : 'rank-other'
      }`}>{item.rank}</span>
      <span className="brand-name flex-1 font-medium">{item.text}</span>
      <span className="brand-percent font-semibold">{item.percent}%</span>
    </div>
  );

  return (
    <div className="brand-mention-rate">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-slate-200 flex items-center gap-3 m-0">
          <div className="w-1 h-6 bg-gradient-to-b from-violet-400 to-violet-600 rounded-full shadow-[0_0_10px_rgba(124,58,237,0.5)]"></div>
          品牌总提及率
        </h2>
      </div>
      
      <div className="mention-rate-content flex-1 flex flex-col items-center justify-center gap-8">
        <div className="circular-progress-container relative flex items-center justify-center">
            <svg
              className="circular-progress transform -rotate-90"
              height={radius * 2}
              width={radius * 2}
              viewBox={`0 0 ${radius * 2} ${radius * 2}`}
            >
              <circle
                stroke="rgba(255,255,255,0.05)"
                fill="transparent"
                strokeWidth={strokeWidth}
                r={normalizedRadius}
                cx={radius}
                cy={radius}
              />
              <circle
                stroke="url(#progressGradient)"
                fill="transparent"
                strokeWidth={strokeWidth}
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                r={normalizedRadius}
                cx={radius}
                cy={radius}
                className="transition-all duration-1000 ease-out"
              />
              <defs>
                <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#a78bfa" />
                  <stop offset="100%" stopColor="#7c3aed" />
                </linearGradient>
              </defs>
            </svg>
            <div className="progress-text absolute flex flex-col items-center">
              <span className="text-4xl font-bold text-slate-100 leading-none">{formatPercentage(data.mentionRate)}</span>
              <span className="mt-1 text-sm font-medium text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-full">+{formatPercentage(data.change)}</span>
            </div>
          </div>
          
          <div className="rate-info w-full">
            <div className="brand-rankings">
              <div className="brand-columns flex gap-4 w-full">
                <div className="brand-column flex-1 flex flex-col gap-2">
                  {leftBrands.map(renderBrand)}
                </div>
                <div className="brand-column flex-1 flex flex-col gap-2">
                  {rightBrands.map(renderBrand)}
                </div>
              </div>
            </div>
          </div>
        </div>
    </div>
  );
}

export default BrandMentionRate;
