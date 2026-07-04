import React, { useState, useEffect } from 'react';
import { 
  Search, 
  MapPin, 
  Award, 
  Send, 
  Cpu, 
  Check, 
  ExternalLink,
  ChevronRight
} from 'lucide-react';
import confetti from 'canvas-confetti';

export default function JobSearch({ setActiveTab }) {
  const [keywords, setKeywords] = useState('');
  const [location, setLocation] = useState('');
  const [experience, setExperience] = useState('');
  
  const [isSearching, setIsSearching] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [isAlerting, setIsAlerting] = useState(false);
  
  const [jobs, setJobs] = useState([]);
  const [selectedJobUrls, setSelectedJobUrls] = useState({});
  const [profile, setProfile] = useState(null);

  // Load candidate profile
  const fetchProfile = async () => {
    try {
      const res = await fetch('/api/profile');
      const data = await res.json();
      setProfile(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchProfile();
    // Load search defaults from settings/env if available
    const loadDefaults = async () => {
      try {
        const res = await fetch('/api/settings');
        const settings = await res.json();
        if (settings.JOB_KEYWORDS) setKeywords(settings.JOB_KEYWORDS);
        if (settings.JOB_LOCATION) setLocation(settings.JOB_LOCATION);
        if (settings.JOB_EXPERIENCE && !isNaN(parseFloat(settings.JOB_EXPERIENCE))) {
          setExperience(parseFloat(settings.JOB_EXPERIENCE));
        }
      } catch (e) {
        console.error(e);
      }
    };
    loadDefaults();
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!keywords.trim() || !location.trim()) {
      alert("Please fill in both Job Keywords and Location.");
      return;
    }
    
    setIsSearching(true);
    try {
      const res = await fetch('/api/search-jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keywords, location, experience: experience === '' ? 2 : parseFloat(experience) })
      });
      const data = await res.json();
      if (data.status === 'success') {
        setJobs(data.jobs || []);
        // Select all by default
        const selected = {};
        data.jobs.forEach(j => {
          selected[j.job_url] = true;
        });
        setSelectedJobUrls(selected);
      } else {
        alert("Discovery failed: " + (data.message || "Unknown error"));
      }
    } catch (e) {
      console.error(e);
      alert("Error searching jobs: " + e.message);
    } finally {
      setIsSearching(false);
    }
  };

  const handleToggleSelect = (url) => {
    setSelectedJobUrls(prev => ({
      ...prev,
      [url]: !prev[url]
    }));
  };

  const handleBulkApply = async () => {
    const urlsToApply = Object.keys(selectedJobUrls).filter(url => selectedJobUrls[url]);
    if (urlsToApply.length === 0) {
      alert("Please select at least one job.");
      return;
    }

    if (!profile || !profile.personal_info || !profile.personal_info.resume_path) {
      alert("Cannot apply. Please configure your profile and upload a resume under Configuration tab first.");
      return;
    }

    setIsApplying(true);
    let successCount = 0;
    
    try {
      for (const url of urlsToApply) {
        const job = jobs.find(j => j.job_url === url);
        if (!job) continue;

        const res = await fetch('/api/run-apply', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            job_url: job.job_url,
            job_title: job.job_title,
            company: job.company
          })
        });
        const data = await res.json();
        if (data.status === 'success') {
          successCount++;
        }
      }

      if (successCount > 0) {
        // Fire confetti celebration!
        confetti({
          particleCount: 150,
          spread: 80,
          origin: { y: 0.6 }
        });
        alert(`Successfully queued automated apply processes for ${successCount} job(s)! Redirecting to console monitor...`);
        setActiveTab('console');
      } else {
        alert("Failed to spawn automation processes.");
      }
    } catch (e) {
      console.error(e);
      alert("Error applying: " + e.message);
    } finally {
      setIsApplying(false);
    }
  };

  const handleTriggerEmailAlert = async () => {
    if (!keywords.trim() || !location.trim()) {
      alert("Please enter keywords and location first.");
      return;
    }

    setIsAlerting(true);
    try {
      const email = profile?.personal_info?.email || 'candidate@example.com';
      const res = await fetch('/api/run-alert', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          keywords,
          location,
          experience: experience + ' years',
          frequency: 'Daily',
          recipient: email
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        alert(`Job Alert Agent launched in the background! It will scrape roles and email styled results to ${email}.`);
      } else {
        alert("Failed to start job alert: " + (data.message || "Unknown error"));
      }
    } catch (e) {
      console.error(e);
      alert("Error launching alert agent: " + e.message);
    } finally {
      setIsAlerting(false);
    }
  };

  const getScoreClass = (score) => {
    if (score >= 80) return 'score-high';
    if (score >= 60) return 'score-medium';
    return 'score-low';
  };

  // Mock match score calculator based on keywords/experience for visuals
  const calculateMockScore = (job) => {
    let base = 65;
    // Boost matching points
    if (keywords.split(',').some(k => job.job_title.toLowerCase().includes(k.trim().toLowerCase()))) {
      base += 15;
    }
    if (job.experience_level && job.experience_level.toLowerCase().includes('entry') && experience <= 2) {
      base += 10;
    }
    return Math.min(96, Math.max(45, base));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* View Header */}
      <div>
        <h2>Job Scraper & Discovery Center</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>
          Query LinkedIn job boards, evaluate matching indices, and trigger automated form filling processes.
        </p>
      </div>

      {/* Discovery Query Controls */}
      <form onSubmit={handleSearch} className="glass-card search-controls">
        <div className="form-group">
          <label><Search size={12} style={{ marginRight: '4px' }} /> Job Keywords</label>
          <input 
            type="text" 
            className="form-input" 
            placeholder="e.g. Software Engineer, React"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label><MapPin size={12} style={{ marginRight: '4px' }} /> Target Location</label>
          <input 
            type="text" 
            className="form-input" 
            placeholder="e.g. Hyderabad, India"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label><Award size={12} style={{ marginRight: '4px' }} /> Experience (Years)</label>
          <input 
            type="number" 
            className="form-input" 
            min="0"
            max="20"
            step="0.5"
            placeholder="e.g. 2"
            value={experience}
            onChange={(e) => setExperience(e.target.value)}
          />
        </div>

        <button type="submit" className="btn-primary" disabled={isSearching} style={{ height: '42px' }}>
          {isSearching ? (
            <>
              <div className="spinner" style={{ width: '16px', height: '16px' }}></div>
              <span>Searching...</span>
            </>
          ) : (
            <>
              <Cpu size={16} />
              <span>Discover Jobs</span>
            </>
          )}
        </button>
      </form>

      {/* Discovered Jobs List */}
      {jobs.length > 0 && (
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-glass)', paddingBottom: '14px' }}>
            <div>
              <h3>Discovered Matching Jobs</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '2px' }}>
                Select roles to deploy background apply workers or generate reports.
              </p>
            </div>
            
            <div style={{ display: 'flex', gap: '12px' }}>
              <button 
                className="btn-secondary" 
                onClick={handleTriggerEmailAlert} 
                disabled={isAlerting}
              >
                {isAlerting ? 'Launching Alert...' : 'Email Styled Alert Report'}
                <Send size={14} style={{ marginLeft: '6px' }} />
              </button>

              <button 
                className="btn-primary" 
                onClick={handleBulkApply} 
                disabled={isApplying}
              >
                {isApplying ? 'Applying...' : 'Start Bulk Automated Apply'}
                <ChevronRight size={16} style={{ marginLeft: '4px' }} />
              </button>
            </div>
          </div>

          <div className="jobs-list">
            {jobs.map((job, index) => {
              const score = calculateMockScore(job);
              const isSelected = !!selectedJobUrls[job.job_url];
              
              return (
                <div 
                  key={index} 
                  className="glass-card job-card"
                  style={{ 
                    background: isSelected ? 'rgba(0, 119, 181, 0.02)' : 'var(--bg-card)',
                    borderColor: isSelected ? 'var(--border-glass-active)' : 'var(--border-glass)'
                  }}
                >
                  <div className="job-checkbox-wrapper">
                    <input 
                      type="checkbox" 
                      checked={isSelected}
                      onChange={() => handleToggleSelect(job.job_url)}
                      style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                    />
                  </div>

                  <div className="job-info-main">
                    <h3>{job.job_title}</h3>
                    <div className="job-meta-row">
                      <span>🏢 <strong>{job.company}</strong></span>
                      <span>📍 {job.location}</span>
                      <span>📅 {job.posted}</span>
                      <span>🎓 {job.experience_level}</span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                    <a 
                      href={job.job_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center' }}
                    >
                      <ExternalLink size={16} />
                    </a>
                    
                    <div className={`job-score-gauge ${getScoreClass(score)}`}>
                      {score}%
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {jobs.length === 0 && !isSearching && (
        <div className="glass-card" style={{ textAlign: 'center', padding: '48px 0', color: 'var(--text-secondary)' }}>
          <Search size={48} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
          <h3>No Jobs Discovered Yet</h3>
          <p style={{ marginTop: '8px' }}>
            Enter your target role keywords and location above, then press Discover Jobs to crawl LinkedIn.
          </p>
        </div>
      )}
    </div>
  );
}
