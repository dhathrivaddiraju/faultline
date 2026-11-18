import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import IncidentsList from './pages/IncidentsList';
import IncidentDetail from './pages/IncidentDetail';
import LiveStream from './pages/LiveStream';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import { 
  fetchProjects, 
  fetchIncidents, 
  fetchAnalytics, 
  updateIncidentStatus, 
  createWebSocketLiveStream 
} from './api/client';

export default function App() {
  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProject] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedIncidentId, setSelectedIncidentId] = useState(null);
  
  const [incidents, setIncidents] = useState([]);
  const [stats, setStats] = useState(null);
  const [liveEvents, setLiveEvents] = useState([]);
  const [wsStatus, setWsStatus] = useState('connecting');

  // Load projects
  const loadProjects = async () => {
    try {
      const projs = await fetchProjects();
      setProjects(projs);
      if (projs.length > 0 && !currentProject) {
        setCurrentProject(projs[0]);
      }
    } catch (e) {
      console.error('Failed to load projects', e);
    }
  };

  // Load telemetry data
  const loadTelemetry = useCallback(async () => {
    if (!currentProject) return;
    try {
      const [incList, statsData] = await Promise.all([
        fetchIncidents({ projectId: currentProject.id }),
        fetchAnalytics(currentProject.id)
      ]);
      setIncidents(incList);
      setStats(statsData);
    } catch (e) {
      console.error('Failed to load telemetry', e);
    }
  }, [currentProject]);

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (currentProject) {
      loadTelemetry();
      const interval = setInterval(loadTelemetry, 8000);
      return () => clearInterval(interval);
    }
  }, [currentProject, loadTelemetry]);

  // Connect real-time WebSocket live stream
  useEffect(() => {
    const cleanup = createWebSocketLiveStream(
      (data) => {
        if (data.type === 'new_event' && data.event) {
          setLiveEvents(prev => [data.event, ...prev.slice(0, 49)]);
          // Refresh incidents list and stats
          loadTelemetry();
        }
      },
      (status) => setWsStatus(status)
    );
    return cleanup;
  }, [loadTelemetry]);

  // Handle triggering a test crash from UI
  const handleSendTestError = async () => {
    if (!currentProject) return;
    try {
      const errorPayload = {
        exception_type: "ZeroDivisionError",
        message: "Division by zero encountered in payment discount calculation: rate/0",
        environment: "production",
        level: "error",
        stack_trace: [
          {
            filename: "app/services/checkout.py",
            lineno: 118,
            function: "calculate_discount",
            code_context: "discount = total_amount / promo_rate",
            in_app: true,
            vars: { "total_amount": 149.99, "promo_rate": 0 }
          }
        ],
        breadcrumbs: [
          { message: "User clicked 'Apply Coupon'", category: "ui" },
          { message: "Coupon code 'BLACKFRIDAY_FREE' verified", category: "promo" }
        ],
        user: { id: "usr_demo_101", email: "customer@demo.io" }
      };

      await fetch('/api/v1/capture', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Project-Key': currentProject.api_key
        },
        body: JSON.stringify(errorPayload)
      });
      // Short delay to let background worker process batch
      setTimeout(loadTelemetry, 400);
    } catch (e) {
      console.error('Test error capture failed', e);
    }
  };

  const handleQuickResolve = async (incidentId) => {
    try {
      await updateIncidentStatus(incidentId, 'resolved');
      setIncidents(prev => prev.map(inc => inc.id === incidentId ? { ...inc, status: 'resolved' } : inc));
    } catch (e) {
      console.error(e);
    }
  };

  const handleSelectIncident = (id) => {
    setSelectedIncidentId(id);
    setActiveTab('incident_detail');
  };

  return (
    <div className="min-h-screen bg-dark-950 text-slate-100 flex flex-col">
      <Navbar
        projects={projects}
        currentProject={currentProject}
        onSelectProject={(p) => {
          setCurrentProject(p);
          setSelectedIncidentId(null);
        }}
        wsStatus={wsStatus}
        onSendTestError={handleSendTestError}
      />

      <div className="flex flex-1">
        <Sidebar
          activeTab={activeTab === 'incident_detail' ? 'incidents' : activeTab}
          onSelectTab={(tab) => {
            setSelectedIncidentId(null);
            setActiveTab(tab);
          }}
          incidentCount={incidents.filter(i => i.status !== 'resolved').length}
        />

        <main className="flex-1 p-8 overflow-y-auto max-h-[calc(100vh-4rem)]">
          {activeTab === 'dashboard' && (
            <Dashboard
              stats={stats}
              incidents={incidents}
              onSelectIncident={handleSelectIncident}
              onNavigateTab={setActiveTab}
            />
          )}

          {activeTab === 'incidents' && (
            <IncidentsList
              incidents={incidents}
              onSelectIncident={handleSelectIncident}
              onQuickResolve={handleQuickResolve}
            />
          )}

          {activeTab === 'incident_detail' && selectedIncidentId && (
            <IncidentDetail
              incidentId={selectedIncidentId}
              onBack={() => {
                setSelectedIncidentId(null);
                setActiveTab('incidents');
              }}
            />
          )}

          {activeTab === 'live' && (
            <LiveStream
              liveEvents={liveEvents}
              onSelectIncident={handleSelectIncident}
              wsStatus={wsStatus}
            />
          )}

          {activeTab === 'analytics' && (
            <Analytics stats={stats} />
          )}

          {activeTab === 'settings' && (
            <Settings project={currentProject} />
          )}
        </main>
      </div>
    </div>
  );
}
