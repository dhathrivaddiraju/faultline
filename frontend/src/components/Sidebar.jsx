import React from 'react';
import { 
  LayoutDashboard, 
  AlertTriangle, 
  Radio, 
  BarChart3, 
  Code2, 
  Settings,
  Cpu
} from 'lucide-react';

export default function Sidebar({ activeTab, onSelectTab, incidentCount }) {
  const navItems = [
    { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
    { id: 'incidents', label: 'Incidents', icon: AlertTriangle, badge: incidentCount },
    { id: 'live', label: 'Live Stream', icon: Radio, pulse: true },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'settings', label: 'SDK & Settings', icon: Code2 },
  ];

  return (
    <aside className="sticky top-16 h-[calc(100vh-4rem)] w-60 border-r border-white/10 bg-dark-950/40 p-4 backdrop-blur-md flex flex-col justify-between">
      <div className="space-y-1">
        <div className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          Telemetry & Crashes
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`group flex w-full items-center justify-between rounded-xl px-3.5 py-2.5 text-xs font-medium transition duration-150 ${
                isActive
                  ? 'bg-rose-500/15 text-rose-300 font-semibold shadow-inner'
                  : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`h-4 w-4 ${isActive ? 'text-rose-400' : 'text-slate-400 group-hover:text-slate-200'}`} />
                <span>{item.label}</span>
              </div>

              {item.badge !== undefined && item.badge > 0 && (
                <span className="rounded-full bg-rose-500/20 px-2 py-0.5 text-[10px] font-bold text-rose-400">
                  {item.badge}
                </span>
              )}

              {item.pulse && (
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan-400 opacity-75"></span>
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-cyan-500"></span>
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Claude AI Engine Badge */}
      <div className="rounded-xl border border-white/10 bg-dark-900/60 p-3.5 text-xs">
        <div className="flex items-center gap-2 text-rose-400">
          <Cpu className="h-4 w-4" />
          <span className="font-semibold text-white">Claude 3.5 Sonnet</span>
        </div>
        <p className="mt-1.5 text-[11px] leading-relaxed text-slate-400">
          Clustered stack traces analyzed for root cause & remediation in real time.
        </p>
      </div>
    </aside>
  );
}
