/**
 * Job Matches — searchable, filterable grid of matched job roles.
 * Connected to live FastAPI ML matching service.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
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

      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 'var(--space-1)' }}>
        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--accent-primary)', fontWeight: 600 }}>
          View Details & Breakdown →
        </span>
      </div>
    </div>
  );
}

// ─── Detail Modal ──────────────────────────────────────────────────
function JobModal({ job, onClose }) {
  if (!job) return null;

  const matchedSkills = job.matched_skills || [];
  const missingSkills = job.missing_skills || [];

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.65)',
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
          maxWidth: 620,
          maxHeight: '85vh',
          overflowY: 'auto',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-6)' }}>
          <div>
            <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700 }}>{job.title}</h2>
            <div style={{ color: 'var(--text-secondary)', marginTop: 4 }}>
              {job.company_name || job.company} · {job.location || 'Remote'}
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-muted)',
              fontSize: '1.5rem',
              lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>

        {/* Score & Key Stats Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: 'var(--space-3)',
            marginBottom: 'var(--space-6)',
            padding: 'var(--space-4)',
            background: 'var(--bg-tertiary)',
            borderRadius: 'var(--border-radius)',
          }}
        >
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 800, color: matchColor(job.match_score) }}>
              {Math.round(job.match_score)}%
            </div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 2 }}>ML Match</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 800, color: 'var(--accent-primary)' }}>
              {Math.round(job.skill_match_pct || 0)}%
            </div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 2 }}>Skill Overlap</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 'var(--font-size-base)', fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
              {formatSalary(job.salary_ctc_min, job.salary_ctc_max)}
            </div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 2 }}>CTC Package</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div
              style={{
                fontSize: 'var(--font-size-sm)',
                fontWeight: 700,
                color: job.eligible ? '#22c55e' : '#ef4444',
                marginTop: 6,
              }}
            >
              {job.eligible ? 'Eligible' : 'Ineligible'}
            </div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 2 }}>Criteria</div>
          </div>
        </div>

        {/* ML Match Score Explanation */}
        <div
          style={{
            padding: 'var(--space-4)',
            borderRadius: 'var(--border-radius)',
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            marginBottom: 'var(--space-5)',
            fontSize: 'var(--font-size-sm)',
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>🤖</span> <span>ML Matching Engine Insight</span>
          </div>
          <p style={{ margin: 0, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            {job.match_score >= 80
              ? `High-priority alignment (${Math.round(job.match_score)}%): The trained Gradient Boosted model identifies strong synergy between your verified skills, academic performance, and the job requirements.`
              : job.match_score >= 65
              ? `Competitive alignment (${Math.round(job.match_score)}%): You satisfy core prerequisites for this role. Closing the skill gaps below will optimize your candidacy.`
              : `Developing match (${Math.round(job.match_score)}%): There are notable skill disparities for this profile. We recommend reviewing the missing competencies below.`}
          </p>
        </div>

        {/* Eligibility Status with Reason */}
        <div
          style={{
            padding: 'var(--space-4)',
            borderRadius: 'var(--border-radius)',
            background: job.eligible ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)',
            border: `1px solid ${job.eligible ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
            marginBottom: 'var(--space-5)',
          }}
        >
          <div
            style={{
              fontWeight: 600,
              color: job.eligible ? '#22c55e' : '#ef4444',
              marginBottom: 4,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            {job.eligible ? '✓ Placement Eligibility Confirmed' : '⚠️ Eligibility Notice'}
          </div>
          <p style={{ margin: 0, fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            {job.eligible
              ? 'Your current CGPA and department meet or exceed all institutional cutoff requirements set by the recruiter.'
              : 'You do not meet one or more hard constraints (such as minimum CGPA cutoff or eligible department list) configured for this drive.'}
          </p>
        </div>

        {/* Real Matched Skills */}
        <div style={{ marginBottom: 'var(--space-4)' }}>
          <div style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)', color: '#22c55e', marginBottom: 'var(--space-2)' }}>
            ✓ Matched Skills ({matchedSkills.length})
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
            {matchedSkills.length > 0 ? (
              matchedSkills.map((s) => (
                <span
                  key={s}
                  style={{
                    padding: '4px 12px',
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
              ))
            ) : (
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                No direct skill matches detected in your profile.
              </span>
            )}
          </div>
        </div>

        {/* Real Missing Skills */}
        <div style={{ marginBottom: 'var(--space-6)' }}>
          <div style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)', color: 'var(--accent-danger)', marginBottom: 'var(--space-2)' }}>
            ✗ Missing Skills to Acquire ({missingSkills.length})
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
            {missingSkills.length > 0 ? (
              missingSkills.map((s) => (
                <span
                  key={s}
                  style={{
                    padding: '4px 12px',
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
              ))
            ) : (
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                You possess all required skills for this role!
              </span>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
          <Link to="/student/drives" style={{ flex: 1 }}>
            <button className="btn btn-primary" style={{ width: '100%' }}>
              Apply via Drives →
            </button>
          </Link>
          <Link
            to={`/student/skill-gap?role=${encodeURIComponent(job.role_category || job.title)}`}
            style={{ flex: 1 }}
          >
            <button className="btn btn-secondary" style={{ width: '100%' }}>
              View Skill Gap →
            </button>
          </Link>
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

      <JobModal job={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
