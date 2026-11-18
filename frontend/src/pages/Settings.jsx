import React, { useState } from 'react';
import { Key, Copy, Check, Terminal, Code2, Shield, Bell, Send } from 'lucide-react';

export default function Settings({ project }) {
  const [copiedKey, setCopiedKey] = useState(false);
  const [copiedCurl, setCopiedCurl] = useState(false);
  const [copiedPython, setCopiedPython] = useState(false);

  const apiKey = project?.api_key || 'fl_live_production_demo_key_99';
  const endpoint = window.location.origin;

  const pythonSnippet = `import faultline

# Initialize Faultline monitoring SDK
faultline.init(
    api_key="${apiKey}",
    endpoint="${endpoint}",
    environment="production"
)

# Optional: Add breadcrumbs leading to the event
faultline.add_breadcrumb("User initiated checkout", category="ui")

# 1. Automatic capture:
# Unhandled exceptions are automatically captured via global hooks!

# 2. Decorator capture:
@faultline.capture_exceptions(tags={"service": "checkout"})
def process_order(order_id):
    # Your business logic
    pass

# 3. Manual capture:
try:
    charge_customer()
except Exception as e:
    faultline.capture_exception(e, tags={"importance": "high"})
`;

  const curlSnippet = `curl -X POST "${endpoint}/api/v1/capture" \\
  -H "Content-Type: application/json" \\
  -H "X-Project-Key: ${apiKey}" \\
  -d '{
    "exception_type": "PaymentFailedError",
    "message": "Gateway timed out during 3D-Secure challenge",
    "environment": "production",
    "level": "error",
    "stack_trace": [
      {
        "filename": "app/services/billing.py",
        "lineno": 142,
        "function": "process_charge",
        "code_context": "raise PaymentFailedError(\\"Gateway timed out\\")",
        "in_app": true
      }
    ],
    "breadcrumbs": [
      {"message": "User initiated checkout", "category": "ui"}
    ]
  }'`;

  const copyText = (text, setCopied) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-xl font-extrabold tracking-tight text-white">Project Configuration & SDK Setup</h1>
        <p className="text-xs text-slate-400 mt-0.5">
          API credentials, SDK integration guides, and ingestion endpoints.
        </p>
      </div>

      {/* Project Key Card */}
      <div className="rounded-2xl border border-white/10 bg-dark-900/60 p-6 backdrop-blur-md space-y-4">
        <div className="flex items-center gap-2 text-sm font-bold text-white">
          <Key className="h-4 w-4 text-rose-400" />
          <span>Project Ingestion API Key</span>
        </div>
        <p className="text-xs text-slate-400">
          Used to authenticate telemetry payloads sent by client/server SDKs to the ingestion pipeline.
        </p>

        <div className="flex items-center gap-2">
          <input
            type="text"
            readOnly
            value={apiKey}
            className="flex-1 rounded-xl border border-white/10 bg-black/60 px-4 py-2.5 font-mono text-xs text-rose-300 focus:outline-none select-all"
          />
          <button
            onClick={() => copyText(apiKey, setCopiedKey)}
            className="flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-xs font-semibold text-slate-200 hover:bg-white/10 transition"
          >
            {copiedKey ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
            <span>{copiedKey ? 'Copied' : 'Copy Key'}</span>
          </button>
        </div>
      </div>

      {/* Python SDK Setup Card */}
      <div className="rounded-2xl border border-white/10 bg-dark-900/60 p-6 backdrop-blur-md space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-bold text-white">
            <Code2 className="h-4 w-4 text-cyan-400" />
            <span>Python SDK Quickstart</span>
          </div>
          <button
            onClick={() => copyText(pythonSnippet, setCopiedPython)}
            className="flex items-center gap-1 text-xs text-slate-400 hover:text-white transition"
          >
            {copiedPython ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
            <span>{copiedPython ? 'Copied' : 'Copy Code'}</span>
          </button>
        </div>

        <div className="rounded-xl border border-white/10 bg-black/70 p-4 font-mono text-xs text-slate-300 overflow-x-auto">
          <pre>{pythonSnippet}</pre>
        </div>
      </div>

      {/* cURL Ingestion Endpoint Card */}
      <div className="rounded-2xl border border-white/10 bg-dark-900/60 p-6 backdrop-blur-md space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-bold text-white">
            <Terminal className="h-4 w-4 text-amber-400" />
            <span>Direct HTTP Ingestion (cURL / Any Language)</span>
          </div>
          <button
            onClick={() => copyText(curlSnippet, setCopiedCurl)}
            className="flex items-center gap-1 text-xs text-slate-400 hover:text-white transition"
          >
            {copiedCurl ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
            <span>{copiedCurl ? 'Copied' : 'Copy cURL'}</span>
          </button>
        </div>

        <div className="rounded-xl border border-white/10 bg-black/70 p-4 font-mono text-xs text-amber-200/90 overflow-x-auto">
          <pre>{curlSnippet}</pre>
        </div>
      </div>
    </div>
  );
}
