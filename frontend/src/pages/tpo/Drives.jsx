/**
 * TPO Drives — manage placement drives: create, monitor progress, shortlist.
 */

import { useState } from 'react';

// ─── Mock Data ────────────────────────────────────────────────────
const MOCK_DRIVES = [
  {
    id: 1, company: 'Google', role: 'SWE Intern', location: 'Bangalore',
    deadline: '2026-09-10', drive_date: '2026-09-20',
    min_cgpa: 7.5, max_backlogs: 0, salary_ctc: 80,
    eligible_departments: ['CS', 'IT'],
    status: 'open',
    registered: 48, shortlisted: 0, selected: 0, total_seats: 6,
    process: ['Online Assessment', 'Tech Round 1', 'Tech Round 2', 'HR'],
  },
  {
    id: 2, company: 'Amazon', role: 'Data Engineer', location: 'Hyderabad',
    deadline: '2026-09-15', drive_date: '2026-09-25',
    min_cgpa: 7.0, max_backlogs: 0, salary_ctc: 25,
    eligible_departments: ['CS', 'IT', 'ECE'],
    status: 'in_progress',
    registered: 62, shortlisted: 18, selected: 0, total_seats: 12,
    process: ['OA', 'Technical', 'Bar Raiser'],
  },
  {
    id: 3, company: 'Infosys', role: 'System Engineer', location: 'Pune',
    deadline: '2026-09-20', drive_date: '2026-10-01',
    min_cgpa: 6.0, max_backlogs: 1, salary_ctc: 3.6,
    eligible_departments: ['CS', 'IT', 'ECE', 'ME', 'EEE'],
    status: 'open',
    registered: 120, shortlisted: 0, selected: 0, total_seats: 38,
    process: ['Aptitude', 'Technical', 'HR'],
  },
  {
    id: 4, company: 'TCS', role: 'Software Engineer', location: 'Multiple',
    deadline: '2026-08-20', drive_date: '2026-08-28',
    min_cgpa: 6.5, max_backlogs: 0, salary_ctc: 7.0,
    eligible_departments: ['CS', 'IT', 'ECE'],
    status: 'completed',
    registered: 88, shortlisted: 35, selected: 32, total_seats: 32,
    process: ['TCS NQT', 'Technical', 'HR'],
  },
];

const SHORTLISTED_STUDENTS = [
  { id: 1, roll: 'CS21B001', name: 'Priya Agarwal',   cgpa: 9.1, skill: 88, stage: 'Technical', result: 'passed' },
  { id: 2, roll: 'CS21B042', name: 'Arjun Sharma',    cgpa: 8.1, skill: 73, stage: 'Technical', result: 'scheduled' },
  { id: 3, roll: 'IT21B015', name: 'Sneha Reddy',     cgpa: 8.6, skill: 81, stage: 'OA',        result: 'passed' },
  { id: 4, roll: 'CS21B088', name: 'Kavya Menon',     cgpa: 9.3, skill: 92, stage: 'Technical', result: 'passed' },
  { id: 5, roll: 'IT21B033', name: 'Mohammed Ali',    cgpa: 7.9, skill: 71, stage: 'OA',        result: 'pending' },
];

const STATUS_CFG = {
  open:        { color: '#22c55e', bg: 'rgba(34,197,94,0.1)', label: 'Open' },
  in_progress: { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', label: 'In Progress' },
  completed:   { color: 'var(--text-muted)', bg: 'var(--bg-tertiary)', label: 'Completed' },
  cancelled:   { color: '#ef4444', bg: 'rgba(239,68,68,0.1)', label: 'Cancelled' },
};

const RESULT_CFG = {
  passed:    { icon: '✓', color: '#22c55e' },
  failed:    { icon: '✗', color: '#ef4444' },
  scheduled: { icon: '◎', color: '#f59e0b' },
  pending:   { icon: '○', color: 'var(--text-muted)' },
};

// ─── Create Drive Modal ────────────────────────────────────────────
function CreateDriveModal({ onClose }) {
  const [form, setForm] = useState({ company: '', role: '', location: '', deadline: '', min_cgpa: 7.0, salary_ctc: '', seats: '' });
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  return (
    <div
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'var(--space-6)' }}
      onClick={onClose}
    >
      <div
        style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 'var(--border-radius-lg)', padding: 'var(--space-8)', width: '100%', maxWidth: 520 }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
          <h2 style={{ fontWeight: 700 }}>Create Placement Drive</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '1.5rem' }}>×</button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
            {[
              { label: 'Company Name', key: 'company', placeholder: 'e.g. Google' },
              { label: 'Role / Position', key: 'role', placeholder: 'e.g. SWE Intern' },
              { label: 'Location', key: 'location', placeholder: 'e.g. Bangalore' },
              { label: 'Salary (LPA)', key: 'salary_ctc', placeholder: 'e.g. 12.5' },
            ].map(f => (
              <div key={f.key} className="input-group">
                <label>{f.label}</label>
                <input className="input" placeholder={f.placeholder} value={form[f.key]} onChange={set(f.key)} />
              </div>
            ))}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--space-4)' }}>
            <div className="input-group">
              <label>Registration Deadline</label>
              <input className="input" type="date" value={form.deadline} onChange={set('deadline')} />
            </div>
            <div className="input-group">
              <label>Min CGPA</label>
              <input className="input" type="number" step="0.1" min="5" max="10" value={form.min_cgpa} onChange={set('min_cgpa')} />
            </div>
            <div className="input-group">
              <label>Total Seats</label>
              <input className="input" type="number" placeholder="e.g. 10" value={form.seats} onChange={set('seats')} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-2)' }}>
            <button className="btn btn-primary" style={{ flex: 1 }}>Create Drive</button>
            <button className="btn btn-secondary" onClick={onClose} style={{ flex: 1 }}>Cancel</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Drive Card ────────────────────────────────────────────────────
function DriveCard({ drive, onViewShortlist }) {
  const sc = STATUS_CFG[drive.status];
  const fillPct = Math.round((drive.selected / drive.total_seats) * 100);
  const regPct = Math.round((drive.shortlisted / drive.registered) * 100) || 0;

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-4)' }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 'var(--font-size-lg)' }}>{drive.company}</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)', marginTop: 2 }}>
            {drive.role} · 📍 {drive.location} · 💰 ₹{drive.salary_ctc}L
          </div>
        </div>
        <span style={{
          padding: '4px 14px', borderRadius: 999,
          fontSize: 'var(--font-size-xs)', fontWeight: 600,
          background: sc.bg, color: sc.color,
        }}>
          ● {sc.label}
        </span>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
        {[
          { label: 'Registered', value: drive.registered, color: '#6366f1' },
          { label: 'Shortlisted', value: drive.shortlisted, color: '#f59e0b' },
          { label: 'Selected', value: drive.selected, color: '#22c55e' },
          { label: 'Total Seats', value: drive.total_seats, color: 'var(--text-secondary)' },
        ].map(s => (
          <div key={s.label} style={{ textAlign: 'center', padding: 'var(--space-3)', background: 'var(--bg-tertiary)', borderRadius: 'var(--border-radius-sm)' }}>
            <div style={{ fontWeight: 700, fontSize: 'var(--font-size-lg)', color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Fill progress */}
      <div style={{ marginBottom: 'var(--space-4)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: 4 }}>
          <span>Seat fill: {drive.selected}/{drive.total_seats}</span>
          <span>{fillPct}%</span>
        </div>
        <div style={{ height: 6, background: 'var(--bg-tertiary)', borderRadius: 3, overflow: 'hidden' }}>
          <div style={{ width: `${fillPct}%`, height: '100%', background: '#22c55e', borderRadius: 3, transition: 'width 0.8s' }} />
        </div>
      </div>

      {/* Meta */}
      <div style={{ display: 'flex', gap: 'var(--space-4)', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: 'var(--space-4)' }}>
        <span>📅 Deadline: {drive.deadline}</span>
        <span>📅 Drive: {drive.drive_date}</span>
        <span>📊 Min CGPA: {drive.min_cgpa}</span>
        <span>🎓 {drive.eligible_departments.join(', ')}</span>
      </div>

      {/* Process steps */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flexWrap: 'wrap', marginBottom: 'var(--space-4)' }}>
        {drive.process.map((step, i) => (
          <span key={step} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <span style={{ padding: '2px 10px', borderRadius: 999, background: 'var(--accent-primary-subtle)', color: 'var(--accent-primary)', fontSize: 'var(--font-size-xs)', fontWeight: 500 }}>
              {i + 1}. {step}
            </span>
            {i < drive.process.length - 1 && <span style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}>→</span>}
          </span>
        ))}
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
        {drive.shortlisted > 0 && (
          <button className="btn btn-primary" style={{ height: 34, fontSize: 'var(--font-size-xs)' }} onClick={() => onViewShortlist(drive)}>
            👥 View Shortlisted ({drive.shortlisted})
          </button>
        )}
        {drive.status === 'open' && (
          <button className="btn btn-secondary" style={{ height: 34, fontSize: 'var(--font-size-xs)' }}>
            📋 View Applications
          </button>
        )}
        <button className="btn btn-ghost" style={{ height: 34, fontSize: 'var(--font-size-xs)' }}>
          ✏️ Edit
        </button>
      </div>
    </div>
  );
}

// ─── Shortlist Modal ───────────────────────────────────────────────
function ShortlistModal({ drive, onClose }) {
  if (!drive) return null;
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'var(--space-6)' }} onClick={onClose}>
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 'var(--border-radius-lg)', padding: 'var(--space-8)', width: '100%', maxWidth: 600, maxHeight: '80vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-5)' }}>
          <h2 style={{ fontWeight: 700 }}>{drive.company} — Shortlisted Students</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '1.5rem' }}>×</button>
        </div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Student</th>
                <th style={{ textAlign: 'center' }}>CGPA</th>
                <th style={{ textAlign: 'center' }}>Skill</th>
                <th>Current Stage</th>
                <th>Result</th>
              </tr>
            </thead>
            <tbody>
              {SHORTLISTED_STUDENTS.map(s => {
                const rc = RESULT_CFG[s.result];
                return (
                  <tr key={s.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{s.name}</div>
                      <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{s.roll}</div>
                    </td>
                    <td style={{ textAlign: 'center', fontWeight: 600 }}>{s.cgpa}</td>
                    <td style={{ textAlign: 'center' }}>{s.skill}</td>
                    <td style={{ fontSize: 'var(--font-size-sm)' }}>{s.stage}</td>
                    <td>
                      <span style={{ color: rc.color, fontWeight: 700 }}>{rc.icon} {s.result}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────
export default function TPODrives() {
  const [showCreate, setShowCreate] = useState(false);
  const [shortlistDrive, setShortlistDrive] = useState(null);
  const [filter, setFilter] = useState('all');

  const filtered = filter === 'all' ? MOCK_DRIVES : MOCK_DRIVES.filter(d => d.status === filter);

  return (
    <div>
      <div className="page-header">
        <h1>Placement Drives</h1>
        <p>Create and manage all placement drives for this academic year</p>
      </div>

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>

        {/* Toolbar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-3)' }}>
          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            {['all', 'open', 'in_progress', 'completed'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`btn ${filter === f ? 'btn-primary' : 'btn-secondary'}`}
                style={{ height: 34, fontSize: 'var(--font-size-xs)', textTransform: 'capitalize' }}
              >
                {f === 'all' ? 'All Drives' : f.replace('_', ' ')}
              </button>
            ))}
          </div>
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            + Create Drive
          </button>
        </div>

        {/* Summary */}
        <div style={{ display: 'flex', gap: 'var(--space-4)' }}>
          {[
            { label: 'Total Drives', value: MOCK_DRIVES.length },
            { label: 'Open', value: MOCK_DRIVES.filter(d => d.status === 'open').length },
            { label: 'In Progress', value: MOCK_DRIVES.filter(d => d.status === 'in_progress').length },
            { label: 'Completed', value: MOCK_DRIVES.filter(d => d.status === 'completed').length },
          ].map(s => (
            <div key={s.label} style={{
              flex: 1, padding: 'var(--space-4)',
              background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 'var(--border-radius)',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--accent-primary)' }}>{s.value}</div>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Drives list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {filtered.map(d => <DriveCard key={d.id} drive={d} onViewShortlist={setShortlistDrive} />)}
        </div>
      </div>

      {showCreate && <CreateDriveModal onClose={() => setShowCreate(false)} />}
      {shortlistDrive && <ShortlistModal drive={shortlistDrive} onClose={() => setShortlistDrive(null)} />}
    </div>
  );
}
