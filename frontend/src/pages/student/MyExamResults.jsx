/**
 * My Exam Results — Students view their own exam/assessment results
 * across all uploaded sheets, with rank and detailed scores.
 */

import { useState, useEffect } from 'react';
import { examUploadApi } from '../../api/endpoints';

export default function MyExamResults() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    examUploadApi.getMyResults()
      .then(res => setResults(res.data || []))
      .catch(() => setResults([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '28px 32px', textAlign: 'center', color: 'var(--text-muted)' }}>
        ⏳ Loading your results...
      </div>
    );
  }

  const getRankBadge = (rank, total) => {
    if (!rank) return null;
    const pct = total ? Math.round((rank / total) * 100) : null;
    let color = '#64748b';
    let icon = `#${rank}`;
    if (rank === 1) { color = '#f59e0b'; icon = '🥇'; }
    else if (rank === 2) { color = '#94a3b8'; icon = '🥈'; }
    else if (rank === 3) { color = '#cd7f32'; icon = '🥉'; }
    else if (pct && pct <= 10) { color = '#10b981'; }
    else if (pct && pct <= 25) { color = '#6366f1'; }

    return (
      <div style={{
        display: 'inline-flex', alignItems: 'center', gap: 6,
        padding: '6px 14px', borderRadius: 20,
        background: `${color}20`, border: `1px solid ${color}40`,
      }}>
        <span style={{ fontSize: rank <= 3 ? 20 : 14 }}>{icon}</span>
        {rank > 3 && <span style={{ fontWeight: 700, color, fontSize: 15 }}>Rank {rank}</span>}
        {total && <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>/ {total}</span>}
      </div>
    );
  };

  return (
    <div style={{ padding: '28px 32px' }}>
      <h1 style={{ margin: '0 0 4px', fontSize: 'var(--font-size-2xl)' }}>📝 My Exam Results</h1>
      <p style={{ margin: '0 0 24px', color: 'var(--text-muted)', fontSize: 14 }}>
        Your results from uploaded assessment sheets
      </p>

      {results.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 60 }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>📭</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-secondary)' }}>No results found</div>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
            Your TPO hasn't uploaded any exam sheets with your roll number yet.
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: 14 }}>
          {results.map(r => {
            const isExpanded = expandedId === r.id;
            const examTypeColors = {
              'MST-1': '#6366f1', 'MST-2': '#8b5cf6', 'End Sem': '#ef4444',
              'Quiz': '#f59e0b', 'Assignment': '#10b981', 'Lab Exam': '#06b6d4',
            };
            const rankVal = r.rank_column && r.row_data?.[r.rank_column];

            return (
              <div key={r.id} className="card" style={{ overflow: 'hidden' }}>
                {/* Main row */}
                <div
                  style={{
                    padding: '16px 20px', cursor: 'pointer', display: 'flex',
                    justifyContent: 'space-between', alignItems: 'center',
                    transition: 'background 0.15s',
                  }}
                  onClick={() => setExpandedId(isExpanded ? null : r.id)}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 16, flex: 1 }}>
                    <div style={{
                      width: 48, height: 48, borderRadius: 12,
                      background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 22, flexShrink: 0,
                    }}>
                      📋
                    </div>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 15 }}>{r.exam_title}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        {r.exam_type && (
                          <span style={{
                            padding: '2px 8px', borderRadius: 8, fontSize: 11, fontWeight: 600,
                            background: `${examTypeColors[r.exam_type] || '#64748b'}20`,
                            color: examTypeColors[r.exam_type] || '#64748b',
                          }}>
                            {r.exam_type}
                          </span>
                        )}
                        {r.department && <span>Dept: {r.department}</span>}
                        {r.section && <span>· Sec: {r.section}</span>}
                        {r.exam_date && <span>· {new Date(r.exam_date).toLocaleDateString()}</span>}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                    {rankVal != null && (
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{r.rank_column}</div>
                        <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--accent-primary)' }}>{rankVal}</div>
                      </div>
                    )}
                    {getRankBadge(r.rank, r.total_students)}
                    <span style={{ color: 'var(--text-muted)', fontSize: 14, transition: 'transform 0.2s', transform: isExpanded ? 'rotate(180deg)' : 'none' }}>▼</span>
                  </div>
                </div>

                {/* Expanded details */}
                {isExpanded && (
                  <div style={{
                    padding: '0 20px 20px', borderTop: '1px solid var(--border-color)',
                    background: 'rgba(99,102,241,0.03)',
                  }}>
                    <div style={{ paddingTop: 16 }}>
                      <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 10 }}>
                        All Columns
                      </div>
                      <div style={{
                        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 8,
                      }}>
                        {Object.entries(r.row_data || {}).map(([key, val]) => (
                          <div key={key} style={{
                            padding: '8px 12px', borderRadius: 8,
                            background: key === r.rank_column ? 'rgba(16,185,129,0.1)' : 'var(--bg-primary)',
                            border: `1px solid ${key === r.rank_column ? 'rgba(16,185,129,0.3)' : 'var(--border-color)'}`,
                          }}>
                            <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>
                              {key} {key === r.rank_column && '🏅'}
                            </div>
                            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>
                              {val != null ? String(val) : '—'}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
