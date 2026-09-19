/**
 * Career Roadmap — phase-based learning plan with task tracking.
 * Phases: Foundation → Core Skills → Projects → Placement Prep
 * Tasks are expandable with status toggles.
 */

import { useState, useEffect, useMemo } from 'react';
import { intelligenceApi } from '../../api/endpoints';

// ─── Target Roles ──────────────────────────────────────────────────
const TARGET_ROLES = ['Data Analyst', 'Software Engineer', 'ML Engineer'];

const STATUS_CONFIG = {
  completed: {
    label: 'Done',
    color: '#22c55e',
    bg: 'rgba(34,197,94,0.15)',
    icon: '✓'
  },
  in_progress: {
    label: 'In Progress',
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.15)',
    icon: '◎'
  },
  pending: {
    label: 'Pending',
    color: 'var(--text-muted)',
    bg: 'var(--bg-tertiary)',
    icon: '○'
  },
};

const NEXT_STATUS = {
  pending: 'in_progress',
  in_progress: 'completed',
  completed: 'pending',
};

const PHASE_CONFIG = [
  {
    id: 1,
    title: 'Foundation',
    icon: '🧱',
    start: 1,
    end: 3,
    color: '#6366f1',
  },
  {
    id: 2,
    title: 'Core Skills',
    icon: '🔬',
    start: 4,
    end: 7,
    color: '#06b6d4',
  },
  {
    id: 3,
    title: 'Projects',
    icon: '🚀',
    start: 8,
    end: 10,
    color: '#8b5cf6',
  },
  {
    id: 4,
    title: 'Placement Prep',
    icon: '🎯',
    start: 11,
    end: 12,
    color: '#f59e0b',
  },
];

// ─── Convert backend roadmap to existing phase UI ───────────────────
function mapRoadmapToPhases(data) {
  if (!data) return null;

  const phases = PHASE_CONFIG.map(config => {
    const tasks = data.tasks
      .filter(
        task =>
          task.week_number >= config.start &&
          task.week_number <= config.end
      )
      .sort((a, b) => {
        if (a.week_number !== b.week_number) {
          return a.week_number - b.week_number;
        }
        return a.order_in_week - b.order_in_week;
      })
      .map(task => {
        let meta = null;
        let cleanDesc = task.description || '';
        const match = cleanDesc.match(/<!-- REMEDIATION_META:(.*?) -->/);
        if (match) {
          try {
            meta = JSON.parse(match[1]);
            cleanDesc = cleanDesc.replace(match[0], '').trim();
          } catch(e) {}
        }
        return {
          id: task.id,
          title: task.title,
          description: cleanDesc,
          meta: meta,
          isRemedial: !!meta,
          hours: task.estimated_hours || 0,
          status: task.status,
          week_number: task.week_number,
        };
      });

    const done = tasks.filter(
      task => task.status === 'completed'
    ).length;

    let status = 'pending';

    if (tasks.length > 0 && done === tasks.length) {
      status = 'completed';
    } else if (tasks.some(task => task.status === 'in_progress')) {
      status = 'in_progress';
    } else if (tasks.some(task => task.status === 'completed')) {
      status = 'in_progress';
    }

    return {
      ...config,
      weeks: `${config.start}–${config.end}`,
      status,
      tasks,
    };
  }).filter(phase => phase.tasks.length > 0);

  return {
    ...data,
    phases,
  };
}

// ─── Phase Card ────────────────────────────────────────────────────
function PhaseCard({ phase, onToggleTask }) {
  const [expanded, setExpanded] = useState(phase.status === 'in_progress');

  const done = phase.tasks.filter(
    t => t.status === 'completed'
  ).length;

  const phasePct = phase.tasks.length
    ? Math.round((done / phase.tasks.length) * 100)
    : 0;

  const cfg = STATUS_CONFIG[phase.status] || STATUS_CONFIG.pending;

  return (
    <div style={{
      border: `1px solid ${
        phase.status === 'in_progress'
          ? phase.color + '50'
          : 'var(--border-color)'
      }`,
      borderRadius: 'var(--border-radius)',
      background: 'var(--bg-card)',
      overflow: 'hidden',
      boxShadow: phase.status === 'in_progress'
        ? `0 0 20px ${phase.color}18`
        : 'none',
    }}>
      {/* Phase header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-4)',
          padding: 'var(--space-5) var(--space-6)',
          cursor: 'pointer',
          borderLeft: `4px solid ${phase.color}`,
        }}
        onClick={() => setExpanded(e => !e)}
      >
        <div style={{ fontSize: '1.6rem' }}>
          {phase.icon}
        </div>

        <div style={{ flex: 1 }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-3)'
          }}>
            <div style={{
              fontWeight: 700,
              fontSize: 'var(--font-size-base)'
            }}>
              {phase.title}
            </div>

            <span style={{
              padding: '2px 10px',
              borderRadius: 999,
              fontSize: 'var(--font-size-xs)',
              fontWeight: 600,
              background: cfg.bg,
              color: cfg.color,
            }}>
              {cfg.icon} {cfg.label}
            </span>
          </div>

          <div style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--text-muted)',
            marginTop: 2
          }}>
            Weeks {phase.weeks} · {done}/{phase.tasks.length} tasks · ~
            {phase.tasks.reduce((s, t) => s + t.hours, 0)}h total
          </div>
        </div>

        {/* Mini progress */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-3)'
        }}>
          <div style={{
            width: 80,
            height: 6,
            background: 'var(--bg-tertiary)',
            borderRadius: 3,
            overflow: 'hidden',
          }}>
            <div style={{
              width: `${phasePct}%`,
              height: '100%',
              background: phase.color,
              borderRadius: 3
            }} />
          </div>

          <span style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--text-muted)',
            width: 32
          }}>
            {phasePct}%
          </span>

          <span style={{
            color: 'var(--text-muted)',
            fontSize: '0.75rem',
            transition: 'transform 0.2s',
            transform: expanded ? 'rotate(180deg)' : ''
          }}>
            ▼
          </span>
        </div>
      </div>

      {/* Tasks */}
      {expanded && (
        <div style={{
          borderTop: '1px solid var(--border-color)'
        }}>
          {phase.tasks.map((task, idx) => {
            const tc =
              STATUS_CONFIG[task.status] || STATUS_CONFIG.pending;

            return (
              <div
                key={task.id}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 'var(--space-4)',
                  padding: 'var(--space-4) var(--space-6)',
                  borderBottom:
                    idx < phase.tasks.length - 1
                      ? '1px solid var(--border-color)'
                      : 'none',
                  background:
                    task.status === 'in_progress'
                      ? 'rgba(245,158,11,0.04)'
                      : task.isRemedial
                        ? 'rgba(245,158,11,0.06)'
                        : 'transparent',
                  transition: 'background 0.2s',
                }}
              >
                {/* Status toggle */}
                <button
                  onClick={() => onToggleTask(task.id, task.status)}
                  title="Click to change status"
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: '50%',
                    border: `2px solid ${tc.color}`,
                    background:
                      task.status === 'completed'
                        ? tc.color
                        : 'transparent',
                    color:
                      task.status === 'completed'
                        ? 'white'
                        : tc.color,
                    cursor: 'pointer',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    transition: 'all 0.2s',
                    marginTop: 2,
                  }}
                >
                  {tc.icon}
                </button>

                {/* Task info */}
                <div style={{ flex: 1 }}>
                  <div style={{
                    fontWeight: 500,
                    fontSize: 'var(--font-size-sm)',
                    textDecoration:
                      task.status === 'completed'
                        ? 'line-through'
                        : 'none',
                    color:
                      task.status === 'completed'
                        ? 'var(--text-muted)'
                        : task.isRemedial
                          ? '#d97706' // amber/orange for remediation
                          : 'var(--text-primary)',
                  }}>
                    {task.isRemedial && <span style={{ marginRight: 6 }} title="Quiz Remediation Task">🎯</span>}
                    {task.title}
                  </div>

                  {task.description && (
                    <div style={{
                      fontSize: 'var(--font-size-xs)',
                      color: 'var(--text-muted)',
                      marginTop: 4,
                      lineHeight: 1.4
                    }}>
                      {task.description}
                    </div>
                  )}

                  {task.isRemedial && task.meta && (
                    <div style={{ marginTop: 8, padding: '8px 12px', background: 'rgba(245,158,11,0.1)', borderRadius: 6, border: '1px solid rgba(245,158,11,0.2)' }}>
                      <div style={{ fontSize: '0.8rem', color: '#b45309', marginBottom: 4 }}>
                        <strong>Triggered by:</strong> {task.meta.assessment_topic} Assessment (Score: {Math.round(task.meta.assessment_score * 100)}%)
                      </div>
                      {task.meta.resources && task.meta.resources.length > 0 && (
                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
                          {task.meta.resources.map((res, i) => (
                            <a
                              key={i}
                              href={res.url}
                              target="_blank"
                              rel="noreferrer"
                              style={{
                                fontSize: '0.75rem', padding: '4px 8px', background: 'white', border: '1px solid #fcd34d',
                                borderRadius: 4, color: '#d97706', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4
                              }}
                            >
                              {res.type === 'tool' ? '🛠' : res.type === 'article' ? '📄' : '💻'} {res.title}
                            </a>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  <div style={{
                    fontSize: 'var(--font-size-xs)',
                    color: 'var(--text-muted)',
                    marginTop: 2,
                    display: 'flex',
                    gap: 'var(--space-3)',
                    flexWrap: 'wrap'
                  }}>
                    <span>📅 Week {task.week_number}</span>
                    <span>⏱ {task.hours}h</span>
                  </div>
                </div>

                <span style={{
                  fontSize: 'var(--font-size-xs)',
                  padding: '2px 8px',
                  borderRadius: 999,
                  background: tc.bg,
                  color: tc.color,
                  fontWeight: 600,
                  flexShrink: 0,
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

// ─── Main ──────────────────────────────────────────────────────────
export default function Roadmap() {
  const [role, setRole] = useState('Data Analyst');
  const [rawRoadmap, setRawRoadmap] = useState(null);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  const roadmap = useMemo(() => {
    if (!rawRoadmap) return null;
    let filteredData = { ...rawRoadmap, tasks: rawRoadmap.tasks };
    if (filter === 'regular') {
      filteredData.tasks = filteredData.tasks.filter(t => !(t.description || '').includes('REMEDIATION_META'));
    } else if (filter === 'remediation') {
      filteredData.tasks = filteredData.tasks.filter(t => (t.description || '').includes('REMEDIATION_META'));
    }
    return mapRoadmapToPhases(filteredData);
  }, [rawRoadmap, filter]);

  // Fetch existing roadmap
  useEffect(() => {
    const loadRoadmap = async () => {
      try {
        setLoading(true);
        const response = await intelligenceApi.getRoadmap();

        if (response.data) {
          setRole(response.data.target_role);
          setRawRoadmap(response.data);
        }
      } catch (err) {
        console.error('Failed to load roadmap:', err);
        setError('Failed to load roadmap.');
      } finally {
        setLoading(false);
      }
    };

    loadRoadmap();
  }, []);

  // Generate roadmap
  const handleGenerateRoadmap = async () => {
    try {
      setGenerating(true);
      setError('');

      const response =
        await intelligenceApi.generateRoadmap(role);

      setRawRoadmap(response.data);
      setFilter('all');
    } catch (err) {
      console.error('Failed to generate roadmap:', err);
      setError('Failed to generate roadmap.');
    } finally {
      setGenerating(false);
    }
  };

  // Update task status
  const handleToggleTask = async (taskId, currentStatus) => {
    const nextStatus = NEXT_STATUS[currentStatus];

    try {
      await intelligenceApi.updateTask(taskId, nextStatus);

      setRawRoadmap(prev => ({
        ...prev,
        tasks: prev.tasks.map(task =>
          task.id === taskId ? { ...task, status: nextStatus } : task
        ),
      }));
    } catch (err) {
      console.error('Failed to update task:', err);
      setError('Failed to update task status.');
    }
  };

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <h1>Career Roadmap</h1>
          <p>Your personalised week-by-week plan to placement readiness</p>
        </div>

        <div className="page-body">
          <p>Loading roadmap...</p>
        </div>
      </div>
    );
  }

  const totalTasks = roadmap
    ? roadmap.phases.reduce(
        (s, p) => s + p.tasks.length,
        0
      )
    : 0;

  const doneTasks = roadmap
    ? roadmap.phases.reduce(
        (s, p) =>
          s +
          p.tasks.filter(
            t => t.status === 'completed'
          ).length,
        0
      )
    : 0;

  const progress = roadmap
    ? roadmap.progress_pct
    : 0;

  const totalHours = roadmap
    ? roadmap.phases.reduce(
        (s, p) =>
          s +
          p.tasks.reduce(
            (ss, t) => ss + t.hours,
            0
          ),
        0
      )
    : 0;

  return (
    <div>
      <div className="page-header">
        <h1>Career Roadmap</h1>
        <p>
          Your personalised week-by-week plan to placement readiness
        </p>
      </div>

      <div
        className="page-body"
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-6)'
        }}
      >
        {/* Role selector */}
        <div style={{
          display: 'flex',
          gap: 'var(--space-3)',
          flexWrap: 'wrap',
          alignItems: 'center'
        }}>
          <span style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--text-muted)',
            alignSelf: 'center'
          }}>
            Target role:
          </span>

          {TARGET_ROLES.map(r => (
            <button
              key={r}
              onClick={() => setRole(r)}
              className={`btn ${
                role === r
                  ? 'btn-primary'
                  : 'btn-secondary'
              }`}
              style={{
                height: 36,
                fontSize: 'var(--font-size-sm)'
              }}
            >
              {r}
            </button>
          ))}

          <button
            onClick={handleGenerateRoadmap}
            className="btn btn-primary"
            disabled={generating}
            style={{
              height: 36,
              fontSize: 'var(--font-size-sm)'
            }}
          >
            {generating
              ? 'Generating...'
              : 'Generate Roadmap'}
          </button>
        </div>

        {/* Task Filter */}
        <div style={{
          display: 'flex',
          gap: 'var(--space-2)',
          marginTop: '-var(--space-2)'
        }}>
          {['all', 'regular', 'remediation'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`btn ${filter === f ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '4px 12px', fontSize: '12px', borderRadius: 20 }}
            >
              {f === 'all' ? 'All Tasks' : f === 'regular' ? 'Regular Tasks' : 'Remediation Only'}
            </button>
          ))}
        </div>

        {error && (
          <div style={{
            color: '#ef4444',
            fontSize: 'var(--font-size-sm)'
          }}>
            {error}
          </div>
        )}

        {!roadmap ? (
          <div className="stat-card">
            <div className="stat-card-label">
              No roadmap generated
            </div>
            <p style={{
              color: 'var(--text-muted)',
              marginTop: 'var(--space-2)'
            }}>
              Select a target role and click Generate Roadmap.
            </p>
          </div>
        ) : (
          <>
            {/* Overview stats */}
            <div className="stat-grid">
              <div className="stat-card">
                <div className="stat-card-label">
                  Overall Progress
                </div>

                <div className="stat-card-value">
                  {Math.round(progress)}
                  <span style={{
                    fontSize: 'var(--font-size-lg)',
                    WebkitTextFillColor: 'inherit'
                  }}>
                    %
                  </span>
                </div>

                <div style={{
                  marginTop: 'var(--space-3)',
                  height: 6,
                  background: 'var(--bg-tertiary)',
                  borderRadius: 3,
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${progress}%`,
                    height: '100%',
                    background: 'var(--gradient-accent)',
                    borderRadius: 3
                  }} />
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-card-label">
                  Tasks Completed
                </div>

                <div className="stat-card-value">
                  {doneTasks}
                  <span style={{
                    fontSize: 'var(--font-size-lg)',
                    WebkitTextFillColor: 'inherit'
                  }}>
                    /{totalTasks}
                  </span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-card-label">
                  Total Duration
                </div>

                <div className="stat-card-value">
                  {roadmap.total_weeks}
                  <span style={{
                    fontSize: 'var(--font-size-lg)',
                    WebkitTextFillColor: 'inherit'
                  }}>
                    {' '}wks
                  </span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-card-label">
                  Estimated Effort
                </div>

                <div className="stat-card-value">
                  {totalHours}
                  <span style={{
                    fontSize: 'var(--font-size-lg)',
                    WebkitTextFillColor: 'inherit'
                  }}>
                    {' '}hrs
                  </span>
                </div>
              </div>
            </div>

            {/* Phase timeline */}
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-4)'
            }}>
              {roadmap.phases.map(phase => (
                <PhaseCard
                  key={phase.id}
                  phase={phase}
                  onToggleTask={handleToggleTask}
                />
              ))}
            </div>

            {/* Legend */}
            <div style={{
              display: 'flex',
              gap: 'var(--space-6)',
              fontSize: 'var(--font-size-xs)',
              color: 'var(--text-muted)'
            }}>
              <span>
                Click the circle to cycle task status:
              </span>

              {Object.entries(STATUS_CONFIG).map(
                ([key, cfg]) => (
                  <span
                    key={key}
                    style={{ color: cfg.color }}
                  >
                    {cfg.icon} {cfg.label}
                  </span>
                )
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}