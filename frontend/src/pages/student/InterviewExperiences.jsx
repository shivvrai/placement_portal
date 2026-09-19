/**
 * Student Company Interview Experiences & Question Bank Hub.
 * Lets students browse past interview questions, difficulty levels, and tips shared by seniors,
 * as well as submit their own experiences.
 */

import { useState, useEffect } from 'react';
import { experiencesApi } from '../../api/endpoints';

function formatTimeAgo(isoString) {
  if (!isoString) return '';
  const now = new Date();
  const date = new Date(isoString);
  const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 30) return `${diffDays} days ago`;
  const diffMonths = Math.floor(diffDays / 30);
  return `${diffMonths} month${diffMonths > 1 ? 's' : ''} ago`;
}

export default function InterviewExperiences() {
  const [experiences, setExperiences] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [difficulty, setDifficulty] = useState('All');
  const [verdict, setVerdict] = useState('All');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [expandedId, setExpandedId] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    company_name: '',
    role: '',
    difficulty: 'Medium',
    verdict: 'Selected',
    overall_experience: '',
    questions_asked: [''],
    tips_for_juniors: '',
  });

  const loadExperiences = async () => {
    try {
      setLoading(true);
      const params = {};
      if (search.trim()) params.company = search.trim();
      if (difficulty !== 'All') params.difficulty = difficulty;
      if (verdict !== 'All') params.verdict = verdict;

      const res = await experiencesApi.getExperiences(params);
      if (res.data) {
        setExperiences(res.data.items || []);
      }
    } catch (err) {
      console.error('Failed to load experiences:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadExperiences();
  }, [difficulty, verdict]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadExperiences();
  };

  const handleUpvote = async (id, e) => {
    e.stopPropagation();
    try {
      const res = await experiencesApi.upvoteExperience(id);
      setExperiences(prev =>
        prev.map(exp => (exp.id === id ? { ...exp, upvotes: res.data.upvotes } : exp))
      );
    } catch (err) {
      console.error('Failed to upvote:', err);
    }
  };

  const handleAddQuestion = () => {
    setFormData(prev => ({ ...prev, questions_asked: [...prev.questions_asked, ''] }));
  };

  const handleQuestionChange = (index, value) => {
    const updated = [...formData.questions_asked];
    updated[index] = value;
    setFormData(prev => ({ ...prev, questions_asked: updated }));
  };

  const handleRemoveQuestion = (index) => {
    const updated = formData.questions_asked.filter((_, i) => i !== index);
    setFormData(prev => ({ ...prev, questions_asked: updated.length ? updated : [''] }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.company_name || !formData.role || !formData.overall_experience) {
      alert('Please fill out company, role, and overall experience narrative.');
      return;
    }

    try {
      setSubmitting(true);
      const payload = {
        ...formData,
        questions_asked: formData.questions_asked.filter(q => q.trim().length > 0),
      };
      await experiencesApi.submitExperience(payload);
      setIsModalOpen(false);
      setFormData({
        company_name: '',
        role: '',
        difficulty: 'Medium',
        verdict: 'Selected',
        overall_experience: '',
        questions_asked: [''],
        tips_for_juniors: '',
      });
      loadExperiences();
    } catch (err) {
      console.error('Submission failed:', err);
      alert('Failed to submit experience.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ padding: 'var(--space-6) var(--space-8)', maxWidth: 1200, margin: '0 auto' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16, marginBottom: 'var(--space-6)' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 700, margin: 0 }}>
            💡 Interview Experiences & Question Bank
          </h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: 4 }}>
            Direct insights, interview questions, and preparation advice shared by placed students and seniors.
          </p>
        </div>

        <button
          className="btn btn-primary"
          onClick={() => setIsModalOpen(true)}
          style={{ display: 'flex', alignItems: 'center', gap: 8 }}
        >
          <span>✍️</span> Share Your Experience
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div
        className="card"
        style={{
          padding: 'var(--space-4)',
          marginBottom: 'var(--space-6)',
          display: 'flex',
          flexWrap: 'wrap',
          gap: 12,
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: 8, flex: '1 1 280px' }}>
          <input
            type="text"
            className="input"
            placeholder="Search by company (e.g. Amazon, Google, TCS)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ flex: 1 }}
          />
          <button type="submit" className="btn btn-secondary">
            Search
          </button>
        </form>

        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Difficulty:</span>
            <select
              className="input"
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              style={{ width: 110, height: 38 }}
            >
              <option value="All">All</option>
              <option value="Easy">Easy</option>
              <option value="Medium">Medium</option>
              <option value="Hard">Hard</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Verdict:</span>
            <select
              className="input"
              value={verdict}
              onChange={(e) => setVerdict(e.target.value)}
              style={{ width: 130, height: 38 }}
            >
              <option value="All">All</option>
              <option value="Selected">Selected</option>
              <option value="In Progress">In Progress</option>
              <option value="Rejected">Rejected</option>
            </select>
          </div>
        </div>
      </div>

      {/* Experience Cards Grid */}
      {loading ? (
        <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading community experiences...
        </div>
      ) : experiences.length === 0 ? (
        <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--text-muted)' }} className="card">
          <span style={{ fontSize: '2rem', display: 'block', marginBottom: 12 }}>🔍</span>
          <h3>No interview experiences found</h3>
          <p>Try searching for a different company or be the first to share an experience!</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 20 }}>
          {experiences.map((exp) => {
            const isExpanded = expandedId === exp.id;
            const diffColor =
              exp.difficulty === 'Hard' ? '#ef4444' : exp.difficulty === 'Medium' ? '#f59e0b' : '#22c55e';
            const verdictColor =
              exp.verdict === 'Selected' ? '#22c55e' : exp.verdict === 'In Progress' ? '#3b82f6' : '#9ca3af';

            return (
              <div
                key={exp.id}
                className="card"
                style={{
                  padding: 'var(--space-5)',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  position: 'relative',
                }}
              >
                <div>
                  {/* Top Tags & Upvote */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <span
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: 12,
                          background: `${diffColor}18`,
                          color: diffColor,
                          border: `1px solid ${diffColor}40`,
                        }}
                      >
                        {exp.difficulty}
                      </span>
                      <span
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: 12,
                          background: `${verdictColor}18`,
                          color: verdictColor,
                          border: `1px solid ${verdictColor}40`,
                        }}
                      >
                        {exp.verdict === 'Selected' ? '🎉 Selected' : exp.verdict}
                      </span>
                    </div>

                    <button
                      onClick={(e) => handleUpvote(exp.id, e)}
                      className="btn btn-ghost"
                      style={{
                        padding: '2px 8px',
                        fontSize: '0.78rem',
                        height: 28,
                        borderRadius: 14,
                        border: '1px solid var(--border-color)',
                      }}
                      title="Helpful interview experience"
                    >
                      ⬆ {exp.upvotes || 0}
                    </button>
                  </div>

                  {/* Company & Role */}
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 700, margin: '0 0 2px 0', color: 'var(--text-primary)' }}>
                    {exp.company_name}
                  </h3>
                  <div style={{ fontSize: '0.85rem', color: 'var(--accent-primary)', fontWeight: 500, marginBottom: 8 }}>
                    {exp.role}
                  </div>

                  {/* Author Meta */}
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 14 }}>
                    By {exp.student_name} {exp.department && `• ${exp.department}`} • {formatTimeAgo(exp.created_at)}
                  </div>

                  {/* Overall Narrative */}
                  <p
                    style={{
                      fontSize: '0.88rem',
                      color: 'var(--text-secondary)',
                      lineHeight: 1.45,
                      marginBottom: 12,
                    }}
                  >
                    {isExpanded || exp.overall_experience.length <= 160
                      ? exp.overall_experience
                      : `${exp.overall_experience.slice(0, 160)}...`}
                  </p>

                  {/* Questions Asked Box */}
                  {exp.questions_asked && exp.questions_asked.length > 0 && (
                    <div style={{ background: 'var(--bg-tertiary)', borderRadius: 8, padding: '10px 12px', marginBottom: 12 }}>
                      <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
                        ❓ Questions Asked:
                      </div>
                      <ul style={{ margin: 0, paddingLeft: 18, fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {exp.questions_asked.map((q, idx) => (
                          <li key={idx} style={{ marginBottom: 4 }}>
                            {q}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Tips for Juniors Box */}
                  {exp.tips_for_juniors && (
                    <div
                      style={{
                        borderLeft: '3px solid var(--accent-primary)',
                        paddingLeft: 10,
                        fontSize: '0.8rem',
                        color: 'var(--text-muted)',
                        fontStyle: 'italic',
                        marginBottom: 12,
                      }}
                    >
                      💡 "{exp.tips_for_juniors}"
                    </div>
                  )}
                </div>

                {/* Read More Toggle */}
                {exp.overall_experience.length > 160 && (
                  <button
                    onClick={() => setExpandedId(isExpanded ? null : exp.id)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--accent-primary)',
                      fontSize: '0.78rem',
                      cursor: 'pointer',
                      padding: 0,
                      fontWeight: 600,
                      textAlign: 'left',
                    }}
                  >
                    {isExpanded ? 'Show Less ▲' : 'Read Full Experience ▼'}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Share Experience Modal */}
      {isModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.65)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1100,
            padding: 16,
          }}
        >
          <div
            className="card"
            style={{
              width: 580,
              maxWidth: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: 'var(--space-6)',
              background: 'var(--bg-secondary)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0 }}>
                ✍️ Share Your Interview Experience
              </h2>
              <button
                onClick={() => setIsModalOpen(false)}
                style={{ background: 'none', border: 'none', fontSize: '1.2rem', cursor: 'pointer', color: 'var(--text-muted)' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: 4 }}>
                    Company Name *
                  </label>
                  <input
                    type="text"
                    className="input"
                    placeholder="e.g. Amazon, Google"
                    value={formData.company_name}
                    onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                    required
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: 4 }}>
                    Role Offered *
                  </label>
                  <input
                    type="text"
                    className="input"
                    placeholder="e.g. SDE-I, Analyst"
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: 4 }}>
                    Interview Difficulty *
                  </label>
                  <select
                    className="input"
                    value={formData.difficulty}
                    onChange={(e) => setFormData({ ...formData, difficulty: e.target.value })}
                  >
                    <option value="Easy">Easy</option>
                    <option value="Medium">Medium</option>
                    <option value="Hard">Hard</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: 4 }}>
                    Final Verdict *
                  </label>
                  <select
                    className="input"
                    value={formData.verdict}
                    onChange={(e) => setFormData({ ...formData, verdict: e.target.value })}
                  >
                    <option value="Selected">Selected</option>
                    <option value="In Progress">In Progress</option>
                    <option value="Rejected">Rejected</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: 4 }}>
                  Overall Interview Experience * (min 30 chars)
                </label>
                <textarea
                  className="input"
                  rows={4}
                  placeholder="Describe the recruitment rounds, timeline, panel behavior, and technical focus..."
                  value={formData.overall_experience}
                  onChange={(e) => setFormData({ ...formData, overall_experience: e.target.value })}
                  required
                />
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'right' }}>
                  {formData.overall_experience.length} characters
                </div>
              </div>

              {/* Dynamic Questions Asked */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>Questions Asked (OA / Interviews):</label>
                  <button
                    type="button"
                    onClick={handleAddQuestion}
                    className="btn btn-ghost"
                    style={{ fontSize: '0.75rem', height: 26, padding: '0 6px' }}
                  >
                    + Add Question
                  </button>
                </div>

                {formData.questions_asked.map((q, idx) => (
                  <div key={idx} style={{ display: 'flex', gap: 6, marginBottom: 8 }}>
                    <input
                      type="text"
                      className="input"
                      placeholder={`Question ${idx + 1}...`}
                      value={q}
                      onChange={(e) => handleQuestionChange(idx, e.target.value)}
                      style={{ flex: 1 }}
                    />
                    {formData.questions_asked.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveQuestion(idx)}
                        className="btn btn-ghost"
                        style={{ height: 38, width: 38, padding: 0, color: '#ef4444' }}
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: 4 }}>
                  Tips for Juniors & Recommended Focus Areas:
                </label>
                <textarea
                  className="input"
                  rows={2}
                  placeholder="e.g. Master dynamic programming, prepare behavioral STAR stories..."
                  value={formData.tips_for_juniors}
                  onChange={(e) => setFormData({ ...formData, tips_for_juniors: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setIsModalOpen(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={submitting}
                >
                  {submitting ? 'Submitting...' : 'Post Experience'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
