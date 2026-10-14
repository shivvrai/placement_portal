/**
 * Quiz Center V2 — AI-recommended quizzes, quick quiz mode, remediation plans.
 */

import { useState, useEffect, useRef } from 'react';
import { assessmentsApi } from '../../api/endpoints';

const URGENCY_STYLES = {
  high: { bg: '#7f1d1d', border: '#ef4444', text: '#fca5a5', badge: '🔴 High Priority' },
  medium: { bg: '#78350f', border: '#f59e0b', text: '#fde68a', badge: '🟡 Medium' },
  low: { bg: '#064e3b', border: '#10b981', text: '#6ee7b7', badge: '🟢 Low' },
};

export default function QuizCenter() {
  const [tab, setTab] = useState('recommended'); // recommended | quick | history
  const [recommended, setRecommended] = useState([]);
  const [history, setHistory] = useState([]);
  const [trends, setTrends] = useState({});
  const [loading, setLoading] = useState(true);

  // Quick quiz state
  const [quizActive, setQuizActive] = useState(false);
  const [quizSession, setQuizSession] = useState(null);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState({});
  const [quizResult, setQuizResult] = useState(null);
  const [quizSubmitting, setQuizSubmitting] = useState(false);
  const [timer, setTimer] = useState(30);
  const [remediation, setRemediation] = useState(null);

  const timerRef = useRef(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [recRes, histRes, trendRes] = await Promise.all([
        assessmentsApi.getRecommended().catch(() => ({ data: [] })),
        assessmentsApi.getHistory().catch(() => ({ data: [] })),
        assessmentsApi.getTrends().catch(() => ({ data: { trends: {} } })),
      ]);
      setRecommended(recRes.data || []);
      setHistory(histRes.data || []);
      setTrends(trendRes.data?.trends || {});
    } finally {
      setLoading(false);
    }
  };

  // ─── Quick Quiz Logic ─────────────────────────────────────────────
  const startQuiz = async (topic, difficulty = 'medium') => {
    try {
      const res = await assessmentsApi.startQuickQuiz(topic, difficulty);
      setQuizSession(res.data);
      setCurrentQ(0);
      setAnswers({});
      setQuizResult(null);
      setRemediation(null);
      setQuizActive(true);
      setTimer(30);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to start quiz');
    }
  };

  // Timer countdown
  useEffect(() => {
    if (quizActive && !quizResult) {
      timerRef.current = setInterval(() => {
        setTimer(t => {
          if (t <= 1) {
            // Auto-advance on timeout
            handleNextQuestion();
            return 30;
          }
          return t - 1;
        });
      }, 1000);
      return () => clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [quizActive, quizResult, currentQ]);

  const handleAnswer = (questionId, option) => {
    setAnswers(prev => ({ ...prev, [questionId]: option }));
  };

  const handleNextQuestion = () => {
    const questions = quizSession?.questions || [];
    if (currentQ < questions.length - 1) {
      setCurrentQ(prev => prev + 1);
      setTimer(30);
    }
  };

  const handleSubmitQuiz = async () => {
    setQuizSubmitting(true);
    clearInterval(timerRef.current);
    try {
      const answerList = Object.entries(answers).map(([qId, opt]) => ({
        question_id: qId, selected_option: opt,
      }));
      const res = await assessmentsApi.submit(quizSession.id, answerList);
      setQuizResult(res.data);
    } catch (err) {
      alert('Failed to submit quiz');
    } finally {
      setQuizSubmitting(false);
    }
  };

  const handleRemediate = async () => {
    try {
      const res = await assessmentsApi.generateRemediation(quizSession.id);
      setRemediation(res.data);
    } catch (err) {
      alert('Failed to generate remediation plan');
    }
  };

  const formatDate = (iso) => iso ? new Date(iso).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short',
  }) : '';

  // ═══════════════════════════════════════════════════════════════════
  // ACTIVE QUIZ VIEW
  // ═══════════════════════════════════════════════════════════════════
  if (quizActive && quizSession) {
    const questions = quizSession.questions || [];

    // Quiz Result
    if (quizResult) {
      const pct = quizResult.percentage || 0;
      const passed = pct >= 60;
      return (
        <div style={{ padding: 24, maxWidth: 700, margin: '0 auto' }}>
          <h2 style={{ fontSize: 24, fontWeight: 800, color: '#f1f5f9', marginBottom: 16 }}>
            {passed ? '🎉' : '📚'} Quiz Results — {quizSession.topic}
          </h2>

          {/* Score */}
          <div style={{
            textAlign: 'center', padding: 28, borderRadius: 16,
            background: passed ? '#064e3b' : '#7f1d1d',
            border: `1px solid ${passed ? '#065f46' : '#991b1b'}`, marginBottom: 24,
          }}>
            <div style={{ fontSize: 48, fontWeight: 800, color: passed ? '#6ee7b7' : '#fca5a5' }}>
              {Math.round(pct)}%
            </div>
            <div style={{ color: passed ? '#a7f3d0' : '#fecaca', fontSize: 14, marginTop: 4 }}>
              {quizResult.correct}/{quizResult.total_questions} correct
            </div>
          </div>

          {/* Questions Review */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 24 }}>
            {(quizResult.questions || []).map((q, i) => (
              <div key={q.id} style={{
                padding: '14px 16px', borderRadius: 12,
                background: q.is_correct ? '#064e3b' : '#451a03',
                border: `1px solid ${q.is_correct ? '#065f46' : '#78350f'}`,
              }}>
                <div style={{ fontSize: 13, color: '#e2e8f0', marginBottom: 8 }}>
                  <strong>Q{i + 1}:</strong> {q.question_text}
                </div>
                <div style={{ fontSize: 12, color: q.is_correct ? '#6ee7b7' : '#fca5a5' }}>
                  {q.is_correct ? '✓' : '✗'} Your answer: {q.selected_option || 'Skipped'} {!q.is_correct && `| Correct: ${q.correct_answer}`}
                </div>
                {q.explanation && (
                  <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 6, fontStyle: 'italic' }}>
                    💡 {q.explanation}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Remediation */}
          {!passed && !remediation && (
            <button onClick={handleRemediate} style={{
              width: '100%', padding: '14px', borderRadius: 12, border: 'none',
              background: 'linear-gradient(135deg, #f59e0b, #d97706)',
              color: '#fff', fontSize: 14, fontWeight: 700, cursor: 'pointer', marginBottom: 16,
            }}>📚 Generate Remediation Plan</button>
          )}

          {remediation && remediation.tasks && remediation.tasks.length > 0 && (
            <div style={{ marginBottom: 24 }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: '#fde68a', marginBottom: 12 }}>
                📋 Remediation Plan — {remediation.tasks.length} tasks added to your roadmap
              </h3>
              {remediation.tasks.map((t, i) => (
                <div key={i} style={{
                  padding: '12px 16px', borderRadius: 10, background: '#1e293b',
                  border: '1px solid #334155', marginBottom: 8,
                }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>{t.title}</div>
                  <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>{t.description}</div>
                  {t.resource_url && (
                    <a href={t.resource_url} target="_blank" rel="noreferrer" style={{
                      fontSize: 12, color: '#6366f1', marginTop: 6, display: 'inline-block',
                    }}>🔗 {t.resource_type} resource →</a>
                  )}
                </div>
              ))}
            </div>
          )}

          <div style={{ display: 'flex', gap: 12 }}>
            <button onClick={() => { setQuizActive(false); loadData(); }} style={{
              flex: 1, padding: '12px', borderRadius: 10, border: '1px solid #6366f1',
              background: 'transparent', color: '#a5b4fc', fontSize: 14, fontWeight: 600, cursor: 'pointer',
            }}>← Back to Quiz Center</button>
            <button onClick={() => startQuiz(quizSession.topic)} style={{
              flex: 1, padding: '12px', borderRadius: 10, border: 'none',
              background: '#6366f1', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer',
            }}>🔄 Retry Quiz</button>
          </div>
        </div>
      );
    }

    // Active Question
    const q = questions[currentQ];
    if (!q) return <div style={{ padding: 24, color: '#94a3b8' }}>No questions available</div>;

    const progress = ((currentQ + 1) / questions.length) * 100;
    const isLastQ = currentQ === questions.length - 1;

    return (
      <div style={{ padding: 24, maxWidth: 700, margin: '0 auto' }}>
        {/* Progress */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
          <div style={{ flex: 1, height: 6, borderRadius: 3, background: '#1e293b' }}>
            <div style={{
              height: '100%', borderRadius: 3, background: '#6366f1',
              width: `${progress}%`, transition: 'width 0.3s',
            }} />
          </div>
          <span style={{ fontSize: 13, color: '#94a3b8', fontWeight: 600 }}>
            {currentQ + 1}/{questions.length}
          </span>
          <span style={{
            padding: '4px 10px', borderRadius: 8, fontSize: 13, fontWeight: 700,
            background: timer <= 10 ? '#7f1d1d' : '#1e293b',
            color: timer <= 10 ? '#fca5a5' : '#94a3b8',
          }}>⏱ {timer}s</span>
        </div>

        {/* Topic label */}
        <div style={{
          padding: '4px 12px', borderRadius: 20, background: '#312e81',
          color: '#a5b4fc', fontSize: 12, fontWeight: 600, display: 'inline-block', marginBottom: 16,
        }}>{quizSession.topic} • {quizSession.difficulty}</div>

        {/* Question */}
        <div style={{
          padding: '24px', borderRadius: 16, background: '#1e293b',
          border: '1px solid #334155', marginBottom: 20,
        }}>
          <p style={{ fontSize: 16, color: '#f1f5f9', lineHeight: 1.7, fontWeight: 500 }}>
            {q.question_text}
          </p>
        </div>

        {/* Options */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 24 }}>
          {(q.options || []).map((opt, i) => {
            const selected = answers[q.id] === opt;
            return (
              <button key={i} onClick={() => handleAnswer(q.id, opt)} style={{
                padding: '14px 18px', borderRadius: 12, textAlign: 'left',
                border: `2px solid ${selected ? '#6366f1' : '#334155'}`,
                background: selected ? '#312e81' : '#0f172a',
                color: selected ? '#a5b4fc' : '#e2e8f0',
                fontSize: 14, cursor: 'pointer', transition: 'all 0.2s',
              }}>
                <span style={{
                  display: 'inline-flex', width: 24, height: 24, borderRadius: '50%',
                  background: selected ? '#6366f1' : '#1e293b', color: '#fff',
                  alignItems: 'center', justifyContent: 'center', fontSize: 12,
                  fontWeight: 700, marginRight: 12,
                }}>{String.fromCharCode(65 + i)}</span>
                {opt}
              </button>
            );
          })}
        </div>

        {/* Navigation */}
        <div style={{ display: 'flex', gap: 12 }}>
          {currentQ > 0 && (
            <button onClick={() => { setCurrentQ(prev => prev - 1); setTimer(30); }} style={{
              padding: '12px 20px', borderRadius: 10, border: '1px solid #334155',
              background: '#1e293b', color: '#94a3b8', fontSize: 14, cursor: 'pointer',
            }}>← Previous</button>
          )}
          <div style={{ flex: 1 }} />
          {isLastQ ? (
            <button onClick={handleSubmitQuiz} disabled={quizSubmitting} style={{
              padding: '12px 24px', borderRadius: 10, border: 'none',
              background: quizSubmitting ? '#475569' : 'linear-gradient(135deg, #10b981, #059669)',
              color: '#fff', fontSize: 14, fontWeight: 700, cursor: quizSubmitting ? 'not-allowed' : 'pointer',
            }}>{quizSubmitting ? 'Submitting...' : '✓ Submit Quiz'}</button>
          ) : (
            <button onClick={() => { handleNextQuestion(); }} style={{
              padding: '12px 24px', borderRadius: 10, border: 'none',
              background: '#6366f1', color: '#fff', fontSize: 14, fontWeight: 700, cursor: 'pointer',
            }}>Next →</button>
          )}
        </div>
      </div>
    );
  }

  // ═══════════════════════════════════════════════════════════════════
  // MAIN QUIZ CENTER
  // ═══════════════════════════════════════════════════════════════════
  return (
    <div style={{ padding: 24, maxWidth: 1000, margin: '0 auto' }}>
      <h1 style={{ fontSize: 28, fontWeight: 800, color: '#f1f5f9', marginBottom: 4 }}>
        🧠 Quiz Center
      </h1>
      <p style={{ color: '#94a3b8', marginBottom: 24, fontSize: 14 }}>
        AI-recommended assessments based on your skill gaps and active placement drives
      </p>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 24 }}>
        {[
          { key: 'recommended', label: '🎯 Recommended' },
          { key: 'quick', label: '⚡ Quick Quiz' },
          { key: 'history', label: '📜 History' },
        ].map(t => (
          <button key={t.key} onClick={() => setTab(t.key)} style={{
            padding: '10px 20px', borderRadius: 10, border: 'none',
            background: tab === t.key ? '#312e81' : '#1e293b',
            color: tab === t.key ? '#a5b4fc' : '#94a3b8',
            fontSize: 14, fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s',
          }}>{t.label}</button>
        ))}
      </div>

      {loading && <p style={{ color: '#94a3b8' }}>Loading...</p>}

      {/* Recommended Tab */}
      {tab === 'recommended' && !loading && (
        <div>
          {recommended.length === 0 ? (
            <div style={{
              padding: 40, textAlign: 'center', borderRadius: 16,
              background: '#1e293b', border: '1px solid #334155',
            }}>
              <p style={{ color: '#94a3b8' }}>No recommendations yet. Complete some quizzes to get personalized suggestions!</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280, 1fr))', gap: 16 }}>
              {recommended.map((r, i) => {
                const style = URGENCY_STYLES[r.urgency] || URGENCY_STYLES.low;
                return (
                  <div key={i} style={{
                    padding: '20px', borderRadius: 14, background: style.bg,
                    border: `1px solid ${style.border}30`,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 12 }}>
                      <h3 style={{ fontSize: 16, fontWeight: 700, color: '#f1f5f9' }}>{r.topic}</h3>
                      <span style={{ fontSize: 11, color: style.text, fontWeight: 600 }}>{style.badge}</span>
                    </div>
                    <p style={{ fontSize: 13, color: '#cbd5e1', marginBottom: 12, lineHeight: 1.5 }}>{r.reason}</p>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: 12, color: '#64748b' }}>
                        {r.question_count} questions{r.last_score != null ? ` • Last: ${Math.round(r.last_score)}%` : ''}
                      </span>
                      <button onClick={() => startQuiz(r.topic)} style={{
                        padding: '8px 16px', borderRadius: 8, border: 'none',
                        background: '#6366f1', color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer',
                      }}>Start →</button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Quick Quiz Tab */}
      {tab === 'quick' && !loading && (
        <div>
          <p style={{ color: '#94a3b8', fontSize: 14, marginBottom: 16 }}>
            Choose a topic for a quick 5-question timed quiz (30s per question)
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
            {['Python', 'JavaScript', 'Data Structures', 'SQL', 'React', 'Operating Systems',
              'Computer Networks', 'DBMS', 'OOP Concepts', 'System Design', 'Machine Learning',
              'Java', 'C++', 'HTML/CSS', 'Git', 'REST APIs',
            ].map(topic => {
              const topicTrend = trends[topic] || [];
              const lastScore = topicTrend.length > 0 ? topicTrend[topicTrend.length - 1].score : null;
              return (
                <button key={topic} onClick={() => startQuiz(topic)} style={{
                  padding: '16px', borderRadius: 12, border: '1px solid #334155',
                  background: '#1e293b', color: '#e2e8f0', fontSize: 14, fontWeight: 600,
                  cursor: 'pointer', transition: 'all 0.2s', textAlign: 'left',
                }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = '#6366f1'}
                  onMouseLeave={e => e.currentTarget.style.borderColor = '#334155'}
                >
                  {topic}
                  {lastScore != null && (
                    <div style={{
                      fontSize: 11, marginTop: 4,
                      color: lastScore >= 80 ? '#10b981' : lastScore >= 60 ? '#f59e0b' : '#ef4444',
                    }}>Last: {Math.round(lastScore)}%</div>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* History Tab */}
      {tab === 'history' && !loading && (
        <div>
          {history.length === 0 ? (
            <p style={{ color: '#94a3b8', textAlign: 'center', padding: 40 }}>No assessments taken yet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {/* Header */}
              <div style={{
                display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr',
                padding: '10px 16px', fontSize: 12, color: '#64748b', fontWeight: 600,
              }}>
                <span>Topic</span><span>Difficulty</span><span>Score</span><span>Status</span><span>Date</span>
              </div>
              {history.map(h => (
                <div key={h.id} style={{
                  display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr',
                  padding: '12px 16px', borderRadius: 10, background: '#1e293b',
                  border: '1px solid #334155', alignItems: 'center', fontSize: 13,
                }}>
                  <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{h.topic}</span>
                  <span style={{ color: '#94a3b8' }}>{h.difficulty}</span>
                  <span style={{
                    fontWeight: 700,
                    color: (h.percentage || 0) >= 80 ? '#10b981' : (h.percentage || 0) >= 60 ? '#f59e0b' : '#ef4444',
                  }}>{h.percentage != null ? `${Math.round(h.percentage)}%` : '—'}</span>
                  <span style={{
                    padding: '3px 10px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                    background: h.status === 'completed' ? '#064e3b' : '#1e293b',
                    color: h.status === 'completed' ? '#6ee7b7' : '#94a3b8',
                    display: 'inline-block', width: 'fit-content',
                  }}>{h.status}</span>
                  <span style={{ color: '#64748b' }}>{formatDate(h.started_at)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
