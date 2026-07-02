import React, { useState, useEffect } from 'react';
import { 
  User, 
  Upload, 
  Key, 
  Lock, 
  Save, 
  Check, 
  Globe, 
  Mail,
  RefreshCw,
  Play
} from 'lucide-react';

export default function Settings({ onProfileUpdated }) {
  const [profile, setProfile] = useState({
    personal_info: {
      full_name: '',
      email: '',
      phone: '',
      location: '',
      linkedin: '',
      github: '',
      resume_path: ''
    },
    skills: {
      languages: [],
      databases: [],
      tools_and_platforms: [],
      analytical_skills: []
    },
    education: [],
    experience: []
  });

  const [settings, setSettings] = useState({
    JOB_KEYWORDS: '',
    JOB_LOCATION: '',
    RECIPIENT_EMAIL: '',
    JOB_EXPERIENCE: 'Any Experience',
    ALERT_FREQUENCY: 'Daily',
    EMAIL_JOB_LIMIT: '5',
    GEMINI_API_KEY: '',
    LINKEDIN_USERNAME: '',
    LINKEDIN_PASSWORD: '',
    SMTP_SERVER: '',
    SMTP_PORT: '',
    SMTP_USERNAME: '',
    SMTP_PASSWORD: ''
  });

  const [isParsing, setIsParsing] = useState(false);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [isSavingSettings, setIsSavingSettings] = useState(false);
  const [sessionChecking, setSessionChecking] = useState(false);
  const [sessionResult, setSessionResult] = useState(null);
  const [launchingLogin, setLaunchingLogin] = useState(false);

  const fetchProfile = async () => {
    try {
      const res = await fetch('/api/profile');
      const data = await res.json();
      if (data && data.personal_info) {
        setProfile(data);
      }
    } catch (e) {
      console.error("Failed to load profile:", e);
    }
  };

  const fetchSettings = async () => {
    try {
      const res = await fetch('/api/settings');
      const data = await res.json();
      setSettings(data);
    } catch (e) {
      console.error("Failed to load settings:", e);
    }
  };

  useEffect(() => {
    fetchProfile();
    fetchSettings();
  }, []);

  const handleProfileSave = async (e) => {
    e.preventDefault();
    setIsSavingProfile(true);
    try {
      const res = await fetch('/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile)
      });
      const data = await res.json();
      if (data.status === 'success') {
        alert("Profile saved successfully!");
      } else {
        alert("Save failed: " + data.message);
      }
    } catch (e) {
      console.error(e);
      alert("Error saving profile");
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleSettingsSave = async (e) => {
    e.preventDefault();
    setIsSavingSettings(true);
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      const data = await res.json();
      if (data.status === 'success') {
        alert("Credentials saved to .env!");
        fetchSettings();
      } else {
        alert("Save failed: " + data.message);
      }
    } catch (e) {
      console.error(e);
      alert("Error saving settings");
    } finally {
      setIsSavingSettings(false);
    }
  };

  const handleResumeUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setIsParsing(true);
    try {
      const res = await fetch('/api/upload-resume', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.status === 'success') {
        setProfile(data.profile);
        alert("Resume successfully parsed! Candidate profile populated below.");
      } else {
        alert("Parse failed: " + data.message);
      }
    } catch (e) {
      console.error(e);
      alert("Error uploading resume: " + e.message);
    } finally {
      setIsParsing(false);
    }
  };

  const checkLinkedInSession = async () => {
    setSessionChecking(true);
    try {
      const res = await fetch('/api/linkedin/status');
      const data = await res.json();
      setSessionResult(data);
      if (onProfileUpdated) onProfileUpdated();
    } catch (e) {
      console.error(e);
      setSessionResult({ logged_in: false, message: 'Check failed: ' + e.message });
    } finally {
      setSessionChecking(false);
    }
  };

  const launchLinkedInLogin = async () => {
    setLaunchingLogin(true);
    try {
      const res = await fetch('/api/linkedin/login', { method: 'POST' });
      const data = await res.json();
      alert("Headful Chromium window launching. Please look at your desktop and log in manually. The background thread will save the cookies when completed.");
      checkLinkedInSession();
    } catch (e) {
      console.error(e);
      alert("Failed to launch login browser window.");
    } finally {
      setLaunchingLogin(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* View Header */}
      <div>
        <h2>Credentials & Profile Workspace</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>
          Configure your career attributes, upload resumes, authenticate LinkedIn sessions, and manage environment parameters.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.8fr', gap: '24px' }}>
        {/* Left Column: File uploads & Settings */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Resume Upload widget */}
          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <h3>Resume Ingestion Engine</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
              Drop your PDF resume here. The AI model extracts structural personal information, skills, and experience items.
            </p>
            
            <label style={{
              border: '2px dashed var(--border-glass)',
              borderRadius: '8px',
              padding: '24px',
              textAlign: 'center',
              cursor: 'pointer',
              background: 'rgba(0,0,0,0.15)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '12px',
              transition: 'var(--transition-smooth)'
            }} className="hover-glow">
              <Upload size={32} color={isParsing ? 'var(--color-accent)' : 'var(--text-muted)'} className={isParsing ? 'spin' : ''} />
              <span style={{ fontSize: '13px', fontWeight: '500' }}>
                {isParsing ? 'Extracting Resume Text...' : 'Click to Upload PDF Resume'}
              </span>
              <input type="file" accept=".pdf" onChange={handleResumeUpload} style={{ display: 'none' }} />
            </label>
            
            {profile.personal_info.resume_path && (
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Loaded from path: <code style={{ color: 'var(--text-secondary)' }}>{profile.personal_info.resume_path.split(/[\\/]/).pop()}</code>
              </span>
            )}
          </div>

          {/* LinkedIn Login check */}
          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <h3>LinkedIn Session Authentication</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
              Verify cookies session persistence status or launch manual browser login gate.
            </p>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button 
                className="btn-secondary" 
                onClick={checkLinkedInSession} 
                disabled={sessionChecking}
                style={{ flex: 1 }}
              >
                <RefreshCw size={14} className={sessionChecking ? 'spin' : ''} style={{ marginRight: '6px' }} />
                Check Status
              </button>
              <button 
                className="btn-primary" 
                onClick={launchLinkedInLogin} 
                disabled={launchingLogin}
                style={{ flex: 1 }}
              >
                <Play size={14} style={{ marginRight: '6px' }} />
                Launch Login
              </button>
            </div>

            {sessionResult && (
              <div style={{ 
                fontSize: '13px', 
                padding: '12px', 
                borderRadius: '8px', 
                background: sessionResult.logged_in ? 'rgba(16,185,129,0.05)' : 'rgba(239,68,68,0.05)',
                border: `1px solid ${sessionResult.logged_in ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`,
                color: sessionResult.logged_in ? 'var(--color-success)' : 'var(--color-error)'
              }}>
                <strong>{sessionResult.logged_in ? 'Authenticated' : 'No Active Session'}:</strong> {sessionResult.message}
              </div>
            )}
          </div>

          {/* Secrets Form */}
          <form onSubmit={handleSettingsSave} className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <h3>System Credentials & .env</h3>

            <div className="form-group">
              <label>LinkedIn Username</label>
              <input 
                type="text" 
                className="form-input" 
                value={settings.LINKEDIN_USERNAME} 
                onChange={(e) => setSettings({...settings, LINKEDIN_USERNAME: e.target.value})}
                placeholder="example@domain.com"
              />
            </div>

            <div className="form-group">
              <label>LinkedIn Password</label>
              <input 
                type="password" 
                className="form-input" 
                value={settings.LINKEDIN_PASSWORD} 
                onChange={(e) => setSettings({...settings, LINKEDIN_PASSWORD: e.target.value})}
                placeholder="Enter LinkedIn password"
              />
            </div>

            <button type="submit" className="btn-primary" disabled={isSavingSettings} style={{ marginTop: '10px' }}>
              <Save size={16} style={{ marginRight: '6px' }} />
              {isSavingSettings ? 'Saving...' : 'Save Secrets to .env'}
            </button>
          </form>
        </div>

        {/* Right Column: Profile fields & Email Alert Config */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <form onSubmit={handleProfileSave} className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3>Candidate Profile Details</h3>
              <button type="submit" className="btn-primary" disabled={isSavingProfile}>
                <Save size={16} style={{ marginRight: '6px' }} />
                {isSavingProfile ? 'Saving...' : 'Save Profile'}
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label>Full Name</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={profile.personal_info.full_name || ''} 
                  onChange={(e) => setProfile({
                    ...profile,
                    personal_info: { ...profile.personal_info, full_name: e.target.value }
                  })}
                  placeholder="e.g. John Doe"
                />
              </div>
              <div className="form-group">
                <label>Email Address</label>
                <input 
                  type="email" 
                  className="form-input" 
                  value={profile.personal_info.email || ''} 
                  onChange={(e) => setProfile({
                    ...profile,
                    personal_info: { ...profile.personal_info, email: e.target.value }
                  })}
                  placeholder="example@domain.com"
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label>Contact Phone</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={profile.personal_info.phone || ''} 
                  onChange={(e) => setProfile({
                    ...profile,
                    personal_info: { ...profile.personal_info, phone: e.target.value }
                  })}
                  placeholder="e.g. +91 9876543210"
                />
              </div>
              <div className="form-group">
                <label>Location (City, State)</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={profile.personal_info.location || ''} 
                  onChange={(e) => setProfile({
                    ...profile,
                    personal_info: { ...profile.personal_info, location: e.target.value }
                  })}
                  placeholder="e.g. Mumbai, Maharashtra"
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label>LinkedIn URL</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={profile.personal_info.linkedin || ''} 
                  onChange={(e) => setProfile({
                    ...profile,
                    personal_info: { ...profile.personal_info, linkedin: e.target.value }
                  })}
                  placeholder="https://linkedin.com/in/username"
                />
              </div>
              <div className="form-group">
                <label>Github URL</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={profile.personal_info.github || ''} 
                  onChange={(e) => setProfile({
                    ...profile,
                    personal_info: { ...profile.personal_info, github: e.target.value }
                  })}
                  placeholder="https://github.com/username"
                />
              </div>
            </div>

            <div className="form-group">
              <label>Languages & Frameworks (Comma separated)</label>
              <input 
                type="text" 
                className="form-input" 
                value={profile.skills.languages?.join(', ') || ''} 
                onChange={(e) => setProfile({
                  ...profile,
                  skills: { ...profile.skills, languages: e.target.value.split(',').map(s => s.trim()) }
                })}
                placeholder="e.g. Python, Javascript, React"
              />
            </div>

            <div className="form-group">
              <label>Databases & Cloud systems (Comma separated)</label>
              <input 
                type="text" 
                className="form-input" 
                value={profile.skills.databases?.join(', ') || ''} 
                onChange={(e) => setProfile({
                  ...profile,
                  skills: { ...profile.skills, databases: e.target.value.split(',').map(s => s.trim()) }
                })}
                placeholder="e.g. PostgreSQL, MongoDB, GCP"
              />
            </div>

            <div className="form-group">
              <label>Tools & Platforms (Comma separated)</label>
              <input 
                type="text" 
                className="form-input" 
                value={profile.skills.tools_and_platforms?.join(', ') || ''} 
                onChange={(e) => setProfile({
                  ...profile,
                  skills: { ...profile.skills, tools_and_platforms: e.target.value.split(',').map(s => s.trim()) }
                })}
                placeholder="e.g. Docker, Git, Kubernetes"
              />
            </div>
          </form>

          {/* Email Alert Configuration Form */}
          <form onSubmit={handleSettingsSave} className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3>Email Alert Configuration</h3>
              <button type="submit" className="btn-primary" disabled={isSavingSettings}>
                <Save size={16} style={{ marginRight: '6px' }} />
                {isSavingSettings ? 'Saving...' : 'Save Preferences'}
              </button>
            </div>
            
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
              Configure automatic email notification frequency and listing counts matching your preferences.
            </p>

            <div className="form-group">
              <label>Recipient Email Address</label>
              <input 
                type="email" 
                className="form-input" 
                value={settings.RECIPIENT_EMAIL || ''} 
                onChange={(e) => setSettings({...settings, RECIPIENT_EMAIL: e.target.value})}
                placeholder="example@domain.com"
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label>Job Keywords</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={settings.JOB_KEYWORDS || ''} 
                  onChange={(e) => setSettings({...settings, JOB_KEYWORDS: e.target.value})}
                  placeholder="e.g. Talent Acquisition, Software Engineer"
                />
              </div>
              <div className="form-group">
                <label>Job Location</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={settings.JOB_LOCATION || ''} 
                  onChange={(e) => setSettings({...settings, JOB_LOCATION: e.target.value})}
                  placeholder="e.g. Hyderabad, India"
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label>Alert Frequency</label>
                <select
                  className="form-input"
                  value={settings.ALERT_FREQUENCY || 'Daily'}
                  onChange={(e) => setSettings({...settings, ALERT_FREQUENCY: e.target.value})}
                >
                  <option value="Hourly">Hourly</option>
                  <option value="Daily">Daily</option>
                  <option value="Weekly">Weekly</option>
                  <option value="Monthly">Monthly</option>
                </select>
              </div>
              <div className="form-group">
                <label>Email Jobs Limit</label>
                <input 
                  type="number" 
                  className="form-input" 
                  value={settings.EMAIL_JOB_LIMIT || '5'} 
                  onChange={(e) => setSettings({...settings, EMAIL_JOB_LIMIT: e.target.value})}
                  placeholder="e.g. 5"
                  min="1"
                  max="50"
                />
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
