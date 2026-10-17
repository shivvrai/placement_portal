/**
 * CompanyReviews — Anonymous Company Reviews & Peer Interview Intelligence Hub.
 * Glassdoor-style company cards, interview breakdown, topic tags, and review submission.
 *
 * Task 1 (Anjula Final Submission)
 */

import { useState, useEffect, useCallback } from 'react';
import { companyReviewsApi } from '../../api/endpoints';

const MOCK_FALLBACK_REVIEWS = [
  {
    id: '1',
    company_name: 'Google',
    role: 'Software Development Engineer',
    academic_year: '2025-26',
    overall_rating: 5,
    difficulty_rating: 5,
    selection_outcome: 'Selected',
    offered_ctc_lpa: 38.5,
    stipend_monthly: 110000,
    round_breakdown: [
      { round_number: 1, round_name: 'Online Assessment', duration_mins: 90, platform: 'HackerEarth', description: '2 medium-hard graph/DP problems.' },
      { round_number: 2, round_name: 'Technical Round 1', duration_mins: 45, platform: 'Google Meet', description: 'Trie and dynamic programming on trees.' },
      { round_number: 3, round_name: 'Googliness & Leadership', duration_mins: 45, platform: 'Google Meet', description: 'Situational behavioral questions.' },
    ],
    question_tags: ['Dynamic Programming', 'Trie', 'Graph BFS', 'System Design'],
    pros: 'Incredible engineering culture, top-tier compensation, and friendly interviewers.',
    cons: 'High problem difficulty bar requires 6+ months of dedicated LeetCode prep.',
    advice_to_juniors: 'Focus heavily on problem-solving patterns rather than memorizing solutions.',
    upvotes: 42,
    created_at: '2026-09-12',
  },
  {
    id: '2',
    company_name: 'TCS',
    role: 'Digital Ninja / Innovator',
    academic_year: '2025-26',
    overall_rating: 4,
    difficulty_rating: 3,
    selection_outcome: 'Selected',
    offered_ctc_lpa: 7.2,
    stipend_monthly: 25000,
    round_breakdown: [
      { round_number: 1, round_name: 'NQT Aptitude & Coding', duration_mins: 120, platform: 'iON', description: 'Advanced quantitative aptitude and 2 DSA questions.' },
      { round_number: 2, round_name: 'Technical + Managerial', duration_mins: 35, platform: 'MS Teams', description: 'OOPS concepts, SQL indexing, and final year project.' },
    ],
    question_tags: ['SQL Joins', 'Binary Search', 'OOPS', 'DBMS Indexing'],
    pros: 'Consistent hiring volumes and good early-career corporate training.',
    cons: 'Results take 3-4 weeks to be announced.',
    advice_to_juniors: 'Master foundational DBMS queries and your resume projects.',
    upvotes: 27,
    created_at: '2026-09-18',
  },
];

const MOCK_FALLBACK_INSIGHTS = [
  {
    company_name: 'Google',
    total_reviews: 14,
    avg_rating: 4.8,
    avg_difficulty: 4.6,
    selection_rate_pct: 14.3,
    topic_tags_cloud: ['Dynamic Programming', 'Graphs', 'System Design', 'Trie'],
    salary_range: '₹32.0 - ₹48.0 LPA',
  },
  {
    company_name: 'TCS',
    total_reviews: 48,
    avg_rating: 3.9,
    avg_difficulty: 2.8,
    selection_rate_pct: 68.7,
    topic_tags_cloud: ['SQL Joins', 'OOPs', 'Array Manipulation', 'Java Basics'],
    salary_range: '₹3.6 - ₹9.0 LPA',
  },
];

export default function CompanyReviews() {
  const [activeTab, setActiveTab] = useState('reviews'); // 'reviews' | 'insights'
  const [reviews, setReviews] = useState(MOCK_FALLBACK_REVIEWS);
  const [insights, setInsights] = useState(MOCK_FALLBACK_INSIGHTS);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [outcomeFilter, setOutcomeFilter] = useState('all');
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [notification, setNotification] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    company_name: '',
    role: '',
    academic_year: '2025-26',
    overall_rating: 5,
    difficulty_rating: 3,
    selection_outcome: 'Selected',
    offered_ctc_lpa: '',
    stipend_monthly: '',
    pros: '',
    cons: '',
    advice_to_juniors: '',
    question_tags: '',
    round_breakdown: [
      { round_number: 1, round_name: 'Online Assessment', duration_mins: 60, platform: 'HackerRank', description: '' },
    ],
  });

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [revRes, insRes] = await Promise.allSettled([
        companyReviewsApi.getReviews({ page: 1, page_size: 50 }),
        companyReviewsApi.getInsights(),
      ]);

      if (revRes.status === 'fulfilled' && revRes.value?.data?.data?.length) {
        setReviews(revRes.value.data.data);
      }
      if (insRes.status === 'fulfilled' && Array.isArray(insRes.value?.data)) {
        setInsights(insRes.value.data);
      }
    } catch {
      // Keep fallbacks
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleUpvote = async (id) => {
    try {
      await companyReviewsApi.upvoteReview(id);
      setReviews(prev => prev.map(r => r.id === id ? { ...r, upvotes: (r.upvotes || 0) + 1 } : r));
    } catch {
      // Optimistic update fallback
      setReviews(prev => prev.map(r => r.id === id ? { ...r, upvotes: (r.upvotes || 0) + 1 } : r));
    }
  };

  const handleAddRound = () => {
    setFormData(prev => ({
      ...prev,
      round_breakdown: [
        ...prev.round_breakdown,
        {
          round_number: prev.round_breakdown.length + 1,
          round_name: `Technical Round ${prev.round_breakdown.length}`,
          duration_mins: 45,
          platform: 'Google Meet',
          description: '',
        },
      ],
    }));
  };

  const handleSubmitReview = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = {
        company_name: formData.company_name.trim(),
        role: formData.role.trim(),
        academic_year: formData.academic_year,
        overall_rating: Number(formData.overall_rating),
        difficulty_rating: Number(formData.difficulty_rating),
        selection_outcome: formData.selection_outcome,
        offered_ctc_lpa: formData.offered_ctc_lpa ? Number(formData.offered_ctc_lpa) : null,
        stipend_monthly: formData.stipend_monthly ? Number(formData.stipend_monthly) : null,
        pros: formData.pros,
        cons: formData.cons,
        advice_to_juniors: formData.advice_to_juniors,
        question_tags: formData.question_tags
          ? formData.question_tags.split(',').map(t => t.trim()).filter(Boolean)
          : [],
        round_breakdown: formData.round_breakdown,
      };

      const res = await companyReviewsApi.submitReview(payload);
      if (res.data) {
        setReviews(prev => [res.data, ...prev]);
      }
      setNotification('🎉 Review submitted anonymously. Thank you for helping your peers!');
      setShowModal(false);
      setTimeout(() => setNotification(null), 5000);
    } catch (err) {
      console.error(err);
      setNotification('❌ Could not submit review. Please check all required fields.');
      setTimeout(() => setNotification(null), 4000);
    } finally {
      setSubmitting(false);
    }
  };

  const filteredReviews = reviews.filter(r => {
    const matchesSearch = !search ||
      r.company_name.toLowerCase().includes(search.toLowerCase()) ||
      r.role.toLowerCase().includes(search.toLowerCase()) ||
      (r.question_tags || []).some(t => t.toLowerCase().includes(search.toLowerCase()));
    const matchesOutcome = outcomeFilter === 'all' || (r.selection_outcome && r.selection_outcome.toLowerCase() === outcomeFilter.toLowerCase());
    return matchesSearch && matchesOutcome;
  });

  const renderStars = (n) => '★'.repeat(Math.round(n || 0)) + '☆'.repeat(Math.max(0, 5 - Math.round(n || 0)));

  return (
    <div style={{ padding: '2rem', maxWidth: '1280px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
            🏢 Anonymous Peer Interview Intelligence Hub
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: '0.35rem 0 0' }}>
            Real interview round breakdowns, tested coding topics, and realistic compensation shared by seniors.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          style={{
            padding: '0.65rem 1.4rem',
            borderRadius: '8px',
            border: 'none',
            cursor: 'pointer',
            background: 'var(--accent-primary)',
            color: '#fff',
            fontWeight: 600,
            fontSize: '0.92rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            boxShadow: '0 4px 12px rgba(99, 102, 241, 0.25)',
          }}
        >
          ✍️ Share Anonymous Experience
        </button>
      </div>

      {notification && (
        <div style={{
          padding: '0.8rem 1.2rem',
          borderRadius: '8px',
          marginBottom: '1.5rem',
          background: notification.includes('❌') ? 'rgba(239, 68, 68, 0.15)' : 'rgba(34, 197, 94, 0.15)',
          border: `1px solid ${notification.includes('❌') ? '#ef4444' : '#22c55e'}`,
          color: notification.includes('❌') ? '#ef4444' : '#22c55e',
          fontWeight: 600,
          fontSize: '0.9rem',
        }}>
          {notification}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <button
          onClick={() => setActiveTab('reviews')}
          style={{
            padding: '0.6rem 1.25rem',
            borderRadius: '8px',
            border: 'none',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: '0.9rem',
            background: activeTab === 'reviews' ? 'var(--accent-primary)' : 'var(--bg-secondary)',
            color: activeTab === 'reviews' ? '#fff' : 'var(--text-secondary)',
          }}
        >
          💬 Interview Reviews ({reviews.length})
        </button>
        <button
          onClick={() => setActiveTab('insights')}
          style={{
            padding: '0.6rem 1.25rem',
            borderRadius: '8px',
            border: 'none',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: '0.9rem',
            background: activeTab === 'insights' ? 'var(--accent-primary)' : 'var(--bg-secondary)',
            color: activeTab === 'insights' ? '#fff' : 'var(--text-secondary)',
          }}
        >
          📊 Aggregated Company Metrics ({insights.length})
        </button>
      </div>

      {/* REVIEWS TAB */}
      {activeTab === 'reviews' && (
        <>
          {/* Search & Filters */}
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
            <input
              type="text"
              placeholder="Search company, role, or topic (e.g. Google, SDE, Graphs)..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{
                flex: 1,
                minWidth: '260px',
                padding: '0.65rem 1rem',
                borderRadius: '8px',
                border: '1px solid var(--border-primary)',
                background: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
              }}
            />
            <select
              value={outcomeFilter}
              onChange={e => setOutcomeFilter(e.target.value)}
              style={{
                padding: '0.65rem 1rem',
                borderRadius: '8px',
                border: '1px solid var(--border-primary)',
                background: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
              }}
            >
              <option value="all">All Outcomes</option>
              <option value="selected">Selected</option>
              <option value="rejected">Rejected</option>
              <option value="offer declined">Offer Declined</option>
            </select>
          </div>

          {/* Review Cards Grid */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {filteredReviews.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
                No reviews match your filters. Be the first to share one!
              </div>
            ) : (
              filteredReviews.map(r => (
                <div
                  key={r.id}
                  style={{
                    background: 'var(--bg-secondary)',
                    borderRadius: '12px',
                    padding: '1.5rem',
                    border: '1px solid var(--border-primary)',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                          {r.company_name}
                        </h3>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '6px',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          background: r.selection_outcome === 'Selected' ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
                          color: r.selection_outcome === 'Selected' ? '#22c55e' : '#ef4444',
                        }}>
                          {r.selection_outcome || 'Verified Submission'}
                        </span>
                      </div>
                      <p style={{ margin: '0.2rem 0', color: 'var(--accent-primary)', fontSize: '0.9rem', fontWeight: 600 }}>
                        {r.role} · Batch {r.academic_year || '2025-26'}
                      </p>
                    </div>

                    <div style={{ display: 'flex', gap: '1.5rem', textAlign: 'right' }}>
                      <div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>OVERALL</div>
                        <div style={{ color: '#f59e0b', fontSize: '0.95rem' }}>{renderStars(r.overall_rating)}</div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>DIFFICULTY</div>
                        <div style={{
                          fontWeight: 700,
                          fontSize: '0.95rem',
                          color: (r.difficulty_rating || 3) >= 4 ? '#ef4444' : (r.difficulty_rating || 3) >= 3 ? '#f59e0b' : '#22c55e',
                        }}>
                          {r.difficulty_rating || 3} / 5
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Compensation Badge */}
                  {(r.offered_ctc_lpa || r.stipend_monthly) && (
                    <div style={{
                      margin: '0.75rem 0',
                      padding: '0.5rem 0.85rem',
                      background: 'rgba(99,102,241,0.08)',
                      borderRadius: '8px',
                      display: 'inline-flex',
                      gap: '12px',
                      fontSize: '0.85rem',
                    }}>
                      {r.offered_ctc_lpa && <span>💰 <strong>CTC Offered:</strong> ₹{r.offered_ctc_lpa} LPA</span>}
                      {r.stipend_monthly && <span>⏳ <strong>Monthly Stipend:</strong> ₹{r.stipend_monthly.toLocaleString()}/mo</span>}
                    </div>
                  )}

                  {/* Round breakdown accordion/list */}
                  {Array.isArray(r.round_breakdown) && r.round_breakdown.length > 0 && (
                    <div style={{ marginTop: '0.75rem', borderTop: '1px solid var(--border-primary)', paddingTop: '0.75rem' }}>
                      <strong style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Recruitment Rounds Breakdown:</strong>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem', marginTop: '0.5rem' }}>
                        {r.round_breakdown.map((rnd, i) => (
                          <div key={i} style={{ background: 'var(--bg-tertiary)', padding: '0.65rem 0.85rem', borderRadius: '8px', fontSize: '0.82rem' }}>
                            <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                              R{rnd.round_number || i + 1}: {rnd.round_name}
                            </div>
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>
                              ⏱️ {rnd.duration_mins || 45} mins · 💻 {rnd.platform || 'Online'}
                            </div>
                            {rnd.description && <p style={{ margin: '0.35rem 0 0', color: 'var(--text-muted)' }}>{rnd.description}</p>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Question Tags */}
                  {Array.isArray(r.question_tags) && r.question_tags.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', margin: '0.85rem 0' }}>
                      {r.question_tags.map((tag, i) => (
                        <span key={i} style={{
                          padding: '2px 8px',
                          borderRadius: '999px',
                          background: 'rgba(99,102,241,0.12)',
                          color: 'var(--accent-primary)',
                          fontSize: '0.78rem',
                          fontWeight: 600,
                        }}>
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Advice & Upvote Footer */}
                  {r.advice_to_juniors && (
                    <div style={{ fontSize: '0.85rem', margin: '0.5rem 0', color: 'var(--text-secondary)' }}>
                      💡 <strong>Advice to Juniors:</strong> {r.advice_to_juniors}
                    </div>
                  )}

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem', paddingTop: '0.5rem', borderTop: '1px solid var(--border-primary)' }}>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      🔒 Anonymous Verified Student · {r.created_at?.slice(0, 10)}
                    </span>
                    <button
                      onClick={() => handleUpvote(r.id)}
                      style={{
                        padding: '0.35rem 0.75rem',
                        borderRadius: '6px',
                        border: '1px solid var(--border-primary)',
                        background: 'var(--bg-tertiary)',
                        color: 'var(--text-primary)',
                        cursor: 'pointer',
                        fontSize: '0.82rem',
                        fontWeight: 600,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                    >
                      👍 Helpful ({r.upvotes || 0})
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </>
      )}

      {/* INSIGHTS TAB */}
      {activeTab === 'insights' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {insights.map(item => (
            <div
              key={item.company_name}
              style={{
                background: 'var(--bg-secondary)',
                borderRadius: '12px',
                padding: '1.5rem',
                border: '1px solid var(--border-primary)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {item.company_name}
                </h3>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  {item.total_reviews} reviews
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ background: 'var(--bg-tertiary)', padding: '0.75rem', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Avg Difficulty</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 700, color: item.avg_difficulty >= 4 ? '#ef4444' : '#f59e0b' }}>
                    {item.avg_difficulty ? Number(item.avg_difficulty).toFixed(1) : '3.0'} / 5.0
                  </div>
                </div>
                <div style={{ background: 'var(--bg-tertiary)', padding: '0.75rem', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Selection Rate</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#22c55e' }}>
                    {item.selection_rate_pct ? Number(item.selection_rate_pct).toFixed(1) : '50.0'}%
                  </div>
                </div>
              </div>

              {item.salary_range && (
                <div style={{ fontSize: '0.85rem', marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
                  💼 <strong>Salary Range:</strong> {item.salary_range}
                </div>
              )}

              {Array.isArray(item.topic_tags_cloud) && item.topic_tags_cloud.length > 0 && (
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>FREQUENTLY TESTED:</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                    {item.topic_tags_cloud.map((t, idx) => (
                      <span key={idx} style={{
                        padding: '2px 8px',
                        borderRadius: '999px',
                        background: 'rgba(99,102,241,0.1)',
                        color: 'var(--accent-primary)',
                        fontSize: '0.75rem',
                      }}>
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* SUBMISSION MODAL */}
      {showModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.6)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '1rem',
        }}>
          <div style={{
            background: 'var(--bg-secondary)',
            borderRadius: '16px',
            border: '1px solid var(--border-primary)',
            padding: '2rem',
            width: '100%',
            maxWidth: '680px',
            maxHeight: '90vh',
            overflowY: 'auto',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                ✍️ Submit Anonymous Interview Review
              </h2>
              <button
                onClick={() => setShowModal(false)}
                style={{ background: 'none', border: 'none', fontSize: '1.3rem', cursor: 'pointer', color: 'var(--text-secondary)' }}
              >
                ✕
              </button>
            </div>

            <p style={{ fontSize: '0.82rem', color: '#f59e0b', background: 'rgba(245,158,11,0.1)', padding: '0.6rem 0.85rem', borderRadius: '8px', margin: '0 0 1.25rem' }}>
              🔒 <strong>Complete Privacy Guarantee:</strong> Your student ID will never be linked to this review publicly.
            </p>

            <form onSubmit={handleSubmitReview} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Company Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Microsoft, Google, TCS"
                    value={formData.company_name}
                    onChange={e => setFormData({ ...formData, company_name: e.target.value })}
                    style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', marginTop: '4px' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Job Role Applied For *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. SDE 1, Data Analyst"
                    value={formData.role}
                    onChange={e => setFormData({ ...formData, role: e.target.value })}
                    style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', marginTop: '4px' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Overall Rating (1-5)</label>
                  <input
                    type="number"
                    min="1"
                    max="5"
                    value={formData.overall_rating}
                    onChange={e => setFormData({ ...formData, overall_rating: e.target.value })}
                    style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', marginTop: '4px' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Difficulty (1-5)</label>
                  <input
                    type="number"
                    min="1"
                    max="5"
                    value={formData.difficulty_rating}
                    onChange={e => setFormData({ ...formData, difficulty_rating: e.target.value })}
                    style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', marginTop: '4px' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Selection Outcome</label>
                  <select
                    value={formData.selection_outcome}
                    onChange={e => setFormData({ ...formData, selection_outcome: e.target.value })}
                    style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', marginTop: '4px' }}
                  >
                    <option value="Selected">Selected</option>
                    <option value="Rejected">Rejected</option>
                    <option value="Offer Declined">Offer Declined</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Offered CTC (LPA) (Optional)</label>
                  <input
                    type="number"
                    step="0.1"
                    placeholder="e.g. 12.5"
                    value={formData.offered_ctc_lpa}
                    onChange={e => setFormData({ ...formData, offered_ctc_lpa: e.target.value })}
                    style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', marginTop: '4px' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Monthly Stipend (₹) (Optional)</label>
                  <input
                    type="number"
                    placeholder="e.g. 45000"
                    value={formData.stipend_monthly}
                    onChange={e => setFormData({ ...formData, stipend_monthly: e.target.value })}
                    style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', marginTop: '4px' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Question Topics (comma separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Dynamic Programming, Graphs, SQL Joins, System Design"
                  value={formData.question_tags}
                  onChange={e => setFormData({ ...formData, question_tags: e.target.value })}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', marginTop: '4px' }}
                />
              </div>

              {/* Rounds Breakdown */}
              <div style={{ border: '1px solid var(--border-primary)', borderRadius: '8px', padding: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>Recruitment Rounds Detail</label>
                  <button
                    type="button"
                    onClick={handleAddRound}
                    style={{ background: 'none', border: 'none', color: 'var(--accent-primary)', cursor: 'pointer', fontWeight: 600, fontSize: '0.82rem' }}
                  >
                    + Add Another Round
                  </button>
                </div>
                {formData.round_breakdown.map((rnd, i) => (
                  <div key={i} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 2fr', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <input
                      type="text"
                      placeholder="Round Name"
                      value={rnd.round_name}
                      onChange={e => {
                        const copy = [...formData.round_breakdown];
                        copy[i].round_name = e.target.value;
                        setFormData({ ...formData, round_breakdown: copy });
                      }}
                      style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border-primary)', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', fontSize: '0.82rem' }}
                    />
                    <input
                      type="number"
                      placeholder="Mins"
                      value={rnd.duration_mins}
                      onChange={e => {
                        const copy = [...formData.round_breakdown];
                        copy[i].duration_mins = Number(e.target.value);
                        setFormData({ ...formData, round_breakdown: copy });
                      }}
                      style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border-primary)', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', fontSize: '0.82rem' }}
                    />
                    <input
                      type="text"
                      placeholder="Description / Topics covered"
                      value={rnd.description}
                      onChange={e => {
                        const copy = [...formData.round_breakdown];
                        copy[i].description = e.target.value;
                        setFormData({ ...formData, round_breakdown: copy });
                      }}
                      style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border-primary)', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', fontSize: '0.82rem' }}
                    />
                  </div>
                ))}
              </div>

              <div>
                <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Advice to Juniors</label>
                <textarea
                  rows="2"
                  placeholder="What resources or strategies would you recommend to a candidate preparing for this company?"
                  value={formData.advice_to_juniors}
                  onChange={e => setFormData({ ...formData, advice_to_juniors: e.target.value })}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', marginTop: '4px' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  style={{ padding: '0.6rem 1.2rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'transparent', color: 'var(--text-secondary)', cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  style={{ padding: '0.6rem 1.4rem', borderRadius: '8px', border: 'none', background: 'var(--accent-primary)', color: '#fff', fontWeight: 600, cursor: 'pointer' }}
                >
                  {submitting ? 'Submitting...' : 'Submit Anonymous Review'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
