import React from 'react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid 
} from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-lg border border-white/10 bg-dark-900/90 p-3 shadow-xl backdrop-blur-md text-xs">
        <p className="font-semibold text-slate-300 mb-1.5">{label || payload[0]?.payload?.display_time}</p>
        <div className="space-y-1">
          <p className="flex items-center gap-2 text-rose-400 font-mono">
            <span className="w-2 h-2 rounded-full bg-rose-500"></span>
            Critical: {payload.find(p => p.dataKey === 'critical')?.value || 0}
          </p>
          <p className="flex items-center gap-2 text-orange-400 font-mono">
            <span className="w-2 h-2 rounded-full bg-orange-500"></span>
            Error: {payload.find(p => p.dataKey === 'error')?.value || 0}
          </p>
          <p className="flex items-center gap-2 text-amber-400 font-mono">
            <span className="w-2 h-2 rounded-full bg-amber-500"></span>
            Warning: {payload.find(p => p.dataKey === 'warning')?.value || 0}
          </p>
          <div className="border-t border-white/10 pt-1 mt-1 font-mono font-bold text-white flex justify-between">
            <span>Total:</span>
            <span>{payload.reduce((sum, p) => sum + (p.value || 0), 0)}</span>
          </div>
        </div>
      </div>
    );
  }
  return null;
};

export default function ErrorFrequencyChart({ data = [] }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-xs text-slate-500 font-mono">
        No timeseries data captured in the selected window.
      </div>
    );
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="criticalGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0} />
            </linearGradient>
            <linearGradient id="errorGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#f97316" stopOpacity={0.0} />
            </linearGradient>
            <linearGradient id="warningGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#eab308" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#eab308" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#ffffff0a" vertical={false} />
          <XAxis 
            dataKey="display_time" 
            stroke="#64748b" 
            fontSize={11} 
            tickLine={false} 
            axisLine={false} 
          />
          <YAxis 
            stroke="#64748b" 
            fontSize={11} 
            tickLine={false} 
            axisLine={false} 
            allowDecimals={false} 
          />
          <Tooltip content={<CustomTooltip />} />
          <Area 
            type="monotone" 
            dataKey="critical" 
            stackId="1" 
            stroke="#f43f5e" 
            fill="url(#criticalGrad)" 
            strokeWidth={2} 
          />
          <Area 
            type="monotone" 
            dataKey="error" 
            stackId="1" 
            stroke="#f97316" 
            fill="url(#errorGrad)" 
            strokeWidth={2} 
          />
          <Area 
            type="monotone" 
            dataKey="warning" 
            stackId="1" 
            stroke="#eab308" 
            fill="url(#warningGrad)" 
            strokeWidth={1.5} 
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
