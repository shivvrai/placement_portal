/**
 * Comprehensive Placement Drive Detail Page with Multi-Round Logistics.
 * Route: /student/drives/:id and /tpo/drives/:id
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { placementApi, studentApi } from '../../api/endpoints';

const DEFAULT_ROUNDS = [
  {
    round_number: 1,
    name: 'Online Coding & Aptitude Assessment',
    format: 'Online Platform',
    platform: 'HackerRank Assessment Suite',
    duration: '90 Minutes',
    details: 'Covers Data Structures, Algorithms, Core CS fundamentals, and logical reasoning.',
  },
  {
    round_number: 2,
    name: 'Technical Interview Round I',
    format: 'Virtual Video Call',
    platform: 'Google Meet / MS Teams',
    duration: '45-60 Minutes',
    details: 'Live coding on shared IDE. In-depth algorithmic problem solving and time complexity analysis.',
  },
  {
    round_number: 3,
    name: 'Technical Interview Round II & Design',
    format: 'Virtual / In-Person',
    platform: 'CS Department Placement Hall',
    duration: '45 Minutes',
    details: 'System architecture, database schema design, and final year projects evaluation.',
  },
  {
    round_number: 4,
    name: 'HR & Leadership Fit Discussion',
    format: 'In-Person / Virtual',
    platform: 'Corporate Conference Room',
    duration: '30 Minutes',
    details: 'Discussion on organizational culture, communication, relocation preferences, and offer terms.',
  },
];

export default function DriveDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const isTpo = user?.role === 'tpo' || user?.role === 'admin';

  const [drive, setDrive] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [hasApplied, setHasApplied] = useState(false);
  const [applySuccess, setApplySuccess] = useState(false);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const driveRes = await placementApi.getDrive(id);
        if (driveRes.data) {
          setDrive(driveRes.data);
          setHasApplied(driveRes.data.has_applied || false);
        }

        if (!isTpo) {
          const profRes = await studentApi.getProfile();
          if (profRes.data) {
            setProfile(profRes.data);
          }
        }
      } catch (err) {
        console.error('Failed to load drive detail:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id, isTpo]);

  // Eligibility evaluation
  const checkEligibility = () => {
    if (!profile || !drive) return { eligible: true, reasons: [] };
    const reasons = [];

    if (drive.min_cgpa && profile.cgpa != null && profile.cgpa < drive.min_cgpa) {
      reasons.push(`Requires CGPA ≥ ${drive.min_cgpa} (Your CGPA: ${Number(profile.cgpa).toFixed(2)})`);
    }

    const depts = drive.eligible_departments || [];
    const studentDept = profile.department?.code;
    if (depts.length > 0 && studentDept && !depts.includes(studentDept)) {
      reasons.push(`Eligible departments: ${depts.join(', ')} (Your department: ${studentDept})`);
    }

    const backlogs = profile.backlogs_count || 0;
    if (drive.max_backlogs != null && backlogs > drive.max_backlogs) {
      reasons.push(`Max backlogs allowed: ${drive.max_backlogs} (You have: ${backlogs})`);
    }

    return {
      eligible: reasons.length === 0,
      reasons,
    };
  };

  const { eligible, reasons } = checkEligibility();

  // Apply Handler
  const handleApply = async () => {
    try {
      setApplying(true);
      await placementApi.apply(id);
      setHasApplied(true);
      setApplySuccess(true);
    } catch (err) {
      console.error('Application failed:', err);
      alert(err.response?.data?.detail || 'Failed to submit application.');
    } finally {
      setApplying(false);
    }
  };

  // TPO Roster CSV Export
  const handleExportRoster = async () => {
    try {
      setExporting(true);
      const res = await placementApi.shortlistStudents(id);
      const students = res.data?.shortlisted_students || res.data || [];

      if (!Array.isArray(students) || students.length === 0) {
        alert('No registered applicants found for this drive.');
        return;
      }

      const headers = ['Roll Number', 'Full Name', 'Department', 'CGPA', 'Status', 'Applied At'];
      const rows = students.map(s => [
        s.roll_number || s.student_id || 'N/A',
        s.student_name || s.name || 'N/A',
        s.department || 'N/A',
        s.cgpa || 'N/A',
        s.status || 'applied',
        s.applied_at ? new Date(s.applied_at).toLocaleDateString() : 'N/A',
      ]);

      const csvContent = [headers.join(','), ...rows.map(r => r.map(f => `"${f}"`).join(','))].join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Attendance_Roster_${drive?.title || 'Drive'}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error('Export failed:', err);
      alert('Failed to export candidate roster.');
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--text-muted)' }}>
        Loading drive logistics...
      </div>
    );
  }

  if (!drive) {
    return (
      <div style={{ padding: 'var(--space-8)', textAlign: 'center' }}>
        <h2>Drive Not Found</h2>
        <button className="btn btn-secondary" onClick={() => navigate(-1)} style={{ marginTop: 16 }}>
          ← Back
        </button>
      </div>
    );
  }

  const rounds = drive.rounds && drive.rounds.length > 0 ? drive.rounds : DEFAULT_ROUNDS;

  return (
    <div style={{ padding: 'var(--space-6) var(--space-8)', maxWidth: 1200, margin: '0 auto' }}>
      {/* Back Link */}
      <button
        onClick={() => navigate(isTpo ? '/tpo/drives' : '/student/drives')}
        style={{
          background: 'none',
          border: 'none',
          color: 'var(--text-secondary)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          fontSize: '0.9rem',
          marginBottom: 'var(--space-4)',
        }}
      >
        ← Back to Placement Drives
      </button>

      {/* Hero Header Card */}
      <div
        className="card"
        style={{
          padding: 'var(--space-6)',
          background: 'var(--bg-secondary)',
          borderRadius: 'var(--border-radius-lg, 16px)',
          border: '1px solid var(--border-color)',
          marginBottom: 'var(--space-6)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: 14,
                background: 'linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '2rem',
                color: 'white',
                boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)',
              }}
            >
              🏢
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <h1 style={{ fontSize: '1.6rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                  {drive.company?.name || drive.title}
                </h1>
                <span
                  style={{
                    padding: '4px 10px',
                    borderRadius: 20,
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    background: drive.status === 'open' ? 'rgba(34,197,94,0.15)' : 'rgba(99,102,241,0.15)',
                    color: drive.status === 'open' ? '#22c55e' : '#6366f1',
                    border: `1px solid ${drive.status === 'open' ? '#22c55e' : '#6366f1'}40`,
                  }}
                >
                  {drive.status}
                </span>
              </div>

              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: 4 }}>
                {drive.company?.industry || 'Technology'} • {drive.company?.location || 'Pan-India'}
                {drive.company?.website && (
                  <a
                    href={drive.company.website}
                    target="_blank"
                    rel="noreferrer"
                    style={{ marginLeft: 12, color: 'var(--accent-primary)', textDecoration: 'none' }}
                  >
                    🌐 {drive.company.website.replace('https://', '')}
                  </a>
                )}
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <div style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Package CTC</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#22c55e' }}>
                ₹{drive.salary_ctc ? `${drive.salary_ctc} LPA` : 'Competitive'}
              </div>
            </div>

            {isTpo && (
              <button
                className="btn btn-primary"
                onClick={handleExportRoster}
                disabled={exporting}
                style={{ padding: '8px 16px', fontSize: '0.85rem' }}
              >
                {exporting ? 'Exporting...' : '📋 Download Attendance Roster (CSV)'}
              </button>
            )}
          </div>
        </div>

        {/* Company About / Description */}
        <p style={{ marginTop: 'var(--space-4)', color: 'var(--text-secondary)', lineHeight: 1.5, fontSize: '0.95rem' }}>
          {drive.company?.about || drive.description}
        </p>

        {/* Roles & Conditions Pill Grid */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginTop: 'var(--space-4)', paddingTop: 'var(--space-4)', borderTop: '1px solid var(--border-color)' }}>
          <div style={{ padding: '6px 12px', background: 'var(--bg-tertiary)', borderRadius: 8, fontSize: '0.82rem' }}>
            💼 <strong>Roles:</strong> {drive.roles_offered?.join(', ') || 'Software Engineer'}
          </div>
          <div style={{ padding: '6px 12px', background: 'var(--bg-tertiary)', borderRadius: 8, fontSize: '0.82rem' }}>
            🛡 <strong>Bond:</strong> {drive.bond_terms || 'None'}
          </div>
          <div style={{ padding: '6px 12px', background: 'var(--bg-tertiary)', borderRadius: 8, fontSize: '0.82rem' }}>
            ⏱ <strong>Probation:</strong> {drive.probation_period || '6 Months'}
          </div>
          <div style={{ padding: '6px 12px', background: 'var(--bg-tertiary)', borderRadius: 8, fontSize: '0.82rem' }}>
            👥 <strong>Registered:</strong> {drive.registered_count || 0} students
          </div>
        </div>
      </div>

      {/* Two-Column Layout for Schedule and Eligibility */}
      <div style={{ display: 'grid', gridTemplateColumns: isTpo ? '1fr' : '2fr 1.2fr', gap: 'var(--space-6)', alignItems: 'start' }}>
        {/* Multi-Round Logistics Timeline */}
        <div className="card" style={{ padding: 'var(--space-6)' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: 'var(--space-4)', display: 'flex', alignItems: 'center', gap: 8 }}>
            📅 Multi-Round Interview Schedule
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {rounds.map((r, index) => {
              const roundColors = ['#3b82f6', '#8b5cf6', '#f59e0b', '#10b981'];
              const color = roundColors[index % roundColors.length];

              return (
                <div
                  key={index}
                  style={{
                    display: 'flex',
                    gap: 16,
                    position: 'relative',
                    paddingBottom: index < rounds.length - 1 ? 16 : 0,
                    borderBottom: index < rounds.length - 1 ? '1px dashed var(--border-color)' : 'none',
                  }}
                >
                  {/* Badge circle */}
                  <div
                    style={{
                      width: 36,
                      height: 36,
                      borderRadius: '50%',
                      background: `${color}20`,
                      color: color,
                      border: `2px solid ${color}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                      fontSize: '0.9rem',
                      flexShrink: 0,
                    }}
                  >
                    R{r.round_number || index + 1}
                  </div>

                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                      <div style={{ fontWeight: 600, fontSize: '0.98rem', color: 'var(--text-primary)' }}>
                        {r.name}
                      </div>
                      <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: 4, background: 'var(--bg-tertiary)', color: 'var(--text-muted)' }}>
                        {r.duration || '60 mins'}
                      </span>
                    </div>

                    <div style={{ fontSize: '0.82rem', color: 'var(--accent-primary)', marginTop: 2 }}>
                      📍 {r.format} • {r.platform}
                    </div>

                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: 6, marginBottom: 8, lineHeight: 1.4 }}>
                      {r.details}
                    </p>

                    <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                      {r.scheduled_at && (
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                          ⏰ Scheduled: {new Date(r.scheduled_at).toLocaleString()}
                        </div>
                      )}
                      {r.platform?.includes('Meet') || r.platform?.includes('Chime') ? (
                        <button
                          className="btn btn-ghost"
                          style={{ fontSize: '0.75rem', height: 28, padding: '0 8px' }}
                          onClick={() => window.open('https://meet.google.com', '_blank')}
                        >
                          🔗 Virtual Room Link
                        </button>
                      ) : null}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Student Eligibility & Application Card */}
        {!isTpo && (
          <div className="card" style={{ padding: 'var(--space-6)', position: 'sticky', top: 20 }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: 'var(--space-4)' }}>
              🎯 Your Eligibility Status
            </h3>

            {/* Criteria Breakdown */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 'var(--space-6)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.88rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Minimum CGPA:</span>
                <span style={{ fontWeight: 600, color: profile?.cgpa >= (drive.min_cgpa || 0) ? '#22c55e' : '#ef4444' }}>
                  {profile?.cgpa ? Number(profile.cgpa).toFixed(2) : 'N/A'} (Req: {drive.min_cgpa || 'Any'})
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.88rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Department:</span>
                <span style={{ fontWeight: 600, color: eligible ? '#22c55e' : '#f59e0b' }}>
                  {profile?.department?.code || 'CS'}
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.88rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Active Backlogs:</span>
                <span style={{ fontWeight: 600, color: (profile?.backlogs_count || 0) <= (drive.max_backlogs || 0) ? '#22c55e' : '#ef4444' }}>
                  {profile?.backlogs_count || 0} allowed (Max: {drive.max_backlogs || 0})
                </span>
              </div>
            </div>

            {/* Ineligible Warning */}
            {!eligible && (
              <div style={{ padding: '12px', borderRadius: 8, background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.25)', marginBottom: 16 }}>
                <div style={{ color: '#ef4444', fontWeight: 600, fontSize: '0.85rem', marginBottom: 4 }}>
                  Ineligible for this Drive
                </div>
                {reasons.map((r, i) => (
                  <div key={i} style={{ fontSize: '0.78rem', color: '#f87171' }}>• {r}</div>
                ))}
              </div>
            )}

            {/* Application Success Banner */}
            {applySuccess && (
              <div style={{ padding: '12px', borderRadius: 8, background: 'rgba(34, 197, 94, 0.15)', border: '1px solid #22c55e40', marginBottom: 16 }}>
                <div style={{ color: '#22c55e', fontWeight: 600, fontSize: '0.9rem' }}>
                  ✓ Application Submitted Successfully!
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: 4 }}>
                  Your profile has been forwarded to the placement cell and hiring team.
                </div>
              </div>
            )}

            {/* Action CTA */}
            {hasApplied ? (
              <div style={{ textAlign: 'center', padding: '12px', background: 'var(--bg-tertiary)', borderRadius: 8 }}>
                <span style={{ color: '#22c55e', fontWeight: 600 }}>✓ Application Registered</span>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 4 }}>
                  Status: Under Review by Placement Committee
                </div>
              </div>
            ) : (
              <button
                className="btn btn-primary"
                onClick={handleApply}
                disabled={!eligible || applying}
                style={{ width: '100%', padding: '12px', fontSize: '0.95rem' }}
              >
                {applying ? 'Submitting Application...' : '🚀 Apply Now for this Drive'}
              </button>
            )}

            {drive.registration_deadline && (
              <div style={{ textAlign: 'center', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 12 }}>
                Deadline: {new Date(drive.registration_deadline).toLocaleDateString()}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
