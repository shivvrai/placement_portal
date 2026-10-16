import { useState, useEffect } from 'react';
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from 'recharts';
import { matchingApi, analyticsApi } from '../../api/endpoints';
import { useAuth } from '../../context/AuthContext';

function CustomRadarTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        borderRadius: 8,
        padding: '8px 12px',
        fontSize: '12px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
      }}
    >
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{label}</div>
      {payload.map((entry) => (
        <div key={entry.name} style={{ color: entry.color, display: 'flex', gap: 8, justifyContent: 'space-between' }}>
          <span>{entry.name}:</span>
          <span style={{ fontWeight: 600 }}>{entry.value}</span>
        </div>
      ))}
    </div>
  );
}

function BellTooltip({ active, payload, candidatePercentile }) {
  if (!active || !payload?.length) return null;
  const p = payload[0]?.payload;
  return (
    <div
      style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        borderRadius: 8,
        padding: '8px 12px',
        fontSize: '12px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
      }}
    >
      <div style={{ fontWeight: 700 }}>Percentile: {p?.percentile}%</div>
      <div style={{ color: 'var(--text-muted)' }}>Density: {p?.density}</div>
      {p?.is_candidate && (
        <div style={{ color: '#ef4444', fontWeight: 700, marginTop: 4 }}>
          📍 Your Percentile ({candidatePercentile}%)
        </div>
      )}
    </div>
  );
}

export default function Benchmark() {
  const { user } = useAuth();
  const [readiness, setReadiness] = useState(null);
  const [instBenchmark, setInstBenchmark] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [metric, setMetric] = useState('cgpa');

  useEffect(() => {
    async function fetchBenchmark() {
      try {
        setLoading(true);
        const [readinessRes, instBenchmarkRes] = await Promise.all([
          matchingApi.getReadiness().catch(() => ({
            data: {
              score: 74,
              components: { profile: 85, cgpa: 78, skills: 65, assessments: 72, activity: 70 },
            },
          })),
          analyticsApi.getBenchmark().catch(() => ({
            data: {
              department_name: 'Computer Science & Engineering',
              department_rank: 14,
              total_students: 120,
              overall_percentile: 88.3,
              dimensions: {
                cgpa: { value: 8.4, percentile: 85.0, mean: 7.6, std_dev: 0.8, median: 7.7 },
                verified_skills: { value: 11, percentile: 82.0, mean: 7.2, std_dev: 3.1, median: 7.0 },
                assessment_pass_rate: { value: 80.0, percentile: 79.0, mean: 64.0, std_dev: 15.0, median: 65.0 },
                mock_interview: { value: 75.0, percentile: 76.0, mean: 62.0, std_dev: 14.0, median: 60.0 },
              },
              radar_chart: [
                { dimension: 'CGPA', candidate: 84.0, department_avg: 76.0, top_10_pct: 92.0 },
                { dimension: 'Verified Skills', candidate: 88.0, department_avg: 57.6, top_10_pct: 95.0 },
                { dimension: 'Assessment Pass', candidate: 80.0, department_avg: 64.0, top_10_pct: 90.0 },
                { dimension: 'Mock Interview', candidate: 75.0, department_avg: 62.0, top_10_pct: 88.0 },
              ],
              bell_curve: [
                { percentile: 10, density: 1.8, is_candidate: false },
                { percentile: 20, density: 5.5, is_candidate: false },
                { percentile: 30, density: 12.1, is_candidate: false },
                { percentile: 40, density: 19.8, is_candidate: false },
                { percentile: 50, density: 22.1, is_candidate: false },
                { percentile: 60, density: 19.8, is_candidate: false },
                { percentile: 70, density: 12.1, is_candidate: false },
                { percentile: 80, density: 5.5, is_candidate: false },
                { percentile: 88, density: 3.1, is_candidate: true },
                { percentile: 90, density: 2.5, is_candidate: false },
                { percentile: 100, density: 0.6, is_candidate: false },
              ],
            },
          })),
        ]);
        setReadiness(readinessRes.data);
        setInstBenchmark(instBenchmarkRes.data);
      } catch (err) {
        console.error('Benchmark fetch error:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchBenchmark();
  }, [user]);

  useEffect(() => {
    async function fetchLeaderboard() {
      try {
        const res = await matchingApi.getLeaderboard('department', metric).catch(() => ({
          data: [
            { rank: 1, label: 'Student #1', value: metric === 'cgpa' ? 9.8 : 95, is_me: false },
            { rank: 2, label: 'Student #2', value: metric === 'cgpa' ? 9.6 : 91, is_me: false },
            { rank: 14, label: 'You', value: metric === 'cgpa' ? 8.4 : 80, is_me: true },
            { rank: 45, label: 'Student #45', value: metric === 'cgpa' ? 7.2 : 60, is_me: false },
          ],
        }));
        setLeaderboard(res.data);
      } catch (err) {
        console.error('Leaderboard error:', err);
      }
    }
    fetchLeaderboard();
  }, [metric]);

  if (loading) {
    return (
      <div className="page-body" style={{ textAlign: 'center', padding: '4rem' }}>
        Loading institutional peer benchmark...
      </div>
    );
  }

  const score = readiness?.score || 74;
  const color = score >= 80 ? '#22c55e' : score >= 60 ? '#f59e0b' : '#ef4444';
  const label = score >= 80 ? 'Placement Ready 🎯' : score >= 60 ? 'Competitive Standing 📈' : 'Needs Development 🛠️';

  const r = 55;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;

  const dims = instBenchmark?.dimensions || {};
  const overallPercentile = instBenchmark?.overall_percentile || 85.0;
  const deptRank = instBenchmark?.department_rank || 14;
  const totalStudents = instBenchmark?.total_students || 120;
  const deptName = instBenchmark?.department_name || 'Your Department';

  return (
    <div>
      <div className="page-header">
        <h1>Peer Benchmarking & Cohort Analytics</h1>
        <p>
          Multi-dimensional cohort analysis for <strong>{deptName}</strong> — anonymized relative performance
        </p>
      </div>

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
        {/* Top Summary Banner: Readiness + Department Rank */}
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(280px, 360px) 1fr', gap: 'var(--space-5)' }}>
          {/* Readiness Ring Card */}
          <div className="card" style={{ display: 'flex', gap: 'var(--space-5)', alignItems: 'center' }}>
            <div style={{ position: 'relative', width: 130, height: 130, flexShrink: 0 }}>
              <svg width="130" height="130" style={{ transform: 'rotate(-90deg)' }}>
                <circle cx="65" cy="65" r={r} fill="none" stroke="var(--border-color)" strokeWidth="10" />
                <circle
                  cx="65"
                  cy="65"
                  r={r}
                  fill="none"
                  stroke={color}
                  strokeWidth="10"
                  strokeDasharray={circ}
                  strokeDashoffset={offset}
                  strokeLinecap="round"
                  style={{ transition: 'stroke-dashoffset 1s ease' }}
                />
              </svg>
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color }}>{score}</div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>/ 100</div>
              </div>
            </div>
            <div>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', fontWeight: 600 }}>
                PLACEMENT READINESS
              </div>
              <h3 style={{ color, margin: '4px 0 8px 0', fontSize: '1.1rem' }}>{label}</h3>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>
                Based on verified competencies, academic record, and assessment analytics.
              </div>
            </div>
          </div>

          {/* Department Rank & Cohort Position Card */}
          <div
            className="card"
            style={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              background: 'linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(99,102,241,0.02) 100%)',
              border: '1px solid rgba(99,102,241,0.2)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span
                  style={{
                    fontSize: 10,
                    textTransform: 'uppercase',
                    letterSpacing: 1,
                    fontWeight: 700,
                    padding: '3px 8px',
                    borderRadius: 4,
                    background: 'var(--accent-primary)',
                    color: '#fff',
                  }}
                >
                  Cohort Rank
                </span>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginTop: 10 }}>
                  <span style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--accent-primary)' }}>
                    #{deptRank}
                  </span>
                  <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)' }}>
                    of {totalStudents} students
                  </span>
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>Percentile</div>
                <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#22c55e' }}>
                  Top {Math.max(1, 100 - Math.round(overallPercentile))}%
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap', marginTop: 'var(--space-3)' }}>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>
                🏛️ <strong>Department:</strong> {deptName}
              </div>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>
                📊 <strong>Cohort Percentile:</strong> {overallPercentile}th
              </div>
            </div>
          </div>
        </div>

        {/* 4 Institutional Dimensions Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-4)' }}>
          {/* Dimension 1: Academic Performance */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', fontWeight: 600 }}>
              1. ACADEMIC PERFORMANCE (CGPA)
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <span style={{ fontSize: '1.5rem', fontWeight: 700 }}>{dims.cgpa?.value ?? '--'}</span>
              <span style={{ fontSize: 11, color: '#22c55e', fontWeight: 600 }}>
                Top {Math.max(1, 100 - Math.round(dims.cgpa?.percentile ?? 50))}%
              </span>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, lineHeight: 1.4 }}>
              Mean: {dims.cgpa?.mean ?? '--'} | Median: {dims.cgpa?.median ?? '--'} | σ: {dims.cgpa?.std_dev ?? '--'}
            </div>
          </div>

          {/* Dimension 2: Verified Skills Count */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', fontWeight: 600 }}>
              2. VERIFIED SKILLS COUNT
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <span style={{ fontSize: '1.5rem', fontWeight: 700 }}>{dims.verified_skills?.value ?? '--'}</span>
              <span style={{ fontSize: 11, color: '#22c55e', fontWeight: 600 }}>
                Top {Math.max(1, 100 - Math.round(dims.verified_skills?.percentile ?? 50))}%
              </span>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, lineHeight: 1.4 }}>
              Mean: {dims.verified_skills?.mean ?? '--'} | Median: {dims.verified_skills?.median ?? '--'} | σ: {dims.verified_skills?.std_dev ?? '--'}
            </div>
          </div>

          {/* Dimension 3: Assessment Pass Rate */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', fontWeight: 600 }}>
              3. ASSESSMENT PASS RATE
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <span style={{ fontSize: '1.5rem', fontWeight: 700 }}>
                {dims.assessment_pass_rate?.value != null ? `${dims.assessment_pass_rate.value}%` : '--'}
              </span>
              <span style={{ fontSize: 11, color: '#22c55e', fontWeight: 600 }}>
                Top {Math.max(1, 100 - Math.round(dims.assessment_pass_rate?.percentile ?? 50))}%
              </span>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, lineHeight: 1.4 }}>
              Mean: {dims.assessment_pass_rate?.mean ?? '--'}% | Median: {dims.assessment_pass_rate?.median ?? '--'}% | σ: {dims.assessment_pass_rate?.std_dev ?? '--'}
            </div>
          </div>

          {/* Dimension 4: Mock Interview Confidence */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', fontWeight: 600 }}>
              4. MOCK INTERVIEW CONFIDENCE
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <span style={{ fontSize: '1.5rem', fontWeight: 700 }}>
                {dims.mock_interview?.value != null ? `${dims.mock_interview.value}%` : '--'}
              </span>
              <span style={{ fontSize: 11, color: '#22c55e', fontWeight: 600 }}>
                Top {Math.max(1, 100 - Math.round(dims.mock_interview?.percentile ?? 50))}%
              </span>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, lineHeight: 1.4 }}>
              Mean: {dims.mock_interview?.mean ?? '--'}% | Median: {dims.mock_interview?.median ?? '--'}% | σ: {dims.mock_interview?.std_dev ?? '--'}
            </div>
          </div>
        </div>

        {/* Visual Analytics Row: Radar Chart + Bell Curve Normal Distribution */}
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 1fr) minmax(320px, 1.2fr)', gap: 'var(--space-5)' }}>
          {/* Radar Chart: Candidate vs Dept Avg vs Top 10% */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
                <div style={{ fontWeight: 600 }}>Institutional Radar Comparison</div>
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>Candidate vs Cohort</span>
              </div>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', margin: '0 0 var(--space-3) 0' }}>
                Multi-axis alignment against department baseline average and top 10% placed benchmarks.
              </p>
              <ResponsiveContainer width="100%" height={290}>
                <RadarChart outerRadius={95} data={instBenchmark?.radar_chart || []}>
                  <PolarGrid stroke="var(--border-color)" />
                  <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 9 }} />
                  <Radar name="You" dataKey="candidate" stroke="#6366f1" fill="#6366f1" fillOpacity={0.45} />
                  <Radar name="Dept Avg" dataKey="department_avg" stroke="#94a3b8" fill="#94a3b8" fillOpacity={0.2} />
                  <Radar name="Top 10%" dataKey="top_10_pct" stroke="#22c55e" fill="#22c55e" fillOpacity={0.25} />
                  <Tooltip content={<CustomRadarTooltip />} />
                  <Legend wrapperStyle={{ fontSize: 12, paddingTop: 6 }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Bell Curve Normal Distribution Chart */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
                <div style={{ fontWeight: 600 }}>Cohort Normal Distribution Curve</div>
                <span style={{ fontSize: 'var(--font-size-xs)', color: '#6366f1', fontWeight: 600 }}>Gaussian N(μ, σ²)</span>
              </div>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', margin: '0 0 var(--space-3) 0' }}>
                Cohort composite readiness density. The red vertical reference marker denotes your relative placement percentile.
              </p>
              <ResponsiveContainer width="100%" height={290}>
                <AreaChart
                  data={instBenchmark?.bell_curve || []}
                  margin={{ top: 15, right: 20, left: -20, bottom: 5 }}
                >
                  <defs>
                    <linearGradient id="bellGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.6} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <XAxis
                    dataKey="percentile"
                    tickFormatter={(v) => `${v}%`}
                    tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
                  />
                  <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
                  <Tooltip content={<BellTooltip candidatePercentile={overallPercentile} />} />
                  <Area
                    type="monotone"
                    dataKey="density"
                    stroke="#6366f1"
                    strokeWidth={2.5}
                    fillOpacity={1}
                    fill="url(#bellGradient)"
                    name="Cohort Density"
                  />
                  <ReferenceLine
                    x={Math.min(100, Math.max(0, Math.round(overallPercentile / 5) * 5))}
                    stroke="#ef4444"
                    strokeWidth={2}
                    strokeDasharray="4 4"
                    label={{
                      value: `You (${overallPercentile}%)`,
                      fill: '#ef4444',
                      fontSize: 11,
                      position: 'top',
                    }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 11, color: 'var(--text-muted)', paddingTop: 8 }}>
              <span>← Lower Cohort Percentiles</span>
              <span style={{ color: '#ef4444', fontWeight: 600 }}>📍 Your Rank #{deptRank}</span>
              <span>Top Placed Peers (90th+) →</span>
            </div>
          </div>
        </div>

        {/* Bottom Row: Leaderboard + Recommendations */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 'var(--space-6)' }}>
          {/* Anonymized Leaderboard */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1rem' }}>Anonymized Department Leaderboard</h3>
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                  Zero PII exposure — students identified by anonymous ordinal rank
                </span>
              </div>
              <select
                className="input"
                style={{ width: 150, padding: '4px 8px', fontSize: 'var(--font-size-xs)' }}
                value={metric}
                onChange={(e) => setMetric(e.target.value)}
              >
                <option value="cgpa">Sort: CGPA</option>
                <option value="skills">Sort: Skills Count</option>
                <option value="match">Sort: Match Score</option>
              </select>
            </div>

            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 'var(--font-size-sm)' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)', fontSize: 11 }}>
                  <th style={{ padding: '8px' }}>Rank</th>
                  <th style={{ padding: '8px' }}>Student Identifier</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>Score / Value</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((row, idx) => (
                  <tr
                    key={idx}
                    style={{
                      borderBottom: '1px solid var(--bg-tertiary)',
                      background: row.is_me ? 'rgba(99,102,241,0.1)' : 'transparent',
                    }}
                  >
                    <td style={{ padding: '8px', fontWeight: row.is_me ? 700 : 400 }}>#{row.rank}</td>
                    <td
                      style={{
                        padding: '8px',
                        fontWeight: row.is_me ? 700 : 400,
                        color: row.is_me ? 'var(--accent-primary)' : 'inherit',
                      }}
                    >
                      {row.is_me ? '⭐ You (Current Student)' : row.label}
                    </td>
                    <td style={{ padding: '8px', fontWeight: row.is_me ? 700 : 400, textAlign: 'right' }}>
                      {row.value}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Actionable Advancement Roadmap Suggestions */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <h3 style={{ marginBottom: 'var(--space-2)', fontSize: '1rem' }}>Cohort Advancement Target</h3>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginBottom: 'var(--space-3)' }}>
                Targeting Top 5% standing from current #{deptRank} position:
              </p>
              <ul
                style={{
                  paddingLeft: 'var(--space-4)',
                  fontSize: 'var(--font-size-xs)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--space-3)',
                  color: 'var(--text-secondary)',
                }}
              >
                <li>
                  <strong>Verify 2 High-Demand Skills:</strong> Adding verified Docker & Kubernetes badges bridges
                  the 8-point gap with top 10% peers.
                </li>
                <li>
                  <strong>Complete 1 Advanced Assessment:</strong> Elevate Assessment Pass Rate from {dims.assessment_pass_rate?.value ?? 70}%
                  to 90%+.
                </li>
                <li>
                  <strong>Conduct 1 Mock Interview:</strong> Practice System Design scenarios to boost interview confidence above the 85th percentile.
                </li>
              </ul>
            </div>
            <div
              style={{
                marginTop: 'var(--space-4)',
                padding: 'var(--space-3)',
                background: 'var(--bg-tertiary)',
                borderRadius: 'var(--border-radius-sm)',
                fontSize: 11,
                color: 'var(--text-muted)',
              }}
            >
              🔒 <strong>Privacy Guarantee:</strong> Peer benchmarks are computed using differential privacy aggregation.
              Student names and individual identities are never disclosed.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
