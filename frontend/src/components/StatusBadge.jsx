import React from 'react';

export function SeverityBadge({ severity }) {
  const s = (severity || 'error').toLowerCase();
  
  if (s === 'critical' || s === 'fatal') {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
        <span className="w-1.5 h-1.5 rounded-full bg-rose-500 mr-1.5 animate-pulse"></span>
        Critical
      </span>
    );
  }
  
  if (s === 'warning') {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mr-1.5"></span>
        Warning
      </span>
    );
  }
  
  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-orange-500/10 text-orange-400 border border-orange-500/30">
      <span className="w-1.5 h-1.5 rounded-full bg-orange-500 mr-1.5"></span>
      Error
    </span>
  );
}

export function StatusBadge({ status }) {
  const st = (status || 'unresolved').toLowerCase();
  
  if (st === 'resolved') {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
        Resolved
      </span>
    );
  }
  
  if (st === 'investigating') {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/30">
        Investigating
      </span>
    );
  }
  
  if (st === 'ignored') {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-500/10 text-slate-400 border border-slate-500/30">
        Ignored
      </span>
    );
  }
  
  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/15 text-rose-400 border border-rose-500/40">
      Unresolved
    </span>
  );
}
