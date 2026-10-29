/**
 * Section Exam Results — Faculty views exam results for their section/department.
 * Can browse all uploaded sheets and filter by section.
 */

import { useState, useEffect } from 'react';
import { examUploadApi } from '../../api/endpoints';

export default function SectionExamResults() {
  const [uploads, setUploads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUpload, setSelectedUpload] = useState(null);
  const [sectionFilter, setSectionFilter] = useState('');
  const [results, setResults] = useState([]);
  const [loadingResults, setLoadingResults] = useState(false);
  const [stats, setStats] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortCol, setSortCol] = useState(null);
  const [sortAsc, setSortAsc] = useState(true);

  useEffect(() => {
    examUploadApi.list({})
      .then(res => setUploads(res.data || []))
      .catch(() => setUploads([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedUpload) return;
    setLoadingResults(true);
    const params = {};
    if (sectionFilter.trim()) params.section = sectionFilter.trim();

    Promise.all([
      examUploadApi.getSectionResults(selectedUpload.id, params).catch(() => ({ data: [] })),
      examUploadApi.getStats(selectedUpload.id).catch(() => ({ data: null })),
    ]).then(([resResults, resStats]) => {
      setResults(resResults.data || []);
      setStats(resStats.data);
      setLoadingResults(false);
    });
  }, [selectedUpload, sectionFilter]);

  const columns = selectedUpload?.column_headers || [];

  // Search filter
  let filteredResults = results;
  if (searchTerm.trim()) {
    const q = searchTerm.toLowerCase();
    filteredResults = results.filter(r =>
      (r.roll_number || '').toLowerCase().includes(q) ||
      (r.student_name || '').toLowerCase().includes(q)
    );
  }

  // Sort
  if (sortCol) {
    filteredResults = [...filteredResults].sort((a, b) => {
      let va = a.row_data?.[sortCol] ?? '';
      let vb = b.row_data?.[sortCol] ?? '';
      const na = parseFloat(va);
      const nb = parseFloat(vb);
      if (!isNaN(na) && !isNaN(nb)) return sortAsc ? na - nb : nb - na;
      return sortAsc ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
    });
  }

  const thStyle = {
    padding: '10px 12px', textAlign: 'left', fontWeight: 700, fontSize: 12,
    color: 'var(--text-secondary)', borderBottom: '2px solid var(--border-color)',
    whiteSpace: 'nowrap',
  };
  const tdStyle = {
    padding: '8px 12px', whiteSpace: 'nowrap', color: 'var(--text-primary)',
  };

  return (
    <div style={{ padding: '28px 32px' }}>
      <h1 style={{ margin: '0 0 4px', fontSize: 'var(--font-size-2xl)' }}>📊 Section Exam Results</h1>
      <p style={{ margin: '0 0 24px', color: 'var(--text-muted)', fontSize: 14 }}>
        View exam results for your section students
      </p>

      <div style={{ display: 'flex', gap: 20 }}>
        {/* Left: Upload List */}
        <div style={{ width: 320, flexShrink: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 10 }}>Exam Sheets</div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: 30, color: 'var(--text-muted)' }}>Loading...</div>
          ) : uploads.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: 30 }}>
              <div style={{ fontSize: 32, marginBottom: 8 }}>📂</div>
              <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>No exam sheets uploaded yet</div>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: 8 }}>
              {uploads.map(u => (
                <div
                  key={u.id}
                  className="card"
                  style={{
                    padding: '12px 16px', cursor: 'pointer', transition: 'all 0.2s',
                    border: selectedUpload?.id === u.id ? '1px solid #6366f1' : '1px solid var(--border-color)',
                    background: selectedUpload?.id === u.id ? 'rgba(99,102,241,0.08)' : undefined,
                  }}
                  onClick={() => { setSelectedUpload(u); setSearchTerm(''); setSortCol(null); }}
                >
                  <div style={{ fontWeight: 600, fontSize: 13 }}>{u.title}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {u.exam_type && <span style={{
                      padding: '1px 6px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                      background: 'rgba(99,102,241,0.15)', color: '#818cf8',
                    }}>{u.exam_type}</span>}
                    {u.department && <span>{u.department}</span>}
                    <span>· {u.total_rows} students</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: Results */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {!selectedUpload ? (
            <div className="card" style={{ textAlign: 'center', padding: 60 }}>
              <div style={{ fontSize: 48, marginBottom: 12 }}>👈</div>
              <div style={{ fontSize: 14, color: 'var(--text-muted)' }}>Select an exam sheet from the left to view results</div>
            </div>
          ) : (
            <>
              {/* Header + Section Filter */}
              <div style={{ display: 'flex', gap: 12, marginBottom: 14, alignItems: 'center' }}>
                <input
                  style={{
                    flex: 1, padding: '8px 14px', borderRadius: 8,
                    border: '1px solid var(--border-color)', background: 'var(--bg-secondary)',
                    color: 'var(--text-primary)', fontSize: 13,
                  }}
                  placeholder="🔍 Search by name or roll number..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                <input
                  style={{
                    width: 140, padding: '8px 14px', borderRadius: 8,
                    border: '1px solid var(--border-color)', background: 'var(--bg-secondary)',
                    color: 'var(--text-primary)', fontSize: 13,
                  }}
                  placeholder="Section (e.g. A)"
                  value={sectionFilter}
                  onChange={(e) => setSectionFilter(e.target.value)}
                />
              </div>

              {/* Stats Row */}
              {stats && stats.total_students && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: 8, marginBottom: 14 }}>
                  {[
                    { icon: '👥', label: 'Total', value: filteredResults.length, color: '#6366f1' },
                    { icon: '🏆', label: 'Highest', value: stats.highest, color: '#10b981' },
                    { icon: '📉', label: 'Lowest', value: stats.lowest, color: '#ef4444' },
                    { icon: '📊', label: 'Average', value: stats.average, color: '#f59e0b' },
                  ].map(s => (
                    <div key={s.label} className="card" style={{ padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 10, borderLeft: `3px solid ${s.color}` }}>
                      <span style={{ fontSize: 20 }}>{s.icon}</span>
                      <div>
                        <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{s.label}</div>
                        <div style={{ fontSize: 16, fontWeight: 800, color: s.color }}>{s.value}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Table */}
              {loadingResults ? (
                <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>Loading results...</div>
              ) : (
                <div style={{ overflowX: 'auto', borderRadius: 8, border: '1px solid var(--border-color)' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                    <thead>
                      <tr style={{ background: 'rgba(99,102,241,0.1)' }}>
                        <th style={thStyle}>Rank</th>
                        {columns.map(col => (
                          <th
                            key={col}
                            style={{ ...thStyle, cursor: 'pointer', userSelect: 'none', background: col === selectedUpload.rank_column ? 'rgba(16,185,129,0.15)' : undefined }}
                            onClick={() => {
                              if (sortCol === col) setSortAsc(!sortAsc);
                              else { setSortCol(col); setSortAsc(true); }
                            }}
                          >
                            {col} {sortCol === col && (sortAsc ? '↑' : '↓')} {col === selectedUpload.rank_column && '🏅'}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {filteredResults.map((r, i) => (
                        <tr key={r.id} style={{ background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)', borderBottom: '1px solid var(--border-color)' }}>
                          <td style={{ ...tdStyle, fontWeight: 700, textAlign: 'center', color: r.rank && r.rank <= 3 ? '#10b981' : 'var(--text-secondary)' }}>
                            {r.rank ? (r.rank <= 3 ? ['🥇', '🥈', '🥉'][r.rank - 1] : `#${r.rank}`) : '—'}
                          </td>
                          {columns.map(col => (
                            <td key={col} style={{ ...tdStyle, background: col === selectedUpload.rank_column ? 'rgba(16,185,129,0.05)' : undefined }}>
                              {r.row_data?.[col] != null ? String(r.row_data[col]) : '—'}
                            </td>
                          ))}
                        </tr>
                      ))}
                      {filteredResults.length === 0 && (
                        <tr>
                          <td colSpan={columns.length + 1} style={{ ...tdStyle, textAlign: 'center', padding: 30, color: 'var(--text-muted)' }}>
                            No results found
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}

              <div style={{ textAlign: 'right', marginTop: 8, fontSize: 12, color: 'var(--text-muted)' }}>
                Showing {filteredResults.length} of {results.length} records
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
