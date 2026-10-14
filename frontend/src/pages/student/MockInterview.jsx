/**
 * Mock Interview V2 — Three-screen AI interview component.
 * Screens: Setup → Active Interview → Report
 */

import { useState, useRef, useEffect } from 'react';
import { mockInterviewApi } from '../../api/endpoints';

const ROLES = [
  'Software Engineer', 'Data Analyst', 'ML Engineer', 'Full Stack Developer',
  'DevOps Engineer', 'Business Analyst', 'Product Manager', 'Data Engineer',
];

const COMPANY_STYLES = ['Product', 'Service', 'Startup', 'Consulting'];
const DIFFICULTIES = [
  { value: 'campus', label: 'Campus Recruit', desc: 'Entry-level — typical college placements' },
  { value: 'fresher', label: 'Fresher', desc: '0-1 year experience level' },
  { value: 'experienced', label: 'Experienced', desc: '2+ years experience level' },
];

const FILLER_REGEX = /\b(um|uh|like|basically|you know|kind of|sort of|i mean|actually|literally|right)\b/gi;

function countFillers(text) {
  return (text.match(FILLER_REGEX) || []).length;
}

// ─── Score Gauge ────────────────────────────────────────────────────
function ScoreGauge({ label, score, max = 10 }) {
  const pct = Math.round((score / max) * 100);
  const color = pct >= 80 ? '#10b981' : pct >= 60 ? '#f59e0b' : '#ef4444';
  return (
    <div style={{ textAlign: 'center', flex: 1 }}>
      <div style={{
        width: 80, height: 80, borderRadius: '50%', margin: '0 auto 8px',
        background: `conic-gradient(${color} ${pct * 3.6}deg, #1e293b ${pct * 3.6}deg)`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <div style={{
          width: 60, height: 60, borderRadius: '50%', background: '#0f172a',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 20, fontWeight: 700, color,
        }}>{score}</div>
      </div>
      <div style={{ fontSize: 12, color: '#94a3b8', fontWeight: 500 }}>{label}</div>
    </div>
  );
}

// ─── Verdict Badge ──────────────────────────────────────────────────
function VerdictBadge({ verdict }) {
  const colors = {
    'Strong Hire': { bg: '#065f46', text: '#6ee7b7' },
    'Hire': { bg: '#1e3a5f', text: '#7dd3fc' },
    'Borderline': { bg: '#78350f', text: '#fde68a' },
    'No Hire': { bg: '#7f1d1d', text: '#fca5a5' },
  };
  const c = colors[verdict] || colors['Borderline'];
  return (
    <span style={{
      padding: '8px 20px', borderRadius: 20, fontSize: 16, fontWeight: 700,
      background: c.bg, color: c.text, display: 'inline-block',
    }}>{verdict}</span>
  );
}

export default function MockInterview() {
  const [screen, setScreen] = useState('setup'); // setup | active | report
  const [role, setRole] = useState(ROLES[0]);
  const [companyStyle, setCompanyStyle] = useState('Product');
  const [difficulty, setDifficulty] = useState('campus');

  // Active interview state
  const [sessionId, setSessionId] = useState(null);
  const [interviewerName, setInterviewerName] = useState('');
  const [interviewerTitle, setInterviewerTitle] = useState('');
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [fillerCount, setFillerCount] = useState(0);
  const [exchangeCount, setExchangeCount] = useState(0);
  const [timer, setTimer] = useState(0);
  const [interviewEnded, setInterviewEnded] = useState(false);
  const [startError, setStartError] = useState('');

  // Report state
  const [report, setReport] = useState(null);

  // Past sessions
  const [pastSessions, setPastSessions] = useState([]);

  const chatEndRef = useRef(null);
  const timerRef = useRef(null);
  const inputRef = useRef(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load past sessions
  useEffect(() => {
    mockInterviewApi.getMyHistory(5)
      .then(res => setPastSessions(res.data || []))
      .catch(() => {});
  }, []);

  // Timer
  useEffect(() => {
    if (screen === 'active' && !interviewEnded) {
      timerRef.current = setInterval(() => setTimer(t => t + 1), 1000);
      return () => clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [screen, interviewEnded]);

  const formatTime = (s) => `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`;

  // ─── Start Interview ──────────────────────────────────────────────
  const handleStart = async () => {
    setLoading(true);
    setStartError('');
    try {
      const res = await mockInterviewApi.start(role, companyStyle, difficulty);
      const data = res.data;
      setSessionId(data.session_id);
      setInterviewerName(data.interviewer_name);
      setInterviewerTitle(data.interviewer_title);
      setMessages([{ role: 'interviewer', content: data.interviewer_message }]);
      setExchangeCount(data.exchange_count || 1);
      setFillerCount(0);
      setTimer(0);
      setScreen('active');
    } catch (err) {
      setStartError(err.response?.data?.detail || 'Failed to start interview');
    } finally {
      setLoading(false);
    }
  };

  // ─── Send Message ─────────────────────────────────────────────────
  const handleSend = async () => {
    if (!inputText.trim() || loading || interviewEnded) return;

    const text = inputText.trim();
    const newFillers = countFillers(text);

    setMessages(prev => [...prev, { role: 'candidate', content: text }]);
    setFillerCount(prev => prev + newFillers);
    setInputText('');
    setLoading(true);

    try {
      const res = await mockInterviewApi.sendMessage(sessionId, text);
      const data = res.data;

      setMessages(prev => [...prev, { role: 'interviewer', content: data.interviewer_message }]);
      setExchangeCount(data.exchange_count);
      setFillerCount(data.filler_word_count || 0);

      if (data.interview_ended) {
        setInterviewEnded(true);
        clearInterval(timerRef.current);
        if (data.report) {
          setReport(data.report);
        }
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'system',
        content: 'Connection error. Please try again.',
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const viewReport = async () => {
    if (report) {
      setScreen('report');
      return;
    }
    try {
      const res = await mockInterviewApi.getReport(sessionId);
      setReport(res.data);
      setScreen('report');
    } catch {
      setScreen('report');
    }
  };

  // ═══════════════════════════════════════════════════════════════════
  // SETUP SCREEN
  // ═══════════════════════════════════════════════════════════════════
  if (screen === 'setup') {
    return (
      <div style={{ padding: 24, maxWidth: 900, margin: '0 auto' }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: '#f1f5f9', marginBottom: 8 }}>
          🎤 AI Mock Interview
        </h1>
        <p style={{ color: '#94a3b8', marginBottom: 28, fontSize: 15 }}>
          Practice with an AI interviewer that adapts to your responses. Get scored on 4 dimensions with evidence-based feedback.
        </p>

        {/* Config Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
          {/* Role */}
          <div>
            <label style={{ color: '#cbd5e1', fontSize: 13, fontWeight: 600, marginBottom: 8, display: 'block' }}>
              Target Role
            </label>
            <select
              value={role} onChange={e => setRole(e.target.value)}
              style={{
                width: '100%', padding: '10px 14px', borderRadius: 10, border: '1px solid #334155',
                background: '#1e293b', color: '#f1f5f9', fontSize: 14, cursor: 'pointer',
              }}
            >
              {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>

          {/* Company Style */}
          <div>
            <label style={{ color: '#cbd5e1', fontSize: 13, fontWeight: 600, marginBottom: 8, display: 'block' }}>
              Company Type
            </label>
            <div style={{ display: 'flex', gap: 8 }}>
              {COMPANY_STYLES.map(cs => (
                <button
                  key={cs} onClick={() => setCompanyStyle(cs)}
                  style={{
                    flex: 1, padding: '10px 8px', borderRadius: 10, border: '1px solid',
                    borderColor: companyStyle === cs ? '#6366f1' : '#334155',
                    background: companyStyle === cs ? '#312e81' : '#1e293b',
                    color: companyStyle === cs ? '#a5b4fc' : '#94a3b8',
                    fontSize: 13, fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s',
                  }}
                >{cs}</button>
              ))}
            </div>
          </div>
        </div>

        {/* Difficulty */}
        <label style={{ color: '#cbd5e1', fontSize: 13, fontWeight: 600, marginBottom: 8, display: 'block' }}>
          Difficulty
        </label>
        <div style={{ display: 'flex', gap: 12, marginBottom: 28 }}>
          {DIFFICULTIES.map(d => (
            <button
              key={d.value} onClick={() => setDifficulty(d.value)}
              style={{
                flex: 1, padding: '14px 16px', borderRadius: 12, border: '1px solid',
                borderColor: difficulty === d.value ? '#6366f1' : '#334155',
                background: difficulty === d.value ? '#312e81' : '#1e293b',
                color: '#f1f5f9', textAlign: 'left', cursor: 'pointer', transition: 'all 0.2s',
              }}
            >
              <div style={{ fontWeight: 700, fontSize: 14, color: difficulty === d.value ? '#a5b4fc' : '#e2e8f0' }}>
                {d.label}
              </div>
              <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>{d.desc}</div>
            </button>
          ))}
        </div>

        {/* Start Button */}
        <button
          onClick={handleStart} disabled={loading}
          style={{
            width: '100%', padding: '16px 24px', borderRadius: 14, border: 'none',
            background: loading ? '#475569' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            color: '#fff', fontSize: 16, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.3s', boxShadow: '0 4px 20px rgba(99, 102, 241, 0.3)',
          }}
        >
          {loading ? '⏳ Preparing Interview...' : '🚀 Start Interview'}
        </button>
        {startError && <p style={{ color: '#ef4444', marginTop: 12, fontSize: 13 }}>{startError}</p>}

        {/* Past Sessions */}
        {pastSessions.length > 0 && (
          <div style={{ marginTop: 32 }}>
            <h3 style={{ color: '#cbd5e1', fontSize: 15, fontWeight: 600, marginBottom: 12 }}>
              Recent Sessions
            </h3>
            <div style={{ display: 'flex', gap: 12, overflowX: 'auto', paddingBottom: 8 }}>
              {pastSessions.map(s => (
                <div key={s.id} style={{
                  minWidth: 200, padding: '14px 16px', borderRadius: 12, border: '1px solid #334155',
                  background: '#1e293b',
                }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#e2e8f0' }}>{s.role_target}</div>
                  <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>{s.company_style} • {s.difficulty}</div>
                  <div style={{ fontSize: 12, color: s.verdict === 'Strong Hire' ? '#10b981' : s.verdict === 'Hire' ? '#7dd3fc' : '#f59e0b', fontWeight: 600, marginTop: 6 }}>
                    {s.verdict || s.status}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // ═══════════════════════════════════════════════════════════════════
  // ACTIVE INTERVIEW SCREEN
  // ═══════════════════════════════════════════════════════════════════
  if (screen === 'active') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', maxWidth: 900, margin: '0 auto' }}>
        {/* Top Bar */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '14px 20px', borderBottom: '1px solid #1e293b', background: '#0f172a',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{
              padding: '4px 12px', borderRadius: 20, background: '#312e81',
              color: '#a5b4fc', fontSize: 12, fontWeight: 700,
            }}>{role}</span>
            <span style={{ color: '#64748b', fontSize: 13 }}>with {interviewerName}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: 13 }}>
            <span style={{ color: '#94a3b8' }}>⏱ {formatTime(timer)}</span>
            <span style={{ color: '#94a3b8' }}>💬 {exchangeCount}</span>
            <span style={{ color: fillerCount > 5 ? '#ef4444' : '#94a3b8' }}>
              🔤 {fillerCount} fillers
            </span>
          </div>
        </div>

        {/* Chat Area */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {messages.map((msg, i) => (
            <div key={i} style={{
              display: 'flex',
              justifyContent: msg.role === 'candidate' ? 'flex-end' : 'flex-start',
            }}>
              <div style={{
                maxWidth: '80%', padding: '14px 18px', borderRadius: 16,
                background: msg.role === 'candidate' ? '#312e81' : '#1e293b',
                border: msg.role === 'system' ? '1px solid #ef4444' : 'none',
                color: msg.role === 'system' ? '#fca5a5' : '#e2e8f0',
              }}>
                {msg.role === 'interviewer' && (
                  <div style={{ fontSize: 11, color: '#6366f1', fontWeight: 600, marginBottom: 6 }}>
                    {interviewerName} • {interviewerTitle}
                  </div>
                )}
                <div style={{ fontSize: 14, lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{msg.content}</div>
              </div>
            </div>
          ))}

          {loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div style={{
                padding: '14px 18px', borderRadius: 16, background: '#1e293b',
                color: '#6366f1', fontSize: 14,
              }}>
                <span className="thinking-dots">●●●</span> {interviewerName} is thinking...
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input Area */}
        <div style={{
          padding: '16px 20px', borderTop: '1px solid #1e293b', background: '#0f172a',
          display: 'flex', gap: 12, alignItems: 'flex-end',
        }}>
          {interviewEnded ? (
            <button
              onClick={viewReport}
              style={{
                flex: 1, padding: '14px 24px', borderRadius: 12, border: 'none',
                background: 'linear-gradient(135deg, #10b981, #059669)',
                color: '#fff', fontSize: 15, fontWeight: 700, cursor: 'pointer',
              }}
            >📊 View Your Interview Report</button>
          ) : (
            <>
              <textarea
                ref={inputRef}
                value={inputText}
                onChange={e => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your response..."
                disabled={loading}
                rows={2}
                style={{
                  flex: 1, padding: '12px 16px', borderRadius: 12, border: '1px solid #334155',
                  background: '#1e293b', color: '#f1f5f9', fontSize: 14, resize: 'none',
                  fontFamily: 'inherit', outline: 'none', lineHeight: 1.6,
                }}
              />
              <button
                onClick={handleSend} disabled={!inputText.trim() || loading}
                style={{
                  padding: '12px 20px', borderRadius: 12, border: 'none',
                  background: !inputText.trim() || loading ? '#475569' : '#6366f1',
                  color: '#fff', fontWeight: 700, cursor: !inputText.trim() || loading ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s', fontSize: 14,
                }}
              >Send ↵</button>
            </>
          )}
        </div>

        {/* Filler encouragement */}
        {!interviewEnded && inputText && countFillers(inputText) > 0 && (
          <div style={{
            padding: '8px 20px', background: '#78350f', color: '#fde68a',
            fontSize: 12, textAlign: 'center',
          }}>
            💡 Tip: Try to avoid filler words like "um", "like", "basically" — detected {countFillers(inputText)} in your draft
          </div>
        )}
      </div>
    );
  }

  // ═══════════════════════════════════════════════════════════════════
  // REPORT SCREEN
  // ═══════════════════════════════════════════════════════════════════
  if (screen === 'report') {
    const r = report || {};
    return (
      <div style={{ padding: 24, maxWidth: 800, margin: '0 auto' }}>
        <h2 style={{ fontSize: 24, fontWeight: 800, color: '#f1f5f9', marginBottom: 16 }}>
          📊 Interview Performance Report
        </h2>

        {/* Verdict */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <VerdictBadge verdict={r.verdict || 'Borderline'} />
          <p style={{ color: '#94a3b8', marginTop: 12, fontSize: 14 }}>{r.overall_feedback || ''}</p>
        </div>

        {/* Score Gauges */}
        <div style={{
          display: 'flex', gap: 16, marginBottom: 28, padding: 20,
          background: '#1e293b', borderRadius: 16, border: '1px solid #334155',
        }}>
          <ScoreGauge label="Technical" score={r.technical_score || 0} />
          <ScoreGauge label="Communication" score={r.communication_score || 0} />
          <ScoreGauge label="Confidence" score={r.confidence_score || 0} />
          <ScoreGauge label="Relevance" score={r.relevance_score || 0} />
        </div>

        {/* Stats Row */}
        <div style={{ display: 'flex', gap: 12, marginBottom: 28 }}>
          {[
            { label: 'Duration', value: r.duration_seconds ? formatTime(r.duration_seconds) : 'N/A' },
            { label: 'Words', value: r.total_words || 0 },
            { label: 'Fillers', value: `${r.filler_word_count || 0} (${r.filler_word_rate || 0}%)` },
            { label: 'Exchanges', value: r.exchange_count || 0 },
          ].map(s => (
            <div key={s.label} style={{
              flex: 1, padding: '14px', borderRadius: 12, background: '#1e293b',
              border: '1px solid #334155', textAlign: 'center',
            }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: '#e2e8f0' }}>{s.value}</div>
              <div style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Strengths */}
        <div style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: '#10b981', marginBottom: 12 }}>💪 Strengths</h3>
          {(r.strengths || []).map((s, i) => (
            <div key={i} style={{
              padding: '14px 16px', borderRadius: 12, background: '#064e3b',
              border: '1px solid #065f46', marginBottom: 8,
            }}>
              <div style={{ fontWeight: 600, color: '#6ee7b7', fontSize: 14 }}>{s.point}</div>
              <div style={{ color: '#a7f3d0', fontSize: 13, marginTop: 4, fontStyle: 'italic' }}>"{s.evidence}"</div>
            </div>
          ))}
        </div>

        {/* Improvements */}
        <div style={{ marginBottom: 28 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: '#f59e0b', marginBottom: 12 }}>📈 Areas to Improve</h3>
          {(r.improvements || []).map((s, i) => (
            <div key={i} style={{
              padding: '14px 16px', borderRadius: 12, background: '#451a03',
              border: '1px solid #78350f', marginBottom: 8,
            }}>
              <div style={{ fontWeight: 600, color: '#fde68a', fontSize: 14 }}>{s.point}</div>
              <div style={{ color: '#fed7aa', fontSize: 13, marginTop: 4 }}>{s.advice}</div>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 12 }}>
          <button
            onClick={() => { setScreen('setup'); setReport(null); setInterviewEnded(false); setMessages([]); }}
            style={{
              flex: 1, padding: '14px 24px', borderRadius: 12, border: '1px solid #6366f1',
              background: 'transparent', color: '#a5b4fc', fontSize: 14, fontWeight: 700,
              cursor: 'pointer',
            }}
          >🔄 New Interview</button>
          <button
            onClick={() => window.location.href = '/student/mock-interview/history'}
            style={{
              flex: 1, padding: '14px 24px', borderRadius: 12, border: 'none',
              background: '#1e293b', color: '#94a3b8', fontSize: 14, fontWeight: 600,
              cursor: 'pointer',
            }}
          >📜 View History</button>
        </div>

        {/* Collapsible Transcript */}
        <details style={{ marginTop: 28 }}>
          <summary style={{ cursor: 'pointer', color: '#94a3b8', fontSize: 14, fontWeight: 600 }}>
            📝 View Full Transcript
          </summary>
          <div style={{
            marginTop: 12, padding: 16, borderRadius: 12,
            background: '#1e293b', border: '1px solid #334155',
            maxHeight: 400, overflowY: 'auto',
          }}>
            {messages.map((msg, i) => (
              <div key={i} style={{
                padding: '10px 0', borderBottom: '1px solid #0f172a',
                color: msg.role === 'interviewer' ? '#a5b4fc' : '#e2e8f0',
              }}>
                <span style={{ fontWeight: 700, fontSize: 12, textTransform: 'uppercase' }}>
                  {msg.role === 'interviewer' ? `${interviewerName}:` : 'You:'}
                </span>
                <p style={{ margin: '4px 0 0', fontSize: 13, lineHeight: 1.6 }}>{msg.content}</p>
              </div>
            ))}
          </div>
        </details>
      </div>
    );
  }

  return null;
}
