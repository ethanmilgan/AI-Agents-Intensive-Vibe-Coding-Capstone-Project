import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Pause, 
  CheckCircle, 
  XCircle, 
  HelpCircle, 
  Terminal, 
  Image as ImageIcon,
  RefreshCw,
  AlertTriangle
} from 'lucide-react';

export default function AgentConsole({ activeHITL, refreshHITL, initialSelectedAppId, setInitialSelectedAppId, initialStatusFilter, setInitialStatusFilter }) {
  const [apps, setApps] = useState([]);
  const [selectedAppId, setSelectedAppId] = useState(initialSelectedAppId || null);
  const [selectedApp, setSelectedApp] = useState(null);
  const [logs, setLogs] = useState([]);
  const [hitlPrompt, setHitlPrompt] = useState(null);
  const [hitlAnswer, setHitlAnswer] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [screenshotVersion, setScreenshotVersion] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState(initialStatusFilter || 'All');

  const fetchApplications = async () => {
    try {
      const res = await fetch('/api/applications');
      const data = await res.json();
      setApps(data);
      
      if (data.length > 0) {
        setSelectedAppId(prev => prev || data[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchLogs = async (id) => {
    if (!id) return;
    try {
      const res = await fetch(`/api/applications/${id}/logs`);
      const data = await res.json();
      setLogs(data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchHITLPrompt = async (appId) => {
    if (!appId) return;
    try {
      // Find matching HITL from pending
      const res = await fetch('/api/hitl/pending');
      const prompts = await res.json();
      const match = prompts.find(p => p.application_id === appId);
      setHitlPrompt(match || null);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchApplications();
    const interval = setInterval(fetchApplications, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (initialSelectedAppId) {
      setSelectedAppId(initialSelectedAppId);
      if (setInitialSelectedAppId) setInitialSelectedAppId(null);
    }
  }, [initialSelectedAppId]);

  useEffect(() => {
    if (initialStatusFilter) {
      setStatusFilter(initialStatusFilter);
      if (setInitialStatusFilter) setInitialStatusFilter(null);
    }
  }, [initialStatusFilter]);

  useEffect(() => {
    if (apps.length > 0 && selectedAppId) {
      const current = apps.find(a => a.id === selectedAppId);
      setSelectedApp(current || null);
    }
  }, [apps, selectedAppId]);

  useEffect(() => {
    if (selectedAppId) {
      fetchLogs(selectedAppId);
      fetchHITLPrompt(selectedAppId);
      // Increment version to reload screenshot image if running
      if (selectedApp && ['Running', 'Waiting for User Input', 'Waiting for Final Review'].includes(selectedApp.status)) {
        setScreenshotVersion(v => v + 1);
      }
      
      const logInterval = setInterval(() => {
        fetchLogs(selectedAppId);
        fetchHITLPrompt(selectedAppId);
        setScreenshotVersion(v => v + 1);
      }, 3000);
      
      return () => clearInterval(logInterval);
    }
  }, [selectedAppId]);

  const handleResolveHITL = async (e) => {
    e.preventDefault();
    if (!hitlPrompt || !hitlAnswer.trim()) return;

    setLoading(true);
    try {
      const res = await fetch('/api/hitl/resolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt_id: hitlPrompt.id,
          answer: hitlAnswer
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        setHitlAnswer('');
        setHitlPrompt(null);
        refreshHITL();
        fetchApplications();
      } else {
        alert("Resolution failed: " + data.message);
      }
    } catch (e) {
      console.error(e);
      alert("Error resolving HITL: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveFinalReview = async () => {
    if (!selectedApp) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/applications/${selectedApp.id}/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: 'Completed'
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        fetchApplications();
        if (refreshHITL) refreshHITL();
      } else {
        alert("Failed to approve: " + data.message);
      }
    } catch (e) {
      console.error(e);
      alert("Error approving: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelApplication = async () => {
    if (!selectedApp) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/applications/${selectedApp.id}/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: 'Cancelled'
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        alert("Application process cancelled.");
        fetchApplications();
        if (refreshHITL) refreshHITL();
      } else {
        alert("Failed to cancel: " + data.message);
      }
    } catch (e) {
      console.error(e);
      alert("Error cancelling: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Completed':
        return <span style={{ color: 'var(--color-success)', fontWeight: 'bold' }}>✓ COMPLETED</span>;
      case 'Failed':
        return <span style={{ color: 'var(--color-error)', fontWeight: 'bold' }}>✗ FAILED</span>;
      case 'Cancelled':
        return <span style={{ color: 'var(--text-muted)', fontWeight: 'bold' }}>⚪ CANCELLED</span>;
      case 'Waiting for User Input':
        return <span style={{ color: 'var(--color-warning)', fontWeight: 'bold' }}>⚠️ WAITING FOR INPUT</span>;
      case 'Waiting for Final Review':
        return <span style={{ color: 'var(--color-warning)', fontWeight: 'bold' }}>🔍 FINAL REVIEW</span>;
      default:
        return <span style={{ color: 'var(--color-info)', fontWeight: 'bold' }}>⏳ {status.toUpperCase()}</span>;
    }
  };

  // Estimate seconds since update
  const getSecondsSinceUpdate = () => {
    if (!selectedApp || !selectedApp.updated_at) return 0;
    try {
      const updated = new Date(selectedApp.updated_at + 'Z');
      const diff = Math.max(0, new Date() - updated);
      return Math.floor(diff / 1000);
    } catch (e) {
      return 0;
    }
  };

  const seconds = getSecondsSinceUpdate();
  const isStuck = selectedApp?.status === 'Running' && seconds > 30;

  const filteredApps = apps.filter(a => {
    const titleMatch = (a.job_title || '').toLowerCase().includes(searchTerm.toLowerCase());
    const companyMatch = (a.company || '').toLowerCase().includes(searchTerm.toLowerCase());
    const searchMatch = titleMatch || companyMatch;
    
    if (statusFilter === 'Needs Input') {
      return searchMatch && ['Waiting for User Input', 'Waiting for Final Review'].includes(a.status);
    }
    if (statusFilter === 'Active') {
      return searchMatch && ['Running', 'Queued'].includes(a.status);
    }
    if (statusFilter === 'Ended') {
      return searchMatch && ['Completed', 'Failed', 'Cancelled'].includes(a.status);
    }
    return searchMatch;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', height: '100%' }}>
      {/* Top Title Bar */}
      <div>
        <h2>Agent Execution Console</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>
          Monitor automated forms filling tasks, view live Playwright screenshots, and resolve HITL blockers.
        </p>
      </div>

      <div style={{ display: 'flex', gap: '24px', alignItems: 'stretch', flex: 1, minHeight: '520px' }}>
        {/* Left Sidebar: Application List, Search & Status filter */}
        <div className="glass-card" style={{ width: '320px', display: 'flex', flexDirection: 'column', gap: '16px', padding: '16px', minWidth: '320px' }}>
          <div className="form-group">
            <input 
              type="text" 
              className="form-input" 
              placeholder="Type company or role name..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ fontSize: '13px', background: 'rgba(0,0,0,0.3)' }}
            />
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {['All', 'Needs Input', 'Active', 'Ended'].map(filterOption => (
              <button
                key={filterOption}
                type="button"
                onClick={() => setStatusFilter(filterOption)}
                style={{
                  padding: '6px 10px',
                  borderRadius: '16px',
                  fontSize: '11px',
                  fontWeight: '600',
                  border: '1px solid',
                  borderColor: statusFilter === filterOption ? 'var(--color-accent)' : 'var(--border-glass)',
                  background: statusFilter === filterOption ? 'var(--color-accent-gradient)' : 'rgba(255,255,255,0.03)',
                  color: '#ffffff',
                  cursor: 'pointer',
                  transition: 'var(--transition-smooth)'
                }}
              >
                {filterOption}
              </button>
            ))}
          </div>

          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '450px', paddingRight: '4px' }}>
            {filteredApps.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center', marginTop: '20px' }}>
                No matching applications
              </div>
            ) : (
              filteredApps.map(a => {
                const isSelected = a.id === selectedAppId;
                const needsInput = a.status === 'Waiting for User Input' || a.status === 'Waiting for Final Review';
                
                return (
                  <div
                    key={a.id}
                    onClick={() => setSelectedAppId(a.id)}
                    style={{
                      padding: '12px',
                      borderRadius: '8px',
                      border: '1px solid',
                      borderColor: isSelected 
                        ? 'var(--color-accent)' 
                        : needsInput 
                          ? 'rgba(245, 158, 11, 0.4)' 
                          : 'var(--border-glass)',
                      background: isSelected 
                        ? 'rgba(99, 102, 241, 0.1)' 
                        : needsInput 
                          ? 'rgba(245, 158, 11, 0.05)' 
                          : 'rgba(255, 255, 255, 0.02)',
                      cursor: 'pointer',
                      transition: 'var(--transition-smooth)'
                    }}
                    className="hover-glow"
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', gap: '8px' }}>
                      <span style={{ fontSize: '13px', fontWeight: '600', color: isSelected ? '#ffffff' : 'var(--text-primary)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '180px' }}>
                        {a.job_title}
                      </span>
                      {needsInput && (
                        <span style={{
                          backgroundColor: 'var(--color-warning)',
                          color: '#000000',
                          fontSize: '9px',
                          fontWeight: 'bold',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          textTransform: 'uppercase',
                          boxShadow: '0 0 6px rgba(245,158,11,0.2)'
                        }}>
                          Input
                        </span>
                      )}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                      <span>{a.company}</span>
                      <span>ID: {a.id}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Area: Terminal Logs, Console view & screenshots */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {selectedApp ? (
            <div className="console-layout" style={{ height: '100%', gridTemplateColumns: '1.1fr 0.9fr' }}>
              {/* Left Column: Terminal Logs */}
              <div className="console-terminal">
                <div className="terminal-header">
                  <div className="terminal-dots">
                    <span className="dot red"></span>
                    <span className="dot yellow"></span>
                    <span className="dot green"></span>
                  </div>
                  <span className="terminal-title">bash - agent_run_{selectedApp.id}.log</span>
                  <Terminal size={14} color="var(--text-muted)" />
                </div>
                
                <div className="terminal-body">
                  {logs.length === 0 ? (
                    <div className="log-line">Initializing console stream...</div>
                  ) : (
                    logs.map((log) => {
                      const time = log.timestamp ? log.timestamp.split('T')[1].split('.')[0] : '';
                      return (
                        <div key={log.id} className={`log-line ${log.level === 'ERROR' ? 'error' : log.level === 'SUCCESS' ? 'success' : ''}`}>
                          <span style={{ color: 'var(--text-muted)' }}>[{time}]</span> [{log.step}] {log.message}
                        </div>
                      );
                    })
                  )}
                </div>
              </div>

              {/* Right Column: Status info, screen and HITL prompt form */}
              <div className="console-right-panel">
                <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 'bold', textTransform: 'uppercase' }}>Worker Status</span>
                    {getStatusBadge(selectedApp.status)}
                  </div>

                  {isStuck && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-error)', fontSize: '13px', background: 'rgba(239,68,68,0.05)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(239,68,68,0.2)' }}>
                      <AlertTriangle size={16} />
                      <span>Stuck Alert: No updates in {seconds}s. Process may have hung.</span>
                    </div>
                  )}

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <h4 style={{ fontSize: '16px' }}>{selectedApp.job_title}</h4>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>🏢 {selectedApp.company}</p>
                    <p style={{ color: 'var(--text-muted)', fontSize: '13px', borderTop: '1px solid rgba(255,255,255,0.03)', marginTop: '8px', paddingTop: '8px' }}>
                      🤖 <strong>Current Action:</strong> {selectedApp.current_step || 'Waiting for script...'}
                    </p>
                  </div>

                  {selectedApp.status === 'Waiting for Final Review' && (
                    <div style={{ display: 'flex', gap: '12px', marginTop: '10px' }}>
                      <button className="btn-primary" onClick={handleApproveFinalReview} style={{ flex: 1 }}>
                        Approve & Submit
                      </button>
                      <button className="btn-secondary" onClick={handleCancelApplication} style={{ flex: 1, color: 'var(--color-error)' }}>
                        Cancel Run
                      </button>
                    </div>
                  )}

                  {['Running', 'Queued'].includes(selectedApp.status) && (
                    <button className="btn-secondary" onClick={handleCancelApplication} style={{ marginTop: '10px', color: 'var(--color-error)', borderColor: 'rgba(239,68,68,0.2)' }}>
                      Cancel Application Process
                    </button>
                  )}
                </div>

                {selectedApp.status === 'Waiting for User Input' && hitlPrompt && (
                  <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '14px', border: '1px solid rgba(245,158,11,0.3)', background: 'linear-gradient(135deg, rgba(245,158,11,0.05), rgba(17,24,39,0.7))' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-warning)' }}>
                      <HelpCircle size={18} />
                      <h3 style={{ fontSize: '15px' }}>Form Blocking Question</h3>
                    </div>

                    <p style={{ fontSize: '14px', fontWeight: '500' }}>{hitlPrompt.question_text}</p>

                    <form onSubmit={handleResolveHITL} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {hitlPrompt.input_type === 'radio' && hitlPrompt.options ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          {hitlPrompt.options.map((opt, idx) => (
                            <label key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', cursor: 'pointer' }}>
                              <input 
                                type="radio" 
                                name="hitl-radio"
                                value={opt}
                                checked={hitlAnswer === opt}
                                onChange={(e) => setHitlAnswer(e.target.value)}
                              />
                              <span>{opt}</span>
                            </label>
                          ))}
                        </div>
                      ) : hitlPrompt.input_type === 'select' && hitlPrompt.options ? (
                        <select 
                          className="form-input" 
                          value={hitlAnswer} 
                          onChange={(e) => setHitlAnswer(e.target.value)}
                        >
                          <option value="">Select option...</option>
                          {hitlPrompt.options.map((opt, idx) => (
                            <option key={idx} value={opt}>{opt}</option>
                          ))}
                        </select>
                      ) : (
                        <input 
                          type="text" 
                          className="form-input" 
                          placeholder="Type your answer here..." 
                          value={hitlAnswer}
                          onChange={(e) => setHitlAnswer(e.target.value)}
                        />
                      )}

                      <button type="submit" className="btn-primary" disabled={loading} style={{ background: 'var(--color-warning)', color: '#000000', fontWeight: 'bold' }}>
                        {loading ? 'Resuming...' : 'Submit Resolution'}
                      </button>
                    </form>
                  </div>
                )}

                <div className="screenshot-container glass-card" style={{ minHeight: '200px' }}>
                  {selectedApp.screenshot_path ? (
                    <img 
                      src={`/api/applications/${selectedApp.id}/screenshot?v=${screenshotVersion}`} 
                      alt="Live Browser Screenshot" 
                      className="screenshot-image"
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                  ) : (
                    <div className="screenshot-placeholder">
                      <ImageIcon size={32} />
                      <span style={{ fontSize: '13px' }}>Live Browser View unavailable</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="glass-card" style={{ textAlign: 'center', padding: '48px 0', color: 'var(--text-secondary)', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
              <Terminal size={48} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
              <h3>No Application Selected</h3>
              <p style={{ marginTop: '8px' }}>
                Select an application from the sidebar to monitor execution.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
