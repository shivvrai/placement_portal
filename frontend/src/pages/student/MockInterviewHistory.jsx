/**
 * Mock Interview History — Card list with score trend visualization.
 */

import { useState, useEffect } from 'react';
import { mockInterviewApi } from '../../api/endpoints';

export default function MockInterviewHistory() {
  const [sessions, setSessions] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      mockInterviewApi.getMyHistory(50).catch(() => ({ data: [] })),
      mockInterviewApi.getMyStats().catch(() => ({ data: null })),
    ]).then(([histRes, statsRes]) => {
      setSessions(histRes.data || []);
      setStats(statsRes.data || null);
      setLoading(false);
    });
  }, []);

  const formatTime = (s) => s ? `${Math.floor(s / 60)}m ${s % 60}s` : 'N/A';
  const formatDate = (iso) => iso ? new Date(iso).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
  }) : 'N/A';

  const verdictColor = (v) => ({
    'Strong Hire': '#10b981', 'Hire': '#7dd3fc', 'Borderline': '#f59e0b', 'No Hire': '#ef4444',
  }[v] || '#94a3b8');

  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center', color: '#94a3b8' }}>
        Loading interview history...
      </div>
    );
  }

  return (
    <div style={{ padding: 24, maxWidth: 1000, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 800, color: '#f1f5f9', marginBottom: 4 }}>
            📜 Interview History
          </h1>
          <p style={{ color: '#94a3b8', fontSize: 14 }}>
            Track your mock interview performance over time
          </p>
        </div>
        <button
          onClick={() => window.location.href = '/student/mock-interview'}
          style={{
            padding: '10px 20px', borderRadius: 10, border: 'none',
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            color: '#fff', fontSize: 14, fontWeight: 700, cursor: 'pointer',
          }}
        >+ New Interview</button>
      </div>

      {/* Stats Summary */}
      {stats && stats.total_sessions > 0 && (
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12,
          marginBottom: 28, padding: 20, borderRadius: 16,
          background: '#1e293b', border: '1px solid #334155',
        }}>
          {[
            { label: 'Total Sessions', value: stats.total_sessions, color: '#a5b4fc' },
            { label: 'Avg Technical', value: `${stats.avg_technical_score}/10`, color: '#10b981' },
            { label: 'Avg Communication', value: `${stats.avg_communication_score}/10`, color: '#7dd3fc' },
            { label: 'Avg Confidence', value: `${stats.avg_confidence_score}/10`, color: '#f59e0b' },
            { label: 'Avg Relevance', value: `${stats.avg_relevance_score}/10`, color: '#c084fc' },
          ].map(s => (
            <div key={s.label} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 22, fontWeight: 800, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Trend Mini Chart */}
      {stats && stats.improvement_trend && stats.improvement_trend.length > 1 && (
        <div style={{
          padding: 20, borderRadius: 16, background: '#1e293b',
          border: '1px solid #334155', marginBottom: 28,
        }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: '#cbd5e1', marginBottom: 12 }}>
            📈 Score Trend (Technical)
          </h3>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6, height: 80 }}>
            {stats.improvement_trend.slice(-15).map((t, i) => {
              const h = Math.max(8, (t.technical / 10) * 80);
              const color = t.technical >= 7 ? '#10b981' : t.technical >= 5 ? '#f59e0b' : '#ef4444';
              return (
                <div key={i} title={`${t.technical}/10 — ${t.verdict}`} style={{
                  flex: 1, height: h, borderRadius: '4px 4px 0 0',
                  background: color, cursor: 'pointer', transition: 'all 0.3s',
                  minWidth: 12, position: 'relative',
                }}>
                  <span style={{
                    position: 'absolute', top: -18, left: '50%', transform: 'translateX(-50%)',
                    fontSize: 10, color: '#94a3b8', whiteSpace: 'nowrap',
                  }}>{t.technical}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Session Cards */}
      {sessions.length === 0 ? (
        <div style={{
          padding: 40, textAlign: 'center', borderRadius: 16,
          background: '#1e293b', border: '1px solid #334155',
        }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>🎤</div>
          <p style={{ color: '#94a3b8', fontSize: 15 }}>No interviews yet. Start your first mock interview!</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {sessions.map(s => (
            <div key={s.id} style={{
              padding: '18px 20px', borderRadius: 14, background: '#1e293b',
              border: '1px solid #334155', display: 'flex', alignItems: 'center',
              gap: 16, cursor: 'pointer', transition: 'all 0.2s',
            }}
              onClick={() => window.location.href = `/student/mock-interview?session=${s.id}`}
              onMouseEnter={e => e.currentTarget.style.borderColor = '#6366f1'}
              onMouseLeave={e => e.currentTarget.style.borderColor = '#334155'}
            >
              {/* Role badge */}
              <div style={{
                width: 48, height: 48, borderRadius: 12, background: '#312e81',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 20, flexShrink: 0,
              }}>🎤</div>

              {/* Info */}
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 15, fontWeight: 700, color: '#e2e8f0' }}>{s.role_target}</div>
                <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>
                  {s.company_style} • {s.difficulty} • {formatDate(s.started_at)}
                </div>
              </div>

              {/* Scores */}
              {s.performance_scores && (
                <div style={{ display: 'flex', gap: 8 }}>
                  {['technical', 'communication', 'confidence', 'relevance'].map(key => (
                    <div key={key} style={{
                      width: 36, height: 36, borderRadius: 8,
                      background: (s.performance_scores[key] || 0) >= 7 ? '#064e3b' : '#451a03',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 13, fontWeight: 700,
                      color: (s.performance_scores[key] || 0) >= 7 ? '#6ee7b7' : '#fde68a',
                    }}>
                      {s.performance_scores[key] || 0}
                    </div>
                  ))}
                </div>
              )}

              {/* Verdict */}
              <div style={{
                padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 700,
                color: verdictColor(s.verdict), background: '#0f172a',
                border: `1px solid ${verdictColor(s.verdict)}30`,
              }}>
                {s.verdict || s.status}
              </div>

              {/* Duration */}
              <div style={{ fontSize: 12, color: '#64748b', minWidth: 60, textAlign: 'right' }}>
                {formatTime(s.duration_seconds)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
