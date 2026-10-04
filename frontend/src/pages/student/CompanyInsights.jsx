/**
 * CompanyInsights — Company Reviews & Insights Dashboard.
 * Browse company reviews, view aggregated insights.
 *
 * Sprint 3 — Anjula
 */

import { useState } from 'react';

const MOCK_REVIEWS = [
  { id: '1', company_name: 'TCS', role: 'System Engineer', review_type: 'placement', overall_rating: 4, work_culture_rating: 4, growth_rating: 3, compensation_rating: 3, pros: 'Strong training programs (ILP), job security, and global exposure.', cons: 'Slower career growth, fixed salary structure for initial years.', interview_process: 'Online test → Technical Interview → HR Interview. Focus on coding basics and aptitude.', salary_range: '3.36-7 LPA', student_name: 'Anonymous', upvotes: 34, created_at: '2025-09-20', is_verified: true },
  { id: '2', company_name: 'Infosys', role: 'Systems Engineer', review_type: 'placement', overall_rating: 4, work_culture_rating: 4, growth_rating: 3, compensation_rating: 3, pros: 'Good work-life balance, mysore training campus is excellent.', cons: 'Limited tech exposure initially, bench period possible.', interview_process: 'InfyTQ → Online Assessment → Technical + HR. Focus on InfyTQ platform.', salary_range: '3.6-6.5 LPA', student_name: 'Rahul S.', upvotes: 28, created_at: '2025-09-18', is_verified: true },
  { id: '3', company_name: 'Wipro', role: 'Project Engineer', review_type: 'placement', overall_rating: 3, work_culture_rating: 4, growth_rating: 3, compensation_rating: 3, pros: 'Good mentorship, diverse project exposure.', cons: 'Lower initial CTC compared to peers, slower promotions.', interview_process: 'National talent hunt → Online test → Coding + Interview.', salary_range: '3.5-5 LPA', student_name: 'Anonymous', upvotes: 19, created_at: '2025-09-15' },
  { id: '4', company_name: 'Google', role: 'SDE Intern', review_type: 'internship', overall_rating: 5, work_culture_rating: 5, growth_rating: 5, compensation_rating: 5, pros: 'World-class engineering culture, amazing perks, mentorship.', cons: 'Extremely competitive, imposter syndrome is real.', interview_process: '2 coding rounds + 1 googleyness. Focus heavily on DSA.', salary_range: '1.5L/month stipend', student_name: 'Priya K.', upvotes: 67, created_at: '2025-08-10', is_verified: true },
];

const MOCK_INSIGHTS = [
  { company_name: 'TCS', avg_rating: 3.8, total_reviews: 45, total_hires: 32, avg_package: 4.2, max_package: 7.0, min_package: 3.36, common_roles: ['System Engineer', 'Digital Lead'], selection_ratio: 0.65 },
  { company_name: 'Infosys', avg_rating: 3.9, total_reviews: 38, total_hires: 28, avg_package: 4.5, max_package: 6.5, min_package: 3.6, common_roles: ['Systems Engineer', 'Specialist Programmer'], selection_ratio: 0.55 },
  { company_name: 'Google', avg_rating: 4.8, total_reviews: 8, total_hires: 2, avg_package: 42.0, max_package: 60.0, min_package: 30.0, common_roles: ['SDE', 'SRE'], selection_ratio: 0.05 },
  { company_name: 'Wipro', avg_rating: 3.5, total_reviews: 30, total_hires: 22, avg_package: 3.8, max_package: 5.0, min_package: 3.5, common_roles: ['Project Engineer', 'Turbo Engineer'], selection_ratio: 0.70 },
];

export default function CompanyInsights() {
  const [activeTab, setActiveTab] = useState('reviews');
  const [reviews, setReviews] = useState(MOCK_REVIEWS);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [showReviewModal, setShowReviewModal] = useState(false);

  const filteredReviews = reviews.filter(r => {
    if (search && !r.company_name.toLowerCase().includes(search.toLowerCase())) return false;
    if (typeFilter !== 'all' && r.review_type !== typeFilter) return false;
    return true;
  });

  const renderStars = (n) => '★'.repeat(n) + '☆'.repeat(5 - n);

  const ratingColor = (r) => r >= 4 ? '#22c55e' : r >= 3 ? '#f59e0b' : '#ef4444';

  return (
    <div style={{ padding: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>🏢 Company Insights</h1>
          <p style={{ color: 'var(--text-secondary)', margin: '0.25rem 0 0' }}>Real reviews from students who've been through the placement process.</p>
        </div>
        <button onClick={() => setShowReviewModal(true)} style={{
          padding: '0.6rem 1.2rem', borderRadius: '8px', border: 'none', cursor: 'pointer',
          background: 'var(--accent-primary)', color: '#fff', fontWeight: 600, fontSize: '0.9rem',
        }}>✍️ Write Review</button>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        {[{ key: 'reviews', label: '📝 Reviews' }, { key: 'insights', label: '📊 Company Insights' }].map(tab => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)} style={{
            padding: '0.6rem 1.2rem', borderRadius: '8px', border: 'none', cursor: 'pointer',
            background: activeTab === tab.key ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
            color: activeTab === tab.key ? '#fff' : 'var(--text-secondary)',
            fontWeight: 600, fontSize: '0.9rem',
          }}>{tab.label}</button>
        ))}
      </div>

      {activeTab === 'reviews' && (
        <>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search company..."
              style={{ flex: 1, minWidth: '200px', padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }} />
            <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} style={{
              padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--border-primary)',
              background: 'var(--bg-secondary)', color: 'var(--text-primary)',
            }}>
              <option value="all">All Types</option>
              <option value="placement">Placement</option>
              <option value="internship">Internship</option>
              <option value="ppo">PPO</option>
            </select>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {filteredReviews.map(r => (
              <div key={r.id} style={{
                background: 'var(--bg-secondary)', borderRadius: '12px', padding: '1.5rem',
                border: '1px solid var(--border-primary)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <div>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>{r.company_name}</h3>
                    <p style={{ color: 'var(--accent-primary)', fontSize: '0.85rem', margin: '0.2rem 0' }}>{r.role} · {r.review_type}</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ color: ratingColor(r.overall_rating), fontWeight: 700, fontSize: '1.2rem' }}>{r.overall_rating}/5</div>
                    <div style={{ color: '#f59e0b', fontSize: '0.8rem' }}>{renderStars(r.overall_rating)}</div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                  <div><strong style={{ color: 'var(--text-primary)', fontSize: '0.85rem' }}>Pros:</strong><p style={{ color: '#22c55e', fontSize: '0.82rem', margin: '0.2rem 0 0' }}>{r.pros}</p></div>
                  <div><strong style={{ color: 'var(--text-primary)', fontSize: '0.85rem' }}>Cons:</strong><p style={{ color: '#ef4444', fontSize: '0.82rem', margin: '0.2rem 0 0' }}>{r.cons}</p></div>
                </div>

                {r.interview_process && (
                  <div style={{ background: 'var(--bg-tertiary)', borderRadius: '8px', padding: '0.75rem', marginBottom: '0.75rem' }}>
                    <strong style={{ color: 'var(--text-primary)', fontSize: '0.82rem' }}>Interview Process:</strong>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', margin: '0.2rem 0 0' }}>{r.interview_process}</p>
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  <span>By {r.student_name} · {r.created_at} {r.is_verified ? '✅ Verified' : ''}</span>
                  <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    {r.salary_range && <span style={{ background: 'rgba(34,197,94,0.12)', color: '#22c55e', padding: '0.15rem 0.5rem', borderRadius: '6px' }}>💰 {r.salary_range}</span>}
                    <button onClick={() => setReviews(prev => prev.map(rv => rv.id === r.id ? { ...rv, upvotes: rv.upvotes + 1 } : rv))}
                      style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                      👍 {r.upvotes}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {activeTab === 'insights' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {MOCK_INSIGHTS.map(ci => (
            <div key={ci.company_name} style={{
              background: 'var(--bg-secondary)', borderRadius: '12px', padding: '1.5rem',
              border: '1px solid var(--border-primary)',
              transition: 'transform 0.2s, box-shadow 0.2s',
            }} onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 8px 25px rgba(0,0,0,0.15)'; }}
               onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = ''; }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>{ci.company_name}</h3>
                <div style={{ color: ratingColor(ci.avg_rating), fontWeight: 700, fontSize: '1.1rem' }}>
                  ★ {ci.avg_rating.toFixed(1)}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ background: 'var(--bg-tertiary)', borderRadius: '8px', padding: '0.6rem', textAlign: 'center' }}>
                  <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--accent-primary)' }}>{ci.total_hires}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Hires</div>
                </div>
                <div style={{ background: 'var(--bg-tertiary)', borderRadius: '8px', padding: '0.6rem', textAlign: 'center' }}>
                  <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#22c55e' }}>{ci.avg_package} LPA</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Avg Package</div>
                </div>
                <div style={{ background: 'var(--bg-tertiary)', borderRadius: '8px', padding: '0.6rem', textAlign: 'center' }}>
                  <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f59e0b' }}>{(ci.selection_ratio * 100).toFixed(0)}%</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Selection Rate</div>
                </div>
                <div style={{ background: 'var(--bg-tertiary)', borderRadius: '8px', padding: '0.6rem', textAlign: 'center' }}>
                  <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#6366f1' }}>{ci.total_reviews}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Reviews</div>
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>Common Roles</div>
                <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
                  {ci.common_roles.map(role => (
                    <span key={role} style={{ background: 'rgba(99,102,241,0.12)', color: '#6366f1', padding: '0.15rem 0.5rem', borderRadius: '6px', fontSize: '0.72rem' }}>{role}</span>
                  ))}
                </div>
              </div>

              <div style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Package Range: ₹{ci.min_package}L — ₹{ci.max_package}L
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
