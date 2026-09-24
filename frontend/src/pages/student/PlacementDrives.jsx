import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { placementApi, matchingApi } from '../../api/endpoints';

const APP_STATUS_COLORS = {
  applied:     { color: '#6366f1', bg: 'rgba(99,102,241,0.1)', label: 'Applied' },
  shortlisted: { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', label: 'Shortlisted' },
  in_progress: { color: '#06b6d4', bg: 'rgba(6,182,212,0.1)',  label: 'In Progress' },
  selected:    { color: '#22c55e', bg: 'rgba(34,197,94,0.1)',  label: '🎉 Selected' },
  rejected:    { color: '#ef4444', bg: 'rgba(239,68,68,0.1)',  label: 'Rejected' },
  withdrawn:   { color: 'var(--text-muted)', bg: 'var(--bg-tertiary)', label: 'Withdrawn' },
};

const STAGE_STATUS = {
  passed:    { icon: '✓', color: '#22c55e' },
  failed:    { icon: '✗', color: '#ef4444' },
  scheduled: { icon: '◎', color: '#f59e0b' },
  pending:   { icon: '○', color: 'var(--text-muted)' },
};

function daysLeft(deadline) {
  const d = Math.ceil((new Date(deadline) - new Date()) / (1000 * 60 * 60 * 24));
  return d > 0 ? d : 0;
}

// ─── Drive Card ────────────────────────────────────────────────────
function DriveCard({ drive, onApply }) {
  const [expanded, setExpanded] = useState(false);
  const navigate = useNavigate();
  const days = daysLeft(drive.deadline);
  const urgency = days <= 3 ? '#ef4444' : days <= 7 ? '#f59e0b' : '#22c55e';
  
  const score = drive.match_score ? Math.round(drive.match_score) : null;
  const matchColor = score >= 75 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444';

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', gap: 'var(--space-4)', alignItems: 'center' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <div style={{ fontWeight: 700, fontSize: 'var(--font-size-lg)' }}>{drive.company}</div>
              {score !== null && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <svg width="24" height="24" viewBox="0 0 24 24" style={{ transform: 'rotate(-90deg)' }}>
                    <circle cx="12" cy="12" r="10" fill="none" stroke="var(--bg-secondary)" strokeWidth="3" />
                    <circle cx="12" cy="12" r="10" fill="none" stroke={matchColor} strokeWidth="3" 
                      strokeDasharray="62.8" strokeDashoffset={62.8 - (score / 100) * 62.8} />
                  </svg>
                  <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: matchColor }}>🎯 {score}% match</span>
                </div>
              )}
            </div>
            <div style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)', marginTop: 2 }}>
              {drive.roles_offered?.join(', ')} · 📍 {drive.location}
            </div>
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', color: urgency, fontWeight: 600 }}>
            {days > 0 ? `⏰ ${days} days left` : 'Deadline passed'}
          </div>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 2 }}>
            {drive.deadline}
          </div>
        </div>
      </div>

      {/* Meta row */}
      <div style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap', fontSize: 'var(--font-size-xs)' }}>
        <span style={{ color: 'var(--accent-success)', fontWeight: 600 }}>💰 ₹{drive.salary_ctc}L CTC</span>
        <span style={{ color: 'var(--text-muted)' }}>📊 Min CGPA {drive.min_cgpa}</span>
        <span style={{ color: 'var(--text-muted)' }}>🚫 Max backlogs: {drive.max_backlogs}</span>
        <span style={{ color: 'var(--text-muted)' }}>🎓 {drive.eligible_departments?.join(', ')}</span>
      </div>

      {/* Expand */}
      {expanded && (
        <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: 'var(--space-4)' }}>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: 'var(--space-4)' }}>
            {drive.description}
          </p>
        </div>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'auto', alignItems: 'center' }}>
        <button className="btn btn-ghost" style={{ height: 36, fontSize: 'var(--font-size-sm)' }} onClick={() => setExpanded(e => !e)}>
          {expanded ? 'Show less ▲' : 'View details ▼'}
        </button>
        <button className="btn btn-secondary" style={{ height: 36, fontSize: 'var(--font-size-sm)' }} onClick={() => navigate(`/student/drives/${drive.id}`)}>
          View Match Analysis →
        </button>
        <div style={{ flex: 1 }}></div>
        {drive.applied ? (
          <span style={{ display: 'inline-flex', alignItems: 'center', padding: '0 var(--space-4)', borderRadius: 'var(--border-radius-sm)', fontSize: 'var(--font-size-sm)', background: 'rgba(34,197,94,0.1)', color: '#22c55e', fontWeight: 600, height: 36 }}>
            ✓ Applied
          </span>
        ) : (
          <button className="btn btn-primary" style={{ height: 36 }} onClick={() => onApply(drive.id)}>
            Apply Now →
          </button>
        )}
      </div>
    </div>
  );
}

// ─── Application Card ──────────────────────────────────────────────
function ApplicationCard({ app }) {
  const sc = APP_STATUS_COLORS[app.status] || APP_STATUS_COLORS.applied;
  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-4)' }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 'var(--font-size-base)' }}>{app.company}</div>
          <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>{app.role} · ₹{app.salary_ctc}L</div>
        </div>
        <span style={{ padding: '4px 14px', borderRadius: 999, fontSize: 'var(--font-size-xs)', fontWeight: 600, background: sc.bg, color: sc.color }}>
          {sc.label}
        </span>
      </div>
      <div>
        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: 'var(--space-3)' }}>
          Current stage: <strong style={{ color: 'var(--text-secondary)' }}>{app.current_stage}</strong>
        </div>
        <div style={{ display: 'flex', gap: 0, flexWrap: 'wrap', alignItems: 'center' }}>
          {app.stages?.map((stage, i) => {
            const ss = STAGE_STATUS[stage.status] || STAGE_STATUS.pending;
            return (
              <span key={stage.name} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <span style={{ padding: '3px 10px', borderRadius: 999, fontSize: 'var(--font-size-xs)', fontWeight: 600, background: `${ss.color}18`, color: ss.color, border: `1px solid ${ss.color}40`, whiteSpace: 'nowrap' }}>
                  {ss.icon} {stage.name}
                </span>
                {i < app.stages.length - 1 && <span style={{ color: 'var(--text-muted)', fontSize: '0.65rem', margin: '0 2px' }}>→</span>}
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────
export default function PlacementDrives() {
  const [tab, setTab] = useState('drives');
  const [drives, setDrives] = useState([]);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortByMatch, setSortByMatch] = useState(false);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [drivesRes, appsRes] = await Promise.all([
          placementApi.getDrives(),
          placementApi.getMyApplications()
        ]);
        
        let drivesData = drivesRes.data || [];
        
        // Fetch match scores for drives
        const matchPromises = drivesData.map(d => matchingApi.getDriveMatch(d.id).catch(() => ({ data: { match_score: 0 } })));
        const matchResults = await Promise.all(matchPromises);
        
        drivesData = drivesData.map((d, i) => ({
          ...d,
          match_score: matchResults[i].data.match_score
        }));
        
        setDrives(drivesData);
        setApplications(appsRes.data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const handleApply = async (driveId) => {
    try {
      await placementApi.apply(driveId);
      setDrives(prev => prev.map(d => d.id === driveId ? { ...d, applied: true } : d));
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return <div className="page-body">Loading...</div>;

  let displayDrives = [...drives];
  if (sortByMatch) {
    displayDrives.sort((a, b) => (b.match_score || 0) - (a.match_score || 0));
  }

  return (
    <div>
      <div className="page-header">
        <h1>Placement Drives</h1>
        <p>Track active placement drives and your applications</p>
      </div>

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
        
        <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: 0 }}>
          {[
            { id: 'drives', label: `Available Drives (${drives.filter(d => !d.applied).length})` },
            { id: 'applications', label: `My Applications (${applications.length})` },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              style={{
                padding: 'var(--space-3) var(--space-5)',
                background: 'none', border: 'none', cursor: 'pointer',
                fontSize: 'var(--font-size-sm)', fontWeight: 600,
                color: tab === t.id ? 'var(--accent-primary)' : 'var(--text-muted)',
                borderBottom: `2px solid ${tab === t.id ? 'var(--accent-primary)' : 'transparent'}`,
                marginBottom: -1,
                transition: 'all 0.15s',
              }}
            >
              {t.label}
            </button>
          ))}
        </div>

        {tab === 'drives' && (
          <>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '-var(--space-4)' }}>
              <button className="btn btn-secondary" style={{ fontSize: 'var(--font-size-xs)' }} onClick={() => setSortByMatch(!sortByMatch)}>
                {sortByMatch ? 'Sort by Date' : 'Sort by Match %'}
              </button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {displayDrives.map(drive => (
                <DriveCard key={drive.id} drive={drive} onApply={handleApply} />
              ))}
            </div>
          </>
        )}

        {tab === 'applications' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            {applications.map(app => (
              <ApplicationCard key={app.id} app={app} />
            ))}
          </div>
        )}

      </div>
    </div>
  );
}
