import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Code, FileText, Check, Copy } from 'lucide-react';

export default function StackTraceViewer({ frames = [] }) {
  const [inAppOnly, setInAppOnly] = useState(false);
  const [expandedIndices, setExpandedIndices] = useState(() => {
    // Expand the last in-app frame by default
    const set = new Set();
    const inAppFrames = frames.map((f, i) => ({ f, i })).filter(item => item.f.in_app);
    if (inAppFrames.length > 0) {
      set.add(inAppFrames[inAppFrames.length - 1].i);
    } else if (frames.length > 0) {
      set.add(frames.length - 1);
    }
    return set;
  });

  const toggleFrame = (index) => {
    const next = new Set(expandedIndices);
    if (next.has(index)) {
      next.delete(index);
    } else {
      next.add(index);
    }
    setExpandedIndices(next);
  };

  const filteredFrames = inAppOnly ? frames.filter(f => f.in_app) : frames;

  if (!frames || frames.length === 0) {
    return (
      <div className="rounded-xl border border-white/10 bg-dark-900/60 p-6 text-center text-xs text-slate-400 font-mono">
        No stack trace available for this event.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Code className="h-4 w-4 text-rose-400" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Stack Trace ({filteredFrames.length} Frames)
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={() => setInAppOnly(!inAppOnly)}
            className={`rounded-lg px-2.5 py-1 text-xs font-medium border transition ${
              inAppOnly
                ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                : 'bg-white/5 text-slate-400 border-white/10 hover:text-slate-200'
            }`}
          >
            In-App Frames Only
          </button>
        </div>
      </div>

      {/* Frame list */}
      <div className="space-y-2">
        {filteredFrames.map((frame, idx) => {
          const isExpanded = expandedIndices.has(idx);
          const hasLocals = frame.vars && Object.keys(frame.vars).length > 0;

          return (
            <div
              key={idx}
              className={`rounded-xl border transition-all duration-200 overflow-hidden ${
                frame.in_app
                  ? 'border-white/15 bg-dark-900/90'
                  : 'border-white/5 bg-dark-950/60 opacity-80'
              }`}
            >
              {/* Frame header row */}
              <button
                onClick={() => toggleFrame(idx)}
                className="flex w-full items-center justify-between p-3.5 text-left text-xs hover:bg-white/[0.03] transition"
              >
                <div className="flex items-center gap-3 truncate">
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4 text-slate-400 shrink-0" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-slate-400 shrink-0" />
                  )}
                  
                  <span className="font-mono text-slate-200 truncate">
                    {frame.filename}
                  </span>
                  
                  <span className="text-slate-500">in</span>
                  
                  <span className="font-mono font-semibold text-rose-400">
                    {frame.function}
                  </span>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  {frame.in_app && (
                    <span className="rounded bg-rose-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-rose-400 border border-rose-500/20">
                      app
                    </span>
                  )}
                  <span className="font-mono text-slate-400">
                    line {frame.lineno || '?'}
                  </span>
                </div>
              </button>

              {/* Code context & locals expanded view */}
              {isExpanded && (
                <div className="border-t border-white/10 bg-black/60 p-4 font-mono text-xs space-y-4">
                  {/* Surrounding code lines */}
                  {frame.code_context && (
                    <div className="rounded-lg bg-black/80 border border-white/5 p-3 overflow-x-auto space-y-0.5">
                      {frame.pre_context?.map((line, lIdx) => (
                        <div key={`pre-${lIdx}`} className="flex text-slate-500 hover:text-slate-400">
                          <span className="w-10 select-none text-right pr-4 text-slate-600">
                            {(frame.lineno || 0) - (frame.pre_context.length - lIdx)}
                          </span>
                          <span>{line}</span>
                        </div>
                      ))}

                      {/* Failing line */}
                      <div className="flex bg-rose-500/20 text-rose-200 py-0.5 font-bold rounded">
                        <span className="w-10 select-none text-right pr-4 text-rose-400">
                          {frame.lineno}
                        </span>
                        <span>{frame.code_context}</span>
                      </div>

                      {frame.post_context?.map((line, lIdx) => (
                        <div key={`post-${lIdx}`} className="flex text-slate-500 hover:text-slate-400">
                          <span className="w-10 select-none text-right pr-4 text-slate-600">
                            {(frame.lineno || 0) + lIdx + 1}
                          </span>
                          <span>{line}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Local Variables */}
                  {hasLocals && (
                    <div className="space-y-1.5">
                      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                        Local Variables
                      </div>
                      <div className="rounded-lg border border-white/5 bg-black/50 p-3 grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px]">
                        {Object.entries(frame.vars).map(([key, val]) => (
                          <div key={key} className="flex items-baseline gap-2 truncate">
                            <span className="text-cyan-400 font-semibold">{key}:</span>
                            <span className="text-slate-300 truncate">{String(val)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
