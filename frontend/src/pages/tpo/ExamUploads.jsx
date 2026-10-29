/**
 * Exam Uploads — TPO page for uploading exam/assessment sheets (PDF/Excel/CSV)
 * and viewing parsed data with dynamic columns, ranks, and statistics.
 */

import { useState, useEffect, useRef } from 'react';
import { examUploadApi } from '../../api/endpoints';

// ─── Stat Card ─────────────────────────────────────────────────────
function StatCard({ icon, label, value, color = 'var(--accent-primary)' }) {
  return (
    <div className="card" style={{
      display: 'flex', alignItems: 'center', gap: 16, padding: '18px 22px',
      borderLeft: `4px solid ${color}`,
    }}>
      <span style={{ fontSize: 28 }}>{icon}</span>
      <div>
        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>{label}</div>
        <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 800, color }}>{value}</div>
      </div>
    </div>
  );
}

// ─── Upload Modal ──────────────────────────────────────────────────
function UploadModal({ open, onClose, onSuccess }) {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [department, setDepartment] = useState('');
  const [section, setSection] = useState('');
  const [semester, setSemester] = useState('');
  const [examType, setExamType] = useState('');
  const [academicYear, setAcademicYear] = useState('');
  const [rankColumn, setRankColumn] = useState('');
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const fileRef = useRef(null);

  if (!open) return null;

  const handleUpload = async () => {
    if (!file || !title.trim()) {
      setError('Please provide a title and select a file.');
      return;
    }
    setError('');
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title.trim());
      if (description.trim()) formData.append('description', description.trim());
      if (department.trim()) formData.append('department', department.trim());
      if (section.trim()) formData.append('section', section.trim());
      if (semester) formData.append('semester', semester);
      if (examType.trim()) formData.append('exam_type', examType.trim());
      if (academicYear.trim()) formData.append('academic_year', academicYear.trim());
      if (rankColumn.trim()) formData.append('rank_column', rankColumn.trim());

      const res = await examUploadApi.upload(formData);
      onSuccess(res.data);
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const overlayStyle = {
    position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 1000,
    display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(4px)',
  };
  const modalStyle = {
    background: 'var(--bg-secondary)', borderRadius: 16, padding: 32,
    width: '90%', maxWidth: 600, maxHeight: '90vh', overflowY: 'auto',
    border: '1px solid var(--border-color)', boxShadow: '0 24px 64px rgba(0,0,0,0.4)',
  };
  const inputStyle = {
    width: '100%', padding: '10px 14px', borderRadius: 8,
    border: '1px solid var(--border-color)', background: 'var(--bg-primary)',
    color: 'var(--text-primary)', fontSize: 14, outline: 'none',
  };
  const labelStyle = { fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4, display: 'block' };

  return (
    <div style={overlayStyle} onClick={onClose}>
      <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
        <h2 style={{ margin: '0 0 20px', fontSize: 20 }}>📤 Upload Exam Sheet</h2>

        {error && (
          <div style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid #ef4444', borderRadius: 8, padding: '10px 14px', marginBottom: 16, color: '#fca5a5', fontSize: 13 }}>
            {error}
          </div>
        )}

        <div style={{ display: 'grid', gap: 14 }}>
          {/* Title */}
          <div>
            <label style={labelStyle}>Title *</label>
            <input style={inputStyle} placeholder="e.g. MST-1 Data Structures Results" value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>

          {/* File */}
          <div>
            <label style={labelStyle}>File (PDF / Excel / CSV) *</label>
            <div
              style={{
                border: '2px dashed var(--border-color)', borderRadius: 12, padding: '24px 16px',
                textAlign: 'center', cursor: 'pointer', transition: 'all 0.2s',
                background: file ? 'rgba(99,102,241,0.08)' : 'transparent',
              }}
              onClick={() => fileRef.current?.click()}
            >
              <input
                ref={fileRef} type="file" hidden
                accept=".pdf,.xlsx,.xls,.csv"
                onChange={(e) => setFile(e.target.files[0])}
              />
              {file ? (
                <div>
                  <span style={{ fontSize: 28 }}>📄</span>
                  <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4 }}>{file.name}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{(file.size / 1024).toFixed(1)} KB</div>
                </div>
              ) : (
                <div>
                  <span style={{ fontSize: 28 }}>📁</span>
                  <div style={{ fontSize: 14, color: 'var(--text-muted)', marginTop: 4 }}>Click to select a file</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Supports PDF, Excel (.xlsx/.xls), CSV</div>
                </div>
              )}
            </div>
          </div>

          {/* Grid: Dept + Section */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={labelStyle}>Department</label>
              <input style={inputStyle} placeholder="e.g. CSE" value={department} onChange={(e) => setDepartment(e.target.value)} />
            </div>
            <div>
              <label style={labelStyle}>Section</label>
              <input style={inputStyle} placeholder="e.g. A" value={section} onChange={(e) => setSection(e.target.value)} />
            </div>
          </div>

          {/* Grid: Semester + Exam Type */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={labelStyle}>Semester</label>
              <input style={inputStyle} type="number" placeholder="e.g. 4" value={semester} onChange={(e) => setSemester(e.target.value)} />
            </div>
            <div>
              <label style={labelStyle}>Exam Type</label>
              <select style={inputStyle} value={examType} onChange={(e) => setExamType(e.target.value)}>
                <option value="">Select type</option>
                <option value="MST-1">MST-1</option>
                <option value="MST-2">MST-2</option>
                <option value="End Sem">End Semester</option>
                <option value="Quiz">Quiz</option>
                <option value="Assignment">Assignment</option>
                <option value="Lab Exam">Lab Exam</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          {/* Grid: Academic Year + Rank Column */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={labelStyle}>Academic Year</label>
              <input style={inputStyle} placeholder="e.g. 2025-26" value={academicYear} onChange={(e) => setAcademicYear(e.target.value)} />
            </div>
            <div>
              <label style={labelStyle}>Rank Column (auto-detected if empty)</label>
              <input style={inputStyle} placeholder="e.g. Total Marks" value={rankColumn} onChange={(e) => setRankColumn(e.target.value)} />
            </div>
          </div>

          {/* Description */}
          <div>
            <label style={labelStyle}>Description (optional)</label>
            <textarea style={{ ...inputStyle, minHeight: 60, resize: 'vertical' }} placeholder="Notes about this upload..." value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 12, marginTop: 20, justifyContent: 'flex-end' }}>
          <button className="btn btn-secondary" onClick={onClose} disabled={uploading}>Cancel</button>
          <button className="btn btn-primary" onClick={handleUpload} disabled={uploading || !file || !title.trim()}>
            {uploading ? '⏳ Processing...' : '📤 Upload & Process'}
          </button>
        </div>
      </div>
    </div>
  );
}


// ─── Detail View Modal ─────────────────────────────────────────────
function DetailModal({ upload, onClose }) {
  const [data, setData] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortCol, setSortCol] = useState(null);
  const [sortAsc, setSortAsc] = useState(true);

  useEffect(() => {
    if (!upload) return;
    setLoading(true);
    Promise.all([
      examUploadApi.getDetail(upload.id).catch(() => ({ data: null })),
      examUploadApi.getStats(upload.id).catch(() => ({ data: null })),
    ]).then(([detailRes, statsRes]) => {
      setData(detailRes.data);
      setStats(statsRes.data);
      setLoading(false);
    });
  }, [upload]);

  if (!upload) return null;

  const overlayStyle = {
    position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 1000,
    display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(4px)',
  };
  const modalStyle = {
    background: 'var(--bg-secondary)', borderRadius: 16, padding: '24px 28px',
    width: '95%', maxWidth: 1200, maxHeight: '92vh', overflowY: 'auto',
    border: '1px solid var(--border-color)', boxShadow: '0 24px 64px rgba(0,0,0,0.4)',
  };

  if (loading) {
    return (
      <div style={overlayStyle} onClick={onClose}>
        <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
          <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>⏳ Loading data...</div>
        </div>
      </div>
    );
  }

  const columns = data?.upload?.column_headers || [];
  let results = data?.results || [];

  // Search filter
  if (searchTerm.trim()) {
    const q = searchTerm.toLowerCase();
    results = results.filter(r =>
      (r.roll_number || '').toLowerCase().includes(q) ||
      (r.student_name || '').toLowerCase().includes(q) ||
      Object.values(r.row_data || {}).some(v => String(v || '').toLowerCase().includes(q))
    );
  }

  // Sort
  if (sortCol) {
    results = [...results].sort((a, b) => {
      let va = a.row_data?.[sortCol] ?? '';
      let vb = b.row_data?.[sortCol] ?? '';
      // Try numeric sort
      const na = parseFloat(va);
      const nb = parseFloat(vb);
      if (!isNaN(na) && !isNaN(nb)) {
        return sortAsc ? na - nb : nb - na;
      }
      return sortAsc ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
    });
  }

  const rankCol = data?.upload?.rank_column;

  return (
    <div style={overlayStyle} onClick={onClose}>
      <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 20 }}>📋 {data?.upload?.title}</h2>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
              {data?.upload?.department && <span>Dept: {data.upload.department} · </span>}
              {data?.upload?.section && <span>Sec: {data.upload.section} · </span>}
              {data?.upload?.exam_type && <span>{data.upload.exam_type} · </span>}
              {data?.total} students · {columns.length} columns
              {rankCol && <span> · Ranked by: <strong>{rankCol}</strong></span>}
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: 22, cursor: 'pointer' }}>✕</button>
        </div>

        {/* Stats */}
        {stats && stats.total_students && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10, marginBottom: 16 }}>
            <StatCard icon="👥" label="Total" value={stats.total_students} color="#6366f1" />
            <StatCard icon="🏆" label="Highest" value={stats.highest} color="#10b981" />
            <StatCard icon="📉" label="Lowest" value={stats.lowest} color="#ef4444" />
            <StatCard icon="📊" label="Average" value={stats.average} color="#f59e0b" />
            <StatCard icon="✅" label="Pass" value={stats.pass_count} color="#10b981" />
            <StatCard icon="❌" label="Fail" value={stats.fail_count} color="#ef4444" />
          </div>
        )}

        {/* Search */}
        <div style={{ marginBottom: 12 }}>
          <input
            style={{
              width: '100%', padding: '10px 14px', borderRadius: 8,
              border: '1px solid var(--border-color)', background: 'var(--bg-primary)',
              color: 'var(--text-primary)', fontSize: 14, outline: 'none',
            }}
            placeholder="🔍 Search by name, roll number, or any value..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* Table */}
        <div style={{ overflowX: 'auto', borderRadius: 8, border: '1px solid var(--border-color)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: 'rgba(99,102,241,0.1)' }}>
                <th style={thStyle}>Rank</th>
                {columns.map(col => (
                  <th
                    key={col}
                    style={{ ...thStyle, cursor: 'pointer', userSelect: 'none', background: col === rankCol ? 'rgba(16,185,129,0.15)' : undefined }}
                    onClick={() => {
                      if (sortCol === col) setSortAsc(!sortAsc);
                      else { setSortCol(col); setSortAsc(true); }
                    }}
                  >
                    {col}
                    {sortCol === col && (sortAsc ? ' ↑' : ' ↓')}
                    {col === rankCol && ' 🏅'}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => (
                <tr key={r.id} style={{ background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)', borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ ...tdStyle, fontWeight: 700, color: r.rank <= 3 ? '#10b981' : 'var(--text-secondary)', textAlign: 'center' }}>
                    {r.rank ? (r.rank <= 3 ? ['🥇', '🥈', '🥉'][r.rank - 1] : `#${r.rank}`) : '—'}
                  </td>
                  {columns.map(col => (
                    <td key={col} style={{ ...tdStyle, background: col === rankCol ? 'rgba(16,185,129,0.05)' : undefined }}>
                      {r.row_data?.[col] != null ? String(r.row_data[col]) : '—'}
                    </td>
                  ))}
                </tr>
              ))}
              {results.length === 0 && (
                <tr>
                  <td colSpan={columns.length + 1} style={{ ...tdStyle, textAlign: 'center', color: 'var(--text-muted)', padding: 30 }}>
                    No results found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div style={{ textAlign: 'right', marginTop: 12, fontSize: 12, color: 'var(--text-muted)' }}>
          Showing {results.length} of {data?.total || 0} records
        </div>
      </div>
    </div>
  );
}

const thStyle = {
  padding: '10px 12px', textAlign: 'left', fontWeight: 700, fontSize: 12,
  color: 'var(--text-secondary)', borderBottom: '2px solid var(--border-color)',
  whiteSpace: 'nowrap',
};
const tdStyle = {
  padding: '8px 12px', whiteSpace: 'nowrap', color: 'var(--text-primary)',
};


// ─── Main Page ─────────────────────────────────────────────────────
export default function ExamUploads() {
  const [uploads, setUploads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [selectedUpload, setSelectedUpload] = useState(null);
  const [filterDept, setFilterDept] = useState('');
  const [filterSection, setFilterSection] = useState('');

  const fetchUploads = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filterDept) params.department = filterDept;
      if (filterSection) params.section = filterSection;
      const res = await examUploadApi.list(params);
      setUploads(res.data || []);
    } catch (err) {
      console.error('Failed to fetch uploads:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUploads(); }, [filterDept, filterSection]);

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this upload and all its results?')) return;
    try {
      await examUploadApi.delete(id);
      setUploads(prev => prev.filter(u => u.id !== id));
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete.');
    }
  };

  const examTypeColors = {
    'MST-1': '#6366f1', 'MST-2': '#8b5cf6', 'End Sem': '#ef4444',
    'Quiz': '#f59e0b', 'Assignment': '#10b981', 'Lab Exam': '#06b6d4', 'Other': '#64748b',
  };

  return (
    <div style={{ padding: '28px 32px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 'var(--font-size-2xl)' }}>📊 Exam Uploads</h1>
          <p style={{ margin: '4px 0 0', color: 'var(--text-muted)', fontSize: 14 }}>
            Upload exam/assessment sheets and view parsed results with rankings
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowUpload(true)} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span>📤</span> Upload Sheet
        </button>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <input
          style={{
            padding: '8px 14px', borderRadius: 8, border: '1px solid var(--border-color)',
            background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: 13, width: 180,
          }}
          placeholder="Filter by department..."
          value={filterDept}
          onChange={(e) => setFilterDept(e.target.value)}
        />
        <input
          style={{
            padding: '8px 14px', borderRadius: 8, border: '1px solid var(--border-color)',
            background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: 13, width: 140,
          }}
          placeholder="Filter by section..."
          value={filterSection}
          onChange={(e) => setFilterSection(e.target.value)}
        />
      </div>

      {/* Upload List */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-muted)' }}>⏳ Loading uploads...</div>
      ) : uploads.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 60 }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>📂</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-secondary)' }}>No uploads yet</div>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>Upload a PDF or Excel sheet to get started</div>
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => setShowUpload(true)}>
            📤 Upload First Sheet
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: 12 }}>
          {uploads.map(u => (
            <div
              key={u.id}
              className="card"
              style={{ padding: '16px 20px', cursor: 'pointer', transition: 'all 0.2s', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
              onClick={() => setSelectedUpload(u)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 16, flex: 1 }}>
                <span style={{ fontSize: 32 }}>
                  {u.file_type === 'pdf' ? '📕' : u.file_type === 'csv' ? '📗' : '📘'}
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: 15 }}>{u.title}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    <span>{u.original_filename}</span>
                    {u.department && <span>· Dept: {u.department}</span>}
                    {u.section && <span>· Sec: {u.section}</span>}
                    {u.semester && <span>· Sem {u.semester}</span>}
                    <span>· {u.total_rows} students</span>
                    <span>· {u.total_columns} columns</span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  {u.exam_type && (
                    <span style={{
                      padding: '4px 10px', borderRadius: 12, fontSize: 11, fontWeight: 700,
                      background: `${examTypeColors[u.exam_type] || '#64748b'}20`,
                      color: examTypeColors[u.exam_type] || '#64748b',
                    }}>
                      {u.exam_type}
                    </span>
                  )}
                  <span style={{
                    padding: '4px 10px', borderRadius: 12, fontSize: 11, fontWeight: 700,
                    background: u.status === 'completed' ? 'rgba(16,185,129,0.15)' : u.status === 'failed' ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)',
                    color: u.status === 'completed' ? '#10b981' : u.status === 'failed' ? '#ef4444' : '#f59e0b',
                  }}>
                    {u.status === 'completed' ? '✅ Processed' : u.status === 'failed' ? '❌ Failed' : '⏳ Processing'}
                  </span>
                </div>
              </div>
              <button
                className="btn btn-secondary"
                style={{ marginLeft: 12, fontSize: 12, padding: '6px 12px' }}
                onClick={(e) => { e.stopPropagation(); handleDelete(u.id); }}
              >
                🗑️
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Modals */}
      <UploadModal open={showUpload} onClose={() => setShowUpload(false)} onSuccess={() => fetchUploads()} />
      <DetailModal upload={selectedUpload} onClose={() => setSelectedUpload(null)} />
    </div>
  );
}
