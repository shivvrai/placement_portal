/**
 * Placement Drives — active drives + my applications.
 * Tabs: Available Drives | My Applications
 */

import { useState } from 'react';

// ─── Mock Data ────────────────────────────────────────────────────
const MOCK_DRIVES = [
  {
    id: 1, company: 'Google', role: 'SWE Intern', location: 'Bangalore',
    deadline: '2026-09-10', drive_date: '2026-09-20',
    min_cgpa: 7.5, max_backlogs: 0, salary_ctc: 80,
    eligible_departments: ['CS', 'IT'],
    roles_offered: ['SWE Intern'],
    status: 'open',
    applied: false,
    description: 'Join Google\'s summer intern cohort. Work on real products with full-time engineers. Strong CS fundamentals required.',
    required_skills: ['Algorithms', 'Data Structures', 'Python / C++', 'System Design'],
    process: ['Online Assessment', 'Technical Round 1', 'Technical Round 2', 'HR'],
  },
  {
    id: 2, company: 'Amazon', role: 'Data Engineer', location: 'Hyderabad',
    deadline: '2026-09-15', drive_date: '2026-09-25',
    min_cgpa: 7.0, max_backlogs: 0, salary_ctc: 25,
    eligible_departments: ['CS', 'IT', 'ECE'],
    roles_offered: ['Data Engineer', 'SDE'],
    status: 'open',
    applied: true,
    description: 'Build robust data pipelines that power Amazon\'s logistics and recommendation systems at petabyte scale.',
    required_skills: ['Python', 'SQL', 'Spark', 'AWS', 'System Design'],
    process: ['OA', 'Technical', 'Bar Raiser'],
  },
  {
    id: 3, company: 'Infosys', role: 'System Engineer', location: 'Pune',
    deadline: '2026-09-20', drive_date: '2026-10-01',
    min_cgpa: 6.0, max_backlogs: 1, salary_ctc: 3.6,
    eligible_departments: ['CS', 'IT', 'ECE', 'ME', 'EEE'],
    roles_offered: ['System Engineer'],
    status: 'open',
    applied: false,
    description: 'Entry-level engineering role. Join Infosys\'s Mysore training campus before deployment to client projects.',
    required_skills: ['Programming Basics', 'DBMS', 'Aptitude', 'Communication'],
    process: ['Aptitude', 'Technical', 'HR'],
  },
  {
    id: 4, company: 'Deloitte', role: 'Analyst', location: 'Mumbai',
    deadline: '2026-10-05', drive_date: '2026-10-15',
    min_cgpa: 6.5, max_backlogs: 0, salary_ctc: 7.5,
    eligible_departments: ['CS', 'IT', 'ECE'],
    roles_offered: ['Technology Analyst'],
    status: 'open',
    applied: false,
    description: 'Work in Deloitte\'s tech consulting practice. Deliver digital transformation projects for enterprise clients.',
    required_skills: ['Programming', 'SQL', 'Communication', 'Problem Solving'],
    process: ['Group Discussion', 'Technical', 'Case Study', 'HR'],
  },
  {
    id: 5, company: 'Wipro', role: 'Project Engineer', location: 'Chennai',
    deadline: '2026-10-10', drive_date: '2026-10-20',
    min_cgpa: 6.0, max_backlogs: 1, salary_ctc: 3.5,
    eligible_departments: ['CS', 'IT', 'ECE', 'ME'],
    roles_offered: ['Project Engineer'],
    status: 'open',
    applied: false,
    description: 'On-campus mass recruitment. Fast selection process. Training provided before project allocation.',
    required_skills: ['Core CS', 'Communication', 'Aptitude'],
    process: ['Aptitude', 'Technical', 'HR'],
  },
];

const MOCK_APPLICATIONS = [
  {
    id: 'app1', company: 'Amazon', role: 'Data Engineer',
    applied_at: '2026-08-20', status: 'shortlisted',
    current_stage: 'Technical Round 1',
    salary_ctc: 25,
    stages: [
      { name: 'Online Assessment', status: 'passed' },
      { name: 'Technical Round 1', status: 'scheduled', scheduled_at: '2026-09-05' },
      { name: 'Bar Raiser', status: 'pending' },
    ],
  },
  {
    id: 'app2', company: 'TCS', role: 'Software Engineer',
    applied_at: '2026-08-10', status: 'selected',
    current_stage: 'Offer Released',
    salary_ctc: 7.0,
    stages: [
      { name: 'TCS NQT', status: 'passed' },
      { name: 'Technical', status: 'passed' },
      { name: 'HR', status: 'passed' },
    ],
  },
  {
    id: 'app3', company: 'Accenture', role: 'Associate SE',
    applied_at: '2026-07-28', status: 'rejected',
    current_stage: 'Technical Round',
    salary_ctc: 4.5,
    stages: [
      { name: 'Aptitude', status: 'passed' },
      { name: 'Technical', status: 'failed' },
    ],
  },
];

const STATUS_COLORS = {
  open:       { label: 'Open',       color: '#22c55e', bg: 'rgba(34,197,94,0.1)' },
  upcoming:   { label: 'Upcoming',   color: '#6366f1', bg: 'rgba(99,102,241,0.1)' },
  completed:  { label: 'Completed',  color: 'var(--text-muted)', bg: 'var(--bg-tertiary)' },
};

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
  const days = daysLeft(drive.deadline);
  const urgency = days <= 3 ? '#ef4444' : days <= 7 ? '#f59e0b' : '#22c55e';

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 'var(--font-size-lg)' }}>{drive.company}</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)', marginTop: 2 }}>
            {drive.roles_offered.join(', ')} · 📍 {drive.location}
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
        <span style={{ color: 'var(--text-muted)' }}>🎓 {drive.eligible_departments.join(', ')}</span>
      </div>

      {/* Skill pills */}
      <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
        {drive.required_skills.map(s => (
          <span key={s} style={{
            padding: '2px 10px', borderRadius: 999, fontSize: 'var(--font-size-xs)',
            background: 'var(--bg-tertiary)', color: 'var(--text-secondary)',
            border: '1px solid var(--border-color)',
          }}>{s}</span>
        ))}
      </div>

      {/* Expand */}
      {expanded && (
        <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: 'var(--space-4)' }}>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: 'var(--space-4)' }}>
            {drive.description}
          </p>
          <div style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-2)' }}>Interview Process</div>
          <div style={{ display: 'flex', gap: 0, alignItems: 'center', flexWrap: 'wrap' }}>
            {drive.process.map((step, i) => (
              <span key={step} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <span style={{
                  padding: '4px 12px', borderRadius: 999, fontSize: 'var(--font-size-xs)',
                  background: 'var(--accent-primary-subtle)', color: 'var(--accent-primary)',
                  fontWeight: 600,
                }}>{i + 1}. {step}</span>
                {i < drive.process.length - 1 && (
                  <span style={{ color: 'var(--text-muted)', margin: '0 4px' }}>→</span>
                )}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'auto' }}>
        <button
          className="btn btn-ghost"
          style={{ height: 36, fontSize: 'var(--font-size-sm)' }}
          onClick={() => setExpanded(e => !e)}
        >
          {expanded ? 'Show less ▲' : 'View details ▼'}
        </button>
        {drive.applied ? (
          <span style={{
            display: 'inline-flex', alignItems: 'center', padding: '0 var(--space-4)',
            borderRadius: 'var(--border-radius-sm)', fontSize: 'var(--font-size-sm)',
            background: 'rgba(34,197,94,0.1)', color: '#22c55e', fontWeight: 600,
          }}>
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
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 2 }}>
            Applied: {app.applied_at}
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
        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: 'var(--space-3)' }}>
          Current stage: <strong style={{ color: 'var(--text-secondary)' }}>{app.current_stage}</strong>
        </div>
        <div style={{ display: 'flex', gap: 0, flexWrap: 'wrap', alignItems: 'center' }}>
          {app.stages.map((stage, i) => {
            const ss = STAGE_STATUS[stage.status] || STAGE_STATUS.pending;
            return (
              <span key={stage.name} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <span style={{
                  padding: '3px 10px', borderRadius: 999, fontSize: 'var(--font-size-xs)',
                  fontWeight: 600, background: `${ss.color}18`, color: ss.color,
                  border: `1px solid ${ss.color}40`,
                  whiteSpace: 'nowrap',
                }}>
                  {ss.icon} {stage.name}
                  {stage.scheduled_at && <span style={{ marginLeft: 4, fontWeight: 400, color: 'inherit', opacity: 0.7 }}>· {stage.scheduled_at}</span>}
                </span>
                {i < app.stages.length - 1 && (
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.65rem', margin: '0 2px' }}>→</span>
                )}
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
  const [filter, setFilter] = useState('all');
  const [drives, setDrives] = useState(MOCK_DRIVES);

  const handleApply = (driveId) => {
    setDrives(prev => prev.map(d => d.id === driveId ? { ...d, applied: true } : d));
  };

  const filtered = filter === 'all' ? drives : drives.filter(d => d.eligible_departments.includes('CS'));

  return (
    <div>
      <div className="page-header">
        <h1>Placement Drives</h1>
        <p>Track active placement drives and your applications</p>
      </div>

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: 0 }}>
          {[
            { id: 'drives', label: `Available Drives (${drives.filter(d => !d.applied).length})` },
            { id: 'applications', label: `My Applications (${MOCK_APPLICATIONS.length})` },
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
            {/* Summary stats */}
            <div style={{ display: 'flex', gap: 'var(--space-4)' }}>
              {[
                { label: 'Active Drives', value: drives.filter(d => d.status === 'open').length, color: '#22c55e' },
                { label: 'Applied', value: drives.filter(d => d.applied).length, color: '#6366f1' },
                { label: 'Eligible for you', value: drives.length, color: '#06b6d4' },
              ].map(s => (
                <div key={s.label} style={{
                  flex: 1, padding: 'var(--space-4) var(--space-5)',
                  background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                  borderRadius: 'var(--border-radius)', textAlign: 'center',
                }}>
                  <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: s.color }}>{s.value}</div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{s.label}</div>
                </div>
              ))}
            </div>

            {/* Drive cards */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {filtered.map(drive => (
                <DriveCard key={drive.id} drive={drive} onApply={handleApply} />
              ))}
            </div>
          </>
        )}

        {tab === 'applications' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            {MOCK_APPLICATIONS.map(app => (
              <ApplicationCard key={app.id} app={app} />
            ))}
          </div>
        )}

      </div>
    </div>
  );
}
