import React, { useState } from 'react';
import { Sparkles, CheckCircle2, RefreshCw, AlertCircle, Copy, Check, GitCommit } from 'lucide-react';

export default function AiSummaryCard({ analysis, onReanalyze, loading }) {
  const [copied, setCopied] = useState(false);

  if (!analysis) {
    return (
      <div className="rounded-xl border border-rose-500/30 bg-gradient-to-br from-rose-950/20 via-dark-900/60 to-dark-950 p-6 backdrop-blur-md">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Claude 3.5 Sonnet Analysis</h3>
              <p className="text-xs text-slate-400">Automated root cause summary and fix recommendation</p>
            </div>
          </div>
          <button
            onClick={onReanalyze}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg bg-rose-600 px-3.5 py-2 text-xs font-semibold text-white shadow-lg shadow-rose-600/30 hover:bg-rose-500 transition disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Analyzing with Claude...' : 'Generate AI Diagnosis'}</span>
          </button>
        </div>
      </div>
    );
  }

  const { hypothesis, vulnerable_code, remediation_steps = [], suggested_fix_diff, confidence, analyzed_at } = analysis;

  const copyDiff = () => {
    if (suggested_fix_diff) {
      navigator.clipboard.writeText(suggested_fix_diff);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="relative overflow-hidden rounded-2xl border border-rose-500/30 bg-gradient-to-br from-rose-950/25 via-dark-900/80 to-dark-950 p-6 shadow-2xl backdrop-blur-xl">
      {/* Glow effect */}
      <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-rose-600/15 blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between pb-5 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-rose-600 to-indigo-600 text-white shadow-lg shadow-rose-600/25">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h3 className="text-sm font-bold tracking-tight text-white">Claude 3.5 Sonnet Incident Diagnosis</h3>
              <span className="rounded-full bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-bold text-emerald-400">
                {Math.round((confidence || 0.95) * 100)}% Confidence
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Auto-generated root-cause hypotheses, vulnerable frames, and remediation diff.
            </p>
          </div>
        </div>

        <button
          onClick={onReanalyze}
          disabled={loading}
          className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-white/10 transition disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-rose-400' : ''}`} />
          <span>{loading ? 'Re-analyzing...' : 'Re-run Analysis'}</span>
        </button>
      </div>

      {/* 1. Root Cause Hypothesis */}
      <div className="mt-5 space-y-2">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-rose-400">
          <AlertCircle className="h-3.5 w-3.5" />
          <span>1. Root Cause Hypothesis</span>
        </div>
        <div className="rounded-xl border border-rose-500/20 bg-rose-950/20 p-4 text-xs leading-relaxed text-slate-200">
          {hypothesis}
        </div>
      </div>

      {/* 2. Vulnerable Code Snippet */}
      {vulnerable_code && (
        <div className="mt-5 space-y-2">
          <div className="text-xs font-bold uppercase tracking-wider text-amber-400">
            2. Vulnerable Code Snippet
          </div>
          <div className="rounded-xl border border-white/10 bg-black/60 p-4 font-mono text-xs text-amber-200/90 overflow-x-auto">
            <pre>{vulnerable_code}</pre>
          </div>
        </div>
      )}

      {/* 3. Step-by-Step Remediation Plan */}
      {remediation_steps.length > 0 && (
        <div className="mt-5 space-y-2">
          <div className="text-xs font-bold uppercase tracking-wider text-cyan-400">
            3. Step-by-Step Remediation Plan
          </div>
          <div className="space-y-2">
            {remediation_steps.map((step, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 rounded-lg border border-white/5 bg-white/[0.02] p-3 text-xs text-slate-300"
              >
                <CheckCircle2 className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{step}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. Suggested Fix Diff */}
      {suggested_fix_diff && (
        <div className="mt-5 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-400">
              <GitCommit className="h-3.5 w-3.5" />
              <span>4. Suggested Fix Diff</span>
            </div>
            <button
              onClick={copyDiff}
              className="flex items-center gap-1 text-[11px] font-medium text-slate-400 hover:text-white transition"
            >
              {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
              <span>{copied ? 'Copied' : 'Copy Diff'}</span>
            </button>
          </div>

          <div className="rounded-xl border border-white/10 bg-black/70 p-4 font-mono text-xs overflow-x-auto space-y-1">
            {suggested_fix_diff.split('\n').map((line, idx) => {
              const isRem = line.startsWith('-');
              const isAdd = line.startsWith('+');
              return (
                <div
                  key={idx}
                  className={`px-1 py-0.5 rounded ${
                    isRem ? 'bg-rose-500/20 text-rose-300' : isAdd ? 'bg-emerald-500/20 text-emerald-300' : 'text-slate-400'
                  }`}
                >
                  {line}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
