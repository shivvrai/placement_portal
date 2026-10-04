/**
 * AlumniMentorship — Alumni Network & Mentorship Hub for students.
 * Browse alumni mentors, request mentorship, track connections.
 *
 * Sprint 3 — Sakshi Kumari
 */

import { useState, useEffect } from 'react';
import { studentApi } from '../../api/endpoints';

const MOCK_ALUMNI = [
  {
    id: '1', user_name: 'Rajesh Kumar', graduation_year: 2022, department_code: 'CSE',
    current_company: 'Google', current_designation: 'SDE-2',
    expertise_areas: ['System Design', 'DSA', 'Python'], bio: 'Passionate about mentoring juniors in tech.',
    rating: 4.8, total_sessions: 24, is_available_for_mentorship: true, max_mentees: 3,
    linkedin_url: 'https://linkedin.com/in/rajesh-k',
  },
  {
    id: '2', user_name: 'Priya Sharma', graduation_year: 2021, department_code: 'CSE',
    current_company: 'Microsoft', current_designation: 'Program Manager',
    expertise_areas: ['Product Management', 'Agile', 'UX'], bio: 'Helping students transition into PM roles.',
    rating: 4.9, total_sessions: 31, is_available_for_mentorship: true, max_mentees: 2,
  },
  {
    id: '3', user_name: 'Amit Patel', graduation_year: 2023, department_code: 'ECE',
    current_company: 'Amazon', current_designation: 'SDE-1',
    expertise_areas: ['Java', 'AWS', 'Microservices'], bio: 'Recent grad sharing interview tips.',
    rating: 4.5, total_sessions: 12, is_available_for_mentorship: true, max_mentees: 5,
  },
  {
    id: '4', user_name: 'Sneha Reddy', graduation_year: 2020, department_code: 'IT',
    current_company: 'Flipkart', current_designation: 'Senior Data Scientist',
    expertise_areas: ['ML', 'Data Science', 'Statistics'], bio: 'Data science career guidance.',
    rating: 4.7, total_sessions: 18, is_available_for_mentorship: true, max_mentees: 3,
  },
];

const MOCK_CONNECTIONS = [
  { id: 'c1', alumni_name: 'Rajesh Kumar', alumni_company: 'Google', status: 'active', goals: ['System Design', 'DSA'], created_at: '2025-09-15' },
  { id: 'c2', alumni_name: 'Sneha Reddy', alumni_company: 'Flipkart', status: 'pending', goals: ['ML', 'Data Science'], created_at: '2025-10-01' },
];

export default function AlumniMentorship() {
  const [alumni, setAlumni] = useState(MOCK_ALUMNI);
  const [connections, setConnections] = useState(MOCK_CONNECTIONS);
  const [activeTab, setActiveTab] = useState('discover');
  const [search, setSearch] = useState('');
  const [deptFilter, setDeptFilter] = useState('all');
  const [requestModal, setRequestModal] = useState(null);
  const [requestMessage, setRequestMessage] = useState('');
  const [requestGoals, setRequestGoals] = useState('');

  const filteredAlumni = alumni.filter(a => {
    if (search && !a.user_name.toLowerCase().includes(search.toLowerCase()) &&
        !a.current_company.toLowerCase().includes(search.toLowerCase()) &&
        !a.expertise_areas.some(e => e.toLowerCase().includes(search.toLowerCase()))) return false;
    if (deptFilter !== 'all' && a.department_code !== deptFilter) return false;
    return true;
  });

  const handleRequestMentorship = (alumniItem) => {
    const newConn = {
      id: `c${Date.now()}`, alumni_name: alumniItem.user_name,
      alumni_company: alumniItem.current_company, status: 'pending',
      goals: requestGoals.split(',').map(g => g.trim()).filter(Boolean),
      created_at: new Date().toISOString().split('T')[0],
    };
    setConnections(prev => [newConn, ...prev]);
    setRequestModal(null);
    setRequestMessage('');
    setRequestGoals('');
  };

  const renderStars = (rating) => {
    const full = Math.floor(rating);
    return '★'.repeat(full) + (rating % 1 >= 0.5 ? '½' : '') + '☆'.repeat(5 - Math.ceil(rating));
  };

  return (
    <div style={{ padding: '2rem' }}>
      <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
        🎓 Alumni Network & Mentorship
      </h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
        Connect with alumni mentors from top companies for career guidance.
      </p>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        {[{ key: 'discover', label: '🔍 Discover Mentors' }, { key: 'connections', label: '🤝 My Connections' }].map(tab => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)} style={{
            padding: '0.6rem 1.2rem', borderRadius: '8px', border: 'none', cursor: 'pointer',
            background: activeTab === tab.key ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
            color: activeTab === tab.key ? '#fff' : 'var(--text-secondary)',
            fontWeight: 600, fontSize: '0.9rem', transition: 'all 0.2s',
          }}>{tab.label}</button>
        ))}
      </div>

      {activeTab === 'discover' && (
        <>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by name, company, or skill..."
              style={{ flex: 1, minWidth: '200px', padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }} />
            <select value={deptFilter} onChange={e => setDeptFilter(e.target.value)} style={{
              padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--border-primary)',
              background: 'var(--bg-secondary)', color: 'var(--text-primary)',
            }}>
              <option value="all">All Departments</option>
              <option value="CSE">CSE</option><option value="ECE">ECE</option>
              <option value="IT">IT</option><option value="ME">ME</option>
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.25rem' }}>
            {filteredAlumni.map(a => (
              <div key={a.id} style={{
                background: 'var(--bg-secondary)', borderRadius: '12px', padding: '1.5rem',
                border: '1px solid var(--border-primary)', transition: 'transform 0.2s, box-shadow 0.2s',
              }} onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 8px 25px rgba(0,0,0,0.15)'; }}
                 onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = ''; }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <div>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>{a.user_name}</h3>
                    <p style={{ color: 'var(--accent-primary)', fontWeight: 600, fontSize: '0.85rem', margin: '0.2rem 0' }}>
                      {a.current_designation} @ {a.current_company}
                    </p>
                  </div>
                  <span style={{ background: 'rgba(34,197,94,0.12)', color: '#22c55e', padding: '0.2rem 0.6rem', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 600 }}>
                    Class of {a.graduation_year}
                  </span>
                </div>

                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.75rem', lineHeight: 1.4 }}>{a.bio}</p>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginBottom: '0.75rem' }}>
                  {a.expertise_areas.map(skill => (
                    <span key={skill} style={{ background: 'rgba(99,102,241,0.12)', color: '#6366f1', padding: '0.15rem 0.5rem', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 500 }}>
                      {skill}
                    </span>
                  ))}
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    <span style={{ color: '#f59e0b' }}>{renderStars(a.rating)}</span> {a.rating} · {a.total_sessions} sessions
                  </div>
                  <button onClick={() => setRequestModal(a)} style={{
                    padding: '0.45rem 1rem', borderRadius: '8px', border: 'none', cursor: 'pointer',
                    background: 'var(--accent-primary)', color: '#fff', fontWeight: 600, fontSize: '0.8rem',
                  }}>Request Mentor</button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {activeTab === 'connections' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {connections.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
              No mentorship connections yet. Discover mentors to get started!
            </div>
          ) : connections.map(c => (
            <div key={c.id} style={{
              background: 'var(--bg-secondary)', borderRadius: '12px', padding: '1.25rem',
              border: '1px solid var(--border-primary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>{c.alumni_name}</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: '0.25rem 0' }}>{c.alumni_company}</p>
                <div style={{ display: 'flex', gap: '0.35rem', marginTop: '0.4rem' }}>
                  {c.goals.map(g => (
                    <span key={g} style={{ background: 'rgba(99,102,241,0.12)', color: '#6366f1', padding: '0.15rem 0.5rem', borderRadius: '6px', fontSize: '0.7rem' }}>{g}</span>
                  ))}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{
                  display: 'inline-block', padding: '0.25rem 0.75rem', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 600,
                  background: c.status === 'active' ? 'rgba(34,197,94,0.12)' : c.status === 'pending' ? 'rgba(245,158,11,0.12)' : 'rgba(239,68,68,0.12)',
                  color: c.status === 'active' ? '#22c55e' : c.status === 'pending' ? '#f59e0b' : '#ef4444',
                }}>{c.status.charAt(0).toUpperCase() + c.status.slice(1)}</span>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', margin: '0.3rem 0 0' }}>Since {c.created_at}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Request Mentorship Modal */}
      {requestModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}
             onClick={() => setRequestModal(null)}>
          <div style={{ background: 'var(--bg-primary)', borderRadius: '16px', padding: '2rem', width: '450px', maxWidth: '90vw' }}
               onClick={e => e.stopPropagation()}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--text-primary)' }}>
              Request Mentorship with {requestModal.user_name}
            </h2>
            <textarea value={requestMessage} onChange={e => setRequestMessage(e.target.value)}
              placeholder="Introduce yourself and explain why you'd like mentorship..."
              style={{ width: '100%', minHeight: '100px', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', resize: 'vertical', marginBottom: '1rem' }} />
            <input value={requestGoals} onChange={e => setRequestGoals(e.target.value)}
              placeholder="Goals (comma-separated, e.g.: System Design, DSA)"
              style={{ width: '100%', padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', marginBottom: '1rem' }} />
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button onClick={() => setRequestModal(null)} style={{ padding: '0.5rem 1.2rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'transparent', color: 'var(--text-secondary)', cursor: 'pointer' }}>Cancel</button>
              <button onClick={() => handleRequestMentorship(requestModal)} style={{ padding: '0.5rem 1.2rem', borderRadius: '8px', border: 'none', background: 'var(--accent-primary)', color: '#fff', fontWeight: 600, cursor: 'pointer' }}>Send Request</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
