/**
 * TPO Students — searchable, filterable student roster with live data,
 * pagination, status badges, and expandable profile & UMS sync actions.
 */

import { useState, useEffect, useCallback, Fragment } from 'react';
import { tpoApi } from '../../api/endpoints';


const STATUS_CFG = {
  selected:    { color: '#22c55e', bg: 'rgba(34,197,94,0.1)',  label: '✅ Selected' },
  shortlisted: { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', label: '⭐ Shortlisted' },
  applied:     { color: '#6366f1', bg: 'rgba(99,102,241,0.1)', label: '📋 Applied' },
  in_progress: { color: '#06b6d4', bg: 'rgba(6,182,212,0.1)', label: '⏳ In Progress' },
  unregistered:{ color: 'var(--text-muted)', bg: 'var(--bg-tertiary)', label: '○ Unregistered' },
};

const DEPTS = ['All', 'CS', 'IT', 'ECE', 'ME', 'EEE'];
const STATUSES = ['All', 'selected', 'shortlisted', 'applied', 'in_progress', 'unregistered'];

export default function TPOStudents() {
  const [students, setStudents] = useState([]);
  const [totalStudents, setTotalStudents] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [perPage] = useState(50);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [search, setSearch] = useState('');
  const [dept, setDept] = useState('All');
  const [status, setStatus] = useState('All');
  const [minCGPA, setMinCGPA] = useState(0);
  const [expanded, setExpanded] = useState(null);
  const [sortBy, setSortBy] = useState('name');
  const [sortDir, setSortDir] = useState(1);

  const [syncingId, setSyncingId] = useState(null);
  const [selectedStudent, setSelectedStudent] = useState(null);

  const fetchStudents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await tpoApi.getStudents({
        department_code: dept !== 'All' ? dept : undefined,
        min_cgpa: minCGPA > 0 ? minCGPA : undefined,
        status: status !== 'All' ? status : undefined,
        page,
        per_page: perPage,
      });

      const list = res.data?.data || res.data || [];
      const meta = res.data?.meta || {};
      setStudents(list);
      setTotalStudents(meta.total ?? list.length);
      setTotalPages(meta.total_pages ?? Math.max(1, Math.ceil((meta.total ?? list.length) / perPage)));
    } catch (err) {
      console.error('Failed to load students:', err);
      setError('Failed to load student roster from database.');
    } finally {
      setLoading(false);
    }
  }, [dept, minCGPA, status, page, perPage]);

  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  const handleSyncUMS = async (student) => {
    try {
      setSyncingId(student.id);
      await tpoApi.syncUMS(student.roll_number);
      alert(`UMS sync completed successfully for ${student.roll_number} (${student.first_name} ${student.last_name})`);
      fetchStudents();
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Unknown error occurred during UMS sync';
      alert(`UMS sync failed: ${msg}`);
    } finally {
      setSyncingId(null);
    }
  };

  const toggleSort = (col) => {
    if (sortBy === col) setSortDir(d => -d);
    else { setSortBy(col); setSortDir(1); }
  };

  const filtered = students
    .filter(s => {
      const fullName = `${s.first_name || ''} ${s.last_name || ''}`.toLowerCase();
      const roll = (s.roll_number || '').toLowerCase();
      const q = search.toLowerCase().trim();
      if (!q) return true;
      return fullName.includes(q) || roll.includes(q);
    })
    .sort((a, b) => {
      const nameA = `${a.first_name || ''} ${a.last_name || ''}`;
      const nameB = `${b.first_name || ''} ${b.last_name || ''}`;
      const v = sortBy === 'name' ? nameA.localeCompare(nameB)
               : sortBy === 'cgpa' ? ((a.cgpa || 0) - (b.cgpa || 0))
               : sortBy === 'skill' ? ((a.skill_score || 0) - (b.skill_score || 0))
               : 0;
      return v * sortDir;
    });

  const totalPlaced = filtered.filter(s => s.placement_status === 'selected').length;
  const totalShortlisted = filtered.filter(s => s.placement_status === 'shortlisted').length;
  const totalUnregistered = filtered.filter(s => s.placement_status === 'unregistered').length;

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Students</h1>
          <p>Monitor placement status and skill readiness for all registered students</p>
        </div>
        <button
          className="btn btn-secondary"
          onClick={fetchStudents}
          disabled={loading}
          style={{ fontSize: 'var(--font-size-xs)' }}
        >
          {loading ? 'Refreshing...' : '🔄 Refresh Roster'}
        </button>
      </div>

      {error && (
        <div style={{
          padding: 'var(--space-4)',
          marginBottom: 'var(--space-6)',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid #ef4444',
          borderRadius: 'var(--border-radius)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          color: '#ef4444'
        }}>
          <span>{error}</span>
          <button className="btn btn-primary" onClick={fetchStudents} style={{ height: 28, fontSize: 'var(--font-size-xs)' }}>
            Retry
          </button>
        </div>
      )}

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>

        {/* Summary metrics */}
        <div style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap' }}>
          {[
            { label: 'Showing', value: filtered.length, color: 'var(--text-primary)' },
            { label: 'Placed', value: totalPlaced, color: '#22c55e' },
            { label: 'Shortlisted', value: totalShortlisted, color: '#f59e0b' },
            { label: 'Unregistered', value: totalUnregistered, color: 'var(--text-muted)' },
            { label: 'Total in DB', value: totalStudents, color: 'var(--accent-primary)' },
          ].map(s => (
            <div key={s.label} style={{
              flex: 1, minWidth: 120, padding: 'var(--space-4)',
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
          <select className="input" value={dept} onChange={e => { setDept(e.target.value); setPage(1); }} style={{ width: 120 }}>
            {DEPTS.map(d => <option key={d} value={d}>{d === 'All' ? 'All Depts' : d}</option>)}
          </select>
          <select className="input" value={status} onChange={e => { setStatus(e.target.value); setPage(1); }} style={{ width: 160 }}>
            {STATUSES.map(s => (
              <option key={s} value={s}>
                {s === 'All' ? 'All statuses' : STATUS_CFG[s]?.label.replace(/[✅⭐📋⏳○] /u, '') || s}

              </option>
            ))}
          </select>
          <select className="input" value={minCGPA} onChange={e => { setMinCGPA(+e.target.value); setPage(1); }} style={{ width: 150 }}>
            <option value={0}>Any CGPA</option>
            <option value={7.0}>≥ 7.0</option>
            <option value={7.5}>≥ 7.5</option>
            <option value={8.0}>≥ 8.0</option>
          </select>
        </div>

        {/* Table */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: 'var(--space-12)', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '1.25rem', marginBottom: 'var(--space-2)' }}>⏳ Loading students from database...</div>
            </div>
          ) : (
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
                    const studentStatus = s.placement_status || 'unregistered';
                    const sc = STATUS_CFG[studentStatus] || STATUS_CFG.unregistered;
                    const isExp = expanded === s.id;
                    const studentName = `${s.first_name || ''} ${s.last_name || ''}`.trim() || 'Student';
                    const cgpaValue = s.cgpa != null ? Number(s.cgpa).toFixed(1) : 'N/A';
                    const skillScore = s.skill_score ?? 70;
                    const studentYear = s.year || (s.current_semester ? Math.ceil(s.current_semester / 2) : 4);

                    return (
                      <Fragment key={s.id}>
                        <tr style={{ background: isExp ? 'var(--accent-primary-subtle)' : undefined }}>

                          <td>
                            <div style={{ fontWeight: 600 }}>{studentName}</div>
                            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                              {s.roll_number}
                            </div>
                          </td>
                          <td>
                            <span className="badge badge-primary">{s.department_code}</span>
                          </td>
                          <td style={{
                            textAlign: 'center', fontWeight: 600,
                            color: s.cgpa >= 8.0 ? '#22c55e' : s.cgpa >= 7.0 ? '#f59e0b' : '#ef4444'
                          }}>
                            {cgpaValue}
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', justifyContent: 'center' }}>
                              <div style={{ width: 50, height: 5, background: 'var(--bg-tertiary)', borderRadius: 2, overflow: 'hidden' }}>
                                <div style={{ width: `${Math.min(100, skillScore)}%`, height: '100%', background: '#6366f1', borderRadius: 2 }} />
                              </div>
                              <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>{skillScore}</span>
                            </div>
                          </td>
                          <td>
                            <span style={{
                              padding: '3px 10px', borderRadius: 999,
                              fontSize: 'var(--font-size-xs)', fontWeight: 600,
                              background: sc.bg, color: sc.color,
                            }}>
                              {sc.label}
                            </span>
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
                          <tr style={{ background: 'var(--accent-primary-subtle)' }}>
                            <td colSpan={7} style={{ padding: 'var(--space-4) var(--space-6)' }}>
                              <div style={{ display: 'flex', gap: 'var(--space-8)', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', fontSize: 'var(--font-size-sm)' }}>
                                <div>
                                  <div style={{ fontWeight: 600, marginBottom: 'var(--space-1)', color: 'var(--text-secondary)' }}>
                                    {s.department_name || s.department_code} · Year {studentYear} (Sem {s.current_semester || 8})
                                  </div>
                                  <div style={{ color: 'var(--text-muted)' }}>
                                    Email: {s.email} · {s.backlogs > 0 ? `${s.backlogs} backlog(s)` : 'No backlogs'} · Resume: {s.resume_parsed ? 'Parsed ✅' : 'Pending'}
                                  </div>
                                </div>
                                <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
                                  <button
                                    className="btn btn-primary"
                                    style={{ height: 32, fontSize: 'var(--font-size-xs)' }}
                                    onClick={() => setSelectedStudent(s)}
                                  >
                                    View Full Profile
                                  </button>
                                  <button
                                    className="btn btn-secondary"
                                    style={{ height: 32, fontSize: 'var(--font-size-xs)' }}
                                    onClick={() => handleSyncUMS(s)}
                                    disabled={syncingId === s.id}
                                  >
                                    {syncingId === s.id ? 'Syncing...' : 'Sync UMS'}
                                  </button>
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    );

                  })}
                </tbody>
              </table>
            </div>
          )}

          {!loading && filtered.length === 0 && (
            <div style={{ textAlign: 'center', padding: 'var(--space-10)', color: 'var(--text-muted)' }}>
              No students match the current filters or search query.
            </div>
          )}
        </div>

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'var(--space-2)' }}>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)' }}>
              Page {page} of {totalPages} ({totalStudents} total students)
            </div>
            <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
              <button
                className="btn btn-secondary"
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page <= 1 || loading}
                style={{ height: 32, fontSize: 'var(--font-size-xs)' }}
              >
                Previous
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages || loading}
                style={{ height: 32, fontSize: 'var(--font-size-xs)' }}
              >
                Next
              </button>
            </div>
          </div>
        )}

      </div>

      {/* Modal: Full Profile View */}
      {selectedStudent && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0, 0, 0, 0.6)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }}>
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border-color)',
            borderRadius: 'var(--border-radius)', maxWidth: 500, width: '90%',
            padding: 'var(--space-6)', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ fontSize: 'var(--font-size-lg)', margin: 0 }}>
                {selectedStudent.first_name} {selectedStudent.last_name}
              </h2>
              <button
                className="btn btn-ghost"
                onClick={() => setSelectedStudent(null)}
                style={{ padding: '4px 8px', fontSize: 'var(--font-size-sm)' }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', fontSize: 'var(--font-size-sm)' }}>
              <div><strong>Roll Number:</strong> {selectedStudent.roll_number}</div>
              <div><strong>Department:</strong> {selectedStudent.department_name} ({selectedStudent.department_code})</div>
              <div><strong>Email:</strong> {selectedStudent.email}</div>
              <div><strong>Current Semester:</strong> {selectedStudent.current_semester}</div>
              <div><strong>CGPA:</strong> {selectedStudent.cgpa ?? 'N/A'}</div>
              <div><strong>Skill Score:</strong> {selectedStudent.skill_score ?? 'N/A'}/100</div>
              <div><strong>Backlogs:</strong> {selectedStudent.backlogs ?? 0}</div>
              <div><strong>Placement Status:</strong> {STATUS_CFG[selectedStudent.placement_status]?.label || selectedStudent.placement_status}</div>
              {selectedStudent.company && (
                <div><strong>Placed Company:</strong> {selectedStudent.company} (₹{selectedStudent.package}L)</div>
              )}
              <div><strong>Resume Status:</strong> {selectedStudent.resume_parsed ? 'Parsed' : 'Pending upload/parse'}</div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-3)', marginTop: 'var(--space-4)' }}>
              <button
                className="btn btn-secondary"
                onClick={() => handleSyncUMS(selectedStudent)}
                disabled={syncingId === selectedStudent.id}
              >
                {syncingId === selectedStudent.id ? 'Syncing...' : 'Sync with UMS'}
              </button>
              <button className="btn btn-primary" onClick={() => setSelectedStudent(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
