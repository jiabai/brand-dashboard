import React from 'react';
import { Outlet } from 'react-router-dom';

import AnalysisNav from './AnalysisNav.jsx';

const AnalysisLayout = () => (
  <div className="flex min-w-0 flex-col gap-4">
    <AnalysisNav />
    <Outlet />
  </div>
);

export default AnalysisLayout;
