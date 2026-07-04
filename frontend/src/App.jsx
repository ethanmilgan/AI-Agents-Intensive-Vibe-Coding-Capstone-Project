import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Search, 
  Sparkles, 
  Terminal, 
  Settings as SettingsIcon, 
  Briefcase, 
  AlertTriangle,
  ChevronRight
} from 'lucide-react';
import Dashboard from './components/Dashboard';
import JobSearch from './components/JobSearch';
import Optimizer from './components/Optimizer';
import AgentConsole from './components/AgentConsole';
import Settings from './components/Settings';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [linkedinStatus, setLinkedinStatus] = useState('checking');
  const [pendingHITLs, setPendingHITLs] = useState([]);
  const [activeHITL, setActiveHITL] = useState(null);
  const [consoleSelectedAppId, setConsoleSelectedAppId] = useState(null);
  const [consoleStatusFilter, setConsoleStatusFilter] = useState('All');

  // Poll for LinkedIn Login status
  const checkLinkedinStatus = async () => {
    try {
      const res = await fetch('/api/linkedin/status');
      const data = await res.json();
      if (data.logged_in) {
        setLinkedinStatus('online');
      } else {
        setLinkedinStatus('offline');
      }
    } catch (e) {
      setLinkedinStatus('offline');
    }
  };

  // Poll for pending HITL prompts
  const checkPendingHITLs = async () => {
    try {
      const res = await fetch('/api/hitl/pending');
      const data = await res.json();
      setPendingHITLs(data);
      if (data.length > 0) {
        // Set the first pending prompt as active
        setActiveHITL(data[0]);
      } else {
        setActiveHITL(null);
      }
    } catch (e) {
      console.error("Failed to check HITLs:", e);
    }
  };

  useEffect(() => {
    checkLinkedinStatus();
    checkPendingHITLs();

    // Set up polling intervals
    const statusInterval = setInterval(checkLinkedinStatus, 15000);
    const hitlInterval = setInterval(checkPendingHITLs, 3000);

    return () => {
      clearInterval(statusInterval);
      clearInterval(hitlInterval);
    };
  }, []);

  const handleHITLBannerClick = () => {
    if (pendingHITLs.length > 0) {
      setConsoleSelectedAppId(pendingHITLs[0].application_id);
    } else if (activeHITL) {
      setConsoleSelectedAppId(activeHITL.application_id);
    }
    setConsoleStatusFilter('Needs Input');
    setActiveTab('console');
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard setActiveTab={setActiveTab} />;
      case 'search':
        return <JobSearch setActiveTab={setActiveTab} />;
      case 'optimizer':
        return <Optimizer />;
      case 'console':
        return (
          <AgentConsole 
            activeHITL={activeHITL} 
            refreshHITL={checkPendingHITLs} 
            initialSelectedAppId={consoleSelectedAppId}
            setInitialSelectedAppId={setConsoleSelectedAppId}
            initialStatusFilter={consoleStatusFilter}
            setInitialStatusFilter={setConsoleStatusFilter}
          />
        );
      case 'settings':
        return <Settings onProfileUpdated={checkLinkedinStatus} />;
      default:
        return <Dashboard setActiveTab={setActiveTab} />;
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="logo-container">
          <div className="logo-icon">
            <Briefcase size={20} color="#ffffff" />
          </div>
          <span className="logo-text">AIGravity</span>
        </div>

        <nav className="nav-links">
          <button 
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <LayoutDashboard size={18} />
            <span>Dashboard</span>
          </button>
          
          <button 
            className={`nav-item ${activeTab === 'search' ? 'active' : ''}`}
            onClick={() => setActiveTab('search')}
          >
            <Search size={18} />
            <span>Job Discovery</span>
          </button>
          
          <button 
            className={`nav-item ${activeTab === 'optimizer' ? 'active' : ''}`}
            onClick={() => setActiveTab('optimizer')}
          >
            <Sparkles size={18} />
            <span>ATS Optimizer</span>
          </button>
          
          <button 
            className={`nav-item ${activeTab === 'console' ? 'active' : ''}`}
            onClick={() => setActiveTab('console')}
          >
            <Terminal size={18} />
            <span>Agent Console</span>
            {pendingHITLs.length > 0 && (
              <span style={{
                marginLeft: 'auto',
                backgroundColor: 'var(--color-warning)',
                color: '#000000',
                borderRadius: '50%',
                width: '18px',
                height: '18px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '11px',
                fontWeight: 'bold'
              }}>
                {pendingHITLs.length}
              </span>
            )}
          </button>
          
          <button 
            className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <SettingsIcon size={18} />
            <span>Configuration</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="linkedin-status-badge">
            <span className={`status-dot ${linkedinStatus}`}></span>
            <span>
              {linkedinStatus === 'checking' && 'Verifying Session...'}
              {linkedinStatus === 'online' && 'LinkedIn Active'}
              {linkedinStatus === 'offline' && 'LinkedIn Disconnected'}
            </span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        {/* Global HITL Active Alert Banner */}
        {activeHITL && (
          <div className="hitl-alert-banner">
            <div className="hitl-alert-content">
              <AlertTriangle size={20} color="var(--color-warning)" />
              <div>
                <span className="hitl-alert-title">User Input Required!</span>
                <span className="hitl-alert-desc" style={{ marginLeft: '12px' }}>
                  The agent requires clarification on a screening question to resume submission.
                </span>
              </div>
            </div>
            <button 
              className="btn-primary" 
              style={{ padding: '6px 12px', fontSize: '12px', background: 'var(--color-warning)', color: '#000' }}
              onClick={handleHITLBannerClick}
            >
              <span>Resolve Question</span>
              <ChevronRight size={14} />
            </button>
          </div>
        )}

        {/* View Render */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {renderContent()}
        </div>
      </main>
    </div>
  );
}
