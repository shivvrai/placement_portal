/**
 * Student Dashboard — main landing page for students.
 * Shows skill readiness score, top job matches, upcoming drives, and roadmap progress.
 * Uses mock data initially; switches to live API when backend is ready.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { intelligenceApi, placementApi, analyticsApi } from '../../api/endpoints';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer,
         BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

// ─── Mock data (used until VITE_USE_MOCKS=false) ─────────────────
const MOCK_STATS = {
  skill_score: 73,
  match_count: 12,
  roadmap_progress: 38,
  applications: 3,
};

const MOCK_SKILL_RADAR = [
  { skill: 'Python', score: 85 }, { skill: 'SQL', score: 72 },
  { skill: 'React', score: 60 }, { skill: 'ML Basics', score: 55 },
  { skill: 'Communication', score: 78 }, { skill: 'Data Viz', score: 50 },
];

const MOCK_TOP_MATCHES = [
  { id: 1, title: 'Data Analyst', company: 'Infosys', match_score: 84, role_category: 'Analytics' },
  { id: 2, title: 'Python Developer', company: 'TCS', match_score: 79, role_category: 'Engineering' },
  { id: 3, title: 'ML Engineer Intern', company: 'Wipro', match_score: 71, role_category: 'ML' },
];

const MOCK_SKILL_GAPS = [
  { skill: 'Docker', gap: 100 }, { skill: 'FastAPI', gap: 80 },
  { skill: 'Statistics', gap: 60 }, { skill: 'Git Advanced', gap: 40 },
];

const MOCK_DRIVES = [
  { id: 1, company: 'Google', role: 'SWE Intern', deadline: '2026-09-10', min_cgpa: 7.5 },
  { id: 2, company: 'Amazon', role: 'Data Engineer', deadline: '2026-09-15', min_cgpa: 7.0 },
];

// ─── Stat Card ────────────────────────────────────────────────────
function StatCard({ label, value, unit, icon, to }) {
  const inner = (
    <div className="stat-card" style={{ cursor: to ? 'pointer' : 'default' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div className="stat-card-label">{label}</div>
        <span style={{ fontSize: '1.5rem' }}>{icon}</span>
      </div>
      <div className="stat-card-value">
        {value}<span style={{ fontSize: 'var(--font-size-lg)', WebkitTextFillColor: 'inherit' }}>{unit}</span>
      </div>
    </div>
  );
  return to ? <Link to={to} style={{ textDecoration: 'none' }}>{inner}</Link> : inner;
}

// ─── Section header ────────────────────────────────────────────────
function SectionHeader({ title, action }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
      <h2 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 600 }}>{title}</h2>
      {action}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────
export default function StudentDashboard() {
  const { user } = useAuth();
  const [stats] = useState(MOCK_STATS);
  const [matches] = useState(MOCK_TOP_MATCHES);
  const [gaps] = useState(MOCK_SKILL_GAPS);
  const [drives] = useState(MOCK_DRIVES);

  const matchColor = (score) =>
    score >= 80 ? 'var(--accent-success)' : score >= 65 ? 'var(--accent-warning)' : 'var(--accent-danger)';

  return (
    <div>
      {/* Page header */}
      <div className="page-header">
        <h1>Welcome back, {user?.first_name} 👋</h1>
        <p>Here's your career intelligence snapshot for today</p>
      </div>

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-8)' }}>

        {/* Stat cards */}
        <div className="stat-grid">
          <StatCard label="Skill Readiness Score" value={stats.skill_score} unit="%" icon="🎯" to="/student/skill-gap" />
          <StatCard label="Job Matches" value={stats.match_count} unit=" roles" icon="💼" to="/student/matches" />
          <StatCard label="Roadmap Progress" value={stats.roadmap_progress} unit="%" icon="🗺️" to="/student/roadmap" />
          <StatCard label="Active Applications" value={stats.applications} unit="" icon="📋" to="/student/drives" />
        </div>

        {/* Two-column section: radar + top matches */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-6)' }}>

          {/* Skill radar */}
          <div className="card">
            <SectionHeader title="Skill Profile" />
            <ResponsiveContainer width="100%" height={260}>
              <RadarChart data={MOCK_SKILL_RADAR}>
                <PolarGrid stroke="var(--border-color)" />
                <PolarAngleAxis dataKey="skill" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                <Radar name="Score" dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Top matches */}
          <div className="card">
            <SectionHeader
              title="Top Job Matches"
              action={<Link to="/student/matches" className="btn btn-ghost" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>View all →</Link>}
            />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              {matches.map(job => (
                <div key={job.id} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: 'var(--space-3) var(--space-4)',
                  background: 'var(--bg-tertiary)', borderRadius: 'var(--border-radius-sm)',
                }}>
                  <div>
                    <div style={{ fontWeight: 500, fontSize: 'var(--font-size-sm)' }}>{job.title}</div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                      {job.company} · {job.role_category}
                    </div>
                  </div>
                  <div style={{
                    fontWeight: 700, fontSize: 'var(--font-size-lg)',
                    color: matchColor(job.match_score),
                  }}>
                    {job.match_score}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Two-column section: skill gaps + upcoming drives */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-6)' }}>

          {/* Skill gaps bar chart */}
          <div className="card">
            <SectionHeader
              title="Top Skill Gaps"
              action={<Link to="/student/skill-gap" className="btn btn-ghost" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>Details →</Link>}
            />
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={gaps} layout="vertical" margin={{ left: 8 }}>
                <XAxis type="number" domain={[0, 100]} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                <YAxis type="category" dataKey="skill" width={80} tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} />
                <Tooltip
                  contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 8 }}
                  labelStyle={{ color: 'var(--text-primary)' }}
                />
                <Bar dataKey="gap" fill="#ef4444" radius={[0, 4, 4, 0]} name="Gap %" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Upcoming drives */}
          <div className="card">
            <SectionHeader
              title="Upcoming Drives"
              action={<Link to="/student/drives" className="btn btn-ghost" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>View all →</Link>}
            />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              {drives.map(drive => (
                <div key={drive.id} style={{
                  padding: 'var(--space-4)',
                  background: 'var(--bg-tertiary)', borderRadius: 'var(--border-radius-sm)',
                  borderLeft: '3px solid var(--accent-primary)',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <div style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)' }}>{drive.company}</div>
                    <span className="badge badge-warning">Deadline: {drive.deadline}</span>
                  </div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 'var(--space-1)' }}>
                    {drive.role} · Min CGPA {drive.min_cgpa}
                  </div>
                  <Link to="/student/drives">
                    <button className="btn btn-primary" style={{ height: 28, fontSize: 'var(--font-size-xs)', marginTop: 'var(--space-3)', padding: '0 var(--space-3)' }}>
                      Apply Now
                    </button>
                  </Link>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
