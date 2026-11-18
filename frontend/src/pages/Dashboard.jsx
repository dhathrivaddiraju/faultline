import React from 'react';
import { 
  AlertTriangle, 
  CheckCircle, 
  Gauge, 
  Zap, 
  ChevronRight,
  TrendingUp,
  Cpu
} from 'lucide-react';
import MetricCard from '../components/MetricCard';
import ErrorFrequencyChart from '../components/ErrorFrequencyChart';
import { SeverityBadge } from '../components/StatusBadge';

export default function Dashboard({ stats, incidents = [], onSelectIncident, onNavigateTab }) {
  const unresolvedIncidents = incidents.filter(i => i.status !== 'resolved').slice(0, 6);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">System Observability Overview</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Ingestion throughput, error clustering, and failure telemetry.
          </p>
        </div>

        <button
          onClick={() => onNavigateTab('incidents')}
          className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:bg-white/10 transition"
        >
          <span>View All Incidents</span>
          <ChevronRight className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="Errors (24h)"
          value={stats?.total_events_today ?? 0}
          subtitle="Total captured events"
          icon={AlertTriangle}
          color="rose"
        />
        <MetricCard
          title="Active Clusters"
          value={stats?.active_incidents ?? 0}
          subtitle="Unresolved error groups"
          icon={TrendingUp}
          color="amber"
        />
        <MetricCard
          title="Ingestion Latency"
          value={`${stats?.p99_ingest_latency_ms ?? 0}ms`}
          subtitle="P99 async queue duration"
          icon={Zap}
          color="cyan"
        />
        <MetricCard
          title="Error Rate"
          value={`${stats?.error_rate_per_min ?? 0}/m`}
          subtitle="Events per minute"
          icon={Gauge}
          color="purple"
        />
        <MetricCard
          title="Resolved Clusters"
          value={stats?.resolved_incidents ?? 0}
          subtitle="Closed issues"
          icon={CheckCircle}
          color="emerald"
        />
      </div>

      <div className="rounded-2xl border border-white/10 bg-dark-900/60 p-6 backdrop-blur-md">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-bold tracking-tight text-white">Error Frequency Over Time</h2>
            <p className="text-xs text-slate-400">Hourly event volume partitioned by severity tier</p>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5 text-rose-400">
              <span className="h-2 w-2 rounded-full bg-rose-500"></span>
              Critical
            </span>
            <span className="flex items-center gap-1.5 text-orange-400">
              <span className="h-2 w-2 rounded-full bg-orange-500"></span>
              Error
            </span>
            <span className="flex items-center gap-1.5 text-amber-400">
              <span className="h-2 w-2 rounded-full bg-amber-500"></span>
              Warning
            </span>
          </div>
        </div>

        <ErrorFrequencyChart data={stats?.timeseries || []} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-2xl border border-white/10 bg-dark-900/60 p-6 backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white">Active Incidents</h2>
            <button
              onClick={() => onNavigateTab('incidents')}
              className="text-xs text-rose-400 hover:text-rose-300 font-medium"
            >
              View all
            </button>
          </div>

          {unresolvedIncidents.length === 0 ? (
            <div className="py-10 text-center text-xs text-slate-400">
              No unresolved incident clusters. System operating normally.
            </div>
          ) : (
            <div className="space-y-2.5">
              {unresolvedIncidents.map((inc) => (
                <div
                  key={inc.id}
                  onClick={() => onSelectIncident(inc.id)}
                  className="group flex items-center justify-between rounded-xl border border-white/5 bg-dark-950/60 p-3.5 hover:border-rose-500/30 hover:bg-dark-850 cursor-pointer transition"
                >
                  <div className="flex items-center gap-3.5 min-w-0">
                    <SeverityBadge severity={inc.severity} />
                    <div className="min-w-0">
                      <p className="font-mono text-xs font-semibold text-white group-hover:text-rose-300 transition truncate">
                        {inc.title}
                      </p>
                      <p className="text-[11px] font-mono text-slate-500 mt-0.5 truncate">
                        {inc.culprit || 'unknown:culprit'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 shrink-0">
                    <div className="text-right">
                      <span className="font-mono text-xs font-bold text-slate-200">
                        {inc.events_count}
                      </span>
                      <span className="text-[10px] text-slate-500 block">events</span>
                    </div>
                    {inc.ai_analysis && (
                      <span className="flex items-center gap-1 rounded bg-rose-500/10 px-1.5 py-0.5 text-[10px] font-medium text-rose-400 border border-rose-500/20">
                        <Cpu className="h-3 w-3" />
                        Analyzed
                      </span>
                    )}
                    <ChevronRight className="h-4 w-4 text-slate-600 group-hover:text-rose-400 transition" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-white/10 bg-dark-900/60 p-6 backdrop-blur-md space-y-4">
          <h2 className="text-sm font-bold text-white">Top Failing Culprits</h2>

          <div className="space-y-3">
            {(stats?.top_culprits || []).length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500">
                No failure data collected.
              </div>
            ) : (
              stats.top_culprits.map((item, idx) => (
                <div key={idx} className="rounded-xl border border-white/5 bg-black/40 p-3 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-semibold text-rose-300 truncate max-w-[180px]">
                      {item.culprit}
                    </span>
                    <span className="font-mono text-slate-400 font-bold">
                      {item.count} events
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 truncate">
                    {item.title}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
