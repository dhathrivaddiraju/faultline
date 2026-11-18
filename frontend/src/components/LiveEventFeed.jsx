import React, { useState } from 'react';
import { Radio, Pause, Play, ExternalLink, ShieldAlert } from 'lucide-react';
import { SeverityBadge } from './StatusBadge';

export default function LiveEventFeed({ liveEvents = [], onSelectIncident }) {
  const [paused, setPaused] = useState(false);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className={`absolute inline-flex h-full w-full animate-ping rounded-full ${paused ? 'bg-amber-400' : 'bg-rose-400'} opacity-75`}></span>
            <span className={`relative inline-flex h-2.5 w-2.5 rounded-full ${paused ? 'bg-amber-500' : 'bg-rose-500'}`}></span>
          </span>
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Realtime Ingestion Stream ({liveEvents.length} Captured)
          </span>
        </div>

        <button
          onClick={() => setPaused(!paused)}
          className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-slate-300 hover:bg-white/10 transition"
        >
          {paused ? (
            <>
              <Play className="h-3 w-3 text-emerald-400" />
              <span>Resume Stream</span>
            </>
          ) : (
            <>
              <Pause className="h-3 w-3 text-amber-400" />
              <span>Pause Feed</span>
            </>
          )}
        </button>
      </div>

      {/* Stream list */}
      {liveEvents.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-dark-900/40 p-12 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/5 text-slate-500 border border-white/10 mb-3">
            <Radio className="h-6 w-6 animate-pulse" />
          </div>
          <p className="text-sm font-semibold text-slate-300">Listening for crash events...</p>
          <p className="mt-1 text-xs text-slate-500 max-w-sm">
            Errors captured via SDK or the "Trigger Test Crash" button will stream here in real time over WebSockets.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {liveEvents.map((ev, idx) => (
            <div
              key={ev.id || idx}
              onClick={() => ev.incident_id && onSelectIncident(ev.incident_id)}
              className="group flex items-center justify-between rounded-xl border border-white/10 bg-dark-900/70 p-4 transition duration-200 hover:border-rose-500/40 hover:bg-dark-850 cursor-pointer backdrop-blur-md"
            >
              <div className="flex items-center gap-4 min-w-0">
                <SeverityBadge severity={ev.severity} />
                
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-white group-hover:text-rose-300 transition">
                      {ev.exception_type}
                    </span>
                    <span className="text-xs text-slate-400 truncate max-w-md">
                      {ev.message}
                    </span>
                  </div>
                  
                  <div className="mt-1 flex items-center gap-3 text-[11px] text-slate-500 font-mono">
                    <span>{ev.culprit || 'unknown:culprit'}</span>
                    <span>•</span>
                    <span className="text-slate-400">{ev.environment || 'production'}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                <span className="font-mono text-xs text-slate-400">
                  {new Date(ev.created_at).toLocaleTimeString()}
                </span>
                <ExternalLink className="h-4 w-4 text-slate-500 group-hover:text-rose-400 transition" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
