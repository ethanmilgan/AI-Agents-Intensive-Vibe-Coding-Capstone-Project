import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Search, 
  Sparkles, 
  Terminal, 
  Settings as SettingsIcon, 
  Briefcase, 
  AlertTriangle,
  ChevronRight,
  Lock
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
  
  // Track profile and settings to determine if configuration is complete
  const [profile, setProfile] = useState(null);
  const [settings, setSettings] = useState(null);

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

  // Fetch profile and settings to verify configuration completion
  const fetchConfigData = async () => {
    try {
      const pRes = await fetch('/api/profile');
      const pData = await pRes.json();
      if (pData) {
        setProfile(pData);
      }
      
      const sRes = await fetch('/api/settings');
      const sData = await sRes.json();
      if (sData) {
        setSettings(sData);
      }
    } catch (e) {
      console.error("Failed to fetch profile/settings config:", e);
    }
  };

  const refreshConfig = () => {
    checkLinkedinStatus();
    checkPendingHITLs();
    fetchConfigData();
  };

  useEffect(() => {
    refreshConfig();

    // Set up polling intervals
    const statusInterval = setInterval(checkLinkedinStatus, 15000);
    const hitlInterval = setInterval(checkPendingHITLs, 3000);
    const configInterval = setInterval(fetchConfigData, 10000);

    return () => {
      clearInterval(statusInterval);
      clearInterval(hitlInterval);
      clearInterval(configInterval);
    };
  }, []);

  // Configuration is complete if profile has a name, search settings have keyword/location, and LinkedIn is connected
  const isConfigComplete = 
    profile && 
    profile.personal_info && 
    profile.personal_info.full_name && 
    profile.personal_info.full_name.trim() !== '' &&
    settings &&
    settings.JOB_KEYWORDS && 
    settings.JOB_KEYWORDS.trim() !== '' &&
    settings.JOB_LOCATION && 
    settings.JOB_LOCATION.trim() !== '' &&
    linkedinStatus === 'online';

  const handleTabClick = (tabName) => {
    if (['search', 'console', 'optimizer'].includes(tabName) && !isConfigComplete) {
      alert("Please complete the Configuration first (upload your resume/profile, save preferences, and authenticate LinkedIn).");
      return;
    }
    setActiveTab(tabName);
  };

  const handleHITLBannerClick = () => {
    if (!isConfigComplete) return;
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
        return <Dashboard setActiveTab={handleTabClick} />;
      case 'search':
        return <JobSearch setActiveTab={handleTabClick} />;
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
        return <Settings onProfileUpdated={refreshConfig} />;
      default:
        return <Dashboard setActiveTab={handleTabClick} />;
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
          <span className="logo-text">NextRole.Ai</span>
        </div>

        <nav className="nav-links">
          {/* 1. Dashboard */}
          <button 
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => handleTabClick('dashboard')}
          >
            <LayoutDashboard size={18} />
            <span>Dashboard</span>
          </button>
          
          {/* 2. Configuration */}
          <button 
            className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => handleTabClick('settings')}
          >
            <SettingsIcon size={18} />
            <span>Configuration</span>
          </button>
          
          {/* 3. Job Discovery */}
          <button 
            className={`nav-item ${activeTab === 'search' ? 'active' : ''} ${!isConfigComplete ? 'locked-tab' : ''}`}
            onClick={() => handleTabClick('search')}
          >
            <Search size={18} />
            <span>Job Discovery</span>
            {!isConfigComplete && <Lock size={12} style={{ marginLeft: 'auto', opacity: 0.6 }} />}
          </button>
          
          {/* 4. Agent Console */}
          <button 
            className={`nav-item ${activeTab === 'console' ? 'active' : ''} ${!isConfigComplete ? 'locked-tab' : ''}`}
            onClick={() => handleTabClick('console')}
          >
            <Terminal size={18} />
            <span>Agent Console</span>
            {pendingHITLs.length > 0 && isConfigComplete && (
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
            {!isConfigComplete && <Lock size={12} style={{ marginLeft: 'auto', opacity: 0.6 }} />}
          </button>

          {/* 5. ATS Optimizer */}
          <button 
            className={`nav-item ${activeTab === 'optimizer' ? 'active' : ''} ${!isConfigComplete ? 'locked-tab' : ''}`}
            onClick={() => handleTabClick('optimizer')}
          >
            <Sparkles size={18} />
            <span>ATS Optimizer</span>
            {!isConfigComplete && <Lock size={12} style={{ marginLeft: 'auto', opacity: 0.6 }} />}
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
        {activeHITL && isConfigComplete && (
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
