/**
 * 引用列表组件
 * 显示文章引用信息和引用率
 */

import React, { useState, useEffect } from 'react';
import '../styles/references-table.css';

const ReferencesTable = ({ referencesData, isLoading, error }) => {
  // 内部状态管理
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);

  // 模拟数据
  const mockData = [
    { rank: 1, domain: 'techcrunch.com', rate: 95 },
    { rank: 2, domain: 'reddit.com', rate: 88 },
    { rank: 3, domain: 'twitter.com', rate: 82 },
    { rank: 4, domain: 'youtube.com', rate: 76 },
    { rank: 5, domain: 'medium.com', rate: 71 }
  ];

  // 模拟数据加载
  useEffect(() => {
    if (isLoading !== undefined) {
      setLoading(isLoading);
    } else {
      setLoading(true);
      setTimeout(() => {
        setData(mockData);
        setLoading(false);
      }, 1000);
    }

    if (error) {
      setErrorMsg(error);
    }
  }, [isLoading, error, referencesData]);

  // 使用传入数据或模拟数据
  const displayData = referencesData || data;

  // 加载状态
  if (loading) {
    return (
      <div className="references-table">
        <div className="mb-6">
          <h2 className="text-xl font-bold flex items-center gap-3">
            <div className="w-1 h-6 rounded-full"></div>
            引用链接详情
          </h2>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-violet-400 mx-auto mb-4"></div>
            <p className="text-slate-400">正在加载引用数据...</p>
          </div>
        </div>
      </div>
    );
  }

  // 错误状态
  if (errorMsg) {
    return (
      <div className="references-table">
        <div className="mb-6">
          <h2 className="text-xl font-bold flex items-center gap-3">
            <div className="w-1 h-6 rounded-full"></div>
            引用链接详情
          </h2>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="text-4xl mb-4">❌</div>
            <h3 className="text-lg font-semibold text-slate-300 mb-2">数据加载失败</h3>
            <p className="text-slate-400 mb-4">{errorMsg}</p>
            <button 
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-violet-600 hover:bg-violet-700 rounded-lg transition-colors"
            >
              重试
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 空状态
  if (!displayData || displayData.length === 0) {
    return (
      <div className="references-table">
        <div className="mb-6">
          <h2 className="text-xl font-bold flex items-center gap-3">
            <div className="w-1 h-6 rounded-full"></div>
            引用链接详情
          </h2>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="text-4xl mb-4">🔗</div>
            <h3 className="text-lg font-semibold text-slate-300 mb-2">暂无引用数据</h3>
            <p className="text-slate-400">当前时间范围内没有可用的引用链接数据</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="references-table">
      <div className="mb-6 w-full">
        <h2 className="text-xl font-bold flex items-center gap-3 m-0">
          <div className="w-1 h-6 rounded-full"></div>
          引用链接详情
        </h2>
      </div>
      
      <div className="table-container flex-1 overflow-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left p-4 text-slate-400 font-semibold">排名</th>
              <th className="text-left p-4 text-slate-400 font-semibold">链接域名</th>
              <th className="text-left p-4 text-slate-400 font-semibold">引用率</th>
            </tr>
          </thead>
          <tbody>
            {displayData.map((item) => (
              <tr key={item.rank} className="border-b border-white/5 hover:bg-white/5 transition-all duration-300 group">
                <td className="p-4 font-bold text-slate-300 group-hover:text-white transition-colors">
                  {item.rank}
                </td>
                <td className="p-4">
                  <a 
                    href={`https://${item.domain}`} 
                    target="_blank" 
                    rel="noreferrer" 
                    className="text-slate-300 hover:text-violet-300 transition-colors"
                  >
                    {item.domain}
                  </a>
                </td>
                <td className="p-4 text-left font-semibold text-slate-300 group-hover:text-white transition-colors">
                  {item.rate}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ReferencesTable;