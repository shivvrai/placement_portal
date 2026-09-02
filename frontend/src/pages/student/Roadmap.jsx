/**
 * Career Roadmap — phase-based learning plan with task tracking.
 * Phases: Foundation → Core Skills → Projects → Placement Prep
 * Tasks are expandable with status toggles.
 */

import { useState } from 'react';

// ─── Mock Data ────────────────────────────────────────────────────
const TARGET_ROLES = ['Data Analyst', 'Python Developer', 'ML Engineer', 'Full Stack Developer'];

const ROADMAP_DATA = {
  'Data Analyst': {
    target_role: 'Data Analyst',
    total_weeks: 12,
    progress_pct: 38,
    phases: [
      {
        id: 1, title: 'Foundation', icon: '🧱', weeks: '1–3',
        color: '#6366f1', status: 'completed',
        tasks: [
          { id: 't1', title: 'Python fundamentals & data types', hours: 8, status: 'completed', resource: 'Python for Everybody (Coursera)', difficulty: 'beginner' },
          { id: 't2', title: 'SQL: SELECT, JOIN, aggregation', hours: 6, status: 'completed', resource: 'Mode Analytics SQL Tutorial', difficulty: 'beginner' },
          { id: 't3', title: 'Excel: pivot tables, VLOOKUP, charting', hours: 4, status: 'completed', resource: 'Excel Skills for Business (Coursera)', difficulty: 'beginner' },
        ],
      },
      {
        id: 2, title: 'Core Skills', icon: '🔬', weeks: '4–7',
        color: '#06b6d4', status: 'in_progress',
        tasks: [
          { id: 't4', title: 'Pandas & NumPy for data wrangling', hours: 10, status: 'completed', resource: 'Kaggle: Pandas Course', difficulty: 'intermediate' },
          { id: 't5', title: 'Statistics & probability fundamentals', hours: 12, status: 'in_progress', resource: 'Khan Academy Statistics', difficulty: 'intermediate' },
          { id: 't6', title: 'Data visualization with Matplotlib & Seaborn', hours: 6, status: 'pending', resource: 'Python Data Visualization (DataCamp)', difficulty: 'intermediate' },
          { id: 't7', title: 'Tableau / Power BI basics', hours: 8, status: 'pending', resource: 'Tableau Public Tutorials', difficulty: 'intermediate' },
        ],
      },
      {
        id: 3, title: 'Projects', icon: '🚀', weeks: '8–10',
        color: '#8b5cf6', status: 'pending',
        tasks: [
          { id: 't8', title: 'End-to-end EDA on Kaggle dataset', hours: 15, status: 'pending', resource: 'Kaggle Competitions', difficulty: 'intermediate' },
          { id: 't9', title: 'Build a Tableau dashboard for HR data', hours: 10, status: 'pending', resource: 'Public dataset: HR Analytics', difficulty: 'intermediate' },
          { id: 't10', title: 'SQL case study: E-commerce analysis', hours: 8, status: 'pending', resource: 'StrataScratch SQL Practice', difficulty: 'advanced' },
        ],
      },
      {
        id: 4, title: 'Placement Prep', icon: '🎯', weeks: '11–12',
        color: '#f59e0b', status: 'pending',
        tasks: [
          { id: 't11', title: 'Resume tailoring for data roles', hours: 3, status: 'pending', resource: 'CCIP Profile Builder', difficulty: 'beginner' },
          { id: 't12', title: 'Mock interviews: SQL & case studies', hours: 8, status: 'pending', resource: 'Pramp, Interviewing.io', difficulty: 'advanced' },
          { id: 't13', title: 'Apply to shortlisted companies', hours: 4, status: 'pending', resource: 'CCIP Placement Drives', difficulty: 'beginner' },
        ],
      },
    ],
  },
  'Python Developer': {
    target_role: 'Python Developer',
    total_weeks: 14,
    progress_pct: 22,
    phases: [
      {
        id: 1, title: 'Foundation', icon: '🧱', weeks: '1–3',
        color: '#6366f1', status: 'completed',
        tasks: [
          { id: 't1', title: 'Python OOP & design patterns', hours: 10, status: 'completed', resource: 'Python OOP (Udemy)', difficulty: 'beginner' },
          { id: 't2', title: 'Git & GitHub workflow', hours: 4, status: 'completed', resource: 'Pro Git (free book)', difficulty: 'beginner' },
          { id: 't3', title: 'Linux command line basics', hours: 4, status: 'in_progress', resource: 'Linux Journey', difficulty: 'beginner' },
        ],
      },
      {
        id: 2, title: 'Core Skills', icon: '🔬', weeks: '4–9',
        color: '#06b6d4', status: 'in_progress',
        tasks: [
          { id: 't4', title: 'FastAPI: routing, Pydantic, auth', hours: 12, status: 'pending', resource: 'FastAPI Official Docs', difficulty: 'intermediate' },
          { id: 't5', title: 'PostgreSQL: schema design, indexing', hours: 8, status: 'pending', resource: 'PostgreSQL Tutorial', difficulty: 'intermediate' },
          { id: 't6', title: 'Docker & containerization', hours: 10, status: 'pending', resource: 'Docker for Developers (Udemy)', difficulty: 'intermediate' },
          { id: 't7', title: 'Writing tests with pytest', hours: 6, status: 'pending', resource: 'Test-Driven Development with Python', difficulty: 'intermediate' },
        ],
      },
      {
        id: 3, title: 'Projects', icon: '🚀', weeks: '10–12',
        color: '#8b5cf6', status: 'pending',
        tasks: [
          { id: 't8', title: 'Build a REST API with FastAPI + Postgres', hours: 20, status: 'pending', resource: 'GitHub starter template', difficulty: 'advanced' },
          { id: 't9', title: 'Dockerize and deploy on Railway', hours: 6, status: 'pending', resource: 'Railway.app docs', difficulty: 'intermediate' },
        ],
      },
      {
        id: 4, title: 'Placement Prep', icon: '🎯', weeks: '13–14',
        color: '#f59e0b', status: 'pending',
        tasks: [
          { id: 't10', title: 'LeetCode: Python DSA (50 problems)', hours: 15, status: 'pending', resource: 'LeetCode', difficulty: 'advanced' },
          { id: 't11', title: 'System design primer', hours: 8, status: 'pending', resource: 'System Design Primer (GitHub)', difficulty: 'advanced' },
        ],
      },
    ],
  },
};

const STATUS_CONFIG = {
  completed:   { label: 'Done',        color: '#22c55e', bg: 'rgba(34,197,94,0.15)',    icon: '✓' },
  in_progress: { label: 'In Progress', color: '#f59e0b', bg: 'rgba(245,158,11,0.15)',   icon: '◎' },
  pending:     { label: 'Pending',     color: 'var(--text-muted)', bg: 'var(--bg-tertiary)', icon: '○' },
};

const NEXT_STATUS = {
  pending: 'in_progress',
  in_progress: 'completed',
  completed: 'pending',
};

const DIFF_COLORS = {
  beginner:     '#22c55e',
  intermediate: '#f59e0b',
  advanced:     '#ef4444',
};

// ─── Phase Card ────────────────────────────────────────────────────
function PhaseCard({ phase, onToggleTask }) {
  const [expanded, setExpanded] = useState(phase.status === 'in_progress');
  const done = phase.tasks.filter(t => t.status === 'completed').length;
  const phasePct = Math.round((done / phase.tasks.length) * 100);
  const cfg = STATUS_CONFIG[phase.status];

  return (
    <div style={{
      border: `1px solid ${phase.status === 'in_progress' ? phase.color + '50' : 'var(--border-color)'}`,
      borderRadius: 'var(--border-radius)',
      background: 'var(--bg-card)',
      overflow: 'hidden',
      boxShadow: phase.status === 'in_progress' ? `0 0 20px ${phase.color}18` : 'none',
    }}>
      {/* Phase header */}
      <div
        style={{
          display: 'flex', alignItems: 'center', gap: 'var(--space-4)',
          padding: 'var(--space-5) var(--space-6)',
          cursor: 'pointer',
          borderLeft: `4px solid ${phase.color}`,
        }}
        onClick={() => setExpanded(e => !e)}
      >
        <div style={{ fontSize: '1.6rem' }}>{phase.icon}</div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <div style={{ fontWeight: 700, fontSize: 'var(--font-size-base)' }}>{phase.title}</div>
            <span style={{
              padding: '2px 10px', borderRadius: 999,
              fontSize: 'var(--font-size-xs)', fontWeight: 600,
              background: cfg.bg, color: cfg.color,
            }}>
              {cfg.icon} {cfg.label}
            </span>
          </div>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 2 }}>
            Weeks {phase.weeks} · {done}/{phase.tasks.length} tasks · ~{phase.tasks.reduce((s, t) => s + t.hours, 0)}h total
          </div>
        </div>
        {/* Mini progress */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <div style={{
            width: 80, height: 6, background: 'var(--bg-tertiary)', borderRadius: 3, overflow: 'hidden',
          }}>
            <div style={{ width: `${phasePct}%`, height: '100%', background: phase.color, borderRadius: 3 }} />
          </div>
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', width: 32 }}>{phasePct}%</span>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', transition: 'transform 0.2s', transform: expanded ? 'rotate(180deg)' : '' }}>▼</span>
        </div>
      </div>

      {/* Tasks */}
      {expanded && (
        <div style={{ borderTop: '1px solid var(--border-color)' }}>
          {phase.tasks.map((task, idx) => {
            const tc = STATUS_CONFIG[task.status];
            return (
              <div
                key={task.id}
                style={{
                  display: 'flex', alignItems: 'flex-start', gap: 'var(--space-4)',
                  padding: 'var(--space-4) var(--space-6)',
                  borderBottom: idx < phase.tasks.length - 1 ? '1px solid var(--border-color)' : 'none',
                  background: task.status === 'in_progress' ? 'rgba(245,158,11,0.04)' : 'transparent',
                  transition: 'background 0.2s',
                }}
              >
                {/* Status toggle */}
                <button
                  onClick={() => onToggleTask(phase.id, task.id)}
                  title="Click to change status"
                  style={{
                    width: 28, height: 28, borderRadius: '50%', border: `2px solid ${tc.color}`,
                    background: task.status === 'completed' ? tc.color : 'transparent',
                    color: task.status === 'completed' ? 'white' : tc.color,
                    cursor: 'pointer', fontSize: '0.75rem', fontWeight: 700,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0, transition: 'all 0.2s', marginTop: 2,
                  }}
                >
                  {tc.icon}
                </button>

                {/* Task info */}
                <div style={{ flex: 1 }}>
                  <div style={{
                    fontWeight: 500, fontSize: 'var(--font-size-sm)',
                    textDecoration: task.status === 'completed' ? 'line-through' : 'none',
                    color: task.status === 'completed' ? 'var(--text-muted)' : 'var(--text-primary)',
                  }}>
                    {task.title}
                  </div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 2, display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
                    <span>📚 {task.resource}</span>
                    <span>⏱ {task.hours}h</span>
                    <span style={{ color: DIFF_COLORS[task.difficulty] }}>● {task.difficulty}</span>
                  </div>
                </div>

                <span style={{
                  fontSize: 'var(--font-size-xs)', padding: '2px 8px', borderRadius: 999,
                  background: tc.bg, color: tc.color, fontWeight: 600, flexShrink: 0,
                }}>
                  {tc.label}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────
export default function Roadmap() {
  const [role, setRole] = useState('Data Analyst');

  const baseData = ROADMAP_DATA[role] || ROADMAP_DATA['Data Analyst'];
  const [roadmap, setRoadmap] = useState(baseData);

  const handleRoleChange = (r) => {
    setRole(r);
    setRoadmap(ROADMAP_DATA[r] || ROADMAP_DATA['Data Analyst']);
  };

  const handleToggleTask = (phaseId, taskId) => {
    setRoadmap(prev => ({
      ...prev,
      phases: prev.phases.map(p =>
        p.id !== phaseId ? p : {
          ...p,
          tasks: p.tasks.map(t =>
            t.id !== taskId ? t : { ...t, status: NEXT_STATUS[t.status] }
          ),
        }
      ),
    }));
  };

  const totalTasks = roadmap.phases.reduce((s, p) => s + p.tasks.length, 0);
  const doneTasks = roadmap.phases.reduce((s, p) => s + p.tasks.filter(t => t.status === 'completed').length, 0);
  const progress = Math.round((doneTasks / totalTasks) * 100);
  const totalHours = roadmap.phases.reduce((s, p) => s + p.tasks.reduce((ss, t) => ss + t.hours, 0), 0);

  return (
    <div>
      <div className="page-header">
        <h1>Career Roadmap</h1>
        <p>Your personalised week-by-week plan to placement readiness</p>
      </div>

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>

        {/* Role selector */}
        <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)', alignSelf: 'center' }}>Target role:</span>
          {TARGET_ROLES.map(r => (
            <button
              key={r}
              onClick={() => handleRoleChange(r)}
              className={`btn ${role === r ? 'btn-primary' : 'btn-secondary'}`}
              style={{ height: 36, fontSize: 'var(--font-size-sm)' }}
            >
              {r}
            </button>
          ))}
        </div>

        {/* Overview stats */}
        <div className="stat-grid">
          <div className="stat-card">
            <div className="stat-card-label">Overall Progress</div>
            <div className="stat-card-value">{progress}<span style={{ fontSize: 'var(--font-size-lg)', WebkitTextFillColor: 'inherit' }}>%</span></div>
            <div style={{ marginTop: 'var(--space-3)', height: 6, background: 'var(--bg-tertiary)', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{ width: `${progress}%`, height: '100%', background: 'var(--gradient-accent)', borderRadius: 3 }} />
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Tasks Completed</div>
            <div className="stat-card-value">{doneTasks}<span style={{ fontSize: 'var(--font-size-lg)', WebkitTextFillColor: 'inherit' }}>/{totalTasks}</span></div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Total Duration</div>
            <div className="stat-card-value">{roadmap.total_weeks}<span style={{ fontSize: 'var(--font-size-lg)', WebkitTextFillColor: 'inherit' }}> wks</span></div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Estimated Effort</div>
            <div className="stat-card-value">{totalHours}<span style={{ fontSize: 'var(--font-size-lg)', WebkitTextFillColor: 'inherit' }}> hrs</span></div>
          </div>
        </div>

        {/* Phase timeline */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {roadmap.phases.map(phase => (
            <PhaseCard key={phase.id} phase={phase} onToggleTask={handleToggleTask} />
          ))}
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', gap: 'var(--space-6)', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
          <span>Click the circle to cycle task status:</span>
          {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
            <span key={key} style={{ color: cfg.color }}>{cfg.icon} {cfg.label}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
