import React from 'react';
import { 
  Plus, 
  Home, 
  TrendingUp, 
  BarChart2, 
  MessageSquare, 
  Camera, 
  Settings, 
  Bookmark 
} from 'lucide-react';

const Sidebar = () => {
  const menuItems = [
    { icon: Home, label: '首页', active: true },
    { icon: TrendingUp, label: '趋势分析' },
    { icon: BarChart2, label: '分模型分析' },
    { icon: MessageSquare, label: '信源分析' },
    { icon: Camera, label: '问答快照' },
    { icon: Settings, label: '品牌设置' },
    { icon: Bookmark, label: '订阅' },
  ];

  return (
    <aside className="w-72 lg:w-80 h-screen sticky top-0 flex-shrink-0 p-5 z-30">
      <div className="relative h-full rounded-2xl border border-white/10 bg-[#271E37]/55 backdrop-blur-xl shadow-[0_18px_70px_rgba(0,0,0,0.45)] overflow-hidden">
        <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(900px_circle_at_-20%_-10%,rgba(124,58,237,0.35),transparent_55%),radial-gradient(700px_circle_at_120%_10%,rgba(236,72,153,0.22),transparent_50%),linear-gradient(to_bottom,rgba(255,255,255,0.05),transparent_35%,rgba(255,255,255,0.03))]" />
        <div className="relative h-full flex flex-col p-4">
          <div className="px-2 pt-1 pb-3">
            <div className="text-sm font-semibold tracking-wide text-[#B19EEF]">
              Brand Dashboard
            </div>
            <div className="mt-1 text-xs text-white/45">
              监控 · 分析 · 报告
            </div>
          </div>

          <button className="w-full rounded-xl py-3 px-4 flex items-center justify-center gap-2 font-semibold text-white transition-all duration-200 bg-gradient-to-r from-[#7c3aed] to-[#6d28d9] shadow-[0_10px_30px_rgba(124,58,237,0.25)] hover:shadow-[0_16px_40px_rgba(124,58,237,0.32)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#7c3aed]/60 focus-visible:ring-offset-2 focus-visible:ring-offset-[#060010] active:scale-[0.98]">
            <span className="grid place-items-center w-9 h-9 rounded-lg bg-white/15 ring-1 ring-white/15 shadow-[inset_0_1px_0_rgba(255,255,255,0.12)]">
              <Plus size={18} />
            </span>
            <span className="text-base tracking-wide">任务</span>
          </button>

          <div className="h-px bg-white/10 my-5 mx-2"></div>

          <nav className="sidebar-nav flex-1 min-h-0 space-y-1.5 overflow-y-auto pr-1">
            {menuItems.map((item, index) => {
              const Icon = item.icon;
              return (
                <button
                  key={index}
                  type="button"
                  className={[
                    'group relative w-full flex items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-all duration-200',
                    'focus:outline-none focus-visible:ring-2 focus-visible:ring-[#7c3aed]/60 focus-visible:ring-offset-2 focus-visible:ring-offset-[#060010]',
                    item.active
                      ? 'bg-white/10 text-[#B19EEF] ring-1 ring-white/15 shadow-[0_10px_30px_rgba(0,0,0,0.25)]'
                      : 'text-white/70 hover:bg-white/7 hover:text-[#B19EEF] hover:ring-1 hover:ring-white/10'
                  ].join(' ')}
                >
                  <span
                    className={[
                      'grid place-items-center w-10 h-10 rounded-xl ring-1 transition-all duration-200',
                      item.active
                        ? 'bg-[#7c3aed]/12 ring-[#7c3aed]/25 shadow-[0_0_0_1px_rgba(124,58,237,0.06)]'
                        : 'bg-white/5 ring-white/10 group-hover:bg-white/10'
                    ].join(' ')}
                  >
                    <Icon size={20} className={item.active ? 'text-[#B19EEF]' : 'text-white/60 group-hover:text-[#B19EEF]'} />
                  </span>
                  <span className="tracking-wide font-medium text-[0.95rem]">{item.label}</span>
                  {item.active && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 h-8 w-1 rounded-r-full bg-gradient-to-b from-[#7c3aed] to-[#6d28d9]" />
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
