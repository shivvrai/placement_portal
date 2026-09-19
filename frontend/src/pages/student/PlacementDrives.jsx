/**
 * Placement Drives — Active placement drives + student's real application tracker.
 * Tabs: Available Drives | My Applications.
 * Connected to live FastAPI backend via placementApi and studentApi.
 */

import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { placementApi, studentApi } from '../../api/endpoints';

const STATUS_COLORS = {
  open:       { label: 'Open',       color: '#22c55e', bg: 'rgba(34,197,94,0.12)' },
  upcoming:   { label: 'Upcoming',   color: '#6366f1', bg: 'rgba(99,102,241,0.12)' },
  in_progress:{ label: 'In Progress',color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  completed:  { label: 'Completed',  color: 'var(--text-muted)', bg: 'var(--bg-tertiary)' },
  cancelled:  { label: 'Cancelled',  color: '#ef4444', bg: 'rgba(239,68,68,0.12)' },
};

const APP_STATUS_COLORS = {
  applied:     { color: '#6366f1', bg: 'rgba(99,102,241,0.12)', label: 'Applied' },
  shortlisted: { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', label: 'Shortlisted' },
  in_progress: { color: '#06b6d4', bg: 'rgba(6,182,212,0.12)',  label: 'Interviewing' },
  selected:    { color: '#22c55e', bg: 'rgba(34,197,94,0.12)',  label: '🎉 Selected' },
  rejected:    { color: '#ef4444', bg: 'rgba(239,68,68,0.12)',  label: 'Not Selected' },
  withdrawn:   { color: 'var(--text-muted)', bg: 'var(--bg-tertiary)', label: 'Withdrawn' },
};

const STAGE_STATUS = {
  passed:    { icon: '✓', color: '#22c55e' },
  cleared:   { icon: '✓', color: '#22c55e' },
  failed:    { icon: '✗', color: '#ef4444' },
  scheduled: { icon: '◎', color: '#f59e0b' },
  pending:   { icon: '○', color: 'var(--text-muted)' },
};

function daysLeft(deadline) {
  if (!deadline) return null;
  const d = Math.ceil((new Date(deadline) - new Date()) / (1000 * 60 * 60 * 24));
  return d > 0 ? d : 0;
}

function checkEligibility(drive, profile) {
  if (!profile) return { eligible: true, reason: '' };

  if (drive.min_cgpa && profile.cgpa != null && profile.cgpa < drive.min_cgpa) {
    return {
      eligible: false,
      reason: `Requires CGPA ≥ ${drive.min_cgpa} (yours is ${Number(profile.cgpa).toFixed(2)})`,
    };
  }

  const depts = drive.eligible_departments || [];
  const studentDept = profile.department?.code;
  if (depts.length > 0 && studentDept && !depts.includes(studentDept)) {
    return {
      eligible: false,
      reason: `Eligible branches: ${depts.join(', ')} (your branch: ${studentDept})`,
    };
  }

  return { eligible: true, reason: 'You satisfy all eligibility criteria' };
}

// ─── Drive Card ────────────────────────────────────────────────────
function DriveCard({ drive, profile, onApply, applying }) {
  const [expanded, setExpanded] = useState(false);

  const deadline = drive.registration_deadline || drive.deadline;
  const days = daysLeft(deadline);
  const urgency = days === null ? '#6366f1' : days <= 3 ? '#ef4444' : days <= 7 ? '#f59e0b' : '#22c55e';

  const companyName = drive.company?.name || drive.company || 'Unknown Company';
  const location = drive.company?.location || drive.location || 'Remote / Multiple';
  const roles = drive.roles_offered?.length > 0 ? drive.roles_offered.join(', ') : drive.title;
  const sc = STATUS_COLORS[drive.status] || STATUS_COLORS.open;

  const eligibility = checkEligibility(drive, profile);
  const isEligible = eligibility.eligible;
  const hasApplied = drive.has_applied || drive.applied;
  const isOpen = drive.status === 'open' || drive.status === 'upcoming';

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 'var(--space-3)' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
            <span style={{ fontWeight: 700, fontSize: 'var(--font-size-lg)' }}>{companyName}</span>
            <span style={{
              padding: '2px 10px', borderRadius: 999, fontSize: 'var(--font-size-xs)', fontWeight: 600,
              background: sc.bg, color: sc.color,
            }}>
              ● {sc.label}
            </span>
            <span style={{
              padding: '2px 10px', borderRadius: 999, fontSize: 'var(--font-size-xs)', fontWeight: 600,
              background: isEligible ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
              color: isEligible ? '#22c55e' : '#ef4444',
              border: `1px solid ${isEligible ? '#22c55e40' : '#ef444440'}`,
            }}>
              {isEligible ? '✓ Eligible' : '✗ Ineligible'}
            </span>
          </div>

          <div style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)', marginTop: 4 }}>
            {roles} · 📍 {location} {drive.salary_ctc ? `· 💰 ₹${drive.salary_ctc} LPA` : ''}
          </div>
        </div>

        {days !== null && (
          <div style={{ textAlign: 'right' }}>
            <span style={{
              padding: '4px 12px', borderRadius: 999, fontSize: 'var(--font-size-xs)', fontWeight: 700,
              background: `${urgency}18`, color: urgency, border: `1px solid ${urgency}40`,
            }}>
              ⏳ {days > 0 ? `${days}d left to register` : 'Registration closed'}
            </span>
          </div>
        )}
      </div>

      {/* Eligibility explanation if ineligible */}
      {!isEligible && (
        <div style={{
          padding: '8px 12px', borderRadius: 'var(--border-radius-sm)',
          background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
          color: '#ef4444', fontSize: 'var(--font-size-xs)', display: 'flex', alignItems: 'center', gap: 6,
        }}>
          <span>⚠️</span>
          <span>{eligibility.reason}</span>
        </div>
      )}

      {/* Description preview / full */}
      {drive.description && (
        <div>
          <p style={{
            fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', margin: 0,
            lineHeight: 1.5,
            ...(!expanded && { display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }),
          }}>
            {drive.description}
          </p>
          {drive.description.length > 140 && (
            <button
              onClick={() => setExpanded(e => !e)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent-primary)', fontSize: 'var(--font-size-xs)', padding: 0, marginTop: 4 }}
            >
              {expanded ? 'Show less' : 'Read more'}
            </button>
          )}
        </div>
      )}

      {/* Requirements & Criteria */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-4)', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
        {drive.min_cgpa && <span>📊 Min CGPA: <strong style={{ color: 'var(--text-secondary)' }}>{drive.min_cgpa}</strong></span>}
        <span>🎓 Eligible: <strong style={{ color: 'var(--text-secondary)' }}>{drive.eligible_departments?.join(', ') || 'All Branches'}</strong></span>
        {drive.drive_date && <span>📅 Drive Date: <strong style={{ color: 'var(--text-secondary)' }}>{drive.drive_date}</strong></span>}
        <span>👥 {drive.registered_count || 0} students registered</span>
      </div>

      {/* Action button */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 'var(--space-2)' }}>
        <Link
          to={`/student/drives/${drive.id}`}
          className="btn btn-secondary"
          style={{ textDecoration: 'none' }}
        >
          View Details & Schedule 📋
        </Link>
        {hasApplied ? (
          <button
            className="btn btn-secondary"
            disabled
            style={{ minWidth: 140, cursor: 'default', background: 'rgba(34,197,94,0.15)', color: '#22c55e', borderColor: '#22c55e40' }}
          >
            ✓ Applied
          </button>
        ) : !isOpen ? (
          <button className="btn btn-secondary" disabled style={{ minWidth: 140, cursor: 'not-allowed' }}>
            Drive Closed
          </button>
        ) : !isEligible ? (
          <button className="btn btn-secondary" disabled title={eligibility.reason} style={{ minWidth: 140, cursor: 'not-allowed', opacity: 0.6 }}>
            Not Eligible
          </button>
        ) : (
          <button
            className="btn btn-primary"
            onClick={() => onApply(drive.id)}
            disabled={applying}
            style={{ minWidth: 140 }}
          >
            {applying ? 'Submitting...' : 'Apply Now →'}
          </button>
        )}
      </div>
    </div>
  );
}

// ─── Application Card ──────────────────────────────────────────────
function ApplicationCard({ app }) {
  const sc = APP_STATUS_COLORS[app.status] || APP_STATUS_COLORS.applied;
  const companyName = app.company_name || app.drive?.company?.name || 'Company';
  const roleTitle = app.drive_title || app.drive?.title || 'Position';
  const appliedDate = app.applied_at ? new Date(app.applied_at).toLocaleDateString('en-IN') : '—';
  const stages = app.stages || [];

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 'var(--space-3)' }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 'var(--font-size-base)' }}>{companyName}</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)', marginTop: 2 }}>
            {roleTitle} {app.salary_ctc ? `· 💰 ₹${app.salary_ctc} LPA` : ''} · Applied on {appliedDate}
          </div>
        </div>
        <span style={{
          padding: '4px 14px', borderRadius: 999, fontSize: 'var(--font-size-xs)', fontWeight: 600,
          background: sc.bg, color: sc.color,
        }}>
          {sc.label}
        </span>
      </div>

      {/* Stage pipeline */}
      <div>
        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: 'var(--space-2)' }}>
          Current Stage: <strong style={{ color: 'var(--text-secondary)' }}>{app.current_stage || 'Application Submitted'}</strong>
        </div>

        {stages.length > 0 ? (
          <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap', alignItems: 'center' }}>
            {stages.map((stage, i) => {
              const ss = STAGE_STATUS[stage.status] || STAGE_STATUS.pending;
              return (
                <span key={stage.id || stage.stage_name || i} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <span style={{
                    padding: '3px 10px', borderRadius: 999, fontSize: 'var(--font-size-xs)',
                    fontWeight: 600, background: `${ss.color}18`, color: ss.color,
                    border: `1px solid ${ss.color}40`, whiteSpace: 'nowrap',
                  }}>
                    {ss.icon} {stage.stage_name}
                    {stage.scheduled_at && (
                      <span style={{ marginLeft: 4, fontWeight: 400, opacity: 0.8 }}>
                        · {new Date(stage.scheduled_at).toLocaleDateString('en-IN')}
                      </span>
                    )}
                  </span>
                  {i < stages.length - 1 && (
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>→</span>
                  )}
                </span>
              );
            })}
          </div>
        ) : (
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 12px',
            borderRadius: 999, background: 'var(--bg-tertiary)', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)',
          }}>
            <span>📋</span> Application under initial screening by TPO
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main Placement Drives Component ───────────────────────────────
export default function PlacementDrives() {
  const [tab, setTab] = useState('drives');
  const [drives, setDrives] = useState([]);
  const [applications, setApplications] = useState([]);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [applyingId, setApplyingId] = useState(null);
  const [notification, setNotification] = useState(null);

  const showToast = (msg, type = 'success') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const loadAll = useCallback(async () => {
    try {
      setLoading(true);
      const [drivesRes, appsRes, profileRes] = await Promise.allSettled([
        placementApi.getDrives(),
        placementApi.getMyApplications(),
        studentApi.getProfile(),
      ]);

      if (drivesRes.status === 'fulfilled') {
        const dData = drivesRes.value?.data?.data || (Array.isArray(drivesRes.value?.data) ? drivesRes.value.data : []);
        setDrives(dData);
      }

      if (appsRes.status === 'fulfilled') {
        const aData = Array.isArray(appsRes.value?.data) ? appsRes.value.data : [];
        setApplications(aData);
      }

      if (profileRes.status === 'fulfilled') {
        setProfile(profileRes.value?.data || null);
      }
    } catch (err) {
      console.error('Failed to load student placement data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const handleApply = async (driveId) => {
    try {
      setApplyingId(driveId);
      await placementApi.apply(driveId);

      // Optimistically mark as applied
      setDrives(prev => prev.map(d =>
        d.id === driveId
          ? { ...d, has_applied: true, registered_count: (d.registered_count || 0) + 1 }
          : d
      ));

      showToast('Application submitted successfully! Track it in "My Applications".', 'success');

      // Refresh applications list
      try {
        const updatedApps = await placementApi.getMyApplications();
        setApplications(Array.isArray(updatedApps.data) ? updatedApps.data : []);
      } catch {
        // quiet fallback
      }
    } catch (err) {
      console.error('Application failed:', err);
      if (err.response?.status === 409) {
        showToast('You have already applied to this drive.', 'error');
        setDrives(prev => prev.map(d => d.id === driveId ? { ...d, has_applied: true } : d));
      } else {
        showToast(err.response?.data?.detail || 'Failed to submit application.', 'error');
      }
    } finally {
      setApplyingId(null);
    }
  };

  const activeDrivesCount = drives.filter(d => d.status === 'open' || d.status === 'upcoming').length;
  const appliedCount = drives.filter(d => d.has_applied || d.applied).length || applications.length;
  const eligibleCount = drives.filter(d => checkEligibility(d, profile).eligible).length;

  return (
    <div>
      <div className="page-header">
        <h1>Placement Drives</h1>
        <p>Explore institutional hiring drives, evaluate eligibility, and track your active applications</p>
      </div>

      {notification && (
        <div style={{
          padding: 'var(--space-3) var(--space-4)',
          borderRadius: 'var(--border-radius)',
          marginBottom: 'var(--space-4)',
          fontSize: 'var(--font-size-sm)',
          fontWeight: 500,
          background: notification.type === 'error' ? 'rgba(239,68,68,0.12)' : 'rgba(34,197,94,0.12)',
          color: notification.type === 'error' ? '#ef4444' : '#22c55e',
          border: `1px solid ${notification.type === 'error' ? '#ef444440' : '#22c55e40'}`,
        }}>
          {notification.msg}
        </div>
      )}

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--border-color)' }}>
          {[
            { id: 'drives', label: `Available Drives (${drives.length})` },
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
            {/* Summary cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--space-4)' }}>
              {[
                { label: 'Active Drives', value: activeDrivesCount, color: '#22c55e' },
                { label: 'Drives Applied', value: appliedCount, color: '#6366f1' },
                { label: 'Eligible for You', value: eligibleCount, color: '#06b6d4' },
              ].map(s => (
                <div key={s.label} style={{
                  padding: 'var(--space-4)',
                  background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                  borderRadius: 'var(--border-radius)', textAlign: 'center',
                }}>
                  <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: s.color }}>{s.value}</div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 2 }}>{s.label}</div>
                </div>
              ))}
            </div>

            {/* Drives List */}
            {loading ? (
              <div style={{ padding: 'var(--space-12)', textAlign: 'center', color: 'var(--text-muted)' }}>
                Loading placement drives...
              </div>
            ) : drives.length === 0 ? (
              <div className="card" style={{ textAlign: 'center', padding: 'var(--space-12)' }}>
                <div style={{ fontSize: '3rem', marginBottom: 'var(--space-3)' }}>🏢</div>
                <div style={{ fontWeight: 600, fontSize: 'var(--font-size-lg)', marginBottom: 'var(--space-2)' }}>
                  No Active Placement Drives
                </div>
                <p style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)', margin: 0 }}>
                  There are currently no placement drives scheduled. Please check back later or consult the TPO portal.
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                {drives.map(drive => (
                  <DriveCard
                    key={drive.id}
                    drive={drive}
                    profile={profile}
                    onApply={handleApply}
                    applying={applyingId === drive.id}
                  />
                ))}
              </div>
            )}
          </>
        )}

        {tab === 'applications' && (
          <div>
            {loading ? (
              <div style={{ padding: 'var(--space-12)', textAlign: 'center', color: 'var(--text-muted)' }}>
                Loading your applications...
              </div>
            ) : applications.length === 0 ? (
              <div className="card" style={{ textAlign: 'center', padding: 'var(--space-12)' }}>
                <div style={{ fontSize: '3rem', marginBottom: 'var(--space-3)' }}>📋</div>
                <div style={{ fontWeight: 600, fontSize: 'var(--font-size-lg)', marginBottom: 'var(--space-2)' }}>
                  No Applications Submitted Yet
                </div>
                <p style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)', maxWidth: 440, margin: '0 auto var(--space-4)' }}>
                  Browse the Available Drives tab and click &quot;Apply Now&quot; to begin your placement journey.
                </p>
                <button className="btn btn-primary" onClick={() => setTab('drives')}>
                  Browse Available Drives →
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                {applications.map(app => (
                  <ApplicationCard key={app.id} app={app} />
                ))}
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
