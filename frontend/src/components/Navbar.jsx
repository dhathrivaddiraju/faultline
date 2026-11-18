import React, { useState } from 'react';
import { ShieldAlert, ChevronDown, Zap } from 'lucide-react';

export default function Navbar({ projects, currentProject, onSelectProject, wsStatus, onSendTestError }) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [simulating, setSimulating] = useState(false);

  const handleSimulate = async () => {
    setSimulating(true);
    try {
      await onSendTestError();
    } finally {
      setTimeout(() => setSimulating(false), 600);
    }
  };

  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-white/10 bg-dark-950/80 px-6 backdrop-blur-md">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-rose-600 to-indigo-600 shadow-lg shadow-rose-600/20">
            <ShieldAlert className="h-5 w-5 text-white" />
          </div>
          <div>
            <span className="text-lg font-bold tracking-tight text-white">FAULTLINE</span>
            <span className="ml-2 rounded bg-rose-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-rose-400 border border-rose-500/30">
              OBSERVABILITY
            </span>
          </div>
        </div>

        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 rounded-lg border border-white/10 bg-dark-900/80 px-3 py-1.5 text-xs font-medium text-slate-200 transition hover:bg-dark-800 hover:border-white/20"
          >
            <div className="h-2 w-2 rounded-full bg-emerald-400"></div>
            <span>{currentProject ? currentProject.name : 'Select Project'}</span>
            <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
          </button>

          {dropdownOpen && (
            <div className="absolute left-0 mt-2 w-64 rounded-xl border border-white/10 bg-dark-900 p-2 shadow-2xl z-50 backdrop-blur-xl">
              <div className="px-3 py-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Projects
              </div>
              {projects.map((proj) => (
                <button
                  key={proj.id}
                  onClick={() => {
                    onSelectProject(proj);
                    setDropdownOpen(false);
                  }}
                  className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-xs transition ${
                    currentProject?.id === proj.id ? 'bg-rose-500/15 text-rose-300 font-semibold' : 'text-slate-300 hover:bg-white/5'
                  }`}
                >
                  <span className="truncate">{proj.name}</span>
                  <span className="text-[10px] text-slate-500 uppercase">{proj.environment}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 rounded-full border border-white/10 bg-dark-900/60 px-3 py-1 text-xs text-slate-300">
          <span className="relative flex h-2 w-2">
            <span className={`absolute inline-flex h-full w-full animate-ping rounded-full ${wsStatus === 'connected' ? 'bg-emerald-400 opacity-75' : 'bg-amber-400 opacity-75'}`}></span>
            <span className={`relative inline-flex h-2 w-2 rounded-full ${wsStatus === 'connected' ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
          </span>
          <span className="font-mono text-[11px] text-slate-400">
            {wsStatus === 'connected' ? 'STREAM CONNECTED' : 'CONNECTING...'}
          </span>
        </div>

        <button
          onClick={handleSimulate}
          disabled={simulating}
          className="flex items-center gap-1.5 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-1.5 text-xs font-semibold text-rose-300 transition hover:bg-rose-500/20 active:scale-95 disabled:opacity-50"
        >
          <Zap className={`h-3.5 w-3.5 ${simulating ? 'animate-bounce text-rose-400' : 'text-rose-400'}`} />
          <span>{simulating ? 'Sending...' : 'Trigger Test Error'}</span>
        </button>
      </div>
    </header>
  );
}
