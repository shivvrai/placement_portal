/**
 * Student Skill Gap — shows per-skill gap analysis vs. target job role.
 * Charts: horizontal bar chart per category, detailed skill table.
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, Cell,
} from 'recharts';

// ─── Mock Data ────────────────────────────────────────────────────
const TARGET_ROLES = [
  { id: 1, label: 'Data Analyst' },
  { id: 2, label: 'Python Developer' },
  { id: 3, label: 'ML Engineer' },
  { id: 4, label: 'Full Stack Developer' },
];

const SKILL_DATA = {
  1: {
    overallScore: 67,
    categories: [
      { category: 'Programming', current: 75, required: 85 },
      { category: 'Statistics', current: 45, required: 80 },
      { category: 'SQL & Databases', current: 70, required: 90 },
      { category: 'Data Viz', current: 50, required: 75 },
      { category: 'ML Basics', current: 55, required: 70 },
      { category: 'Communication', current: 78, required: 80 },
    ],
    skills: [
      { skill: 'Python', category: 'Programming', current: 75, required: 85, gap: 10, severity: 'low', resources: 3 },
      { skill: 'Pandas / NumPy', category: 'Programming', current: 60, required: 85, gap: 25, severity: 'medium', resources: 5 },
      { skill: 'SQL', category: 'SQL & Databases', current: 70, required: 90, gap: 20, severity: 'medium', resources: 4 },
      { skill: 'Statistics', category: 'Statistics', current: 45, required: 80, gap: 35, severity: 'high', resources: 7 },
      { skill: 'Tableau / Power BI', category: 'Data Viz', current: 20, required: 75, gap: 55, severity: 'critical', resources: 6 },
      { skill: 'Machine Learning', category: 'ML Basics', current: 55, required: 70, gap: 15, severity: 'low', resources: 8 },
      { skill: 'Excel Advanced', category: 'Data Viz', current: 60, required: 70, gap: 10, severity: 'low', resources: 2 },
      { skill: 'Communication', category: 'Communication', current: 78, required: 80, gap: 2, severity: 'none', resources: 0 },
    ],
  },
  2: {
    overallScore: 74,
    categories: [
      { category: 'Python', current: 80, required: 90 },
      { category: 'Web Frameworks', current: 50, required: 85 },
      { category: 'Databases', current: 65, required: 80 },
      { category: 'DevOps', current: 20, required: 70 },
      { category: 'Testing', current: 40, required: 75 },
      { category: 'System Design', current: 45, required: 65 },
    ],
    skills: [
      { skill: 'Python', category: 'Python', current: 80, required: 90, gap: 10, severity: 'low', resources: 3 },
      { skill: 'FastAPI / Django', category: 'Web Frameworks', current: 50, required: 85, gap: 35, severity: 'high', resources: 6 },
      { skill: 'PostgreSQL', category: 'Databases', current: 65, required: 80, gap: 15, severity: 'low', resources: 4 },
      { skill: 'Docker', category: 'DevOps', current: 20, required: 70, gap: 50, severity: 'critical', resources: 5 },
      { skill: 'Git Advanced', category: 'DevOps', current: 55, required: 70, gap: 15, severity: 'low', resources: 3 },
      { skill: 'pytest', category: 'Testing', current: 40, required: 75, gap: 35, severity: 'high', resources: 4 },
    ],
  },
  3: {
    overallScore: 58,
    categories: [
      { category: 'Math & Stats', current: 45, required: 90 },
      { category: 'ML Frameworks', current: 55, required: 85 },
      { category: 'Python', current: 80, required: 85 },
      { category: 'MLOps', current: 10, required: 70 },
      { category: 'Deep Learning', current: 35, required: 80 },
      { category: 'Data Engineering', current: 30, required: 65 },
    ],
    skills: [
      { skill: 'Linear Algebra', category: 'Math & Stats', current: 45, required: 90, gap: 45, severity: 'critical', resources: 8 },
      { skill: 'scikit-learn', category: 'ML Frameworks', current: 55, required: 85, gap: 30, severity: 'high', resources: 5 },
      { skill: 'PyTorch / TensorFlow', category: 'Deep Learning', current: 35, required: 80, gap: 45, severity: 'critical', resources: 9 },
      { skill: 'MLflow', category: 'MLOps', current: 10, required: 70, gap: 60, severity: 'critical', resources: 4 },
      { skill: 'Feature Engineering', category: 'ML Frameworks', current: 50, required: 85, gap: 35, severity: 'high', resources: 6 },
      { skill: 'Python', category: 'Python', current: 80, required: 85, gap: 5, severity: 'none', resources: 0 },
    ],
  },
  4: {
    overallScore: 70,
    categories: [
      { category: 'React', current: 60, required: 85 },
      { category: 'Node.js', current: 45, required: 80 },
      { category: 'CSS / Design', current: 65, required: 75 },
      { category: 'Databases', current: 60, required: 75 },
      { category: 'DevOps', current: 25, required: 65 },
      { category: 'TypeScript', current: 30, required: 80 },
    ],
    skills: [
      { skill: 'React', category: 'React', current: 60, required: 85, gap: 25, severity: 'medium', resources: 6 },
      { skill: 'TypeScript', category: 'TypeScript', current: 30, required: 80, gap: 50, severity: 'critical', resources: 5 },
      { skill: 'Node.js / Express', category: 'Node.js', current: 45, required: 80, gap: 35, severity: 'high', resources: 7 },
      { skill: 'MongoDB', category: 'Databases', current: 40, required: 75, gap: 35, severity: 'high', resources: 4 },
      { skill: 'Docker', category: 'DevOps', current: 25, required: 65, gap: 40, severity: 'critical', resources: 5 },
      { skill: 'CSS / Tailwind', category: 'CSS / Design', current: 65, required: 75, gap: 10, severity: 'low', resources: 3 },
    ],
  },
};

const SEVERITY_CONFIG = {
  none:     { label: 'No Gap',  color: 'var(--accent-success)', bg: 'rgba(34,197,94,0.1)' },
  low:      { label: 'Low',     color: '#22c55e',               bg: 'rgba(34,197,94,0.1)' },
  medium:   { label: 'Medium',  color: 'var(--accent-warning)', bg: 'rgba(245,158,11,0.1)' },
  high:     { label: 'High',    color: '#f97316',               bg: 'rgba(249,115,22,0.1)' },
  critical: { label: 'Critical',color: 'var(--accent-danger)',  bg: 'rgba(239,68,68,0.1)' },
};

// ─── Score Ring ────────────────────────────────────────────────────
function ScoreRing({ score }) {
  const r = 54;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 75 ? '#22c55e' : score >= 55 ? '#f59e0b' : '#ef4444';

  return (
    <div style={{ position: 'relative', width: 140, height: 140 }}>
      <svg width="140" height="140" style={{ transform: 'rotate(-90deg)' }}>
        <circle cx="70" cy="70" r={r} fill="none" stroke="var(--border-color)" strokeWidth="10" />
        <circle
          cx="70" cy="70" r={r} fill="none"
          stroke={color} strokeWidth="10"
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s ease' }}
        />
      </svg>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      }}>
        <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color }}>{score}</div>
        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>/ 100</div>
      </div>
    </div>
  );
}

// ─── Skill Row ─────────────────────────────────────────────────────
function SkillRow({ skill }) {
  const cfg = SEVERITY_CONFIG[skill.severity];
  return (
    <tr>
      <td>
        <div style={{ fontWeight: 500 }}>{skill.skill}</div>
        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{skill.category}</div>
      </td>
      <td>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <div style={{
            flex: 1, height: 6, background: 'var(--bg-tertiary)', borderRadius: 3, overflow: 'hidden',
          }}>
            <div style={{
              width: `${skill.current}%`, height: '100%',
              background: 'var(--gradient-accent)', borderRadius: 3,
              transition: 'width 0.8s ease',
            }} />
          </div>
          <span style={{ fontSize: 'var(--font-size-xs)', width: 28, textAlign: 'right' }}>{skill.current}</span>
        </div>
      </td>
      <td style={{ textAlign: 'center', fontWeight: 600, color: 'var(--text-secondary)' }}>{skill.required}</td>
      <td>
        <span style={{
          display: 'inline-block',
          padding: '2px 10px',
          borderRadius: 999,
          fontSize: 'var(--font-size-xs)',
          fontWeight: 600,
          background: cfg.bg,
          color: cfg.color,
        }}>
          {skill.severity === 'none' ? '✓' : `−${skill.gap}`} {cfg.label}
        </span>
      </td>
      <td style={{ textAlign: 'center' }}>
        {skill.resources > 0 ? (
          <Link to="/student/roadmap" style={{ fontSize: 'var(--font-size-xs)', color: 'var(--accent-primary)' }}>
            {skill.resources} resources →
          </Link>
        ) : (
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>Sufficient</span>
        )}
      </td>
    </tr>
  );
}

// ─── Custom Tooltip ────────────────────────────────────────────────
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border-color)',
      borderRadius: 8, padding: 'var(--space-3) var(--space-4)',
    }}>
      <div style={{ fontWeight: 600, marginBottom: 'var(--space-2)' }}>{label}</div>
      {payload.map(p => (
        <div key={p.name} style={{ color: p.color, fontSize: 'var(--font-size-sm)' }}>
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────
export default function SkillGap() {
  const [selectedRole, setSelectedRole] = useState(1);
  const [filter, setFilter] = useState('all');
  const data = SKILL_DATA[selectedRole];

  const filteredSkills = filter === 'all'
    ? data.skills
    : data.skills.filter(s => s.severity === filter);

  const chartData = data.categories.map(c => ({
    name: c.category,
    Current: c.current,
    Required: c.required,
  }));

  return (
    <div>
      <div className="page-header">
        <h1>Skill Gap Analysis</h1>
        <p>See exactly where you stand vs. industry requirements for your target role</p>
      </div>

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-8)' }}>

        {/* Role selector */}
        <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
          <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)', alignSelf: 'center' }}>
            Target role:
          </span>
          {TARGET_ROLES.map(r => (
            <button
              key={r.id}
              onClick={() => setSelectedRole(r.id)}
              className={`btn ${selectedRole === r.id ? 'btn-primary' : 'btn-secondary'}`}
              style={{ height: 36, fontSize: 'var(--font-size-sm)' }}
            >
              {r.label}
            </button>
          ))}
        </div>

        {/* Top row: score ring + radar */}
        <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 'var(--space-6)' }}>

          {/* Score card */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 'var(--space-4)' }}>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)', fontWeight: 500 }}>
              Overall Readiness
            </div>
            <ScoreRing score={data.overallScore} />
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                {data.overallScore >= 75 ? '🟢 On track' : data.overallScore >= 55 ? '🟡 Needs work' : '🔴 Significant gaps'}
              </div>
              <Link to="/student/roadmap">
                <button className="btn btn-primary" style={{ marginTop: 'var(--space-4)', height: 36, fontSize: 'var(--font-size-sm)' }}>
                  🗺️ View Roadmap
                </button>
              </Link>
            </div>
          </div>

          {/* Category bar chart */}
          <div className="card">
            <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Skills by Category</div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData} margin={{ left: 0, right: 16, top: 4, bottom: 4 }}>
                <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="Current" fill="#6366f1" radius={[4, 4, 0, 0]} name="Current" />
                <Bar dataKey="Required" fill="rgba(99,102,241,0.2)" radius={[4, 4, 0, 0]} name="Required" />
              </BarChart>
            </ResponsiveContainer>
            <div style={{ display: 'flex', gap: 'var(--space-6)', marginTop: 'var(--space-2)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                <div style={{ width: 12, height: 12, background: '#6366f1', borderRadius: 2 }} />
                Your current level
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                <div style={{ width: 12, height: 12, background: 'rgba(99,102,241,0.35)', borderRadius: 2 }} />
                Required by industry
              </div>
            </div>
          </div>
        </div>

        {/* Skill table */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-5)' }}>
            <div style={{ fontWeight: 600 }}>Skill-Level Breakdown</div>
            <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
              {['all', 'critical', 'high', 'medium', 'low', 'none'].map(f => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  style={{
                    padding: '4px 12px', borderRadius: 999, border: 'none', cursor: 'pointer',
                    fontSize: 'var(--font-size-xs)', fontWeight: 500,
                    background: filter === f ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                    color: filter === f ? 'white' : 'var(--text-muted)',
                    transition: 'all var(--transition-fast)',
                    textTransform: 'capitalize',
                  }}
                >
                  {f === 'all' ? 'All' : f}
                </button>
              ))}
            </div>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Skill</th>
                  <th style={{ minWidth: 180 }}>Your Level</th>
                  <th style={{ textAlign: 'center' }}>Required</th>
                  <th>Gap</th>
                  <th style={{ textAlign: 'center' }}>Resources</th>
                </tr>
              </thead>
              <tbody>
                {filteredSkills.map(s => <SkillRow key={s.skill} skill={s} />)}
              </tbody>
            </table>
          </div>

          {filteredSkills.length === 0 && (
            <div style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--text-muted)' }}>
              No skills match this filter.
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
