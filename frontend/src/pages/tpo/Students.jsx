/**
 * TPO Students — searchable, filterable student roster with expandable details.
 */

import { useState } from 'react';

// ─── Mock Data ────────────────────────────────────────────────────
const MOCK_STUDENTS = [
  { id: 1, roll: 'CS21B001', name: 'Priya Agarwal',   dept: 'CS',  year: 4, cgpa: 9.1, skill_score: 88, status: 'selected',    company: 'Google',     package: 48.5, backlogs: 0 },
  { id: 2, roll: 'CS21B042', name: 'Arjun Sharma',    dept: 'CS',  year: 4, cgpa: 8.1, skill_score: 73, status: 'shortlisted',  company: 'Amazon',     package: null, backlogs: 0 },
  { id: 3, roll: 'IT21B015', name: 'Sneha Reddy',     dept: 'IT',  year: 4, cgpa: 8.6, skill_score: 81, status: 'applied',     company: null,         package: null, backlogs: 0 },
  { id: 4, roll: 'CS21B007', name: 'Rahul Nair',      dept: 'CS',  year: 4, cgpa: 7.4, skill_score: 62, status: 'unregistered',company: null,         package: null, backlogs: 1 },
  { id: 5, roll: 'ECE21B022', name: 'Divya Iyer',    dept: 'ECE', year: 4, cgpa: 8.0, skill_score: 68, status: 'selected',    company: 'Infosys',    package: 3.6,  backlogs: 0 },
  { id: 6, roll: 'IT21B033', name: 'Mohammed Ali',   dept: 'IT',  year: 4, cgpa: 7.9, skill_score: 71, status: 'applied',     company: null,         package: null, backlogs: 0 },
  { id: 7, roll: 'CS21B088', name: 'Kavya Menon',    dept: 'CS',  year: 4, cgpa: 9.3, skill_score: 92, status: 'selected',    company: 'Microsoft',  package: 38.0, backlogs: 0 },
  { id: 8, roll: 'ME21B011', name: 'Aditya Verma',   dept: 'ME',  year: 4, cgpa: 7.0, skill_score: 55, status: 'unregistered',company: null,         package: null, backlogs: 2 },
  { id: 9, roll: 'CS21B054', name: 'Pooja Gupta',    dept: 'CS',  year: 4, cgpa: 8.4, skill_score: 79, status: 'shortlisted', company: 'Deloitte',   package: null, backlogs: 0 },
  { id: 10, roll: 'IT21B061', name: 'Karan Joshi',   dept: 'IT',  year: 4, cgpa: 7.6, skill_score: 67, status: 'applied',     company: null,         package: null, backlogs: 1 },
  { id: 11, roll: 'ECE21B045', name: 'Shreya Das',   dept: 'ECE', year: 4, cgpa: 8.2, skill_score: 75, status: 'selected',    company: 'Wipro',      package: 3.5,  backlogs: 0 },
  { id: 12, roll: 'CS21B019', name: 'Vishal Kumar',  dept: 'CS',  year: 4, cgpa: 7.8, skill_score: 70, status: 'applied',     company: null,         package: null, backlogs: 0 },
];

const STATUS_CFG = {
  selected:    { color: '#22c55e', bg: 'rgba(34,197,94,0.1)',  label: '✅ Selected' },
  shortlisted: { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', label: '⭐ Shortlisted' },
  applied:     { color: '#6366f1', bg: 'rgba(99,102,241,0.1)', label: '📋 Applied' },
  unregistered:{ color: 'var(--text-muted)', bg: 'var(--bg-tertiary)', label: '○ Unregistered' },
};

const DEPTS = ['All', 'CS', 'IT', 'ECE', 'ME', 'EEE'];
const STATUSES = ['All', 'selected', 'shortlisted', 'applied', 'unregistered'];

export default function TPOStudents() {
  const [search, setSearch] = useState('');
  const [dept, setDept] = useState('All');
  const [status, setStatus] = useState('All');
  const [minCGPA, setMinCGPA] = useState(0);
  const [expanded, setExpanded] = useState(null);
  const [sortBy, setSortBy] = useState('name');
  const [sortDir, setSortDir] = useState(1);

  const toggleSort = (col) => {
    if (sortBy === col) setSortDir(d => -d);
    else { setSortBy(col); setSortDir(1); }
  };

  const filtered = MOCK_STUDENTS
    .filter(s =>
      (dept === 'All' || s.dept === dept) &&
      (status === 'All' || s.status === status) &&
      s.cgpa >= minCGPA &&
      (s.name.toLowerCase().includes(search.toLowerCase()) || s.roll.toLowerCase().includes(search.toLowerCase()))
    )
    .sort((a, b) => {
      const v = sortBy === 'name' ? a.name.localeCompare(b.name)
               : sortBy === 'cgpa' ? a.cgpa - b.cgpa
               : sortBy === 'skill' ? a.skill_score - b.skill_score
               : 0;
      return v * sortDir;
    });

  const totalPlaced = filtered.filter(s => s.status === 'selected').length;

  return (
    <div>
      <div className="page-header">
        <h1>Students</h1>
        <p>Monitor placement status and skill readiness for all registered students</p>
      </div>

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>

        {/* Summary */}
        <div style={{ display: 'flex', gap: 'var(--space-4)' }}>
          {[
            { label: 'Showing', value: filtered.length, color: 'var(--text-primary)' },
            { label: 'Placed', value: totalPlaced, color: '#22c55e' },
            { label: 'Shortlisted', value: filtered.filter(s => s.status === 'shortlisted').length, color: '#f59e0b' },
            { label: 'Unregistered', value: filtered.filter(s => s.status === 'unregistered').length, color: 'var(--text-muted)' },
          ].map(s => (
            <div key={s.label} style={{
              flex: 1, padding: 'var(--space-4)',
              background: 'var(--bg-card)', border: '1px solid var(--border-color)',
              borderRadius: 'var(--border-radius)', textAlign: 'center',
            }}>
              <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
          <input
            className="input"
            placeholder="🔍 Search name or roll no..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ flex: 1, minWidth: 200 }}
          />
          <select className="input" value={dept} onChange={e => setDept(e.target.value)} style={{ width: 120 }}>
            {DEPTS.map(d => <option key={d}>{d}</option>)}
          </select>
          <select className="input" value={status} onChange={e => setStatus(e.target.value)} style={{ width: 160 }}>
            {STATUSES.map(s => <option key={s} value={s}>{s === 'All' ? 'All statuses' : STATUS_CFG[s]?.label.replace(/[✅⭐📋○] /, '') || s}</option>)}
          </select>
          <select className="input" value={minCGPA} onChange={e => setMinCGPA(+e.target.value)} style={{ width: 150 }}>
            <option value={0}>Any CGPA</option>
            <option value={7.0}>≥ 7.0</option>
            <option value={7.5}>≥ 7.5</option>
            <option value={8.0}>≥ 8.0</option>
          </select>
        </div>

        {/* Table */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
            <table>
              <thead>
                <tr>
                  <th onClick={() => toggleSort('name')} style={{ cursor: 'pointer', userSelect: 'none' }}>
                    Student {sortBy === 'name' ? (sortDir > 0 ? '↑' : '↓') : '↕'}
                  </th>
                  <th>Dept</th>
                  <th onClick={() => toggleSort('cgpa')} style={{ cursor: 'pointer', userSelect: 'none', textAlign: 'center' }}>
                    CGPA {sortBy === 'cgpa' ? (sortDir > 0 ? '↑' : '↓') : '↕'}
                  </th>
                  <th onClick={() => toggleSort('skill')} style={{ cursor: 'pointer', userSelect: 'none', textAlign: 'center' }}>
                    Skill Score {sortBy === 'skill' ? (sortDir > 0 ? '↑' : '↓') : '↕'}
                  </th>
                  <th>Status</th>
                  <th>Company / Package</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(s => {
                  const sc = STATUS_CFG[s.status] || STATUS_CFG.unregistered;
                  const isExp = expanded === s.id;
                  return (
                    <>
                      <tr key={s.id} style={{ background: isExp ? 'var(--accent-primary-subtle)' : undefined }}>
                        <td>
                          <div style={{ fontWeight: 600 }}>{s.name}</div>
                          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{s.roll}</div>
                        </td>
                        <td>
                          <span className="badge badge-primary">{s.dept}</span>
                        </td>
                        <td style={{ textAlign: 'center', fontWeight: 600, color: s.cgpa >= 8.0 ? '#22c55e' : s.cgpa >= 7.0 ? '#f59e0b' : '#ef4444' }}>
                          {s.cgpa}
                        </td>
                        <td style={{ textAlign: 'center' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', justifyContent: 'center' }}>
                            <div style={{ width: 50, height: 5, background: 'var(--bg-tertiary)', borderRadius: 2, overflow: 'hidden' }}>
                              <div style={{ width: `${s.skill_score}%`, height: '100%', background: '#6366f1', borderRadius: 2 }} />
                            </div>
                            <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>{s.skill_score}</span>
                          </div>
                        </td>
                        <td>
                          <span style={{
                            padding: '3px 10px', borderRadius: 999,
                            fontSize: 'var(--font-size-xs)', fontWeight: 600,
                            background: sc.bg, color: sc.color,
                          }}>{sc.label}</span>
                        </td>
                        <td>
                          {s.company ? (
                            <div>
                              <div style={{ fontWeight: 500, fontSize: 'var(--font-size-sm)' }}>{s.company}</div>
                              {s.package && <div style={{ fontSize: 'var(--font-size-xs)', color: '#22c55e' }}>₹{s.package}L</div>}
                            </div>
                          ) : (
                            <span style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>—</span>
                          )}
                        </td>
                        <td>
                          <button
                            className="btn btn-ghost"
                            style={{ height: 28, fontSize: 'var(--font-size-xs)' }}
                            onClick={() => setExpanded(isExp ? null : s.id)}
                          >
                            {isExp ? '▲ Less' : '▼ More'}
                          </button>
                        </td>
                      </tr>
                      {isExp && (
                        <tr key={`${s.id}-exp`} style={{ background: 'var(--accent-primary-subtle)' }}>
                          <td colSpan={7} style={{ padding: 'var(--space-4) var(--space-6)' }}>
                            <div style={{ display: 'flex', gap: 'var(--space-8)', flexWrap: 'wrap', fontSize: 'var(--font-size-sm)' }}>
                              <div>
                                <div style={{ fontWeight: 600, marginBottom: 'var(--space-2)', color: 'var(--text-secondary)' }}>Profile</div>
                                <div style={{ color: 'var(--text-muted)' }}>Year {s.year} · {s.backlogs > 0 ? `${s.backlogs} backlog(s)` : 'No backlogs'}</div>
                                <div style={{ color: 'var(--text-muted)' }}>CGPA: {s.cgpa} · Skill Score: {s.skill_score}/100</div>
                              </div>
                              <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
                                <button className="btn btn-primary" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>View Full Profile</button>
                                <button className="btn btn-secondary" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>View Skill Gap</button>
                                <button className="btn btn-secondary" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>Sync UMS</button>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  );
                })}
              </tbody>
            </table>
          </div>
          {filtered.length === 0 && (
            <div style={{ textAlign: 'center', padding: 'var(--space-10)', color: 'var(--text-muted)' }}>
              No students match the current filters.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
