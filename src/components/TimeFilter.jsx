/**
 * Time Filter Component
 * Provides time range filtering functionality for dashboard data
 *
 * @component
 * @example
 * return (
 *   <TimeFilter
 *     selectedFilter="7days"
 *     onFilterChange={(filter) => console.log(filter)}
 *   />
 * );
 */

import React, { useState } from 'react';
import { Button } from './ui/button';

// Time filter options configuration
const TIME_FILTER_OPTIONS = [
  { key: 'yesterday', label: '昨天' },
  { key: '7days', label: '过去7天' },
  { key: '30days', label: '过去30天' }
];

/**
 * TimeFilter component renders filter buttons for time range selection
 *
 * @param {Object} props - Component props
 * @param {Function} props.onFilterChange - Callback function when filter changes
 * @param {string} props.selectedFilter - Currently selected filter key
 * @returns {JSX.Element} Time filter UI
 */
const TimeFilter = ({ onFilterChange, selectedFilter }) => {
  /**
   * Handle filter change and notify parent component
   * @param {string} filter - Selected filter key
   */
  const handleFilterChange = (filter) => {
    if (typeof onFilterChange === 'function') {
      onFilterChange(filter);
    }
  };

  return (
    <div className="time-filter">
      <h2>时间范围</h2>
      <div className="filter-buttons flex gap-2 bg-background/95 backdrop-blur-sm p-1 rounded-lg border">
        {TIME_FILTER_OPTIONS.map((option) => (
          <Button
            key={option.key}
            variant={selectedFilter === option.key ? "default" : "ghost"}
            data-variant={selectedFilter === option.key ? "default" : "ghost"}
            size="sm"
            onClick={() => handleFilterChange(option.key)}
            aria-pressed={selectedFilter === option.key}
            className="transition-all duration-200"
          >
            {option.label}
          </Button>
        ))}
      </div>
    </div>
  );
};


export default TimeFilter;
