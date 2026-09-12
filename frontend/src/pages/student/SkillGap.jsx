/**
 * Student Skill Gap — shows per-skill gap analysis vs. target job role.
 * Connected to live ML gap engine with semantic embeddings.
 */

import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { intelligenceApi } from '../../api/endpoints';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts';

const TARGET_ROLES = [
  'Software Engineer',
  'Data Analyst',
  'ML Engineer',
  'Full Stack Developer',
  'DevOps Engineer',
  'Data Engineer',
  'Backend Developer',
];

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

// ─── Main Component ────────────────────────────────────────────────
export default function SkillGap() {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const targetRole = searchParams.get('role') || 'Software Engineer';

  const [gapData, setGapData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    async function fetchGap() {
      try {
        setLoading(true);
        setError(null);
        // This calls the ML gap engine
        const res = await intelligenceApi.getSkillGap(user.id, targetRole);
        setGapData(res.data);
      } catch (err) {
        console.error('Skill gap fetch failed:', err);
        setError(err.response?.data?.detail || 'Failed to compute skill gap analysis');
      } finally {
        setLoading(false);
      }
    }
    if (user?.id) {
      fetchGap();
    }
  }, [user, targetRole]);

  const handleRoleChange = (role) => {
    setSearchParams({ role });
  };

  if (loading) {
    return (
      <div className="page-body" style={{ textAlign: 'center', padding: '4rem' }}>
        Computing semantic skill gap analysis...
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-body" style={{ color: '#ef4444', textAlign: 'center', padding: '4rem' }}>
        {error}
      </div>
    );
  }

  const overallScore = Math.round(gapData?.overall_score ?? 0);

  // Map backend gaps to display items
  const gaps = (gapData?.gaps || []).map((g) => {
    const current = g.current_score > 1 ? Math.round(g.current_score) : Math.round(g.current_score * 100);
    const required = g.required_score > 1 ? Math.round(g.required_score) : Math.round(g.required_score * 100);
    const gap = g.gap > 1 ? Math.round(g.gap) : Math.round(g.gap * 100);
    return {
      skill: g.skill_name,
      category: g.category ? g.category.charAt(0).toUpperCase() + g.category.slice(1) : 'General',
      current,
      required,
      gap: Math.max(0, gap),
      severity: g.severity || 'low',
      resources: gap > 0 ? Math.min(6, Math.max(1, Math.round(gap / 10))) : 0,
    };
  });

  const filteredSkills = filter === 'all'
    ? gaps
    : gaps.filter((s) => s.severity === filter);

  // Compute category averages for the bar chart
  const categoryMap = {};
  gaps.forEach((g) => {
    if (!categoryMap[g.category]) {
      categoryMap[g.category] = { currentSum: 0, requiredSum: 0, count: 0 };
    }
    categoryMap[g.category].currentSum += g.current;
    categoryMap[g.category].requiredSum += g.required;
    categoryMap[g.category].count += 1;
  });

  const chartData = Object.entries(categoryMap).map(([category, data]) => ({
    name: category,
    Current: Math.round(data.currentSum / data.count),
    Required: Math.round(data.requiredSum / data.count),
  }));

  return (
    <div>
      <div className="page-header">
        <h1>Skill Gap Analysis</h1>
        <p>AI semantic intelligence comparing your verified skills to industry standards</p>
      </div>

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-8)' }}>
        {/* Role selector */}
        <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)', alignSelf: 'center' }}>
            Target role:
          </span>
          {TARGET_ROLES.map((r) => (
            <button
              key={r}
              onClick={() => handleRoleChange(r)}
              className={`btn ${targetRole.toLowerCase() === r.toLowerCase() ? 'btn-primary' : 'btn-secondary'}`}
              style={{ height: 36, fontSize: 'var(--font-size-sm)' }}
            >
              {r}
            </button>
          ))}
        </div>

        {/* Top row: score ring + category bar chart */}
        <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 'var(--space-6)' }}>
          {/* Score card */}
          <div
            className="card"
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 'var(--space-4)',
            }}
          >
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)', fontWeight: 500 }}>
              Overall Readiness
            </div>
            <ScoreRing score={overallScore} />
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                {overallScore >= 75 ? '🟢 On track' : overallScore >= 55 ? '🟡 Needs work' : '🔴 Significant gaps'}
              </div>
              <Link to="/student/roadmap">
                <button
                  className="btn btn-primary"
                  style={{ marginTop: 'var(--space-4)', height: 36, fontSize: 'var(--font-size-sm)' }}
                >
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
            <div style={{ fontWeight: 600 }}>Skill-Level Breakdown ({targetRole})</div>
            <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
              {['all', 'critical', 'high', 'medium', 'low', 'none'].map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  style={{
                    padding: '4px 12px',
                    borderRadius: 999,
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: 'var(--font-size-xs)',
                    fontWeight: 500,
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
                {filteredSkills.map((s) => (
                  <SkillRow key={s.skill} skill={s} />
                ))}
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
