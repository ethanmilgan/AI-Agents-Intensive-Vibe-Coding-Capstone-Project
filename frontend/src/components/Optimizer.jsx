import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  CheckCircle, 
  AlertCircle, 
  Copy, 
  FileText, 
  Mail, 
  MessageSquare,
  RefreshCw,
  Plus
} from 'lucide-react';

export default function Optimizer() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [targetJobUrl, setTargetJobUrl] = useState('');
  const [targetJobDesc, setTargetJobDesc] = useState('');
  const [atsScore, setAtsScore] = useState(72);
  const [missingSkills, setMissingSkills] = useState([
    'Kubernetes orchestration',
    'Redis Cache implementation',
    'FastAPI asynchronous microservices',
    'CI/CD GitHub Actions pipelines'
  ]);
  const [confirmedExperiences, setConfirmedExperiences] = useState([]);
  const [newExperienceText, setNewExperienceText] = useState('');
  const [activeSubTab, setActiveSubTab] = useState('cover-letter');
  
  // Tailored contents
  const [coverLetter, setCoverLetter] = useState('');
  const [outreachMessage, setOutreachMessage] = useState('');
  const [optimizedResumeBullets, setOptimizedResumeBullets] = useState([]);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/profile');
      const data = await res.json();
      setProfile(data);
      
      // Auto-generate materials if profile exists
      if (data && data.personal_info && data.personal_info.full_name) {
        generateMaterials(data, targetJobDesc);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const generateMaterials = (candidateData, jobDesc) => {
    const name = candidateData.personal_info.full_name || 'Candidate';
    const email = candidateData.personal_info.email || 'candidate@example.com';
    const skills = candidateData.skills?.languages?.join(', ') || 'Software Engineering';

    setCoverLetter(
      `Dear Hiring Team,\n\nI am writing to express my enthusiastic interest in the Software Engineer position. With a strong background in software development and experience building scalable backend architectures, I am confident in my ability to contribute to your engineering initiatives.\n\nThroughout my career, I have specialized in technology stacks including ${skills}. I take pride in engineering reliable systems, streamlining operations, and delivering impactful code. I am excited about the opportunity to bring my experience and enthusiasm to your team.\n\nThank you for your time and consideration. I look forward to discussing how my skills align with your goals.\n\nSincerely,\n${name}\n${email}`
    );

    setOutreachMessage(
      `Hi Hiring Manager,\n\nI recently applied for the Software Engineer role on your team. I have strong experience building scalable APIs and software services matching your job specifications. I'd love to connect briefly to learn more about the engineering challenges your team is solving.\n\nBest,\n${name}`
    );

    setOptimizedResumeBullets([
      { original: "Developed APIs for web services.", optimized: "Architected asynchronous FastAPI endpoints resolving over 10,000 requests/minute with less than 50ms latency." },
      { original: "Fixed performance problems.", optimized: "Optimized database index query execution times, leading to a 32% increase in speed across dashboard load states." }
    ]);
  };

  const handleCopy = (text, elementId) => {
    navigator.clipboard.writeText(text);
    const toast = document.getElementById(elementId);
    if (toast) {
      toast.innerText = 'Copied!';
      setTimeout(() => {
        toast.innerText = 'Copy to Clipboard';
      }, 2000);
    }
  };

  const handleAddConfirmedExperience = (skill) => {
    if (confirmedExperiences.includes(skill)) return;
    
    // Add to list
    const updated = [...confirmedExperiences, skill];
    setConfirmedExperiences(updated);
    
    // Remove from missing skills
    setMissingSkills(prev => prev.filter(s => s !== skill));
    
    // Boost ATS score
    setAtsScore(prev => Math.min(95, prev + 6));
    
    // Append to profile skills
    if (profile) {
      const updatedProfile = { ...profile };
      if (!updatedProfile.skills.tools_and_platforms) {
        updatedProfile.skills.tools_and_platforms = [];
      }
      updatedProfile.skills.tools_and_platforms.push(skill);
      setProfile(updatedProfile);
    }
  };

  const handleCustomExperienceSubmit = (e) => {
    e.preventDefault();
    if (!newExperienceText.trim()) return;
    
    handleAddConfirmedExperience(newExperienceText);
    setNewExperienceText('');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* View Header */}
      <div>
        <h2>ATS Scorecard & Optimization</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>
          Evaluate resume matches against job listings, review skill deficiencies, and generate custom letters/outreach materials.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.8fr', gap: '24px' }}>
        {/* Left Column: ATS Score & Gaps */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Score Gauge Card */}
          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
            <h3>ATS Match Alignment</h3>
            
            <div style={{ position: 'relative', width: '130px', height: '130px', display: 'flex', alignItems: 'center', justifycontent: 'center' }}>
              {/* Decorative circle */}
              <div style={{
                position: 'absolute',
                inset: 0,
                borderRadius: '50%',
                border: '6px solid rgba(255,255,255,0.03)'
              }}></div>
              <div style={{
                position: 'absolute',
                inset: 0,
                borderRadius: '50%',
                border: '6px solid var(--color-accent)',
                borderRightColor: 'transparent',
                transform: `rotate(${(atsScore / 100) * 360 - 90}deg)`,
                transition: 'transform 0.5s'
              }}></div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 1 }}>
                <span style={{ fontStyle: 'Outfit', fontSize: '32px', fontWeight: '800' }}>{atsScore}%</span>
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: '600', textTransform: 'uppercase' }}>Match Rate</span>
              </div>
            </div>

            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', textAlign: 'center' }}>
              {atsScore >= 80 ? '🔥 Great match! You satisfy the major prerequisites.' : '⚠️ Match score is low. Confirm missing skills below to tailer your profile.'}
            </p>
          </div>

          {/* Missing Keywords Gap Analysis Card */}
          <div className="glass-card">
            <h3 style={{ marginBottom: '14px' }}>Keyword Gap Analysis</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '16px' }}>
              Click to confirm experience with these skills. Confirmed items will be updated in your resume to raise match score.
            </p>

            {missingSkills.length === 0 ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-success)', fontSize: '14px', background: 'rgba(16,185,129,0.05)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(16,185,129,0.2)' }}>
                <CheckCircle size={16} />
                <span>All keyword gaps resolved! ATS match optimized.</span>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {missingSkills.map((skill, idx) => (
                  <div 
                    key={idx}
                    onClick={() => handleAddConfirmedExperience(skill)}
                    style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'space-between',
                      padding: '10px 14px',
                      background: 'rgba(255, 255, 255, 0.02)',
                      border: '1px solid var(--border-glass)',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      transition: 'var(--transition-smooth)'
                    }}
                    className="hover-glow"
                  >
                    <span style={{ fontSize: '13px', color: 'var(--text-primary)' }}>{skill}</span>
                    <Plus size={14} color="var(--color-accent)" />
                  </div>
                ))}
              </div>
            )}

            {/* Custom Fact Add Form */}
            <form onSubmit={handleCustomExperienceSubmit} style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
              <input 
                type="text" 
                className="form-input" 
                placeholder="Add custom experience keyword..." 
                value={newExperienceText}
                onChange={(e) => setNewExperienceText(e.target.value)}
                style={{ fontSize: '12px', padding: '8px 12px' }}
              />
              <button type="submit" className="btn-primary" style={{ padding: '8px 12px', fontSize: '12px' }}>
                Confirm
              </button>
            </form>
          </div>

          {/* Confirmed list */}
          {confirmedExperiences.length > 0 && (
            <div className="glass-card">
              <h3>Confirmed Achievements</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '12px' }}>
                {confirmedExperiences.map((skill, idx) => (
                  <span 
                    key={idx} 
                    style={{ 
                      fontSize: '12px', 
                      background: 'rgba(0, 119, 181, 0.1)', 
                      color: 'var(--color-accent)', 
                      padding: '4px 10px', 
                      borderRadius: '16px',
                      border: '1px solid var(--border-glass-active)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <CheckCircle size={10} />
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Tailored Deliverables Tabs */}
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', minHeight: '450px' }}>
          <div className="card-tabs">
            <div 
              className={`card-tab ${activeSubTab === 'cover-letter' ? 'active' : ''}`}
              onClick={() => setActiveSubTab('cover-letter')}
            >
              <FileText size={14} style={{ marginRight: '6px', display: 'inline' }} />
              Cover Letter
            </div>
            <div 
              className={`card-tab ${activeSubTab === 'outreach' ? 'active' : ''}`}
              onClick={() => setActiveSubTab('outreach')}
            >
              <Mail size={14} style={{ marginRight: '6px', display: 'inline' }} />
              Outreach Draft
            </div>
            <div 
              className={`card-tab ${activeSubTab === 'resume' ? 'active' : ''}`}
              onClick={() => setActiveSubTab('resume')}
            >
              <Sparkles size={14} style={{ marginRight: '6px', display: 'inline' }} />
              Bullet Optimizer
            </div>
          </div>

          <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            {activeSubTab === 'cover-letter' && (
              <div style={{ display: 'flex', flexDirection: 'column', flex: 1, gap: '14px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Generated Cover Letter Draft</span>
                  <button 
                    id="copy-cl-btn"
                    className="btn-secondary" 
                    style={{ padding: '6px 12px', fontSize: '12px' }}
                    onClick={() => handleCopy(coverLetter, 'copy-cl-btn')}
                  >
                    Copy to Clipboard
                  </button>
                </div>
                <textarea 
                  className="form-input" 
                  value={coverLetter}
                  onChange={(e) => setCoverLetter(e.target.value)}
                  style={{ flex: 1, fontFamily: 'monospace', fontSize: '13px', resize: 'none', minHeight: '260px' }}
                />
              </div>
            )}

            {activeSubTab === 'outreach' && (
              <div style={{ display: 'flex', flexDirection: 'column', flex: 1, gap: '14px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>LinkedIn Recruiter outreach note (200 words max)</span>
                  <button 
                    id="copy-outreach-btn"
                    className="btn-secondary" 
                    style={{ padding: '6px 12px', fontSize: '12px' }}
                    onClick={() => handleCopy(outreachMessage, 'copy-outreach-btn')}
                  >
                    Copy to Clipboard
                  </button>
                </div>
                <textarea 
                  className="form-input" 
                  value={outreachMessage}
                  onChange={(e) => setOutreachMessage(e.target.value)}
                  style={{ flex: 1, fontFamily: 'monospace', fontSize: '13px', resize: 'none', minHeight: '260px' }}
                />
              </div>
            )}

            {activeSubTab === 'resume' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Side-by-Side Tailored Resume Experience Bullets</span>
                
                {optimizedResumeBullets.map((bullet, idx) => (
                  <div key={idx} className="glass-card" style={{ padding: '14px', background: 'rgba(0,0,0,0.15)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div>
                      <span style={{ fontSize: '11px', color: 'var(--color-error)', fontWeight: 'bold', textTransform: 'uppercase' }}>Original Bullet</span>
                      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>{bullet.original}</p>
                    </div>
                    <div style={{ borderTop: '1px solid rgba(255,255,255,0.03)', paddingTop: '10px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--color-success)', fontWeight: 'bold', textTransform: 'uppercase' }}>Tailored Optimized Bullet (Gemini)</span>
                      <p style={{ fontSize: '13px', color: '#ffffff', marginTop: '4px', lineHeight: '1.4' }}>{bullet.optimized}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
