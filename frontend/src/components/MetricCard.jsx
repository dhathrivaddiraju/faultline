import React from 'react';

export default function MetricCard({ title, value, subtitle, icon: Icon, color = 'rose', trend }) {
  const colorMap = {
    rose: 'from-rose-500/20 to-transparent border-rose-500/30 text-rose-400',
    amber: 'from-amber-500/20 to-transparent border-amber-500/30 text-amber-400',
    cyan: 'from-cyan-500/20 to-transparent border-cyan-500/30 text-cyan-400',
    emerald: 'from-emerald-500/20 to-transparent border-emerald-500/30 text-emerald-400',
    purple: 'from-purple-500/20 to-transparent border-purple-500/30 text-purple-400'
  };

  const activeColor = colorMap[color] || colorMap.rose;

  return (
    <div className="relative overflow-hidden rounded-xl border border-white/10 bg-dark-900/60 p-5 backdrop-blur-md transition-all duration-300 hover:border-white/20">
      <div className={`absolute -right-10 -top-10 h-32 w-32 rounded-full bg-gradient-to-br ${activeColor} blur-2xl opacity-40`} />
      
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</span>
        {Icon && (
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/5 border border-white/10 text-slate-300">
            <Icon className="h-4 w-4" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-3xl font-bold tracking-tight text-white">{value}</span>
        {trend && (
          <span className={`text-xs font-medium ${trend.isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
            {trend.value}
          </span>
        )}
      </div>

      {subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
    </div>
  );
}
