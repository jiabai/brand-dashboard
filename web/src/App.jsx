import React, { useState, useEffect } from 'react';

// Components
import BrandMentionRate from './components/BrandMentionRate.jsx';
import ModelMentionRates from './components/ModelMentionRates.jsx';
import ReferencesTable from './components/ReferencesTable.jsx';
import ErrorBoundary from './components/ErrorBoundary';
import LoadingSpinner from './components/LoadingSpinner';
import Squares from './components/Squares.jsx';
import GooeyNav from './components/GooeyNav.jsx';
import TaskName from './components/TaskName.jsx';
import Sidebar from './components/Sidebar.jsx';

// Styles
import './App.css';

/**
 * Main application component for Brand Analysis Dashboard
 *
 * @returns {JSX.Element} The rendered dashboard application
 */
function App() {
  // State management
  const [selectedFilter, setSelectedFilter] = useState('7days');
  const [currentTime, setCurrentTime] = useState(new Date());
  const [isLoading, setIsLoading] = useState(false);
  const loadingTimerRef = React.useRef(null);

  // GooeyNav navigation items
  const navItems = [
    { label: '昨天', href: '#yesterday' },
    { label: '过去7天', href: '#7days' },
    { label: '过去30天', href: '#30days' }
  ];

  // Update current time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Cleanup loading timer on unmount
  useEffect(() => {
    return () => {
      if (loadingTimerRef.current) {
        clearTimeout(loadingTimerRef.current);
      }
    };
  }, []);

  /**
   * Handle filter change with loading state
   * @param {string} filter - The selected time filter
   */
  const handleFilterChange = (filter) => {
    setSelectedFilter(filter);
    // Clear any existing timer
    if (loadingTimerRef.current) {
      clearTimeout(loadingTimerRef.current);
    }
    // Simulate loading state for better UX
    setIsLoading(true);
    loadingTimerRef.current = setTimeout(() => setIsLoading(false), 800);
  };

  /**
   * Handle GooeyNav navigation click
   * @param {number} index - The clicked navigation item index
   */
  const handleNavClick = (index) => {
    const filterMap = ['yesterday', '7days', '30days'];
    handleFilterChange(filterMap[index]);
  };

  return (
    <div className="App min-h-screen">
      {/* Background Animation */}
      <div className="fixed inset-0 z-[-1]">
        <Squares
          direction="diagonal"
          speed={1}
          borderColor="#374151"
          squareSize={40}
          hoverFillColor="#1F2937"
        />
      </div>

      <ErrorBoundary className="relative z-10 flex flex-col min-h-screen">
        {/* Main Dashboard Content */}
        <main className="App-main relative z-10 pt-6 w-full flex gap-6">
          <Sidebar />

          <div className="flex-1 flex flex-col min-w-0">
            {/* GooeyNav Sticky Navigation */}
            <div className="sticky top-0 z-10 bg-background/95 backdrop-blur-sm p-4 rounded-lg border mb-6 overflow-hidden">
              <div className="flex items-center justify-between">
                {/* 左侧：任务名称 */}
                <div className="ml-4">
                  <TaskName />
                </div>

                {/* 右侧：导航与状态 */}
                <div className="flex items-center gap-6 mr-4">
                   {/* 状态信息 */}
                   <div className="flex items-center gap-3 text-sm text-slate-400 hidden lg:flex">
                      <span className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 shadow-sm backdrop-blur-md">
                        <span className="relative flex h-2 w-2">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                        </span>
                        <span className="text-xs font-medium text-white/80">实时数据</span>
                      </span>
                      <span className="text-xs font-mono text-white/50 bg-black/20 px-2 py-1 rounded-md border border-white/5">
                        更新: {currentTime.toLocaleTimeString()}
                      </span>
                   </div>

                   <div className="h-6 w-px bg-white/10 hidden lg:block"></div>

                   {/* 时间筛选器 */}
                   <div className="flex-1 max-w-md flex justify-end">
                    <GooeyNav
                      items={navItems}
                      animationTime={600}
                      particleCount={15}
                      particleDistances={[90, 10]}
                      particleR={100}
                      timeVariance={300}
                      colors={[1, 2, 3, 1, 2, 3, 1, 4]}
                      initialActiveIndex={1} // 默认选中 "过去7天"
                      onItemClick={handleNavClick}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Loading State or Dashboard Content */}
            {isLoading ? (
              <LoadingSpinner text="正在加载数据..." />
            ) : (
              <div className="dashboard-content">
                <div className="dashboard-card brand-section">
                  <BrandMentionRate />
                </div>

                <div className="dashboard-card model-section">
                  <ModelMentionRates />
                </div>

                <div className="dashboard-card references-section">
                  <ReferencesTable />
                </div>
              </div>
            )}
          </div>
        </main>
      </ErrorBoundary>
    </div>
  );
}

export default App;
