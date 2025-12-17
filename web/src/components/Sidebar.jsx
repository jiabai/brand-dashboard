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
    <aside className="w-72 lg:w-80 h-screen sticky top-0 flex-shrink-0 p-5 z-50">
      <div className="relative h-full rounded-2xl border border-white/10 bg-[#060010]/40 backdrop-blur-xl shadow-[0_20px_80px_rgba(0,0,0,0.45)] overflow-hidden">
        <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(900px_circle_at_-20%_-10%,rgba(124,58,237,0.35),transparent_55%),radial-gradient(700px_circle_at_120%_10%,rgba(236,72,153,0.22),transparent_50%),linear-gradient(to_bottom,rgba(255,255,255,0.05),transparent_35%,rgba(255,255,255,0.03))]" />
        <div className="relative h-full flex flex-col p-4">
          <button className="w-full rounded-xl py-3 px-4 flex items-center justify-center gap-2 font-semibold text-white transition-all duration-200 bg-gradient-to-r from-[#7c3aed] to-[#6d28d9] shadow-[0_10px_30px_rgba(124,58,237,0.25)] hover:shadow-[0_16px_40px_rgba(124,58,237,0.32)] active:scale-[0.98]">
            <span className="grid place-items-center w-9 h-9 rounded-lg bg-white/15 ring-1 ring-white/15">
              <Plus size={18} />
            </span>
            <span className="text-base tracking-wide">任务</span>
          </button>

          <div className="h-px bg-white/10 my-6 mx-2"></div>

          <nav className="flex-1 space-y-2">
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
                      ? 'bg-white/95 text-[#7c3aed] shadow-[0_14px_40px_rgba(0,0,0,0.25)]'
                      : 'text-white/70 hover:bg-white/10 hover:text-white hover:shadow-[0_12px_30px_rgba(0,0,0,0.18)]'
                  ].join(' ')}
                >
                  <span
                    className={[
                      'grid place-items-center w-10 h-10 rounded-xl ring-1 transition-all duration-200',
                      item.active
                        ? 'bg-[#7c3aed]/12 ring-[#7c3aed]/25'
                        : 'bg-white/5 ring-white/10 group-hover:bg-white/10'
                    ].join(' ')}
                  >
                    <Icon size={20} className={item.active ? 'text-[#7c3aed]' : 'text-white/70 group-hover:text-white'} />
                  </span>
                  <span className="tracking-wide font-medium">{item.label}</span>
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
