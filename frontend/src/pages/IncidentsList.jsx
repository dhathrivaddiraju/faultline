import React, { useState } from 'react';
import { Search, Cpu, Check, Users, AlertTriangle, ArrowRight } from 'lucide-react';
import { SeverityBadge, StatusBadge } from '../components/StatusBadge';

export default function IncidentsList({ incidents = [], onSelectIncident, onQuickResolve }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');

  const filteredIncidents = incidents.filter(incident => {
    if (statusFilter !== 'all' && incident.status !== statusFilter) return false;
    if (severityFilter !== 'all' && incident.severity !== severityFilter) return false;
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      const matchesTitle = incident.title?.toLowerCase().includes(query);
      const matchesCulprit = incident.culprit?.toLowerCase().includes(query);
      const matchesType = incident.exception_type?.toLowerCase().includes(query);
      if (!matchesTitle && !matchesCulprit && !matchesType) return false;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">Incident Clusters</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Normalized error groups clustered by stack trace fingerprint.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {['all', 'unresolved', 'investigating', 'resolved'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold capitalize transition ${
                statusFilter === status
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                  : 'bg-white/5 text-slate-400 hover:text-slate-200 border border-white/5'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by exception, culprit, or error message..."
            className="w-full rounded-xl border border-white/10 bg-dark-900/80 pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:border-rose-500 focus:outline-none focus:ring-1 focus:ring-rose-500"
          />
        </div>

        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="rounded-xl border border-white/10 bg-dark-900/80 px-3 py-2 text-xs text-slate-300 focus:border-rose-500 focus:outline-none"
        >
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="error">Error</option>
          <option value="warning">Warning</option>
        </select>
      </div>

      <div className="rounded-2xl border border-white/10 bg-dark-900/60 overflow-hidden backdrop-blur-md">
        {filteredIncidents.length === 0 ? (
          <div className="py-16 text-center text-xs text-slate-400 space-y-2">
            <AlertTriangle className="h-8 w-8 text-slate-600 mx-auto" />
            <p className="font-semibold text-slate-300">No matching incident clusters found</p>
            <p className="text-slate-500">Modify filter selections or search terms.</p>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {filteredIncidents.map((incident) => (
              <div
                key={incident.id}
                onClick={() => onSelectIncident(incident.id)}
                className="group flex flex-col sm:flex-row sm:items-center justify-between p-4 hover:bg-white/[0.02] cursor-pointer transition gap-4"
              >
                <div className="flex items-start gap-4 min-w-0">
                  <div className="mt-0.5">
                    <SeverityBadge severity={incident.severity} />
                  </div>

                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs font-bold text-white group-hover:text-rose-300 transition truncate max-w-xl">
                        {incident.title}
                      </span>
                      <StatusBadge status={incident.status} />
                      {incident.ai_analysis && (
                        <span className="flex items-center gap-1 rounded bg-rose-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-rose-400 border border-rose-500/20">
                          <Cpu className="h-3 w-3" />
                          Analyzed
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3 text-[11px] text-slate-500 font-mono">
                      <span className="text-slate-400 truncate max-w-md">{incident.culprit || 'unknown:culprit'}</span>
                      <span>•</span>
                      <span>First seen {new Date(incident.first_seen).toLocaleDateString()}</span>
                      <span>•</span>
                      <span>Last seen {new Date(incident.last_seen).toLocaleTimeString()}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-6 shrink-0 self-end sm:self-center">
                  <div className="text-right">
                    <div className="font-mono text-xs font-bold text-white">
                      {incident.events_count.toLocaleString()}
                    </div>
                    <div className="text-[10px] text-slate-500">events</div>
                  </div>

                  <div className="text-right">
                    <div className="font-mono text-xs font-bold text-white flex items-center gap-1 justify-end">
                      <Users className="h-3 w-3 text-slate-400" />
                      {incident.users_impacted.toLocaleString()}
                    </div>
                    <div className="text-[10px] text-slate-500">users</div>
                  </div>

                  {incident.status !== 'resolved' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onQuickResolve(incident.id);
                      }}
                      title="Mark as resolved"
                      className="rounded-lg border border-white/10 p-2 text-slate-400 hover:text-emerald-400 hover:border-emerald-500/40 hover:bg-emerald-500/10 transition"
                    >
                      <Check className="h-4 w-4" />
                    </button>
                  )}

                  <ArrowRight className="h-4 w-4 text-slate-600 group-hover:text-rose-400 transition" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
