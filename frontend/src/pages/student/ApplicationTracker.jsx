/**
 * ApplicationTracker — Visual timeline of all student placement applications.
 * Shows real-time status, next-step guidance, and immutable event history.
 *
 * Sprint 3 — Anjula
 */

import { useState } from 'react';

const MOCK_APPLICATIONS = [
  {
    application_id: '1', drive_title: 'TCS NQT Campus Drive 2025', company_name: 'TCS',
    role: 'System Engineer', current_status: 'shortlisted', applied_at: '2025-09-01',
    next_steps: 'Congratulations! You\'ve been shortlisted. Prepare for the technical interview.',
    timeline: [
      { id: 't1', event_type: 'applied', to_status: 'applied', description: 'Application submitted successfully', created_at: '2025-09-01T10:00:00' },
      { id: 't2', event_type: 'status_change', from_status: 'applied', to_status: 'shortlisted', description: 'Shortlisted based on CGPA ≥ 7.0 and aptitude score', created_at: '2025-09-10T14:30:00' },
    ],
  },
  {
    application_id: '2', drive_title: 'Infosys InfyTQ SP Drive', company_name: 'Infosys',
    role: 'Specialist Programmer', current_status: 'in_progress', applied_at: '2025-08-25',
    next_steps: 'Interview rounds are in progress. Stay prepared for the next round.',
    timeline: [
      { id: 't3', event_type: 'applied', to_status: 'applied', description: 'Application via InfyTQ portal', created_at: '2025-08-25T09:00:00' },
      { id: 't4', event_type: 'status_change', from_status: 'applied', to_status: 'shortlisted', description: 'Cleared online assessment (Score: 85/100)', created_at: '2025-09-05T16:00:00' },
      { id: 't5', event_type: 'interview', from_status: 'shortlisted', to_status: 'in_progress', description: 'Technical Interview Round 1 scheduled', created_at: '2025-09-15T11:00:00' },
    ],
  },
  {
    application_id: '3', drive_title: 'Wipro Elite NLTH', company_name: 'Wipro',
    role: 'Project Engineer', current_status: 'selected', applied_at: '2025-08-15',
    next_steps: '🎉 You\'ve been selected! Check for your offer letter in the Document Vault.',
    timeline: [
      { id: 't6', event_type: 'applied', to_status: 'applied', description: 'Application submitted', created_at: '2025-08-15T08:30:00' },
      { id: 't7', event_type: 'status_change', from_status: 'applied', to_status: 'shortlisted', description: 'Cleared NLTH exam', created_at: '2025-08-28T10:00:00' },
      { id: 't8', event_type: 'interview', from_status: 'shortlisted', to_status: 'in_progress', description: 'Technical + HR Interview completed', created_at: '2025-09-08T15:00:00' },
      { id: 't9', event_type: 'offer', from_status: 'in_progress', to_status: 'selected', description: 'Offer letter received — ₹3.5 LPA', created_at: '2025-09-20T12:00:00' },
    ],
  },
];

const STATUS_CONFIG = {
  applied: { label: 'Applied', color: '#6366f1', bg: 'rgba(99,102,241,0.12)', icon: '📋' },
  shortlisted: { label: 'Shortlisted', color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', icon: '⭐' },
  in_progress: { label: 'In Progress', color: '#06b6d4', bg: 'rgba(6,182,212,0.12)', icon: '⏳' },
  selected: { label: 'Selected', color: '#22c55e', bg: 'rgba(34,197,94,0.12)', icon: '🎉' },
  rejected: { label: 'Rejected', color: '#ef4444', bg: 'rgba(239,68,68,0.12)', icon: '❌' },
  withdrawn: { label: 'Withdrawn', color: '#94a3b8', bg: 'rgba(148,163,184,0.12)', icon: '↩️' },
};

export default function ApplicationTracker() {
  const [applications] = useState(MOCK_APPLICATIONS);
  const [expandedApp, setExpandedApp] = useState(null);

  const stats = {
    total: applications.length,
    selected: applications.filter(a => a.current_status === 'selected').length,
    active: applications.filter(a => ['applied', 'shortlisted', 'in_progress'].includes(a.current_status)).length,
  };

  return (
    <div style={{ padding: '2rem' }}>
      <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
        📊 Application Tracker
      </h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
        Track the status of all your placement applications in one place.
      </p>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        {[
          { label: 'Total Applications', value: stats.total, color: '#6366f1' },
          { label: 'Active', value: stats.active, color: '#06b6d4' },
          { label: 'Selected', value: stats.selected, color: '#22c55e' },
        ].map(s => (
          <div key={s.label} style={{ background: 'var(--bg-secondary)', borderRadius: '12px', padding: '1rem', border: '1px solid var(--border-primary)' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Application Cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {applications.map(app => {
          const statusCfg = STATUS_CONFIG[app.current_status] || STATUS_CONFIG.applied;
          const isExpanded = expandedApp === app.application_id;
          return (
            <div key={app.application_id} style={{
              background: 'var(--bg-secondary)', borderRadius: '12px',
              border: '1px solid var(--border-primary)', overflow: 'hidden',
              borderLeft: `4px solid ${statusCfg.color}`,
            }}>
              {/* Header */}
              <div onClick={() => setExpandedApp(isExpanded ? null : app.application_id)} style={{
                padding: '1.25rem 1.5rem', cursor: 'pointer',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <div>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                    {app.company_name} — {app.role}
                  </h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', margin: '0.2rem 0 0' }}>{app.drive_title}</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span style={{
                    padding: '0.3rem 0.8rem', borderRadius: '20px', fontSize: '0.78rem', fontWeight: 600,
                    background: statusCfg.bg, color: statusCfg.color,
                  }}>{statusCfg.icon} {statusCfg.label}</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '1.2rem', transform: isExpanded ? 'rotate(180deg)' : '', transition: 'transform 0.2s' }}>▼</span>
                </div>
              </div>

              {/* Expanded Timeline */}
              {isExpanded && (
                <div style={{ padding: '0 1.5rem 1.5rem', borderTop: '1px solid var(--border-primary)' }}>
                  {/* Next Steps */}
                  <div style={{
                    background: `${statusCfg.bg}`, borderRadius: '8px', padding: '0.75rem 1rem',
                    margin: '1rem 0', borderLeft: `3px solid ${statusCfg.color}`,
                  }}>
                    <strong style={{ fontSize: '0.82rem', color: statusCfg.color }}>Next Steps:</strong>
                    <p style={{ color: 'var(--text-primary)', fontSize: '0.82rem', margin: '0.2rem 0 0' }}>{app.next_steps}</p>
                  </div>

                  {/* Timeline */}
                  <div style={{ position: 'relative', paddingLeft: '2rem' }}>
                    <div style={{ position: 'absolute', left: '0.65rem', top: 0, bottom: 0, width: '2px', background: 'var(--border-primary)' }} />
                    {app.timeline.map((event, idx) => {
                      const eventStatus = STATUS_CONFIG[event.to_status] || STATUS_CONFIG.applied;
                      return (
                        <div key={event.id} style={{ position: 'relative', paddingBottom: idx < app.timeline.length - 1 ? '1.5rem' : 0 }}>
                          <div style={{
                            position: 'absolute', left: '-1.6rem', top: '0.15rem',
                            width: '14px', height: '14px', borderRadius: '50%',
                            background: eventStatus.color, border: '2px solid var(--bg-secondary)',
                          }} />
                          <div style={{ fontSize: '0.82rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                            {event.description}
                          </div>
                          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                            {new Date(event.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                            {' · '}{new Date(event.created_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
