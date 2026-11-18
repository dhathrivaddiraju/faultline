import React, { useState } from 'react';
import { BarChart3, PieChart, ShieldAlert, Zap, Globe, Cpu } from 'lucide-react';
import ErrorFrequencyChart from '../components/ErrorFrequencyChart';
import MetricCard from '../components/MetricCard';

export default function Analytics({ stats }) {
  const [timeWindow, setTimeWindow] = useState(24);

  const envs = Object.entries(stats?.environment_breakdown || {});
  const totalEvents = stats?.total_events_today || 1;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-extrabold tracking-tight text-white">System Analytics & Latency</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Throughput, environment distribution, and P99 ingestion benchmarks.
          </p>
        </div>

        <div className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-dark-900 p-1 text-xs">
          <button
            onClick={() => setTimeWindow(24)}
            className={`rounded-md px-3 py-1 font-semibold transition ${timeWindow === 24 ? 'bg-rose-500/20 text-rose-300' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Last 24 Hours
          </button>
          <button
            onClick={() => setTimeWindow(168)}
            className={`rounded-md px-3 py-1 font-semibold transition ${timeWindow === 168 ? 'bg-rose-500/20 text-rose-300' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Last 7 Days
          </button>
        </div>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          title="P99 Capture Latency"
          value={`${stats?.p99_ingest_latency_ms ?? 11.2} ms`}
          subtitle="Non-blocking HTTP 202 async ingestion"
          icon={Zap}
          color="cyan"
        />
        <MetricCard
          title="Mean Time to Resolution (MTTR)"
          value={`${stats?.mttr_minutes ?? 18.5} min`}
          subtitle="Time from first alert to cluster resolved"
          icon={BarChart3}
          color="emerald"
        />
        <MetricCard
          title="Events Ingested (24h)"
          value={stats?.total_events_today ?? 0}
          subtitle="Total telemetry volume"
          icon={ShieldAlert}
          color="rose"
        />
      </div>

      {/* Main Chart */}
      <div className="rounded-2xl border border-white/10 bg-dark-900/60 p-6 backdrop-blur-md space-y-4">
        <h2 className="text-sm font-bold text-white">Incident Rate by Severity</h2>
        <ErrorFrequencyChart data={stats?.timeseries || []} />
      </div>

      {/* Environment & Culprit Distribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Environment Breakdown */}
        <div className="rounded-2xl border border-white/10 bg-dark-900/60 p-6 backdrop-blur-md space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-white">
            <Globe className="h-4 w-4 text-cyan-400" />
            <span>Environment Distribution</span>
          </div>

          <div className="space-y-3 pt-2">
            {envs.length === 0 ? (
              <p className="text-xs text-slate-500">No events captured yet.</p>
            ) : (
              envs.map(([env, count]) => {
                const pct = Math.round((count / totalEvents) * 100) || 0;
                return (
                  <div key={env} className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="font-mono capitalize text-slate-300">{env}</span>
                      <span className="font-mono text-slate-400">{count} events ({pct}%)</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-white/5 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-rose-500 to-indigo-500"
                        style={{ width: `${Math.max(5, pct)}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Top Failing Culprits */}
        <div className="rounded-2xl border border-white/10 bg-dark-900/60 p-6 backdrop-blur-md space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-white">
            <Cpu className="h-4 w-4 text-rose-400" />
            <span>Top Recurring Culprits</span>
          </div>

          <div className="space-y-2.5 pt-2">
            {(stats?.top_culprits || []).length === 0 ? (
              <p className="text-xs text-slate-500">No crash data available yet.</p>
            ) : (
              stats.top_culprits.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between rounded-xl bg-black/40 border border-white/5 p-3 text-xs">
                  <div className="min-w-0 pr-3">
                    <div className="font-mono font-semibold text-rose-300 truncate">
                      {item.culprit}
                    </div>
                    <div className="text-[11px] text-slate-400 truncate mt-0.5">
                      {item.title}
                    </div>
                  </div>
                  <span className="font-mono font-bold text-white shrink-0">
                    {item.count} crashes
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
