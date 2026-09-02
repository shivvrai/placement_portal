/**
 * Job Matches — searchable, filterable grid of matched job roles.
 * Shows match %, required skills, and a detail modal.
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';

// ─── Mock Data ────────────────────────────────────────────────────
const MOCK_JOBS = [
  {
    id: 1, title: 'Data Analyst', company: 'Infosys', location: 'Bangalore',
    match_score: 84, role_category: 'Analytics', salary_ctc: 6.5,
    deadline: '2026-09-15', status: 'open',
    required_skills: ['Python', 'SQL', 'Tableau', 'Statistics', 'Excel'],
    matched_skills: ['Python', 'SQL', 'Excel'],
    description: 'Analyse large datasets to extract actionable business insights. Work with cross-functional teams on dashboards and data pipelines.',
    min_cgpa: 7.0, eligible_depts: ['CS', 'IT', 'ECE'],
  },
  {
    id: 2, title: 'Python Developer', company: 'TCS', location: 'Pune',
    match_score: 79, role_category: 'Engineering', salary_ctc: 7.0,
    deadline: '2026-09-20', status: 'open',
    required_skills: ['Python', 'FastAPI', 'PostgreSQL', 'Docker', 'Git'],
    matched_skills: ['Python', 'Git'],
    description: 'Build RESTful APIs and microservices for enterprise-scale applications using Python and modern frameworks.',
    min_cgpa: 7.5, eligible_depts: ['CS', 'IT'],
  },
  {
    id: 3, title: 'ML Engineer Intern', company: 'Wipro', location: 'Hyderabad',
    match_score: 71, role_category: 'ML / AI', salary_ctc: 4.5,
    deadline: '2026-10-01', status: 'open',
    required_skills: ['Python', 'scikit-learn', 'PyTorch', 'Statistics', 'MLflow'],
    matched_skills: ['Python', 'scikit-learn'],
    description: 'Build and deploy ML models for NLP and computer vision tasks. Collaborate with research team on experimental pipelines.',
    min_cgpa: 7.0, eligible_depts: ['CS', 'IT', 'EEE'],
  },
  {
    id: 4, title: 'Frontend Developer', company: 'Accenture', location: 'Chennai',
    match_score: 65, role_category: 'Engineering', salary_ctc: 5.5,
    deadline: '2026-09-28', status: 'open',
    required_skills: ['React', 'TypeScript', 'CSS', 'REST APIs', 'Git'],
    matched_skills: ['CSS', 'Git'],
    description: 'Develop responsive web applications using React and TypeScript, integrating with backend REST APIs.',
    min_cgpa: 6.5, eligible_depts: ['CS', 'IT', 'ECE'],
  },
  {
    id: 5, title: 'Business Analyst', company: 'Deloitte', location: 'Mumbai',
    match_score: 60, role_category: 'Analytics', salary_ctc: 8.0,
    deadline: '2026-10-10', status: 'open',
    required_skills: ['Excel', 'SQL', 'Power BI', 'Communication', 'Agile'],
    matched_skills: ['Excel', 'SQL', 'Communication'],
    description: 'Translate business requirements into technical specs. Drive data-driven decision-making across business units.',
    min_cgpa: 7.0, eligible_depts: ['CS', 'IT', 'ECE', 'ME'],
  },
  {
    id: 6, title: 'DevOps Engineer', company: 'HCL', location: 'Noida',
    match_score: 52, role_category: 'DevOps', salary_ctc: 6.0,
    deadline: '2026-10-05', status: 'open',
    required_skills: ['Docker', 'Kubernetes', 'CI/CD', 'Linux', 'Terraform'],
    matched_skills: ['Linux'],
    description: 'Maintain and evolve CI/CD pipelines. Manage cloud infrastructure using IaC tools.',
    min_cgpa: 6.5, eligible_depts: ['CS', 'IT'],
  },
  {
    id: 7, title: 'Data Engineer', company: 'Amazon', location: 'Bangalore',
    match_score: 68, role_category: 'Data Engineering', salary_ctc: 9.5,
    deadline: '2026-09-25', status: 'open',
    required_skills: ['Python', 'Spark', 'SQL', 'AWS', 'Airflow'],
    matched_skills: ['Python', 'SQL'],
    description: 'Design and build scalable data pipelines on AWS. Work with petabyte-scale datasets.',
    min_cgpa: 7.5, eligible_depts: ['CS', 'IT'],
  },
  {
    id: 8, title: 'Full Stack Developer', company: 'Freshworks', location: 'Chennai',
    match_score: 73, role_category: 'Engineering', salary_ctc: 8.5,
    deadline: '2026-09-30', status: 'open',
    required_skills: ['React', 'Node.js', 'MongoDB', 'REST APIs', 'TypeScript'],
    matched_skills: ['React', 'REST APIs'],
    description: 'Build product features end-to-end across the frontend and backend. Ship fast with quality.',
    min_cgpa: 7.0, eligible_depts: ['CS', 'IT'],
  },
];

const CATEGORIES = ['All', 'Analytics', 'Engineering', 'ML / AI', 'DevOps', 'Data Engineering'];

const matchColor = (score) =>
  score >= 80 ? '#22c55e' : score >= 65 ? '#f59e0b' : '#ef4444';

const matchBg = (score) =>
  score >= 80 ? 'rgba(34,197,94,0.1)' : score >= 65 ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)';

// ─── Job Card ──────────────────────────────────────────────────────
function JobCard({ job, onSelect }) {
  return (
    <div
      className="card"
      onClick={() => onSelect(job)}
      style={{ cursor: 'pointer', transition: 'all var(--transition-normal)', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 'var(--font-size-base)' }}>{job.title}</div>
          <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', marginTop: 2 }}>
            {job.company} · {job.location}
          </div>
        </div>
        <div style={{
          minWidth: 52, height: 52, borderRadius: '50%',
          background: matchBg(job.match_score),
          border: `2px solid ${matchColor(job.match_score)}`,
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        }}>
          <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 800, color: matchColor(job.match_score) }}>
            {job.match_score}%
          </div>
          <div style={{ fontSize: 9, color: matchColor(job.match_score) }}>match</div>
        </div>
      </div>

      {/* Meta */}
      <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
        <span className="badge badge-primary">{job.role_category}</span>
        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
          💰 ₹{job.salary_ctc}L CTC
        </span>
        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
          📅 Deadline: {job.deadline}
        </span>
      </div>

      {/* Match progress bar */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: 4 }}>
          <span>Skills matched: {job.matched_skills.length}/{job.required_skills.length}</span>
        </div>
        <div style={{ height: 4, background: 'var(--bg-tertiary)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{
            width: `${(job.matched_skills.length / job.required_skills.length) * 100}%`,
            height: '100%', background: matchColor(job.match_score), borderRadius: 2,
          }} />
        </div>
      </div>

      {/* Skill pills */}
      <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
        {job.required_skills.slice(0, 4).map(s => (
          <span key={s} style={{
            padding: '2px 8px', borderRadius: 999,
            fontSize: 'var(--font-size-xs)', fontWeight: 500,
            background: job.matched_skills.includes(s) ? 'rgba(34,197,94,0.12)' : 'var(--bg-tertiary)',
            color: job.matched_skills.includes(s) ? '#22c55e' : 'var(--text-muted)',
            border: `1px solid ${job.matched_skills.includes(s) ? 'rgba(34,197,94,0.3)' : 'var(--border-color)'}`,
          }}>
            {job.matched_skills.includes(s) ? '✓ ' : ''}{s}
          </span>
        ))}
        {job.required_skills.length > 4 && (
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', alignSelf: 'center' }}>
            +{job.required_skills.length - 4} more
          </span>
        )}
      </div>
    </div>
  );
}

// ─── Detail Modal ──────────────────────────────────────────────────
function JobModal({ job, onClose }) {
  if (!job) return null;
  return (
    <div
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 1000,
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'var(--space-6)',
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'var(--bg-card)', border: '1px solid var(--border-color)',
          borderRadius: 'var(--border-radius-lg)', padding: 'var(--space-8)',
          width: '100%', maxWidth: 580, maxHeight: '80vh', overflowY: 'auto',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Modal header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-6)' }}>
          <div>
            <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700 }}>{job.title}</h2>
            <div style={{ color: 'var(--text-secondary)', marginTop: 4 }}>{job.company} · {job.location}</div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '1.5rem', lineHeight: 1 }}
          >×</button>
        </div>

        {/* Score */}
        <div style={{
          display: 'flex', gap: 'var(--space-4)', marginBottom: 'var(--space-6)',
          padding: 'var(--space-4)', background: 'var(--bg-tertiary)', borderRadius: 'var(--border-radius)',
        }}>
          <div style={{ textAlign: 'center', flex: 1 }}>
            <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 800, color: matchColor(job.match_score) }}>{job.match_score}%</div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>Match Score</div>
          </div>
          <div style={{ textAlign: 'center', flex: 1 }}>
            <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 800, color: 'var(--accent-primary)' }}>₹{job.salary_ctc}L</div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>CTC</div>
          </div>
          <div style={{ textAlign: 'center', flex: 1 }}>
            <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 800, color: 'var(--accent-warning)' }}>{job.min_cgpa}</div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>Min CGPA</div>
          </div>
        </div>

        {/* Description */}
        <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-5)', lineHeight: 1.7 }}>
          {job.description}
        </p>

        {/* Skills */}
        <div style={{ marginBottom: 'var(--space-5)' }}>
          <div style={{ fontWeight: 600, marginBottom: 'var(--space-3)' }}>Required Skills</div>
          <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
            {job.required_skills.map(s => (
              <span key={s} style={{
                padding: '4px 12px', borderRadius: 999, fontSize: 'var(--font-size-xs)', fontWeight: 500,
                background: job.matched_skills.includes(s) ? 'rgba(34,197,94,0.12)' : 'rgba(239,68,68,0.08)',
                color: job.matched_skills.includes(s) ? '#22c55e' : 'var(--accent-danger)',
                border: `1px solid ${job.matched_skills.includes(s) ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.2)'}`,
              }}>
                {job.matched_skills.includes(s) ? '✓' : '✗'} {s}
              </span>
            ))}
          </div>
        </div>

        {/* Eligibility */}
        <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)', marginBottom: 'var(--space-6)' }}>
          <span style={{ fontWeight: 500, color: 'var(--text-secondary)' }}>Eligible depts: </span>
          {job.eligible_depts.join(', ')} &nbsp;·&nbsp;
          <span style={{ fontWeight: 500, color: 'var(--text-secondary)' }}>Deadline: </span>
          {job.deadline}
        </div>

        {/* CTAs */}
        <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
          <Link to="/student/drives" style={{ flex: 1 }}>
            <button className="btn btn-primary" style={{ width: '100%' }}>Apply via Drives →</button>
          </Link>
          <Link to="/student/skill-gap" style={{ flex: 1 }}>
            <button className="btn btn-secondary" style={{ width: '100%' }}>See Skill Gaps</button>
          </Link>
        </div>
      </div>
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────
export default function JobMatches() {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('All');
  const [minMatch, setMinMatch] = useState(0);
  const [sortBy, setSortBy] = useState('match');
  const [selected, setSelected] = useState(null);

  const filtered = MOCK_JOBS
    .filter(j =>
      (category === 'All' || j.role_category === category) &&
      j.match_score >= minMatch &&
      (j.title.toLowerCase().includes(search.toLowerCase()) ||
       j.company.toLowerCase().includes(search.toLowerCase()))
    )
    .sort((a, b) =>
      sortBy === 'match' ? b.match_score - a.match_score :
      sortBy === 'salary' ? b.salary_ctc - a.salary_ctc :
      a.deadline.localeCompare(b.deadline)
    );

  return (
    <div>
      <div className="page-header">
        <h1>Job Matches</h1>
        <p>{MOCK_JOBS.length} roles matched to your skill profile</p>
      </div>

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>

        {/* Filters */}
        <div style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap', alignItems: 'center' }}>
          <input
            className="input"
            placeholder="🔍 Search role or company..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ flex: 1, minWidth: 220 }}
          />

          <select
            className="input"
            value={category}
            onChange={e => setCategory(e.target.value)}
            style={{ width: 180 }}
          >
            {CATEGORIES.map(c => <option key={c}>{c}</option>)}
          </select>

          <select
            className="input"
            value={minMatch}
            onChange={e => setMinMatch(+e.target.value)}
            style={{ width: 160 }}
          >
            <option value={0}>All scores</option>
            <option value={70}>≥ 70% match</option>
            <option value={80}>≥ 80% match</option>
          </select>

          <select
            className="input"
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            style={{ width: 150 }}
          >
            <option value="match">Sort: Match %</option>
            <option value="salary">Sort: Salary</option>
            <option value="deadline">Sort: Deadline</option>
          </select>
        </div>

        {/* Results count */}
        <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)' }}>
          Showing {filtered.length} of {MOCK_JOBS.length} roles
        </div>

        {/* Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 'var(--space-5)' }}>
          {filtered.map(job => (
            <JobCard key={job.id} job={job} onSelect={setSelected} />
          ))}
        </div>

        {filtered.length === 0 && (
          <div className="card" style={{ textAlign: 'center', padding: 'var(--space-12)', color: 'var(--text-muted)' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: 'var(--space-4)' }}>🔍</div>
            <h2>No matches found</h2>
            <p style={{ marginTop: 'var(--space-2)' }}>Try adjusting your filters</p>
          </div>
        )}
      </div>

      <JobModal job={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
