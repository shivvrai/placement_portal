/**
 * Student Dashboard — main landing page for students.
 * Shows skill readiness score, top job matches, upcoming drives, and roadmap progress.
 * Connected to live FastAPI ML matching service and backend APIs.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { intelligenceApi, placementApi, studentApi } from '../../api/endpoints';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer,
         BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

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
  const [stats, setStats] = useState({
    skill_score: 0,
    match_count: 0,
    roadmap_progress: 0,
    applications: 0,
  });
  const [matches, setMatches] = useState([]);
  const [gaps, setGaps] = useState([]);
  const [drives, setDrives] = useState([]);
  const [radarData, setRadarData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchDashboard() {
      try {
        setLoading(true);
        setError(null);

        const [matchesRes, gapRes, drivesRes, _profileRes, skillsRes, applicationsRes, roadmapRes] =
          await Promise.allSettled([
            intelligenceApi.getMatches(user.id, { limit: 10 }),
            intelligenceApi.getSkillGap(user.id, 'Software Engineer'),
            placementApi.getDrives({ status: 'upcoming', per_page: 5 }),
            studentApi.getMyProfile(),
            studentApi.getMySkills(),
            placementApi.getMyApplications(),
            intelligenceApi.getRoadmap(user.id),
          ]);

        const matchesData = matchesRes.status === 'fulfilled' ? (matchesRes.value.data || []) : [];
        const gapData = gapRes.status === 'fulfilled' ? gapRes.value.data : null;
        const drivesData = drivesRes.status === 'fulfilled' ? (drivesRes.value.data?.data || drivesRes.value.data || []) : [];
        const skillsData = skillsRes.status === 'fulfilled' ? (skillsRes.value.data || []) : [];
        const applicationsData = applicationsRes.status === 'fulfilled' ? (applicationsRes.value.data || []) : [];
        const roadmapData = roadmapRes.status === 'fulfilled' ? roadmapRes.value.data : null;

        const skillScore = Math.round(gapData?.overall_score ?? 0);
        const matchCount = matchesData.length;
        const roadmapProgress = Math.round(roadmapData?.progress_pct ?? 0);
        const applicationsCount = applicationsData.length;

        setStats({
          skill_score: skillScore,
          match_count: matchCount,
          roadmap_progress: roadmapProgress,
          applications: applicationsCount,
        });

        // Top 3 Matches
        setMatches(
          matchesData.slice(0, 3).map((job) => ({
            id: job.job_id || job.id,
            title: job.title,
            company: job.company_name || job.company || 'Recruiter',
            role_category: job.role_category || 'General',
            match_score: Math.round(job.match_score || 0),
          }))
        );

        // Top Skill Gaps
        setGaps(
          (gapData?.gaps || []).slice(0, 5).map((g) => ({
            skill: g.skill_name,
            gap: Math.round(g.gap > 1 ? g.gap : g.gap * 100),
          }))
        );

        // Upcoming Drives
        setDrives(
          drivesData.slice(0, 4).map((d) => ({
            id: d.id,
            company: d.company?.name || d.company || 'Recruiter',
            role: d.title || (d.roles_offered?.[0]) || 'Campus Placement',
            deadline: d.registration_deadline ? d.registration_deadline.split('T')[0] : 'Open',
            min_cgpa: d.min_cgpa ? Number(d.min_cgpa).toFixed(1) : 'None',
          }))
        );

        // Radar Data
        if (skillsData.length > 0) {
          setRadarData(
            skillsData.slice(0, 6).map((s) => ({
              skill: s.skill?.name || s.skill_name || 'Skill',
              score: Math.round((s.confidence || 0) * (s.confidence <= 1 ? 100 : 1)),
            }))
          );
        } else if (gapData?.gaps?.length > 0) {
          setRadarData(
            gapData.gaps.slice(0, 6).map((g) => ({
              skill: g.skill_name,
              score: Math.round(g.current_score > 1 ? g.current_score : g.current_score * 100),
            }))
          );
        } else {
          setRadarData([]);
        }
      } catch (err) {
        console.error('Failed to load dashboard:', err);
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    }

    if (user?.id) {
      fetchDashboard();
    }
  }, [user]);

  const matchColor = (score) =>
    score >= 80 ? 'var(--accent-success)' : score >= 65 ? 'var(--accent-warning)' : 'var(--accent-danger)';

  if (loading) {
    return (
      <div className="page-body" style={{ textAlign: 'center', padding: '4rem' }}>
        Loading career intelligence dashboard...
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

  return (
    <div>
      {/* Page header */}
      <div className="page-header">
        <h1>Welcome back, {user?.first_name || 'Student'} 👋</h1>
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
            {radarData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="var(--border-color)" />
                  <PolarAngleAxis dataKey="skill" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                  <Radar name="Score" dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} />
                </RadarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--text-muted)' }}>
                Add skills to your profile to visualize your skill radar.
              </div>
            )}
          </div>

          {/* Top matches */}
          <div className="card">
            <SectionHeader
              title="Top Job Matches"
              action={<Link to="/student/matches" className="btn btn-ghost" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>View all →</Link>}
            />
            {matches.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {matches.map((job) => (
                  <div
                    key={job.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: 'var(--space-3) var(--space-4)',
                      background: 'var(--bg-tertiary)',
                      borderRadius: 'var(--border-radius-sm)',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 500, fontSize: 'var(--font-size-sm)' }}>{job.title}</div>
                      <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                        {job.company} · {job.role_category}
                      </div>
                    </div>
                    <div
                      style={{
                        fontWeight: 700,
                        fontSize: 'var(--font-size-lg)',
                        color: matchColor(job.match_score),
                      }}
                    >
                      {job.match_score}%
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: 'var(--space-6)', color: 'var(--text-muted)' }}>
                No job matches available yet. Complete your profile to get matched.
              </div>
            )}
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
            {gaps.length > 0 ? (
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
            ) : (
              <div style={{ textAlign: 'center', padding: 'var(--space-6)', color: 'var(--text-muted)' }}>
                No major skill gaps identified. You're on track!
              </div>
            )}
          </div>

          {/* Upcoming drives */}
          <div className="card">
            <SectionHeader
              title="Upcoming Drives"
              action={<Link to="/student/drives" className="btn btn-ghost" style={{ height: 32, fontSize: 'var(--font-size-xs)' }}>View all →</Link>}
            />
            {drives.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {drives.map((drive) => (
                  <div
                    key={drive.id}
                    style={{
                      padding: 'var(--space-4)',
                      background: 'var(--bg-tertiary)',
                      borderRadius: 'var(--border-radius-sm)',
                      borderLeft: '3px solid var(--accent-primary)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <div style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)' }}>{drive.company}</div>
                      <span className="badge badge-warning">Deadline: {drive.deadline}</span>
                    </div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 'var(--space-1)' }}>
                      {drive.role} · Min CGPA {drive.min_cgpa}
                    </div>
                    <Link to="/student/drives">
                      <button
                        className="btn btn-primary"
                        style={{ height: 28, fontSize: 'var(--font-size-xs)', marginTop: 'var(--space-3)', padding: '0 var(--space-3)' }}
                      >
                        Apply Now
                      </button>
                    </Link>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: 'var(--space-6)', color: 'var(--text-muted)' }}>
                No upcoming placement drives at the moment.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
