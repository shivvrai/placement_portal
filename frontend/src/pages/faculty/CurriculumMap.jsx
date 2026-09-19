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
function SubjectCard({ subject, onApplySuggestions, onApplySingleSuggestion, isApplying, isApplyingSingle, onGenerateBoS, generatingBoSId }) {
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

      {/* BoS Proposal Generation */}
      <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: 'var(--space-3)' }}>
        {generatingBoSId === subject.id ? (
          <div style={{
            padding: 'var(--space-3)',
            background: 'var(--bg-card-hover)',
            borderRadius: 'var(--border-radius-sm)',
            textAlign: 'center',
            fontSize: 'var(--font-size-xs)',
            color: 'var(--text-secondary)'
          }}>
            🧠 AI is analyzing industry requirements...
          </div>
        ) : (
          <button
            className="btn btn-secondary"
            onClick={() => onGenerateBoS(subject)}
            style={{ width: '100%', fontSize: 'var(--font-size-sm)', height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
            disabled={!subject.id}
            title={!subject.id ? "Only available for saved subjects" : "Generate Board of Studies Modernization Proposal"}
          >
            📄 Generate BoS Modernization Proposal
          </button>
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
  const [generatingBoSId, setGeneratingBoSId] = useState(null);
  const [bosProposal, setBosProposal] = useState(null);

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

  const handleGenerateBoS = async (subject) => {
    setGeneratingBoSId(subject.id);
    try {
      const res = await curriculumApi.generateBoSProposal(subject.id);
      setBosProposal(res.data);
    } catch (err) {
      console.error('Failed to generate BoS proposal', err);
      setNotification({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to generate proposal. Please try again.',
      });
    } finally {
      setGeneratingBoSId(null);
    }
  };

  const downloadBoSDocument = () => {
    if (!bosProposal) return;
    
    const printWindow = window.open('', '_blank');
    const htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>BoS Syllabus Modernization Proposal - ${bosProposal.subject_name}</title>
        <style>
          body { font-family: 'Times New Roman', Times, serif; line-height: 1.6; color: #000; padding: 40px; margin: 0; }
          .header { text-align: center; margin-bottom: 40px; border-bottom: 2px solid #000; padding-bottom: 20px; }
          .logo-placeholder { width: 80px; height: 80px; border: 1px solid #ccc; background: #f9f9f9; display: inline-flex; align-items: center; justify-content: center; font-size: 10px; color: #888; border-radius: 50%; margin-bottom: 10px; }
          h1 { margin: 0 0 5px 0; font-size: 24px; text-transform: uppercase; }
          h2 { font-size: 16px; margin: 0 0 5px 0; font-weight: normal; }
          .meta { font-size: 14px; text-align: right; margin-bottom: 30px; font-style: italic; }
          h3 { font-size: 18px; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 30px; }
          .highlight { font-weight: bold; }
          table { width: 100%; border-collapse: collapse; margin-top: 15px; }
          th, td { border: 1px solid #000; padding: 10px; text-align: left; vertical-align: top; }
          th { background-color: #f2f2f2; }
          .module-title { font-weight: bold; }
          .hours { text-align: center; width: 60px; }
          ol, ul { margin-top: 5px; margin-bottom: 15px; padding-left: 20px; }
          @media print {
            body { padding: 0; }
            button { display: none; }
          }
        </style>
      </head>
      <body>
        <div class="header">
          <div class="logo-placeholder">[INS LOGO]</div>
          <h1>Board of Studies (BoS) Proposal</h1>
          <h2>Syllabus Modernization & Industry Alignment</h2>
          <h2>Department of ${deptCode}</h2>
        </div>
        
        <div class="meta">
          Date: ${new Date().toLocaleDateString('en-IN')}<br>
          Subject: <span class="highlight">${bosProposal.subject_name}</span>
        </div>

        <h3>1. Revision Rationale</h3>
        <p>${bosProposal.revision_rationale}</p>
        <p><span class="highlight">Industry Alignment Score:</span> ${bosProposal.industry_alignment_score}</p>

        <h3>2. Proposed New Modules</h3>
        <table>
          <thead>
            <tr>
              <th>Module Details</th>
              <th class="hours">Hours</th>
              <th>Industry Justification</th>
            </tr>
          </thead>
          <tbody>
            ${bosProposal.proposed_modules?.map(m => `
              <tr>
                <td>
                  <div class="module-title">${m.module_title}</div>
                  <ul>${m.topics?.map(t => `<li>${t}</li>`).join('') || ''}</ul>
                </td>
                <td class="hours">${m.hours}</td>
                <td>${m.justification}</td>
              </tr>
            `).join('') || ''}
          </tbody>
        </table>

        <h3>3. Recommended Lab Experiments</h3>
        <ol>
          ${bosProposal.recommended_lab_experiments?.map(e => `<li>${e}</li>`).join('') || '<li>None</li>'}
        </ol>

        <h3>4. Obsolete Topics Recommended for Removal</h3>
        <ul>
          ${bosProposal.obsolete_topics_to_remove?.map(o => `
            <li><span class="highlight">${o.topic}</span><br><em>Reason: ${o.reason}</em></li>
          `).join('') || '<li>None</li>'}
        </ul>

        <h3>5. References</h3>
        <ul>
          ${bosProposal.references?.map(r => `<li>${r}</li>`).join('') || '<li>None</li>'}
        </ul>
        
        <div style="margin-top: 50px;">
          <button onclick="window.print()" style="padding: 10px 20px; font-size: 16px; cursor: pointer;">Print / Save as PDF</button>
        </div>
      </body>
      </html>
    `;
    printWindow.document.open();
    printWindow.document.write(htmlContent);
    printWindow.document.close();
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
                onGenerateBoS={handleGenerateBoS}
                generatingBoSId={generatingBoSId}
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

      {/* BoS Proposal Modal */}
      {bosProposal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
          padding: '20px'
        }}>
          <div className="card" style={{
            width: '100%', maxWidth: 800, maxHeight: '90vh', overflowY: 'auto',
            background: 'var(--bg-primary)', display: 'flex', flexDirection: 'column',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, borderBottom: '1px solid var(--border-color)', paddingBottom: 15 }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', margin: 0 }}>BoS Modernization Proposal </h2>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: 4 }}>
                  Subject: {bosProposal.subject_name} | Generated by AI on {new Date().toLocaleDateString()}
                </div>
              </div>
              <button 
                onClick={downloadBoSDocument}
                className="btn btn-primary"
                style={{ fontSize: 'var(--font-size-sm)' }}
              >
                📥 Download Document
              </button>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20, flex: 1 }}>
              <div>
                <h3 style={{ fontSize: '1rem', marginBottom: 8, color: 'var(--text-primary)' }}>Revision Rationale</h3>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
                  {bosProposal.revision_rationale}
                </p>
                <div style={{ marginTop: 10, padding: 10, background: 'rgba(34,197,94,0.1)', color: '#22c55e', borderRadius: 4, fontSize: '0.85rem', fontWeight: 600 }}>
                  Industry Alignment Score: {bosProposal.industry_alignment_score}
                </div>
              </div>

              <div>
                <h3 style={{ fontSize: '1rem', marginBottom: 12, color: 'var(--text-primary)' }}>Proposed New Modules</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {bosProposal.proposed_modules?.map((m, i) => (
                    <div key={i} style={{ border: '1px solid var(--border-color)', borderRadius: 6, padding: '12px 16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                        <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>{m.module_title}</span>
                        <span className="badge badge-secondary">{m.hours} hours</span>
                      </div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 8 }}>
                        <strong style={{ color: 'var(--text-primary)' }}>Topics:</strong> {m.topics?.join(' · ')}
                      </div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                        Industry Justification: {m.justification}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                <div>
                  <h3 style={{ fontSize: '1rem', marginBottom: 8, color: 'var(--text-primary)' }}>Recommended Lab Experiments</h3>
                  <ul style={{ paddingLeft: 20, fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {bosProposal.recommended_lab_experiments?.map((e, i) => (
                      <li key={i}>{e}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 style={{ fontSize: '1rem', marginBottom: 8, color: 'var(--text-primary)' }}>Topics Recommended for Removal</h3>
                  <ul style={{ paddingLeft: 20, fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {bosProposal.obsolete_topics_to_remove?.map((o, i) => (
                      <li key={i}>
                        <div style={{ fontWeight: 500 }}>{o.topic}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{o.reason}</div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            <div style={{ marginTop: 20, paddingTop: 15, borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button 
                onClick={() => setBosProposal(null)} 
                className="btn btn-secondary"
              >
                Close
              </button>
              <button 
                onClick={downloadBoSDocument} 
                className="btn btn-primary"
              >
                📥 Download Formal BoS Document
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
