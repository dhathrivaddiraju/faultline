import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  Check, 
  CheckCircle2, 
  Clock, 
  Users, 
  Hash, 
  Layers, 
  Tag, 
  Server, 
  User, 
  Copy, 
  RefreshCw,
  AlertOctagon
} from 'lucide-react';
import { fetchIncidentDetail, updateIncidentStatus, triggerAiAnalysis } from '../api/client';
import { SeverityBadge, StatusBadge } from '../components/StatusBadge';
import AiSummaryCard from '../components/AiSummaryCard';
import StackTraceViewer from '../components/StackTraceViewer';
import BreadcrumbTrail from '../components/BreadcrumbTrail';

export default function IncidentDetail({ incidentId, onBack }) {
  const [incident, setIncident] = useState(null);
  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('stacktrace'); // stacktrace, breadcrumbs, context, raw
  const [copiedFp, setCopiedFp] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await fetchIncidentDetail(incidentId);
      setIncident(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [incidentId]);

  const handleStatusChange = async (newStatus) => {
    try {
      await updateIncidentStatus(incidentId, newStatus);
      setIncident(prev => ({ ...prev, status: newStatus }));
    } catch (e) {
      console.error('Failed to update status', e);
    }
  };

  const handleAiReanalyze = async () => {
    try {
      setAiLoading(true);
      const res = await triggerAiAnalysis(incidentId);
      if (res.ai_analysis) {
        setIncident(prev => ({ ...prev, ai_analysis: res.ai_analysis }));
      }
    } catch (e) {
      console.error('Failed to trigger AI analysis', e);
    } finally {
      setAiLoading(false);
    }
  };

  const copyFingerprint = () => {
    if (incident?.fingerprint) {
      navigator.clipboard.writeText(incident.fingerprint);
      setCopiedFp(true);
      setTimeout(() => setCopiedFp(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <RefreshCw className="h-6 w-6 animate-spin text-rose-500" />
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="py-12 text-center text-xs text-slate-400">
        Incident not found.
      </div>
    );
  }

  const latestEvent = incident.latest_event || {};

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold text-slate-300 hover:bg-white/10 transition"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Incidents</span>
        </button>

        {/* Status Actions */}
        <div className="flex items-center gap-2">
          {incident.status !== 'resolved' ? (
            <button
              onClick={() => handleStatusChange('resolved')}
              className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white shadow-lg shadow-emerald-600/20 hover:bg-emerald-500 transition"
            >
              <Check className="h-3.5 w-3.5" />
              <span>Mark as Resolved</span>
            </button>
          ) : (
            <button
              onClick={() => handleStatusChange('unresolved')}
              className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold text-slate-300 hover:bg-white/10 transition"
            >
              <span>Re-open Incident</span>
            </button>
          )}

          <select
            value={incident.status}
            onChange={(e) => handleStatusChange(e.target.value)}
            className="rounded-lg border border-white/10 bg-dark-900 px-3 py-1.5 text-xs font-semibold text-slate-300 focus:outline-none"
          >
            <option value="unresolved">Unresolved</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
            <option value="ignored">Ignored</option>
          </select>
        </div>
      </div>

      {/* Incident Header Card */}
      <div className="rounded-2xl border border-white/10 bg-dark-900/80 p-6 backdrop-blur-md space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5 flex-wrap">
              <SeverityBadge severity={incident.severity} />
              <StatusBadge status={incident.status} />
              <span className="font-mono text-xs font-bold text-rose-400">
                {incident.exception_type}
              </span>
            </div>
            <h1 className="text-lg font-bold text-white tracking-tight break-all font-mono">
              {incident.title}
            </h1>
            <p className="font-mono text-xs text-slate-400">
              Culprit: <span className="text-slate-200">{incident.culprit || 'unknown:culprit'}</span>
            </p>
          </div>

          <div className="flex items-center gap-6 shrink-0 bg-dark-950/80 rounded-xl p-3 border border-white/5">
            <div className="text-center">
              <span className="font-mono text-base font-bold text-white">
                {incident.events_count?.toLocaleString()}
              </span>
              <span className="text-[10px] text-slate-500 block">Occurrences</span>
            </div>
            <div className="w-px h-8 bg-white/10"></div>
            <div className="text-center">
              <span className="font-mono text-base font-bold text-white">
                {incident.users_impacted?.toLocaleString()}
              </span>
              <span className="text-[10px] text-slate-500 block">Impacted Users</span>
            </div>
          </div>
        </div>

        {/* Metadata pills */}
        <div className="flex items-center gap-4 text-xs text-slate-400 pt-2 border-t border-white/5 flex-wrap">
          <button
            onClick={copyFingerprint}
            className="flex items-center gap-1.5 rounded bg-white/5 px-2 py-1 font-mono text-[11px] text-slate-300 hover:bg-white/10 transition"
          >
            <Hash className="h-3 w-3 text-slate-500" />
            <span>Fingerprint: {incident.fingerprint?.slice(0, 12)}...</span>
            {copiedFp ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
          </button>
          
          <div className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5 text-slate-500" />
            <span>First seen: {new Date(incident.first_seen).toLocaleString()}</span>
          </div>

          <div className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5 text-slate-500" />
            <span>Last seen: {new Date(incident.last_seen).toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Hero Section: Claude 3.5 Sonnet Analysis */}
      <AiSummaryCard
        analysis={incident.ai_analysis}
        onReanalyze={handleAiReanalyze}
        loading={aiLoading}
      />

      {/* Detailed Inspection Tabs */}
      <div className="space-y-4">
        {/* Tab Buttons */}
        <div className="flex items-center gap-2 border-b border-white/10 pb-2">
          {[
            { id: 'stacktrace', label: 'Stack Trace' },
            { id: 'breadcrumbs', label: 'Breadcrumbs Trail' },
            { id: 'context', label: 'Tags & Context' },
            { id: 'raw', label: 'Raw Event JSON' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition ${
                activeTab === tab.id
                  ? 'bg-white/10 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'stacktrace' && (
          <StackTraceViewer frames={latestEvent.stack_trace || []} />
        )}

        {activeTab === 'breadcrumbs' && (
          <BreadcrumbTrail breadcrumbs={latestEvent.breadcrumbs || []} />
        )}

        {activeTab === 'context' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            {/* User Context */}
            <div className="rounded-xl border border-white/10 bg-dark-900/60 p-5 space-y-3">
              <div className="flex items-center gap-2 font-bold uppercase tracking-wider text-cyan-400">
                <User className="h-4 w-4" />
                <span>User Context</span>
              </div>
              <div className="rounded-lg bg-black/50 p-3 font-mono space-y-1 border border-white/5">
                <div>ID: <span className="text-slate-200">{latestEvent.user_context?.id || 'anonymous'}</span></div>
                <div>Email: <span className="text-slate-200">{latestEvent.user_context?.email || 'N/A'}</span></div>
                <div>IP Address: <span className="text-slate-200">{latestEvent.user_context?.ip_address || '127.0.0.1'}</span></div>
              </div>
            </div>

            {/* Server & Runtime Context */}
            <div className="rounded-xl border border-white/10 bg-dark-900/60 p-5 space-y-3">
              <div className="flex items-center gap-2 font-bold uppercase tracking-wider text-purple-400">
                <Server className="h-4 w-4" />
                <span>Runtime & Environment</span>
              </div>
              <div className="rounded-lg bg-black/50 p-3 font-mono space-y-1 border border-white/5">
                <div>Environment: <span className="text-slate-200">{latestEvent.environment || 'production'}</span></div>
                <div>Release: <span className="text-slate-200">{latestEvent.release || 'v1.0.0'}</span></div>
                <div>Handled: <span className="text-slate-200">{String(latestEvent.handled)}</span></div>
              </div>
            </div>

            {/* Custom Tags */}
            <div className="md:col-span-2 rounded-xl border border-white/10 bg-dark-900/60 p-5 space-y-3">
              <div className="flex items-center gap-2 font-bold uppercase tracking-wider text-amber-400">
                <Tag className="h-4 w-4" />
                <span>Custom Tags</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(latestEvent.tags || {}).length === 0 ? (
                  <span className="text-slate-500 font-mono">No custom tags attached.</span>
                ) : (
                  Object.entries(latestEvent.tags || {}).map(([k, v]) => (
                    <span
                      key={k}
                      className="rounded-lg bg-white/5 border border-white/10 px-2.5 py-1 font-mono text-[11px] text-slate-300"
                    >
                      <span className="text-slate-500">{k}:</span> {String(v)}
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'raw' && (
          <div className="rounded-xl border border-white/10 bg-black/70 p-5 font-mono text-xs overflow-x-auto text-slate-300">
            <pre>{JSON.stringify(latestEvent, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
