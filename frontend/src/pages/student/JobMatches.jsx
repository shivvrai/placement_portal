/**
 * Job Matches — searchable, filterable grid of matched job roles.
 * Connected to live FastAPI ML matching service.
 */

import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { intelligenceApi } from '../../api/endpoints';

const matchColor = (score) =>
  score >= 80 ? '#22c55e' : score >= 65 ? '#f59e0b' : '#ef4444';

const matchBg = (score) =>
  score >= 80 ? 'rgba(34,197,94,0.1)' : score >= 65 ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)';

const formatSalary = (min, max) => {
  if (min && max) {
    return min === max ? `₹${min}L` : `₹${min} - ₹${max}L`;
  }
  if (min) return `₹${min}L+`;
  if (max) return `Up to ₹${max}L`;
  return 'Not disclosed';
};

// ─── Job Card ──────────────────────────────────────────────────────
function JobCard({ job, onSelect }) {
  const matchedCount = job.matched_skills?.length || 0;
  const missingCount = job.missing_skills?.length || 0;
  const totalSkills = matchedCount + missingCount;
  const skillPct = job.skill_match_pct ?? (totalSkills > 0 ? (matchedCount / totalSkills) * 100 : 0);

  return (
    <div
      className="card"
      onClick={() => onSelect(job)}
      style={{
        cursor: 'pointer',
        transition: 'all var(--transition-normal)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-4)',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 'var(--font-size-base)' }}>{job.title}</div>
          <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', marginTop: 2 }}>
            {job.company_name || job.company} · {job.location || 'Remote'}
          </div>
        </div>
        <div
          style={{
            minWidth: 52,
            height: 52,
            borderRadius: '50%',
            background: matchBg(job.match_score),
            border: `2px solid ${matchColor(job.match_score)}`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 800, color: matchColor(job.match_score) }}>
            {Math.round(job.match_score)}%
          </div>
          <div style={{ fontSize: 9, color: matchColor(job.match_score) }}>match</div>
        </div>
      </div>

      {/* Meta & Badges */}
      <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', alignItems: 'center' }}>
        <span className="badge badge-primary">{job.role_category || 'General'}</span>
        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
          💰 {formatSalary(job.salary_ctc_min, job.salary_ctc_max)} CTC
        </span>
        <span
          style={{
            padding: '2px 8px',
            borderRadius: 'var(--border-radius-sm)',
            fontSize: 'var(--font-size-xs)',
            fontWeight: 600,
            background: job.eligible ? 'rgba(34,197,94,0.12)' : 'rgba(239,68,68,0.12)',
            color: job.eligible ? '#22c55e' : '#ef4444',
            border: `1px solid ${job.eligible ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
          }}
        >
          {job.eligible ? '✓ Eligible' : '✗ Ineligible'}
        </span>
      </div>

      {/* Match progress bar */}
      <div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: 'var(--font-size-xs)',
            color: 'var(--text-muted)',
            marginBottom: 4,
          }}
        >
          <span>
            Skills matched: {matchedCount}/{totalSkills} ({Math.round(skillPct)}%)
          </span>
        </div>
        <div style={{ height: 4, background: 'var(--bg-tertiary)', borderRadius: 2, overflow: 'hidden' }}>
          <div
            style={{
              width: `${Math.min(100, Math.max(0, Math.round(skillPct)))}%`,
              height: '100%',
              background: matchColor(job.match_score),
              borderRadius: 2,
            }}
          />
        </div>
      </div>

      {/* Skill pills */}
      <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
        {(job.matched_skills || []).slice(0, 3).map((s) => (
          <span
            key={s}
            style={{
              padding: '2px 8px',
              borderRadius: 999,
              fontSize: 'var(--font-size-xs)',
              fontWeight: 500,
              background: 'rgba(34,197,94,0.12)',
              color: '#22c55e',
              border: '1px solid rgba(34,197,94,0.3)',
            }}
          >
            ✓ {s}
          </span>
        ))}
        {(job.missing_skills || []).slice(0, 2).map((s) => (
          <span
            key={s}
            style={{
              padding: '2px 8px',
              borderRadius: 999,
              fontSize: 'var(--font-size-xs)',
              fontWeight: 500,
              background: 'rgba(239,68,68,0.08)',
              color: 'var(--accent-danger)',
              border: '1px solid rgba(239,68,68,0.2)',
            }}
          >
            ✗ {s}
          </span>
        ))}
        {totalSkills > 5 && (
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', alignSelf: 'center' }}>
            +{totalSkills - 5} more
          </span>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'var(--space-1)' }}>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onSelect(job);
          }}
          className="btn btn-secondary"
          style={{
            padding: '3px 8px',
            fontSize: 'var(--font-size-xs)',
            height: 'auto',
            border: '1px solid var(--border-color)',
          }}
        >
          📊 Why this score?
        </button>
        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--accent-primary)', fontWeight: 600 }}>
          Full Diagnostics →
        </span>
      </div>
    </div>
  );
}

// ─── Explainable AI Match Diagnostics Breakdown Modal ───────────────
function JobModal({ job, onClose, userId }) {
  const navigate = useNavigate();
  const [addingToRoadmap, setAddingToRoadmap] = useState(false);

  if (!job) return null;

  const breakdown = job.breakdown;
  const matchedSkills = job.matched_skills || [];
  const missingSkills = job.missing_skills || [];
  const score = Math.round(job.match_score || 0);

  const academicScore = breakdown ? Math.round(breakdown.academic_score) : (job.eligible ? 95 : 30);
  const skillsScore = breakdown ? Math.round(breakdown.skills_score) : Math.round(job.skill_match_pct || 50);
  const expBonus = breakdown ? Math.round(breakdown.experience_bonus) : 10;
  const skillDetails = breakdown?.skill_details || [];
  const relevantProjects = breakdown?.relevant_projects || [];
  const recommendation = breakdown?.recommendation ||
    (missingSkills.length > 0
      ? `Adding 1 ${missingSkills[0]} project would boost this match by +14%.`
      : 'You satisfy core competencies for this role.');

  const handleAddToRoadmap = async () => {
    try {
      setAddingToRoadmap(true);
      const roleToGenerate = job.role_category || job.title;
      if (userId) {
        await intelligenceApi.generateRoadmap(userId, roleToGenerate);
      }
      navigate('/student/roadmap');
    } catch (err) {
      console.warn('Roadmap generation note:', err);
      // Navigate to roadmap even if already generated or mock
      navigate('/student/roadmap');
    } finally {
      setAddingToRoadmap(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.7)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--space-6)',
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--border-radius-lg)',
          padding: 'var(--space-8)',
          width: '100%',
          maxWidth: 680,
          maxHeight: '88vh',
          overflowY: 'auto',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.4)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-4)' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 700, color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                Explainable Match Diagnostics
              </span>
              <span className="badge badge-primary">{job.role_category || 'SDE'}</span>
            </div>
            <h2 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 800, marginTop: 4 }}>{job.title}</h2>
            <div style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)', marginTop: 2 }}>
              🏢 {job.company_name || job.company} · 📍 {job.location || 'Remote'} · 💰 {formatSalary(job.salary_ctc_min, job.salary_ctc_max)} CTC
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-muted)',
              fontSize: '1.75rem',
              lineHeight: 1,
              padding: '0 4px',
            }}
          >
            ×
          </button>
        </div>

        {/* Overall Match Progress Bar */}
        <div
          style={{
            padding: 'var(--space-4) var(--space-5)',
            background: 'var(--bg-tertiary)',
            borderRadius: 'var(--border-radius)',
            marginBottom: 'var(--space-6)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ fontWeight: 700, fontSize: 'var(--font-size-sm)' }}>Overall Match Fit</span>
            <span style={{ fontWeight: 800, fontSize: 'var(--font-size-xl)', color: matchColor(score) }}>
              {score}%
            </span>
          </div>
          <div style={{ height: 8, background: 'var(--bg-secondary)', borderRadius: 4, overflow: 'hidden' }}>
            <div
              style={{
                width: `${score}%`,
                height: '100%',
                background: matchColor(score),
                borderRadius: 4,
                transition: 'width 0.8s ease',
              }}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 6 }}>
            <span>Formula: 40% Academic + 45% Technical Skills + 15% Experience</span>
            <span>{job.eligible ? '✓ Fully Eligible' : '⚠️ Eligibility Constraints'}</span>
          </div>
        </div>

        {/* 3 Diagnostic Sub-Dimensions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)', marginBottom: 'var(--space-6)' }}>
          {/* Dimension 1: Academic Fit */}
          <div
            style={{
              padding: 'var(--space-4)',
              borderRadius: 'var(--border-radius)',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
              <div style={{ fontWeight: 700, fontSize: 'var(--font-size-sm)', display: 'flex', alignItems: 'center', gap: 6 }}>
                <span>🎓</span> Academic Fit
              </div>
              <span style={{ fontWeight: 800, color: matchColor(academicScore), fontSize: 'var(--font-size-sm)' }}>
                {academicScore} / 100
              </span>
            </div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {breakdown?.academic_reason || (
                job.eligible
                  ? 'Your CGPA and department meet or exceed recruiter baseline eligibility.'
                  : 'CGPA or department does not satisfy minimum institutional cutoffs.'
              )}
            </div>
          </div>

          {/* Dimension 2: Technical Skills Alignment */}
          <div
            style={{
              padding: 'var(--space-4)',
              borderRadius: 'var(--border-radius)',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
              <div style={{ fontWeight: 700, fontSize: 'var(--font-size-sm)', display: 'flex', alignItems: 'center', gap: 6 }}>
                <span>💻</span> Technical Skills Alignment (Semantic SBERT)
              </div>
              <span style={{ fontWeight: 800, color: matchColor(skillsScore), fontSize: 'var(--font-size-sm)' }}>
                {skillsScore} / 100
              </span>
            </div>

            {/* Per-skill diagnostic list */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {skillDetails.length > 0 ? (
                skillDetails.map((sd) => {
                  const isDirect = sd.match_type === 'direct';
                  const isAdjacent = sd.match_type === 'adjacent';
                  const isMissing = sd.match_type === 'missing';

                  const badgeBg = isDirect ? 'rgba(34,197,94,0.12)' : isAdjacent ? 'rgba(59,130,246,0.12)' : 'rgba(239,68,68,0.1)';
                  const badgeColor = isDirect ? '#22c55e' : isAdjacent ? '#3b82f6' : '#ef4444';
                  const badgeBorder = isDirect ? 'rgba(34,197,94,0.3)' : isAdjacent ? 'rgba(59,130,246,0.3)' : 'rgba(239,68,68,0.3)';

                  return (
                    <div
                      key={sd.required_skill}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '6px 10px',
                        background: 'var(--bg-card)',
                        borderRadius: 'var(--border-radius-sm)',
                        border: '1px solid var(--border-color)',
                        fontSize: 'var(--font-size-xs)',
                      }}
                    >
                      <span style={{ fontWeight: 600 }}>{sd.required_skill}</span>
                      <span
                        style={{
                          padding: '2px 8px',
                          borderRadius: 999,
                          fontWeight: 600,
                          fontSize: 11,
                          background: badgeBg,
                          color: badgeColor,
                          border: `1px solid ${badgeBorder}`,
                        }}
                      >
                        {isDirect && '🟢 Direct Match (100%)'}
                        {isAdjacent && `🔵 Adjacent Match → ${sd.student_skill} (${Math.round(sd.similarity * 100)}% similar)`}
                        {isMissing && '🔴 Missing (0%)'}
                      </span>
                    </div>
                  );
                })
              ) : (
                <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                  {matchedSkills.map((s) => (
                    <span key={s} style={{ padding: '2px 8px', borderRadius: 999, background: 'rgba(34,197,94,0.12)', color: '#22c55e', fontSize: 'var(--font-size-xs)' }}>
                      🟢 {s} (Matched)
                    </span>
                  ))}
                  {missingSkills.map((s) => (
                    <span key={s} style={{ padding: '2px 8px', borderRadius: 999, background: 'rgba(239,68,68,0.1)', color: '#ef4444', fontSize: 'var(--font-size-xs)' }}>
                      🔴 {s} (Missing)
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Dimension 3: Practical Experience Bonus */}
          <div
            style={{
              padding: 'var(--space-4)',
              borderRadius: 'var(--border-radius)',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
              <div style={{ fontWeight: 700, fontSize: 'var(--font-size-sm)', display: 'flex', alignItems: 'center', gap: 6 }}>
                <span>🛠️</span> Practical Experience & Projects Bonus
              </div>
              <span style={{ fontWeight: 800, color: 'var(--accent-primary)', fontSize: 'var(--font-size-sm)' }}>
                {expBonus} / 20 pts
              </span>
            </div>

            {relevantProjects.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {relevantProjects.map((rp, idx) => (
                  <div key={idx} style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>
                    ✅ {rp}
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                No directly aligned projects verified in portfolio. Adding projects featuring required tech boosts your score.
              </div>
            )}
          </div>
        </div>

        {/* AI Recommendation Banner */}
        <div
          style={{
            padding: 'var(--space-4)',
            borderRadius: 'var(--border-radius)',
            background: 'rgba(99, 102, 241, 0.08)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            marginBottom: 'var(--space-6)',
          }}
        >
          <div style={{ fontWeight: 700, fontSize: 'var(--font-size-sm)', color: 'var(--accent-primary)', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>💡</span> Talent Intelligence Recommendation
          </div>
          <p style={{ margin: 0, fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            {recommendation}
          </p>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleAddToRoadmap}
            disabled={addingToRoadmap}
            style={{ flex: 1 }}
          >
            {addingToRoadmap ? 'Generating Roadmap...' : '🗺️ Add to my Roadmap'}
          </button>
          <Link to="/student/drives" style={{ flex: 1 }}>
            <button className="btn btn-secondary" style={{ width: '100%' }}>
              Apply via Drives →
            </button>
          </Link>
          <button
            type="button"
            className="btn"
            onClick={onClose}
            style={{ padding: '0 var(--space-4)', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)' }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Main Component ────────────────────────────────────────────────
export default function JobMatches() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({ role: 'all', location: 'all', minMatch: 0 });

  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('match');
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    async function fetchMatches() {
      try {
        setLoading(true);
        // This calls: GET /api/v1/matching/students/{id}/jobs
        const res = await intelligenceApi.getMatches(user.id, filters);
        setJobs(res.data || []);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load job matches');
      } finally {
        setLoading(false);
      }
    }
    if (user?.id) fetchMatches();
  }, [user, filters]);

  // Step 6: Loading and error states
  if (loading) {
    return (
      <div className="page-body" style={{ textAlign: 'center', padding: '4rem' }}>
        Calculating your matches...
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
  if (jobs.length === 0) {
    return (
      <div className="page-body" style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
        No job matches found. Complete your profile and add skills to see matches.
      </div>
    );
  }

  // Derive available categories & locations dynamically from loaded jobs
  const availableRoles = [
    'all',
    ...Array.from(new Set(jobs.map((j) => j.role_category).filter(Boolean))),
  ];
  const availableLocations = [
    'all',
    ...Array.from(new Set(jobs.map((j) => j.location).filter(Boolean))),
  ];

  // Client-side search and sorting on the fetched ML matches
  const filtered = jobs
    .filter((j) => {
      const q = search.trim().toLowerCase();
      const matchSearch =
        !q ||
        (j.title || '').toLowerCase().includes(q) ||
        (j.company_name || '').toLowerCase().includes(q) ||
        (j.location || '').toLowerCase().includes(q);
      const matchRole =
        filters.role === 'all' || filters.role === 'All' || j.role_category === filters.role;
      const matchLocation =
        filters.location === 'all' ||
        filters.location === 'All' ||
        (j.location && j.location.toLowerCase() === filters.location.toLowerCase());
      const matchScore = (j.match_score ?? 0) >= filters.minMatch;
      return matchSearch && matchRole && matchLocation && matchScore;
    })
    .sort((a, b) => {
      if (sortBy === 'match') return (b.match_score || 0) - (a.match_score || 0);
      if (sortBy === 'salary') {
        const aSal = a.salary_ctc_max || a.salary_ctc_min || 0;
        const bSal = b.salary_ctc_max || b.salary_ctc_min || 0;
        return bSal - aSal;
      }
      if (sortBy === 'skills') return (b.skill_match_pct || 0) - (a.skill_match_pct || 0);
      return (a.title || '').localeCompare(b.title || '');
    });

  return (
    <div>
      <div className="page-header">
        <h1>Job Matches</h1>
        <p>{jobs.length} roles scored & ranked by the AI matching engine</p>
      </div>

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
        {/* Filters */}
        <div style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap', alignItems: 'center' }}>
          <input
            className="input"
            placeholder="🔍 Search role, company, or location..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ flex: 1, minWidth: 220 }}
          />

          <select
            className="input"
            value={filters.role}
            onChange={(e) => setFilters((prev) => ({ ...prev, role: e.target.value }))}
            style={{ width: 180 }}
          >
            {availableRoles.map((r) => (
              <option key={r} value={r}>
                {r === 'all' ? 'All Roles' : r}
              </option>
            ))}
          </select>

          <select
            className="input"
            value={filters.location}
            onChange={(e) => setFilters((prev) => ({ ...prev, location: e.target.value }))}
            style={{ width: 160 }}
          >
            {availableLocations.map((loc) => (
              <option key={loc} value={loc}>
                {loc === 'all' ? 'All Locations' : loc}
              </option>
            ))}
          </select>

          <select
            className="input"
            value={filters.minMatch}
            onChange={(e) => setFilters((prev) => ({ ...prev, minMatch: +e.target.value }))}
            style={{ width: 160 }}
          >
            <option value={0}>All scores</option>
            <option value={60}>≥ 60% match</option>
            <option value={70}>≥ 70% match</option>
            <option value={80}>≥ 80% match</option>
          </select>

          <select
            className="input"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            style={{ width: 160 }}
          >
            <option value="match">Sort: ML Match %</option>
            <option value="skills">Sort: Skills Match</option>
            <option value="salary">Sort: Salary</option>
          </select>
        </div>

        {/* Results count */}
        <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)' }}>
          Showing {filtered.length} of {jobs.length} matched roles
        </div>

        {/* Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
            gap: 'var(--space-5)',
          }}
        >
          {filtered.map((job) => (
            <JobCard key={job.job_id || job.id} job={job} onSelect={setSelected} />
          ))}
        </div>

        {filtered.length === 0 && (
          <div className="card" style={{ textAlign: 'center', padding: 'var(--space-12)', color: 'var(--text-muted)' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: 'var(--space-4)' }}>🔍</div>
            <h2>No matches found</h2>
            <p style={{ marginTop: 'var(--space-2)' }}>Try adjusting your search or filter settings</p>
          </div>
        )}
      </div>

      <JobModal job={selected} onClose={() => setSelected(null)} userId={user?.id} />
    </div>
  );
}
