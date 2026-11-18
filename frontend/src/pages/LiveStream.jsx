import React from 'react';
import LiveEventFeed from '../components/LiveEventFeed';

export default function LiveStream({ liveEvents = [], onSelectIncident, wsStatus }) {
  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-xl font-extrabold tracking-tight text-white">Live Error Telemetry Feed</h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Realtime event ingestion stream via WebSocket (`/api/v1/ws/live-stream`).
        </p>
      </div>

      <LiveEventFeed liveEvents={liveEvents} onSelectIncident={onSelectIncident} />
    </div>
  );
}
