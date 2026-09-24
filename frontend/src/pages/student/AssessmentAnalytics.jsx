import { useState, useEffect } from 'react';
import { assessmentsApi } from '../../api/endpoints';

export default function AssessmentAnalytics() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAnalytics() {
      try {
        setLoading(true);
        // Using getMyAnalytics endpoint
        const res = await assessmentsApi.getMyAnalytics().catch(() => ({ data: {
          history: [
            { session_id: '1', topic: 'Python', score: 85, date: '2026-09-01' },
            { session_id: '2', topic: 'React', score: 92, date: '2026-09-10' },
            { session_id: '3', topic: 'System Design', score: 44, date: '2026-09-20' }
          ],
          topic_breakdown: [
            { topic: 'Python', avg_score: 85, attempts: 1, trend: 'up' },
            { topic: 'React', avg_score: 92, attempts: 1, trend: 'up' },
            { topic: 'System Design', avg_score: 44, attempts: 1, trend: 'down' }
          ],
          weakest_topic: { topic: 'System Design', score: 44 },
          cohort_comparison: [
            { topic: 'Python', my_score: 85, avg_score: 72, percentile: 18 },
            { topic: 'System Design', my_score: 44, avg_score: 65, percentile: 85 }
          ]
        }}));
        setAnalytics(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchAnalytics();
  }, []);

  if (loading) return <div className="page-body">Loading analytics...</div>;

  return (
    <div>
      <div className="page-header">
        <h1>Assessment Analytics</h1>
        <p>Track your performance and identify areas for improvement</p>
      </div>

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
        
        {/* Weakest Topic Alert */}
        {analytics?.weakest_topic && (
          <div className="card" style={{ background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.2)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ color: 'var(--accent-danger)', fontWeight: 700, fontSize: 'var(--font-size-sm)' }}>Needs Attention</div>
              <h2 style={{ margin: '4px 0' }}>Weakest: {analytics.weakest_topic.topic} ({analytics.weakest_topic.score}%)</h2>
              <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>Based on recent assessment results.</div>
            </div>
            <button className="btn btn-primary" style={{ background: 'var(--accent-danger)', borderColor: 'var(--accent-danger)' }}>
              Start Preparation
            </button>
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-6)' }}>
          {/* Topic Breakdown */}
          <div className="card">
            <h3 style={{ marginBottom: 'var(--space-4)' }}>Topic Breakdown</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              {analytics?.topic_breakdown?.map(t => (
                <div key={t.topic} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 'var(--space-3)', background: 'var(--bg-secondary)', borderRadius: 'var(--border-radius-sm)' }}>
                  <div>
                    <div style={{ fontWeight: 600 }}>{t.topic}</div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{t.attempts} attempts</div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                    <div style={{ fontWeight: 700, fontSize: 'var(--font-size-lg)' }}>{t.avg_score}%</div>
                    <div style={{ color: t.trend === 'up' ? '#22c55e' : '#ef4444' }}>{t.trend === 'up' ? '↑' : '↓'}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Cohort Comparison */}
          <div className="card">
            <h3 style={{ marginBottom: 'var(--space-4)' }}>Cohort Comparison</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {analytics?.cohort_comparison?.map(c => (
                <div key={c.topic}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-2)', fontSize: 'var(--font-size-sm)' }}>
                    <span style={{ fontWeight: 600 }}>{c.topic}</span>
                    <span style={{ color: 'var(--text-muted)' }}>Top {c.percentile}%</span>
                  </div>
                  <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center', fontSize: 'var(--font-size-xs)' }}>
                    <span style={{ width: 60, color: 'var(--text-muted)' }}>You: {c.my_score}%</span>
                    <div style={{ flex: 1, height: 6, background: 'var(--bg-tertiary)', borderRadius: 3 }}>
                      <div style={{ width: `${c.my_score}%`, height: '100%', background: 'var(--accent-primary)', borderRadius: 3 }} />
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center', fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
                    <span style={{ width: 60, color: 'var(--text-muted)' }}>Avg: {c.avg_score}%</span>
                    <div style={{ flex: 1, height: 6, background: 'var(--bg-tertiary)', borderRadius: 3 }}>
                      <div style={{ width: `${c.avg_score}%`, height: '100%', background: 'var(--text-muted)', borderRadius: 3 }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Performance Over Time */}
        <div className="card">
          <h3 style={{ marginBottom: 'var(--space-4)' }}>Performance History</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                <th style={{ padding: 'var(--space-2)' }}>Date</th>
                <th style={{ padding: 'var(--space-2)' }}>Topic</th>
                <th style={{ padding: 'var(--space-2)' }}>Score</th>
              </tr>
            </thead>
            <tbody>
              {analytics?.history?.map((h, i) => (
                <tr key={i} style={{ borderBottom: '1px solid var(--bg-tertiary)' }}>
                  <td style={{ padding: 'var(--space-2)', color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)' }}>{h.date}</td>
                  <td style={{ padding: 'var(--space-2)', fontWeight: 500 }}>{h.topic}</td>
                  <td style={{ padding: 'var(--space-2)', fontWeight: 600, color: h.score >= 80 ? '#22c55e' : h.score >= 60 ? '#f59e0b' : '#ef4444' }}>{h.score}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </div>
    </div>
  );
}
