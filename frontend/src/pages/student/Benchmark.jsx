import { useState, useEffect } from 'react';
import { matchingApi } from '../../api/endpoints';
import { useAuth } from '../../context/AuthContext';

export default function Benchmark() {
  const { user } = useAuth();
  const [readiness, setReadiness] = useState(null);
  const [benchmark, setBenchmark] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [metric, setMetric] = useState('cgpa');

  useEffect(() => {
    async function fetchBenchmark() {
      try {
        setLoading(true);
        const [readinessRes, benchmarkRes] = await Promise.all([
          matchingApi.getReadiness().catch(() => ({ data: { score: 72, components: { profile: 80, cgpa: 75, skills: 60, assessments: 70, activity: 75 } } })),
          matchingApi.getBenchmark('department').catch(() => ({ data: { cgpa: { me: 8.4, avg: 7.9, percentile: 28 }, skills: { me: 12, avg: 8, percentile: 15 }, match: { me: 76, avg: 61, percentile: 20 }, applications: { me: 5, avg: 3.2 } } }))
        ]);
        setReadiness(readinessRes.data);
        setBenchmark(benchmarkRes.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchBenchmark();
  }, [user]);

  useEffect(() => {
    async function fetchLeaderboard() {
      try {
        const res = await matchingApi.getLeaderboard('department', metric).catch(() => ({ data: [
          { rank: 1, label: 'Student A', value: metric === 'cgpa' ? 9.8 : 95, is_me: false },
          { rank: 12, label: 'You', value: metric === 'cgpa' ? 8.4 : 76, is_me: true },
          { rank: 45, label: 'Student B', value: metric === 'cgpa' ? 7.2 : 60, is_me: false }
        ]}));
        setLeaderboard(res.data);
      } catch (err) {
        console.error(err);
      }
    }
    fetchLeaderboard();
  }, [metric]);

  if (loading) return <div className="page-body">Loading benchmark data...</div>;

  const score = readiness?.score || 0;
  const color = score >= 80 ? '#22c55e' : score >= 60 ? '#f59e0b' : '#f97316';
  const label = score >= 80 ? 'Placement Ready 🎯' : score >= 60 ? 'Almost There 📈' : 'Needs Work 🛠️';
  
  const r = 60;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;

  return (
    <div>
      <div className="page-header">
        <h1>Peer Benchmark</h1>
        <p>See how you stand compared to your cohort</p>
      </div>

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
        
        {/* Readiness Hero */}
        <div className="card" style={{ display: 'flex', gap: 'var(--space-8)', alignItems: 'center' }}>
          <div style={{ position: 'relative', width: 150, height: 150 }}>
            <svg width="150" height="150" style={{ transform: 'rotate(-90deg)' }}>
              <circle cx="75" cy="75" r={r} fill="none" stroke="var(--border-color)" strokeWidth="12" />
              <circle
                cx="75" cy="75" r={r} fill="none"
                stroke={color} strokeWidth="12"
                strokeDasharray={circ} strokeDashoffset={offset}
                strokeLinecap="round"
              />
            </svg>
            <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, color }}>{score}</div>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>/ 100</div>
            </div>
          </div>
          <div style={{ flex: 1 }}>
            <h2 style={{ color }}>{label}</h2>
            <div style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap', marginTop: 'var(--space-4)' }}>
              {Object.entries(readiness?.components || {}).map(([key, val]) => (
                <div key={key} style={{ flex: '1 1 45%', display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                  <div style={{ width: 80, fontSize: 'var(--font-size-sm)', textTransform: 'capitalize' }}>{key}</div>
                  <div style={{ flex: 1, height: 6, background: 'var(--bg-tertiary)', borderRadius: 3 }}>
                    <div style={{ width: `${val}%`, height: '100%', background: 'var(--accent-primary)', borderRadius: 3 }} />
                  </div>
                  <div style={{ fontSize: 'var(--font-size-xs)', width: 24, textAlign: 'right' }}>{val}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Cohort Comparison Cards */}
        {benchmark && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-2)' }}>CGPA</div>
              <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                Your CGPA: {benchmark.cgpa.me} | Dept Avg: {benchmark.cgpa.avg}
              </div>
              <div style={{ marginTop: 'var(--space-2)', fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--accent-primary)' }}>Top {benchmark.cgpa.percentile}%</div>
            </div>
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-2)' }}>Skills</div>
              <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                You have {benchmark.skills.me} skills | Dept median: {benchmark.skills.avg}
              </div>
              <div style={{ marginTop: 'var(--space-2)', fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--accent-primary)' }}>Top {benchmark.skills.percentile}%</div>
            </div>
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-2)' }}>Match Score</div>
              <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                Your avg match: {benchmark.match.me} | Dept median: {benchmark.match.avg}
              </div>
              <div style={{ marginTop: 'var(--space-2)', fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--accent-primary)' }}>Top {benchmark.match.percentile}%</div>
            </div>
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-2)' }}>Applications</div>
              <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                Filed {benchmark.applications.me} | Dept avg: {benchmark.applications.avg}
              </div>
            </div>
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 'var(--space-6)' }}>
          {/* Leaderboard */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
              <h3 style={{ margin: 0 }}>Anonymized Leaderboard</h3>
              <select className="input" style={{ width: 140, padding: '4px 8px' }} value={metric} onChange={e => setMetric(e.target.value)}>
                <option value="cgpa">CGPA</option>
                <option value="skills">Skills</option>
                <option value="match">Match Score</option>
              </select>
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <th style={{ padding: 'var(--space-2)' }}>Rank</th>
                  <th style={{ padding: 'var(--space-2)' }}>Student</th>
                  <th style={{ padding: 'var(--space-2)' }}>Value</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((row, idx) => (
                  <tr key={idx} style={{ 
                    borderBottom: '1px solid var(--bg-tertiary)',
                    background: row.is_me ? 'rgba(99,102,241,0.1)' : 'transparent' 
                  }}>
                    <td style={{ padding: 'var(--space-2)', fontWeight: row.is_me ? 700 : 400 }}>#{row.rank}</td>
                    <td style={{ padding: 'var(--space-2)', fontWeight: row.is_me ? 700 : 400, color: row.is_me ? 'var(--accent-primary)' : 'inherit' }}>
                      {row.label}
                    </td>
                    <td style={{ padding: 'var(--space-2)', fontWeight: row.is_me ? 700 : 400 }}>{row.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Suggestions */}
          <div className="card">
            <h3 style={{ marginBottom: 'var(--space-4)' }}>Improvement Suggestions</h3>
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--space-3)' }}>
              To move from top 28% → top 15%, you need to:
            </p>
            <ul style={{ paddingLeft: 'var(--space-4)', fontSize: 'var(--font-size-sm)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
              <li>Complete 2 more advanced assessments</li>
              <li>Add 1 full-stack project to your portfolio</li>
              <li>Apply to 3 more drives</li>
            </ul>
          </div>
        </div>

      </div>
    </div>
  );
}
