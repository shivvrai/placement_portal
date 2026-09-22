/**
 * Proposal Manager — Faculty / HOD interface for managing BoS curriculum proposals.
 * List, view, review (HOD), download .docx.
 */

import { useState, useEffect } from 'react';
import { curriculumApi } from '../../api/endpoints';

const STATUS_STYLES = {
  draft: { bg: '#1e293b', color: '#94a3b8', label: 'Draft' },
  submitted: { bg: '#1e3a5f', color: '#7dd3fc', label: 'Submitted' },
  approved: { bg: '#064e3b', color: '#6ee7b7', label: 'Approved' },
  rejected: { bg: '#7f1d1d', color: '#fca5a5', label: 'Rejected' },
};

export default function ProposalManager() {
  const [proposals, setProposals] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedDetail, setSelectedDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reviewing, setReviewing] = useState(false);
  const [reviewComments, setReviewComments] = useState('');
  const [generating, setGenerating] = useState(false);
  const [genDept, setGenDept] = useState('CS');
  const [genYear, setGenYear] = useState('2026-27');

  useEffect(() => {
    loadProposals();
  }, []);

  const loadProposals = async () => {
    setLoading(true);
    try {
      const res = await curriculumApi.listProposals();
      setProposals(res.data || []);
    } catch { }
    setLoading(false);
  };

  const viewDetail = async (id) => {
    setSelectedId(id);
    try {
      const res = await curriculumApi.getProposal(id);
      setSelectedDetail(res.data);
    } catch { }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await curriculumApi.createProposal({ department_code: genDept, academic_year: genYear });
      await loadProposals();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to generate proposal');
    }
    setGenerating(false);
  };

  const handleDownload = async (id) => {
    try {
      const res = await curriculumApi.downloadProposal(id);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `BoS_Proposal_${id}.docx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      alert('Failed to download');
    }
  };

  const handleSubmit = async (id) => {
    try {
      await curriculumApi.submitProposal(id);
      await loadProposals();
      if (selectedDetail && selectedDetail.id === id) {
        viewDetail(id);
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to submit');
    }
  };

  const handleReview = async (id, status) => {
    try {
      await curriculumApi.updateProposalStatus(id, status, reviewComments);
      setReviewing(false);
      setReviewComments('');
      await loadProposals();
      if (selectedDetail) viewDetail(id);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update status');
    }
  };

  const formatDate = (iso) => iso ? new Date(iso).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
  }) : 'N/A';

  // ═══════════════════════════════════════════════════════════════════
  // DETAIL VIEW
  // ═══════════════════════════════════════════════════════════════════
  if (selectedDetail) {
    const p = selectedDetail;
    const gap = p.gap_analysis || {};
    const proposal = p.proposed_subjects || {};
    const impact = p.impact_projection || {};
    const ss = STATUS_STYLES[p.status] || STATUS_STYLES.draft;

    return (
      <div style={{ padding: 24, maxWidth: 900, margin: '0 auto' }}>
        <button onClick={() => { setSelectedId(null); setSelectedDetail(null); }} style={{
          padding: '8px 16px', borderRadius: 8, border: '1px solid #334155',
          background: '#1e293b', color: '#94a3b8', fontSize: 13, cursor: 'pointer', marginBottom: 20,
        }}>← Back to list</button>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 24 }}>
          <div>
            <h2 style={{ fontSize: 22, fontWeight: 800, color: '#f1f5f9', marginBottom: 4 }}>
              📋 BoS Proposal — {p.department_code}
            </h2>
            <p style={{ color: '#64748b', fontSize: 13 }}>
              Academic Year: {p.academic_year} • Created: {formatDate(p.created_at)}
            </p>
          </div>
          <span style={{
            padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 700,
            background: ss.bg, color: ss.color,
          }}>{ss.label}</span>
        </div>

        {/* Gap Analysis Summary */}
        <div style={{
          padding: 20, borderRadius: 14, background: '#1e293b',
          border: '1px solid #334155', marginBottom: 20,
        }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: '#cbd5e1', marginBottom: 12 }}>🔍 Gap Analysis</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 16 }}>
            {[
              { label: 'Coverage', value: `${gap.coverage_pct || 0}%`, color: '#a5b4fc' },
              { label: 'Gap Skills', value: (gap.gap_skills || []).length, color: '#ef4444' },
              { label: 'Active Drives', value: gap.active_drives || 0, color: '#10b981' },
              { label: 'Subjects', value: gap.total_subjects || 0, color: '#f59e0b' },
            ].map(s => (
              <div key={s.label} style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 800, color: s.color }}>{s.value}</div>
                <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{s.label}</div>
              </div>
            ))}
          </div>
          {(gap.gap_skills || []).length > 0 && (
            <div>
              <div style={{ fontSize: 12, color: '#94a3b8', fontWeight: 600, marginBottom: 6 }}>Top Gap Skills:</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {(gap.gap_skills || []).slice(0, 12).map((g, i) => (
                  <span key={i} style={{
                    padding: '4px 10px', borderRadius: 6, background: '#312e81',
                    color: '#a5b4fc', fontSize: 11, fontWeight: 600,
                  }}>{g.skill} ({g.demand_count})</span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Proposed Subjects */}
        {(proposal.proposed_subjects || []).length > 0 && (
          <div style={{ marginBottom: 20 }}>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: '#cbd5e1', marginBottom: 12 }}>📚 Proposed Subjects</h3>
            {(proposal.proposed_subjects || []).map((sub, i) => (
              <details key={i} style={{
                marginBottom: 8, borderRadius: 12, background: '#1e293b',
                border: '1px solid #334155', overflow: 'hidden',
              }}>
                <summary style={{
                  padding: '14px 16px', cursor: 'pointer', color: '#e2e8f0',
                  fontWeight: 600, fontSize: 14, display: 'flex', justifyContent: 'space-between',
                }}>
                  <span>{sub.code_suggestion} — {sub.name}</span>
                  <span style={{ fontSize: 12, color: '#64748b' }}>
                    {sub.credits} credits • Sem {sub.semester}
                  </span>
                </summary>
                <div style={{ padding: '0 16px 16px' }}>
                  {sub.topics && (
                    <div style={{ marginBottom: 10 }}>
                      <div style={{ fontSize: 12, color: '#94a3b8', fontWeight: 600, marginBottom: 4 }}>Topics:</div>
                      <div style={{ fontSize: 13, color: '#cbd5e1' }}>{sub.topics.join(' • ')}</div>
                    </div>
                  )}
                  {sub.learning_outcomes && (
                    <div style={{ marginBottom: 10 }}>
                      <div style={{ fontSize: 12, color: '#94a3b8', fontWeight: 600, marginBottom: 4 }}>Learning Outcomes:</div>
                      {sub.learning_outcomes.map((lo, j) => (
                        <div key={j} style={{ fontSize: 12, color: '#cbd5e1', marginLeft: 8 }}>• {lo}</div>
                      ))}
                    </div>
                  )}
                </div>
              </details>
            ))}
          </div>
        )}

        {/* Impact */}
        <div style={{
          padding: 20, borderRadius: 14, background: '#064e3b',
          border: '1px solid #065f46', marginBottom: 24,
        }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: '#6ee7b7', marginBottom: 8 }}>📈 Projected Impact</h3>
          <p style={{ fontSize: 14, color: '#a7f3d0' }}>
            Coverage: {impact.current_coverage || 0}% → {impact.projected_coverage || 0}%
            <strong style={{ color: '#10b981' }}> (+{impact.improvement_pct || 0}%)</strong>
          </p>
        </div>

        {/* HOD Comments */}
        {p.hod_comments && (
          <div style={{
            padding: 16, borderRadius: 12, background: '#1e293b',
            border: '1px solid #334155', marginBottom: 20,
          }}>
            <div style={{ fontSize: 13, color: '#94a3b8', fontWeight: 600, marginBottom: 6 }}>
              HOD Review Comments:
            </div>
            <p style={{ fontSize: 14, color: '#e2e8f0' }}>{p.hod_comments}</p>
          </div>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', gap: 12 }}>
          <button onClick={() => handleDownload(p.id)} style={{
            padding: '12px 20px', borderRadius: 10, border: '1px solid #334155',
            background: '#1e293b', color: '#a5b4fc', fontSize: 13, fontWeight: 600, cursor: 'pointer',
          }}>📄 Download .docx</button>

          {p.status === 'draft' && (
            <button onClick={() => handleSubmit(p.id)} style={{
              padding: '12px 20px', borderRadius: 10, border: 'none',
              background: '#6366f1', color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer',
            }}>📤 Submit to HOD</button>
          )}

          {p.status === 'submitted' && !reviewing && (
            <button onClick={() => setReviewing(true)} style={{
              padding: '12px 20px', borderRadius: 10, border: 'none',
              background: '#10b981', color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer',
            }}>🔍 Review (HOD)</button>
          )}
        </div>

        {/* Review Form */}
        {reviewing && (
          <div style={{
            marginTop: 20, padding: 20, borderRadius: 14,
            background: '#1e293b', border: '1px solid #334155',
          }}>
            <h4 style={{ color: '#cbd5e1', fontSize: 14, fontWeight: 600, marginBottom: 12 }}>HOD Review</h4>
            <textarea
              value={reviewComments}
              onChange={e => setReviewComments(e.target.value)}
              placeholder="Add your comments..."
              rows={3}
              style={{
                width: '100%', padding: '10px 14px', borderRadius: 10, border: '1px solid #334155',
                background: '#0f172a', color: '#f1f5f9', fontSize: 13, resize: 'none',
                fontFamily: 'inherit', marginBottom: 12,
              }}
            />
            <div style={{ display: 'flex', gap: 12 }}>
              <button onClick={() => handleReview(p.id, 'approved')} style={{
                padding: '10px 20px', borderRadius: 8, border: 'none',
                background: '#10b981', color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer',
              }}>✓ Approve</button>
              <button onClick={() => handleReview(p.id, 'rejected')} style={{
                padding: '10px 20px', borderRadius: 8, border: 'none',
                background: '#ef4444', color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer',
              }}>✗ Reject</button>
              <button onClick={() => setReviewing(false)} style={{
                padding: '10px 20px', borderRadius: 8, border: '1px solid #334155',
                background: 'transparent', color: '#94a3b8', fontSize: 13, cursor: 'pointer',
              }}>Cancel</button>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ═══════════════════════════════════════════════════════════════════
  // LIST VIEW
  // ═══════════════════════════════════════════════════════════════════
  return (
    <div style={{ padding: 24, maxWidth: 1000, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 800, color: '#f1f5f9', marginBottom: 4 }}>
            📋 Curriculum Proposals
          </h1>
          <p style={{ color: '#94a3b8', fontSize: 14 }}>
            AI-generated BoS proposals with gap analysis and .docx export
          </p>
        </div>
      </div>

      {/* Generate New */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12, padding: 20,
        borderRadius: 14, background: '#1e293b', border: '1px solid #334155', marginBottom: 24,
      }}>
        <select value={genDept} onChange={e => setGenDept(e.target.value)} style={{
          padding: '10px 14px', borderRadius: 8, border: '1px solid #334155',
          background: '#0f172a', color: '#f1f5f9', fontSize: 13,
        }}>
          {['CS', 'IT', 'ECE', 'EE', 'ME', 'CE'].map(d => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
        <input value={genYear} onChange={e => setGenYear(e.target.value)} placeholder="2026-27" style={{
          padding: '10px 14px', borderRadius: 8, border: '1px solid #334155',
          background: '#0f172a', color: '#f1f5f9', fontSize: 13, width: 100,
        }} />
        <button onClick={handleGenerate} disabled={generating} style={{
          padding: '10px 20px', borderRadius: 10, border: 'none',
          background: generating ? '#475569' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          color: '#fff', fontSize: 14, fontWeight: 700, cursor: generating ? 'not-allowed' : 'pointer',
        }}>{generating ? '⏳ Generating...' : '🤖 Generate New Proposal'}</button>
      </div>

      {/* Proposals List */}
      {loading ? (
        <p style={{ color: '#94a3b8' }}>Loading proposals...</p>
      ) : proposals.length === 0 ? (
        <div style={{
          padding: 40, textAlign: 'center', borderRadius: 16,
          background: '#1e293b', border: '1px solid #334155',
        }}>
          <p style={{ color: '#94a3b8' }}>No proposals yet. Generate your first BoS proposal above!</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {proposals.map(p => {
            const ss = STATUS_STYLES[p.status] || STATUS_STYLES.draft;
            const impact = p.impact_projection || {};
            return (
              <div key={p.id} onClick={() => viewDetail(p.id)} style={{
                padding: '18px 20px', borderRadius: 14, background: '#1e293b',
                border: '1px solid #334155', display: 'flex', alignItems: 'center',
                gap: 16, cursor: 'pointer', transition: 'all 0.2s',
              }}
                onMouseEnter={e => e.currentTarget.style.borderColor = '#6366f1'}
                onMouseLeave={e => e.currentTarget.style.borderColor = '#334155'}
              >
                <div style={{
                  width: 44, height: 44, borderRadius: 10, background: '#312e81',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 18, flexShrink: 0,
                }}>📋</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 15, fontWeight: 700, color: '#e2e8f0' }}>
                    {p.department_code} — {p.academic_year}
                  </div>
                  <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>
                    {formatDate(p.created_at)}
                    {impact.improvement_pct ? ` • +${impact.improvement_pct}% coverage improvement` : ''}
                  </div>
                </div>
                <span style={{
                  padding: '5px 12px', borderRadius: 20, fontSize: 11, fontWeight: 700,
                  background: ss.bg, color: ss.color,
                }}>{ss.label}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
