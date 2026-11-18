import React from 'react';
import { Footprints, Globe, MousePointer, Database, Terminal, Shield } from 'lucide-react';

export default function BreadcrumbTrail({ breadcrumbs = [] }) {
  if (!breadcrumbs || breadcrumbs.length === 0) {
    return (
      <div className="rounded-xl border border-white/10 bg-dark-900/60 p-6 text-center text-xs text-slate-400 font-mono">
        No breadcrumbs captured prior to this event.
      </div>
    );
  }

  const getCategoryIcon = (category) => {
    const c = (category || '').toLowerCase();
    if (c.includes('http') || c.includes('fetch')) return Globe;
    if (c.includes('ui') || c.includes('click')) return MousePointer;
    if (c.includes('db') || c.includes('sql')) return Database;
    if (c.includes('sec') || c.includes('auth')) return Shield;
    return Terminal;
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-300">
        <Footprints className="h-4 w-4 text-cyan-400" />
        <span>Breadcrumb Trail ({breadcrumbs.length} Events)</span>
      </div>

      <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-white/10">
        {breadcrumbs.map((crumb, idx) => {
          const Icon = getCategoryIcon(crumb.category);
          const isError = crumb.level === 'error';
          const isWarning = crumb.level === 'warning';

          return (
            <div key={idx} className="relative flex items-start gap-3 text-xs">
              {/* Dot / Icon */}
              <div
                className={`absolute -left-6 flex h-5 w-5 items-center justify-center rounded-full border ${
                  isError
                    ? 'border-rose-500 bg-rose-950 text-rose-400'
                    : isWarning
                    ? 'border-amber-500 bg-amber-950 text-amber-400'
                    : 'border-white/20 bg-dark-900 text-slate-400'
                }`}
              >
                <Icon className="h-2.5 w-2.5" />
              </div>

              {/* Breadcrumb card */}
              <div className="flex-1 rounded-xl border border-white/10 bg-dark-900/80 p-3 shadow-sm">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-white">{crumb.message}</span>
                  <span className="font-mono text-[10px] text-slate-500">
                    {crumb.timestamp ? new Date(crumb.timestamp).toLocaleTimeString() : ''}
                  </span>
                </div>

                <div className="mt-1 flex items-center gap-2 text-[10px] text-slate-400">
                  <span className="rounded bg-white/5 px-1.5 py-0.5 font-mono uppercase text-slate-300 border border-white/5">
                    {crumb.category}
                  </span>
                  <span>level: {crumb.level}</span>
                </div>

                {crumb.data && Object.keys(crumb.data).length > 0 && (
                  <div className="mt-2 rounded bg-black/40 p-2 font-mono text-[11px] text-slate-300 border border-white/5 overflow-x-auto">
                    <pre>{JSON.stringify(crumb.data, null, 2)}</pre>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
