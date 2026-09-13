/**
 * Faculty Curriculum Map — semester selector, subject grid with coverage scores,
 * skill mappings per subject, and AI-suggested missing skills.
 */

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { curriculumApi } from '../../api/endpoints';

// ─── Fallback Data (used when API is unavailable or offline) ────────
const SEMESTERS = [5, 6, 7, 8];

const FALLBACK_SUBJECTS_BY_SEM = {
  5: [
    {
      code: 'CS301', name: 'Data Structures & Algorithms', credits: 4, coverage: 82,
      mapped_skills: ['Arrays & Linked Lists', 'Trees & Graphs', 'Sorting / Searching', 'Dynamic Programming'],
      demand_score: 95,
      ai_suggestions: ['Advanced Graph Algorithms (BFS/DFS variants)', 'Competitive programming patterns'],
    },
    {
      code: 'CS302', name: 'Database Management', credits: 4, coverage: 75,
      mapped_skills: ['SQL Fundamentals', 'Normalization', 'Transactions', 'ER Modeling'],
      demand_score: 88,
      ai_suggestions: ['Window Functions & CTEs (high employer demand)', 'NoSQL fundamentals (MongoDB)'],
    },
    {
      code: 'CS303', name: 'Operating Systems', credits: 3, coverage: 65,
      mapped_skills: ['Process Management', 'Memory Management', 'File Systems'],
      demand_score: 72,
      ai_suggestions: ['Linux system calls for DevOps relevance', 'Concurrency patterns for backend engineering'],
    },
    {
      code: 'CS304', name: 'Software Engineering', credits: 3, coverage: 58,
      mapped_skills: ['SDLC Models', 'Requirements Engineering', 'UML Diagrams'],
      demand_score: 70,
      ai_suggestions: ['Agile / Scrum practices (highly demanded)', 'Git workflow & CI/CD pipeline basics'],
    },
  ],
  6: [
    {
      code: 'CS401', name: 'Computer Networks', credits: 4, coverage: 55,
      mapped_skills: ['OSI Model', 'TCP/IP', 'Routing Protocols', 'HTTP/HTTPS'],
      demand_score: 78,
      ai_suggestions: ['REST API design & HTTP verbs (critical for backend roles)', 'Load balancing concepts'],
    },
    {
      code: 'CS402', name: 'Machine Learning', credits: 4, coverage: 70,
      mapped_skills: ['Linear Regression', 'Decision Trees', 'Clustering', 'Model Evaluation'],
      demand_score: 90,
      ai_suggestions: ['Feature engineering techniques', 'Model deployment with Flask/FastAPI', 'scikit-learn best practices'],
    },
    {
      code: 'CS403', name: 'Big Data Analytics', credits: 3, coverage: 48,
      mapped_skills: ['Hadoop Basics', 'MapReduce', 'Hive'],
      demand_score: 82,
      ai_suggestions: ['Apache Spark (dominant in industry, not covered)', 'Real-time streaming with Kafka', 'Cloud data lakes (S3, GCS)'],
    },
    {
      code: 'CS404', name: 'Web Technologies', credits: 3, coverage: 60,
      mapped_skills: ['HTML/CSS', 'JavaScript Basics', 'Node.js Intro'],
      demand_score: 85,
      ai_suggestions: ['React / Vue.js (most demanded frontend skill)', 'RESTful API development', 'Authentication & JWT'],
    },
  ],
  7: [
    {
      code: 'CS501', name: 'Cloud Computing', credits: 3, coverage: 35,
      mapped_skills: ['Cloud Concepts', 'AWS Basics', 'Virtualization'],
      demand_score: 88,
      ai_suggestions: ['AWS core services (EC2, S3, Lambda) — essential for 70%+ of roles', 'Infrastructure as Code (Terraform)', 'Kubernetes fundamentals'],
    },
    {
      code: 'CS502', name: 'Deep Learning', credits: 4, coverage: 55,
      mapped_skills: ['Neural Networks', 'CNNs', 'RNNs', 'Backpropagation'],
      demand_score: 85,
      ai_suggestions: ['PyTorch (preferred over TensorFlow in industry)', 'Transformer architecture basics', 'Fine-tuning pre-trained models (HuggingFace)'],
    },
    {
      code: 'CS503', name: 'Natural Language Processing', credits: 3, coverage: 50,
      mapped_skills: ['Text Preprocessing', 'Word Embeddings', 'Sentiment Analysis'],
      demand_score: 80,
      ai_suggestions: ['Large Language Model APIs (OpenAI, Gemini)', 'Retrieval-Augmented Generation (RAG)', 'spaCy for production NLP'],
    },
  ],
  8: [
    {
      code: 'CS601', name: 'Distributed Systems', credits: 3, coverage: 42,
      mapped_skills: ['CAP Theorem', 'Consensus Algorithms', 'Replication'],
      demand_score: 85,
      ai_suggestions: ['Microservices design patterns', 'Message queues (RabbitMQ, Kafka)', 'gRPC for inter-service communication'],
    },
    {
      code: 'CS602', name: 'Information Security', credits: 3, coverage: 60,
      mapped_skills: ['Cryptography', 'Network Security', 'OWASP Top 10'],
      demand_score: 78,
      ai_suggestions: ['JWT and OAuth 2.0 (practical for every web role)', 'Secure coding practices', 'API security testing'],
    },
    {
      code: 'CS603', name: 'Project Work', credits: 6, coverage: 70,
      mapped_skills: ['System Design', 'Documentation', 'Presentation Skills'],
      demand_score: 90,
      ai_suggestions: ['Containerize project with Docker', 'Deploy on a cloud platform for real-world experience', 'Add comprehensive README with architecture diagrams'],
    },
  ],
};

const coverageColor = (pct) =>
  pct >= 75 ? '#22c55e' : pct >= 55 ? '#f59e0b' : '#ef4444';

const coverageBg = (pct) =>
  pct >= 75 ? 'rgba(34,197,94,0.1)' : pct >= 55 ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)';

// ─── Subject Card ──────────────────────────────────────────────────
function SubjectCard({ subject, onApplySuggestions, onApplySingleSuggestion, isApplying, isApplyingSingle }) {
  const [expanded, setExpanded] = useState(false);
  const coverage = Math.round(subject.coverage ?? subject.coverage_pct ?? 0);
  const demandScore = Math.round(subject.demand_score ?? 70);
  const color = coverageColor(coverage);
  const bg = coverageBg(coverage);

  // Normalize mapped skills whether strings or objects { id, skill: { name } }
  const mappedSkills = (subject.mapped_skills || []).map((s) =>
    typeof s === 'string' ? s : (s.skill?.name || s.name || 'Skill')
  );

  const aiSuggestions = subject.ai_suggestions || [];

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 2 }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{subject.code}</span>
            <span className="badge badge-primary">{subject.credits} credits</span>
          </div>
          <div style={{ fontWeight: 700, fontSize: 'var(--font-size-base)' }}>{subject.name}</div>
        </div>
        <div style={{
          minWidth: 56, height: 56, borderRadius: '50%',
          background: bg, border: `2px solid ${color}`,
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        }}>
          <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 800, color }}>{coverage}%</div>
          <div style={{ fontSize: 9, color, opacity: 0.8 }}>coverage</div>
        </div>
      </div>

      {/* Coverage bar */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: 4 }}>
          <span>Industry demand score: <strong style={{ color: 'var(--text-secondary)' }}>{demandScore}/100</strong></span>
        </div>
        <div style={{ height: 6, background: 'var(--bg-tertiary)', borderRadius: 3, overflow: 'hidden' }}>
          <div style={{ width: `${Math.min(100, Math.max(0, coverage))}%`, height: '100%', background: color, borderRadius: 3 }} />
        </div>
      </div>

      {/* Mapped skills */}
      <div>
        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: 'var(--space-2)', fontWeight: 500 }}>
          Currently mapped skills ({mappedSkills.length}):
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
          {mappedSkills.length > 0 ? (
            mappedSkills.map((s, idx) => (
              <span key={`${s}-${idx}`} style={{
                padding: '2px 10px', borderRadius: 999, fontSize: 'var(--font-size-xs)',
                background: 'rgba(99,102,241,0.1)', color: 'var(--accent-primary)',
                border: '1px solid rgba(99,102,241,0.2)',
              }}>{s}</span>
            ))
          ) : (
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', fontStyle: 'italic' }}>
              No skills mapped yet
            </span>
          )}
        </div>
      </div>

      {/* AI suggestions (expandable) */}
      <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: 'var(--space-3)' }}>
        <button
          onClick={() => setExpanded(e => !e)}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            fontSize: 'var(--font-size-xs)', fontWeight: 600,
            color: 'var(--accent-warning)',
            display: 'flex', alignItems: 'center', gap: 'var(--space-2)',
          }}
        >
          🤖 {expanded ? '▲' : '▼'} AI Suggestions ({aiSuggestions.length} missing {aiSuggestions.length === 1 ? 'skill' : 'skills'})
        </button>
        {expanded && (
          <div style={{ marginTop: 'var(--space-3)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            {aiSuggestions.length > 0 ? (
              aiSuggestions.map((s, i) => {
                const isSingleActive = isApplyingSingle === `${subject.id || subject.code}-${s}`;
                return (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: 'var(--space-3)',
                      padding: 'var(--space-2) var(--space-3)',
                      background: 'rgba(245,158,11,0.06)',
                      border: '1px solid rgba(245,158,11,0.2)',
                      borderRadius: 'var(--border-radius-sm)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flex: 1, minWidth: 0 }}>
                      <span style={{ color: '#f59e0b', flexShrink: 0, fontWeight: 700 }}>+</span>
                      <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', lineHeight: 1.4, wordBreak: 'break-word' }}>
                        {s}
                      </span>
                    </div>
                    <button
                      className="btn btn-secondary"
                      disabled={isSingleActive || isApplying}
                      onClick={(e) => {
                        e.stopPropagation();
                        onApplySingleSuggestion(subject, s);
                      }}
                      style={{
                        height: 26,
                        padding: '0 10px',
                        fontSize: 'var(--font-size-xs)',
                        fontWeight: 600,
                        border: '1px solid rgba(245,158,11,0.4)',
                        color: 'var(--accent-warning)',
                        background: 'rgba(245,158,11,0.1)',
                        cursor: (isSingleActive || isApplying) ? 'not-allowed' : 'pointer',
                        flexShrink: 0,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4,
                      }}
                      title={`Add "${s}" to mapped skills`}
                    >
                      {isSingleActive ? 'Adding...' : '+ Add'}
                    </button>
                  </div>
                );
              })
            ) : (
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--accent-success)', padding: 'var(--space-2)' }}>
                ✨ All key industry skills are currently mapped to this subject!
              </div>
            )}
            {aiSuggestions.length > 0 && (
              <button
                className="btn btn-secondary"
                disabled={isApplying || Boolean(isApplyingSingle)}
                onClick={() => onApplySuggestions(subject)}
                style={{
                  height: 32,
                  fontSize: 'var(--font-size-xs)',
                  marginTop: 'var(--space-2)',
                  cursor: (isApplying || Boolean(isApplyingSingle)) ? 'not-allowed' : 'pointer',
                  opacity: (isApplying || Boolean(isApplyingSingle)) ? 0.7 : 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 'var(--space-2)',
                }}
              >
                {isApplying ? 'Applying All Suggestions...' : 'Apply All Suggestions →'}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────
export default function CurriculumMap() {
  const { user } = useAuth();
  const [sem, setSem] = useState(7);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [applyingId, setApplyingId] = useState(null);
  const [applyingSingleKey, setApplyingSingleKey] = useState(null);
  const [notification, setNotification] = useState(null);

  const deptCode = user?.department_code || user?.department?.code || 'CS';

  const fetchSubjects = useCallback(async (semesterNumber = sem) => {
    try {
      setLoading(true);
      setError(null);
      const res = await curriculumApi.getSubjects(deptCode, semesterNumber);
      if (res?.data && res.data.length > 0) {
        setSubjects(res.data);
      } else {
        // Use fallback if database returned empty for this semester
        setSubjects(FALLBACK_SUBJECTS_BY_SEM[semesterNumber] || []);
      }
    } catch (err) {
      console.error('Failed to load curriculum subjects:', err);
      setError('Unable to fetch live subjects. Showing default curriculum map.');
      setSubjects(FALLBACK_SUBJECTS_BY_SEM[semesterNumber] || []);
    } finally {
      setLoading(false);
    }
  }, [deptCode, sem]);

  useEffect(() => {
    fetchSubjects(sem);
  }, [sem, deptCode]);

  const handleApplySingleSuggestion = async (subject, skillName) => {
    const subIdentifier = subject.id || subject.code;
    const key = `${subIdentifier}-${skillName}`;
    setApplyingSingleKey(key);
    try {
      if (subject.id) {
        const res = await curriculumApi.suggestSkillMappings(subject.id, skillName);
        const msg = res.data?.message || `Successfully added "${skillName}" to ${subject.name}`;
        setNotification({ type: 'success', message: msg });
        await fetchSubjects(sem);
      } else {
        // Fallback simulated update
        setSubjects(prev => prev.map(s => {
          if ((s.id && s.id === subject.id) || s.code === subject.code) {
            const currentSuggestions = s.ai_suggestions || [];
            return {
              ...s,
              mapped_skills: [...(s.mapped_skills || []), skillName],
              ai_suggestions: currentSuggestions.filter(item => item !== skillName),
              coverage: Math.min(95, (s.coverage || 60) + 8),
            };
          }
          return s;
        }));
        setNotification({
          type: 'success',
          message: `Added "${skillName}" to ${subject.name} (locally updated).`,
        });
      }
    } catch (err) {
      console.error(`Failed to add skill "${skillName}":`, err);
      setNotification({
        type: 'error',
        message: err.response?.data?.detail || `Failed to add "${skillName}". Please try again.`,
      });
    } finally {
      setApplyingSingleKey(null);
    }
  };

  const handleApplySuggestions = async (subject) => {
    const subIdentifier = subject.id || subject.code;
    setApplyingId(subIdentifier);
    try {
      if (subject.id) {
        const res = await curriculumApi.suggestSkillMappings(subject.id);
        const msg = res.data?.message || `Successfully applied AI suggestions to ${subject.name}`;
        setNotification({ type: 'success', message: msg });
        // Refresh subjects list from backend
        await fetchSubjects(sem);
      } else {
        // Fallback simulated update
        setSubjects(prev => prev.map(s => {
          if ((s.id && s.id === subject.id) || s.code === subject.code) {
            const added = s.ai_suggestions || [];
            return {
              ...s,
              mapped_skills: [...(s.mapped_skills || []), ...added],
              ai_suggestions: [],
              coverage: Math.min(95, (s.coverage || 60) + 18),
            };
          }
          return s;
        }));
        setNotification({
          type: 'success',
          message: `Applied suggestions to ${subject.name} (locally updated).`,
        });
      }
    } catch (err) {
      console.error('Failed to apply suggestions:', err);
      setNotification({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to apply suggestions. Please try again.',
      });
    } finally {
      setApplyingId(null);
    }
  };

  // Auto-dismiss notification after 5 seconds
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => setNotification(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  const avgCoverage = subjects.length > 0
    ? Math.round(subjects.reduce((s, sub) => s + (sub.coverage ?? sub.coverage_pct ?? 0), 0) / subjects.length)
    : 0;
  const highGap = subjects.filter(s => (s.coverage ?? s.coverage_pct ?? 0) < 55).length;
  const totalSuggestions = subjects.reduce((acc, s) => acc + (s.ai_suggestions?.length || 0), 0);

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Curriculum Map</h1>
          <p>Analyse how well each subject covers industry-demanded skills, with AI-powered gap suggestions</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <span className="badge badge-primary">{deptCode} Department</span>
          <button
            onClick={() => fetchSubjects(sem)}
            disabled={loading}
            className="btn btn-secondary"
            style={{ height: 32, fontSize: 'var(--font-size-xs)' }}
            title="Refresh subjects"
          >
            {loading ? 'Refreshing...' : '↻ Refresh'}
          </button>
        </div>
      </div>

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>

        {/* Notification Toast */}
        {notification && (
          <div style={{
            padding: 'var(--space-3) var(--space-4)',
            borderRadius: 'var(--border-radius)',
            background: notification.type === 'success' ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
            border: `1px solid ${notification.type === 'success' ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
            color: notification.type === 'success' ? '#22c55e' : '#ef4444',
            fontSize: 'var(--font-size-sm)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <span>{notification.type === 'success' ? '✓' : '✕'} {notification.message}</span>
            <button
              onClick={() => setNotification(null)}
              style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', fontWeight: 'bold', fontSize: 16 }}
            >
              ×
            </button>
          </div>
        )}

        {/* Error / Offline Notice */}
        {error && (
          <div style={{
            padding: 'var(--space-3) var(--space-4)',
            borderRadius: 'var(--border-radius)',
            background: 'rgba(245,158,11,0.08)',
            border: '1px solid rgba(245,158,11,0.3)',
            color: '#f59e0b',
            fontSize: 'var(--font-size-sm)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <span>⚠️ {error}</span>
            <button
              onClick={() => fetchSubjects(sem)}
              className="btn btn-secondary"
              style={{ height: 26, fontSize: 'var(--font-size-xs)', padding: '0 8px' }}
            >
              Retry
            </button>
          </div>
        )}

        {/* Semester selector */}
        <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center', flexWrap: 'wrap' }}>
          <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)', fontWeight: 500 }}>Semester:</span>
          {SEMESTERS.map(s => (
            <button
              key={s}
              onClick={() => setSem(s)}
              className={`btn ${sem === s ? 'btn-primary' : 'btn-secondary'}`}
              style={{ height: 36, width: 48, padding: 0 }}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Sem summary */}
        <div style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap' }}>
          {[
            { label: 'Subjects', value: subjects.length, color: 'var(--accent-primary)' },
            { label: 'Avg Coverage', value: `${avgCoverage}%`, color: coverageColor(avgCoverage) },
            { label: 'High Gap Subjects', value: highGap, color: '#ef4444' },
            { label: 'AI Suggestions', value: totalSuggestions, color: '#f59e0b' },
          ].map(s => (
            <div key={s.label} style={{
              flex: 1, minWidth: 140, padding: 'var(--space-4)',
              background: 'var(--bg-card)', border: '1px solid var(--border-color)',
              borderRadius: 'var(--border-radius)', textAlign: 'center',
            }}>
              <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', gap: 'var(--space-6)', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', flexWrap: 'wrap' }}>
          <span style={{ fontWeight: 500 }}>Coverage:</span>
          {[{ c: '#22c55e', l: '≥ 75% Good' }, { c: '#f59e0b', l: '55–74% Needs work' }, { c: '#ef4444', l: '< 55% Critical gap' }].map(x => (
            <span key={x.l} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', color: x.c }}>
              <div style={{ width: 10, height: 10, borderRadius: 2, background: x.c }} />{x.l}
            </span>
          ))}
        </div>

        {/* Subject grid */}
        {loading && subjects.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: 'var(--space-12)', color: 'var(--text-muted)' }}>
            <div style={{ fontSize: 'var(--font-size-base)', fontWeight: 500 }}>Loading curriculum mappings for Semester {sem}...</div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 'var(--space-5)' }}>
            {subjects.map(sub => (
              <SubjectCard
                key={sub.code || sub.id}
                subject={sub}
                onApplySuggestions={handleApplySuggestions}
                onApplySingleSuggestion={handleApplySingleSuggestion}
                isApplying={applyingId === (sub.id || sub.code)}
                isApplyingSingle={applyingSingleKey}
              />
            ))}
          </div>
        )}

        {!loading && subjects.length === 0 && (
          <div className="card" style={{ textAlign: 'center', padding: 'var(--space-12)', color: 'var(--text-muted)' }}>
            No subjects mapped for Semester {sem} in the {deptCode} Department.
          </div>
        )}

      </div>
    </div>
  );
}
