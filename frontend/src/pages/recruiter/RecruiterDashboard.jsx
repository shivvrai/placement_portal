/**
 * RecruiterDashboard - Company HR dashboard showing drive stats and shortlisted candidates.
 * Route: /recruiter/dashboard and /recruiter/drives
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { recruiterApi } from '../../api/endpoints';

export default function RecruiterDashboard() {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [drives, setDrives] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [dashRes, drivesRes] = await Promise.all([
          recruiterApi.getDashboard(),
          recruiterApi.getDrives(),
        ]);
        setDashboard(dashRes.data);
        setDrives(Array.isArray(drivesRes.data) ? drivesRes.data : []);
      } catch (err) {
        console.error('Recruiter dashboard load failed:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Loading recruiter portal...</div>;

  const STATUS_COLOR = { upcoming: '#6366f1', open: '#22c55e', in_progress: '#f59e0b', completed: '#6b7280' };

  return (
    <div style={{ padding: 'var(--space-6)', maxWidth: 1100, margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 24 }}>🏢 Recruiter Operations Command</h1>

      {/* Stats Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 32 }}>
        {[
          { label: 'Active Recruitment Drives', value: dashboard?.active_drives ?? 0, color: '#6366f1' },
          { label: 'Shortlisted Candidates', value: dashboard?.shortlisted_total ?? 0, color: '#f59e0b' },
          { label: 'Selected / Final Candidates', value: dashboard?.selected_total ?? 0, color: '#22c55e' },
        ].map(s => (
          <div
            key={s.label}
            style={{
              padding: '20px 24px', borderRadius: 14, background: 'var(--bg-secondary)',
              border: `1px solid ${s.color}30`, textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '2.2rem', fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: 4 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Drives List */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0 }}>Company Drives &amp; Candidate Pools</h2>
      </div>

      {drives.length === 0 && (
        <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)', background: 'var(--bg-secondary)', borderRadius: 12 }}>
          No recruitment drives found for your assigned company. Contact TPO for drive allocation.
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
        {drives.map(drive => (
          <div
            key={drive.id}
            className="card"
            style={{ padding: '20px', cursor: 'pointer', transition: 'transform 0.15s ease' }}
            onClick={() => navigate(`/recruiter/drives/${drive.id}/applicants`)}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
              <div style={{ fontWeight: 700, fontSize: '1.05rem' }}>{drive.title}</div>
              <span style={{
                padding: '3px 10px', borderRadius: 99, fontSize: '0.72rem', fontWeight: 700,
                background: (STATUS_COLOR[drive.status] || '#6366f1') + '20',
                color: STATUS_COLOR[drive.status] || '#6366f1',
              }}>
                {drive.status?.replace('_', ' ').toUpperCase()}
              </span>
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 8 }}>🏢 {drive.company_name}</div>
            {drive.drive_date && (
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 14 }}>
                📅 Scheduled: {new Date(drive.drive_date).toLocaleDateString()}
              </div>
            )}
            <div style={{ display: 'flex', gap: 16, paddingTop: 12, borderTop: '1px solid var(--border-color)' }}>
              <div style={{ textAlign: 'center', flex: 1 }}>
                <div style={{ fontWeight: 700, color: '#f59e0b', fontSize: '1.2rem' }}>{drive.shortlisted_count}</div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Shortlisted</div>
              </div>
              <div style={{ textAlign: 'center', flex: 1 }}>
                <div style={{ fontWeight: 700, color: '#22c55e', fontSize: '1.2rem' }}>{drive.selected_count}</div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Selected</div>
              </div>
            </div>
            <button className="btn btn-secondary" style={{ width: '100%', marginTop: 14, fontSize: '0.82rem' }}>
              Review Candidates →
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
