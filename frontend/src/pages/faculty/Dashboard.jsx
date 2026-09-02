/**
 * Faculty/HOD Dashboard — dept skill score KPIs, coverage donut, gap leaderboard.
 */

import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer,
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip,
} from 'recharts';
import { useAuth } from '../../context/AuthContext';

// ─── Mock Data ────────────────────────────────────────────────────
const DEPT_KPIS = {
  avg_skill_score: 68,
  subjects_high_gap: 5,
  students_at_risk: 23,
  curriculum_coverage: 62,
};

const SKILL_RADAR = [
  { skill: 'Programming',   score: 78, benchmark: 85 },
  { skill: 'Databases',     score: 70, benchmark: 80 },
  { skill: 'ML / AI',       score: 55, benchmark: 80 },
  { skill: 'DevOps',        score: 32, benchmark: 70 },
  { skill: 'Statistics',    score: 48, benchmark: 75 },
  { skill: 'Communication', score: 72, benchmark: 75 },
];

const COVERAGE_DONUT = [
  { name: 'Covered by Curriculum', value: 62, color: '#6366f1' },
  { name: 'Gap (Not Covered)',     value: 38, color: '#ef4444' },
];

const SUBJECT_GAP_RANK = [
  { subject: 'Cloud Computing',   gap: 72, dept: 'CS', sem: 7 },
  { subject: 'DevOps Practices',  gap: 68, dept: 'CS', sem: 8 },
  { subject: 'Deep Learning',     gap: 65, dept: 'CS', sem: 7 },
  { subject: 'System Design',     gap: 58, dept: 'CS', sem: 8 },
  { subject: 'Statistics for ML', gap: 52, dept: 'CS', sem: 6 },
  { subject: 'Microservices',     gap: 48, dept: 'CS', sem: 8 },
  { subject: 'Data Engineering',  gap: 45, dept: 'CS', sem: 7 },
];

const BATCH_SKILL = [
  { batch: '2021', score: 68 },
  { batch: '2022', score: 71 },
  { batch: '2023', score: 65 },
  { batch: '2024', score: 74 },
];

const AT_RISK = [
  { roll: 'CS21B022', name: 'Rohan Mehta',   cgpa: 6.2, skill: 42, risk: 'high' },
  { roll: 'CS21B055', name: 'Priti Singh',   cgpa: 6.8, skill: 48, risk: 'high' },
  { roll: 'CS21B071', name: 'Aakash Rao',    cgpa: 7.1, skill: 51, risk: 'medium' },
  { roll: 'CS21B083', name: 'Nisha Pillai',  cgpa: 6.5, skill: 46, risk: 'high' },
  { roll: 'CS21B039', name: 'Ravi Patel',    cgpa: 7.4, skill: 53, risk: 'medium' },
];

const RISK_CFG = {
  high:   { color: '#ef4444', bg: 'rgba(239,68,68,0.1)',   label: 'High Risk' },
  medium: { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)',  label: 'Medium Risk' },
};

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 8, padding: 'var(--space-3) var(--space-4)' }}>
      <div style={{ fontWeight: 600 }}>{label}</div>
      {payload.map(p => <div key={p.name} style={{ color: p.color || 'var(--text-primary)', fontSize: 'var(--font-size-sm)' }}>{p.name}: {p.value}</div>)}
    </div>
  );
}

export default function FacultyDashboard() {
  const { user } = useAuth();

  return (
    <div>
      <div className="page-header">
        <h1>Faculty Dashboard</h1>
        <p>Curriculum intelligence for {user?.first_name ? `${user.first_name} ${user.last_name}` : 'Department of Computer Science'}</p>
      </div>

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-8)' }}>

        {/* KPI Cards */}
        <div className="stat-grid">
          {[
            { label: 'Dept Avg Skill Score', value: DEPT_KPIS.avg_skill_score, unit: '/100', icon: '📊' },
            { label: 'Curriculum Coverage', value: DEPT_KPIS.curriculum_coverage, unit: '%', icon: '📚' },
            { label: 'High-Gap Subjects', value: DEPT_KPIS.subjects_high_gap, unit: ' subjects', icon: '⚠️' },
            { label: 'Students At Risk', value: DEPT_KPIS.students_at_risk, unit: ' students', icon: '🔴' },
          ].map(s => (
            <div key={s.label} className="stat-card">
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div className="stat-card-label">{s.label}</div>
                <span style={{ fontSize: '1.5rem' }}>{s.icon}</span>
              </div>
              <div className="stat-card-value">{s.value}<span style={{ fontSize: 'var(--font-size-lg)', WebkitTextFillColor: 'inherit' }}>{s.unit}</span></div>
            </div>
          ))}
        </div>

        {/* Row 2: radar + coverage donut */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-6)' }}>

          {/* Skill radar */}
          <div className="card">
            <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Dept Skill Profile vs Industry Benchmark</div>
            <ResponsiveContainer width="100%" height={260}>
              <RadarChart data={SKILL_RADAR}>
                <PolarGrid stroke="var(--border-color)" />
                <PolarAngleAxis dataKey="skill" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                <Radar name="Dept Score" dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} />
                <Radar name="Benchmark" dataKey="benchmark" stroke="#ef4444" fill="#ef4444" fillOpacity={0.08} strokeDasharray="5 3" />
              </RadarChart>
            </ResponsiveContainer>
            <div style={{ display: 'flex', gap: 'var(--space-6)', marginTop: 'var(--space-2)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                <div style={{ width: 12, height: 12, background: '#6366f1', borderRadius: 2, opacity: 0.7 }} /> Dept average
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                <div style={{ width: 12, height: 12, background: '#ef4444', borderRadius: 2, opacity: 0.4 }} /> Industry benchmark
              </div>
            </div>
          </div>

          {/* Coverage donut + batch trend */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
            <div className="card" style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Curriculum → Industry Coverage</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-6)' }}>
                <PieChart width={130} height={130}>
                  <Pie data={COVERAGE_DONUT} cx={65} cy={65} innerRadius={40} outerRadius={60} dataKey="value" startAngle={90} endAngle={-270}>
                    {COVERAGE_DONUT.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                  </Pie>
                </PieChart>
                <div style={{ flex: 1 }}>
                  {COVERAGE_DONUT.map(c => (
                    <div key={c.name} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
                      <div style={{ width: 12, height: 12, borderRadius: 2, background: c.color, flexShrink: 0 }} />
                      <div>
                        <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: c.color }}>{c.value}%</div>
                        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{c.name}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="card" style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-3)' }}>Avg Skill Score by Batch</div>
              <ResponsiveContainer width="100%" height={100}>
                <BarChart data={BATCH_SKILL} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
                  <XAxis dataKey="batch" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                  <YAxis domain={[50, 90]} tick={{ fill: 'var(--text-muted)', fontSize: 10 }} hide />
                  <Tooltip content={<ChartTooltip />} />
                  <Bar dataKey="score" fill="#06b6d4" radius={[4, 4, 0, 0]} name="Avg Score" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Row 3: subject gap leaderboard + at-risk students */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-6)' }}>

          {/* Gap leaderboard */}
          <div className="card">
            <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>
              Subjects with Highest Skill Gap
              <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 400, color: 'var(--text-muted)', marginLeft: 8 }}>
                (industry demand vs curriculum coverage)
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              {SUBJECT_GAP_RANK.map((s, i) => (
                <div key={s.subject} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                  <div style={{
                    width: 24, height: 24, borderRadius: '50%', flexShrink: 0,
                    background: i < 3 ? '#ef444420' : 'var(--bg-tertiary)',
                    color: i < 3 ? '#ef4444' : 'var(--text-muted)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 'var(--font-size-xs)', fontWeight: 700,
                  }}>
                    {i + 1}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 500, fontSize: 'var(--font-size-sm)' }}>{s.subject}</div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>Sem {s.sem}</div>
                  </div>
                  <div style={{ width: 90, height: 6, background: 'var(--bg-tertiary)', borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ width: `${s.gap}%`, height: '100%', background: s.gap > 60 ? '#ef4444' : s.gap > 45 ? '#f59e0b' : '#6366f1', borderRadius: 3 }} />
                  </div>
                  <span style={{ width: 32, textAlign: 'right', fontSize: 'var(--font-size-xs)', fontWeight: 700, color: s.gap > 60 ? '#ef4444' : s.gap > 45 ? '#f59e0b' : '#6366f1' }}>
                    {s.gap}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* At-risk students */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
              <div style={{ fontWeight: 600 }}>Students at Placement Risk</div>
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>Skill score &lt; 55 or CGPA &lt; 7.0</span>
            </div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Student</th>
                    <th style={{ textAlign: 'center' }}>CGPA</th>
                    <th style={{ textAlign: 'center' }}>Skill</th>
                    <th>Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {AT_RISK.map(s => {
                    const rc = RISK_CFG[s.risk];
                    return (
                      <tr key={s.roll}>
                        <td>
                          <div style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)' }}>{s.name}</div>
                          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{s.roll}</div>
                        </td>
                        <td style={{ textAlign: 'center', color: s.cgpa < 6.5 ? '#ef4444' : '#f59e0b', fontWeight: 600 }}>{s.cgpa}</td>
                        <td style={{ textAlign: 'center', color: s.skill < 45 ? '#ef4444' : '#f59e0b', fontWeight: 600 }}>{s.skill}</td>
                        <td>
                          <span style={{ padding: '2px 10px', borderRadius: 999, fontSize: 'var(--font-size-xs)', fontWeight: 600, background: rc.bg, color: rc.color }}>
                            {rc.label}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <button className="btn btn-secondary" style={{ width: '100%', marginTop: 'var(--space-4)', height: 34, fontSize: 'var(--font-size-sm)' }}>
              View All 23 At-Risk Students
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}
