/**
 * RecruiterApplicants - Candidate review table for recruiters.
 * Privacy-anonymized student view with inline feedback submission.
 * Route: /recruiter/drives/:driveId/applicants
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { recruiterApi } from '../../api/endpoints';

export default function RecruiterApplicants() {
  const { driveId } = useParams();
  const navigate = useNavigate();
  const [applicants, setApplicants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [detailedApplicant, setDetailedApplicant] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [feedbackModal, setFeedbackModal] = useState(null);
  const [feedbackForm, setFeedbackForm] = useState({ stage: 'Technical Interview', rating: 4, comments: '', outcome: 'pass' });
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [toast, setToast] = useState(null);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const loadApplicants = async () => {
    try {
      setLoading(true);
      const res = await recruiterApi.getDriveApplicants(driveId);
      setApplicants(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error('Load applicants failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApplicants();
  }, [driveId]);

  const toggleExpand = async (appId) => {
    if (expandedId === appId) {
      setExpandedId(null);
      setDetailedApplicant(null);
      return;
    }
    setExpandedId(appId);
    setDetailLoading(true);
    try {
      const res = await recruiterApi.getApplicant(appId);
      setDetailedApplicant(res.data);
    } catch (err) {
      console.error('Failed to load profile details:', err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleFeedbackSubmit = async () => {
    if (!feedbackModal) return;
    setFeedbackLoading(true);
    try {
      await recruiterApi.submitFeedback(feedbackModal.application_id, feedbackForm);
      showToast('Interview feedback submitted successfully!');
      setFeedbackModal(null);
      await loadApplicants();
      if (expandedId === feedbackModal.application_id) {
        const res = await recruiterApi.getApplicant(feedbackModal.application_id);
        setDetailedApplicant(res.data);
      }
    } catch (err) {
      showToast('Failed to submit feedback: ' + (err.response?.data?.detail || 'Error'), 'error');
    } finally {
      setFeedbackLoading(false);
    }
  };

  const STATUS_COLOR = {
    shortlisted: '#f59e0b',
    in_progress: '#06b6d4',
    selected: '#22c55e',
    rejected: '#ef4444',
  };

  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Loading candidates...</div>;

  return (
    <div style={{ padding: 'var(--space-6)', maxWidth: 1100, margin: '0 auto' }}>
      {toast && (
        <div style={{
          position: 'fixed', top: 20, right: 20, zIndex: 9999, padding: '12px 20px',
          borderRadius: 10, background: toast.type === 'error' ? '#ef4444' : '#22c55e',
          color: '#fff', fontWeight: 600, boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
        }}>{toast.msg}</div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <button className="btn btn-ghost" onClick={() => navigate('/recruiter/dashboard')}>
          ← Back to Drives
        </button>
        <h1 style={{ margin: 0, fontSize: '1.3rem', fontWeight: 700 }}>Candidate Evaluation Roster ({applicants.length})</h1>
      </div>

      {applicants.length === 0 && (
        <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)', background: 'var(--bg-secondary)', borderRadius: 12 }}>
          No shortlisted applicants available for this drive yet.
        </div>
      )}

      {applicants.map(app => (
        <div key={app.application_id} className="card" style={{ marginBottom: 12, padding: '16px 20px' }}>
          <div
            style={{ display: 'flex', alignItems: 'center', gap: 16, cursor: 'pointer' }}
            onClick={() => toggleExpand(app.application_id)}
          >
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontWeight: 700, fontSize: '1rem' }}>{app.display_name}</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  🔒 Anonymized for blind evaluation
                </span>
              </div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: 4 }}>
                Dept: <strong>{app.department || 'N/A'}</strong> · CGPA: <strong>{app.cgpa ? app.cgpa.toFixed(2) : 'N/A'}</strong> · Projects: {app.project_count} · Current Round: <span style={{ color: 'var(--primary)', fontWeight: 600 }}>{app.current_stage || 'Under Review'}</span>
              </div>
            </div>

            <span style={{
              padding: '4px 12px', borderRadius: 99, fontSize: '0.75rem', fontWeight: 700,
              background: (STATUS_COLOR[app.status] || '#6366f1') + '20',
              color: STATUS_COLOR[app.status] || '#6366f1',
            }}>
              {app.status?.replace('_', ' ').toUpperCase()}
            </span>

            <button
              className="btn btn-primary"
              style={{ fontSize: '0.8rem', padding: '6px 14px' }}
              onClick={(e) => {
                e.stopPropagation();
                setFeedbackModal(app);
                setFeedbackForm({ stage: app.current_stage || 'Technical Interview', rating: 4, comments: '', outcome: 'pass' });
              }}
            >
              📝 Submit Feedback
            </button>

            <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              {expandedId === app.application_id ? '▲ Hide' : '▼ View Details'}
            </span>
          </div>

          {/* Expanded Drawer */}
          {expandedId === app.application_id && (
            <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--border-color)' }}>
              {detailLoading ? (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Loading candidate profile...</div>
              ) : detailedApplicant ? (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                  <div>
                    <div style={{ fontWeight: 600, marginBottom: 8, fontSize: '0.88rem' }}>Verified Skills</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 16 }}>
                      {(detailedApplicant.skills || []).map((s, idx) => (
                        <span key={idx} style={{ padding: '3px 10px', borderRadius: 99, background: 'var(--bg-tertiary)', fontSize: '0.75rem', border: '1px solid var(--border-color)' }}>
                          {s.name} {s.confidence ? `(${(s.confidence * 100).toFixed(0)}%)` : ''}
                        </span>
                      ))}
                      {(detailedApplicant.skills || []).length === 0 && (
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>No skills reported</span>
                      )}
                    </div>

                    <div style={{ fontWeight: 600, marginBottom: 8, fontSize: '0.88rem' }}>Interview Rounds &amp; Prior Feedback</div>
                    <div style={{ maxHeight: 160, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {(detailedApplicant.stages || []).map((stg, i) => (
                        <div key={i} style={{ padding: '8px 12px', background: 'var(--bg-tertiary)', borderRadius: 8, fontSize: '0.8rem' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600 }}>
                            <span>{stg.stage_name}</span>
                            <span style={{ color: stg.status === 'completed' ? '#22c55e' : '#f59e0b' }}>{stg.status}</span>
                          </div>
                          {stg.feedback && (
                            <div style={{ color: 'var(--text-secondary)', marginTop: 4, whiteSpace: 'pre-wrap' }}>
                              {stg.feedback}
                            </div>
                          )}
                        </div>
                      ))}
                      {(detailedApplicant.stages || []).length === 0 && (
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>No previous interview stages recorded.</div>
                      )}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontWeight: 600, marginBottom: 8, fontSize: '0.88rem' }}>Portfolio Projects</div>
                    <div style={{ maxHeight: 180, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {(detailedApplicant.projects || []).map((p, i) => (
                        <div key={i} style={{ padding: '8px 12px', background: 'var(--bg-tertiary)', borderRadius: 8, fontSize: '0.8rem' }}>
                          <div style={{ fontWeight: 600 }}>{p.title}</div>
                          {p.description && <div style={{ color: 'var(--text-secondary)', marginTop: 2 }}>{p.description}</div>}
                          {p.technologies && (
                            <div style={{ color: 'var(--primary)', marginTop: 4, fontSize: '0.72rem' }}>
                              Tech: {Array.isArray(p.technologies) ? p.technologies.join(', ') : p.technologies}
                            </div>
                          )}
                        </div>
                      ))}
                      {(detailedApplicant.projects || []).length === 0 && (
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>No projects listed.</div>
                      )}
                    </div>

                    <div style={{ marginTop: 12, padding: '8px 12px', borderRadius: 8, background: 'rgba(99, 102, 241, 0.08)', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      🔒 <strong>Compliance Notice:</strong> Candidate phone and personal email remain masked in compliance with anti-bias hiring protocols until official placement offer release.
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          )}
        </div>
      ))}

      {/* Feedback Modal */}
      {feedbackModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: 16, padding: 32, width: 480 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
              <h2 style={{ margin: 0, fontSize: '1.2rem' }}>Candidate Evaluation Feedback</h2>
              <span style={{ cursor: 'pointer', fontSize: '1.2rem' }} onClick={() => setFeedbackModal(null)}>✕</span>
            </div>
            <div style={{ marginBottom: 4, fontWeight: 700 }}>{feedbackModal.display_name}</div>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: 20 }}>
              Dept: {feedbackModal.department} · CGPA: {feedbackModal.cgpa ? feedbackModal.cgpa.toFixed(2) : 'N/A'}
            </div>

            <div style={{ marginBottom: 14 }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 6 }}>Interview Round / Stage</label>
              <select
                value={feedbackForm.stage}
                onChange={e => setFeedbackForm(f => ({ ...f, stage: e.target.value }))}
                style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
              >
                <option>Technical Interview</option>
                <option>Coding Assessment</option>
                <option>System Design Round</option>
                <option>Managerial Round</option>
                <option>HR Interview</option>
                <option>Final Round</option>
              </select>
            </div>

            <div style={{ marginBottom: 14 }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 6 }}>
                Technical &amp; Problem-Solving Rating: <strong>{feedbackForm.rating} / 5</strong>
              </label>
              <input
                type="range" min="1" max="5" value={feedbackForm.rating}
                onChange={e => setFeedbackForm(f => ({ ...f, rating: parseInt(e.target.value) }))}
                style={{ width: '100%' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                <span>1 - Below Expectations</span>
                <span>3 - Meets Standard</span>
                <span>5 - Outstanding</span>
              </div>
            </div>

            <div style={{ marginBottom: 14 }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 6 }}>Stage Decision</label>
              <div style={{ display: 'flex', gap: 8 }}>
                {[
                  { key: 'pass', label: '✅ Pass / Advance', color: '#22c55e' },
                  { key: 'fail', label: '❌ Reject', color: '#ef4444' },
                  { key: 'on_hold', label: '⏳ Hold', color: '#f59e0b' },
                ].map(o => (
                  <button
                    key={o.key}
                    type="button"
                    onClick={() => setFeedbackForm(f => ({ ...f, outcome: o.key }))}
                    style={{
                      flex: 1, padding: '8px 4px', borderRadius: 8, border: '1px solid', cursor: 'pointer',
                      fontWeight: feedbackForm.outcome === o.key ? 700 : 400,
                      background: feedbackForm.outcome === o.key ? `${o.color}25` : 'var(--bg-primary)',
                      borderColor: feedbackForm.outcome === o.key ? o.color : 'var(--border-color)',
                      color: feedbackForm.outcome === o.key ? o.color : 'var(--text-secondary)',
                      fontSize: '0.8rem',
                    }}
                  >
                    {o.label}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 6 }}>Recruiter Notes / Detailed Feedback</label>
              <textarea
                value={feedbackForm.comments}
                onChange={e => setFeedbackForm(f => ({ ...f, comments: e.target.value }))}
                rows={3}
                placeholder="Candidate demonstrated strong knowledge in data structures, communication was clear..."
                style={{ width: '100%', borderRadius: 8, border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)', padding: '8px 10px', resize: 'vertical' }}
              />
            </div>

            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn btn-secondary" onClick={() => setFeedbackModal(null)}>Cancel</button>
              <button
                className="btn btn-primary"
                style={{ flex: 1 }}
                onClick={handleFeedbackSubmit}
                disabled={feedbackLoading}
              >
                {feedbackLoading ? 'Submitting...' : '✓ Submit Official Feedback'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
