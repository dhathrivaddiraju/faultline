const BASE_URL = import.meta.env.VITE_API_URL || '';

export async function fetchProjects() {
  const res = await fetch(`${BASE_URL}/api/v1/projects`);
  if (!res.ok) throw new Error('Failed to fetch projects');
  return res.json();
}

export async function fetchIncidents(params = {}) {
  const query = new URLSearchParams();
  if (params.projectId) query.set('project_id', params.projectId);
  if (params.status && params.status !== 'all') query.set('status', params.status);
  if (params.severity && params.severity !== 'all') query.set('severity', params.severity);
  if (params.search) query.set('search', params.search);
  query.set('limit', params.limit || 50);

  const res = await fetch(`${BASE_URL}/api/v1/incidents?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch incidents');
  return res.json();
}

export async function fetchIncidentDetail(incidentId) {
  const res = await fetch(`${BASE_URL}/api/v1/incidents/${incidentId}`);
  if (!res.ok) throw new Error('Failed to fetch incident details');
  return res.json();
}

export async function updateIncidentStatus(incidentId, status) {
  const res = await fetch(`${BASE_URL}/api/v1/incidents/${incidentId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status })
  });
  if (!res.ok) throw new Error('Failed to update incident');
  return res.json();
}

export async function triggerAiAnalysis(incidentId) {
  const res = await fetch(`${BASE_URL}/api/v1/incidents/${incidentId}/ai-analyze`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to trigger AI analysis');
  return res.json();
}

export async function fetchAnalytics(projectId = null, hours = 24) {
  const query = new URLSearchParams({ hours });
  if (projectId) query.set('project_id', projectId);
  
  const res = await fetch(`${BASE_URL}/api/v1/analytics/stats?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch analytics');
  return res.json();
}

export function createWebSocketLiveStream(onMessage, onStatusChange) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/live-stream`;
  
  let ws;
  let reconnectTimer;
  let heartbeatTimer;

  function connect() {
    try {
      ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        if (onStatusChange) onStatusChange('connected');
        heartbeatTimer = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 15000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type !== 'pong') {
            onMessage(data);
          }
        } catch (e) {
          console.error('Failed to parse WS message', e);
        }
      };

      ws.onclose = () => {
        if (onStatusChange) onStatusChange('disconnected');
        clearInterval(heartbeatTimer);
        reconnectTimer = setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        if (onStatusChange) onStatusChange('error');
      };
    } catch (e) {
      if (onStatusChange) onStatusChange('error');
      reconnectTimer = setTimeout(connect, 4000);
    }
  }

  connect();

  return () => {
    clearInterval(heartbeatTimer);
    clearTimeout(reconnectTimer);
    if (ws) ws.close();
  };
}
