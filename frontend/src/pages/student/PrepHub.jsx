/**
 * PrepHub — Placement Preparation Resources Hub for students.
 * Browse resources, track progress, explore collections.
 *
 * Sprint 3 — Sakshi Kumari
 */

import { useState, useEffect } from 'react';

const CATEGORIES = [
  { key: 'all', label: 'All', icon: '📚' },
  { key: 'coding', label: 'Coding', icon: '💻' },
  { key: 'aptitude', label: 'Aptitude', icon: '🧮' },
  { key: 'system_design', label: 'System Design', icon: '🏗️' },
  { key: 'behavioral', label: 'Behavioral', icon: '🗣️' },
  { key: 'hr', label: 'HR', icon: '👔' },
  { key: 'resume', label: 'Resume', icon: '📄' },
];

const DIFFICULTIES = [
  { key: 'all', label: 'All Levels' },
  { key: 'beginner', label: '🟢 Beginner' },
  { key: 'intermediate', label: '🟡 Intermediate' },
  { key: 'advanced', label: '🔴 Advanced' },
];

const MOCK_RESOURCES = [
  { id: '1', title: 'Dynamic Programming Complete Guide', description: 'Master DP from basics to advanced patterns — Fibonacci, Knapsack, LCS, Matrix Chain.', category: 'coding', resource_type: 'article', difficulty: 'advanced', tags: ['DP', 'Competitive'], estimated_minutes: 120, upvotes: 245, view_count: 1200, author_name: 'TPO Cell' },
  { id: '2', title: 'Aptitude Mastery: Quant & Logical', description: 'Comprehensive practice sets for TCS, Infosys, and Wipro aptitude rounds.', category: 'aptitude', resource_type: 'problem_set', difficulty: 'intermediate', tags: ['Quant', 'Logical'], estimated_minutes: 90, upvotes: 189, view_count: 980, author_name: 'Placement Team' },
  { id: '3', title: 'System Design Interview Cheatsheet', description: 'Quick reference for load balancers, caching, databases, and microservices architecture.', category: 'system_design', resource_type: 'cheatsheet', difficulty: 'advanced', tags: ['Architecture', 'Scalability'], estimated_minutes: 45, upvotes: 312, view_count: 1500, author_name: 'Alumni Network' },
  { id: '4', title: 'STAR Method for Behavioral Interviews', description: 'Learn the Situation-Task-Action-Result framework with real examples.', category: 'behavioral', resource_type: 'article', difficulty: 'beginner', tags: ['STAR', 'Soft Skills'], estimated_minutes: 20, upvotes: 156, view_count: 750, author_name: 'Career Counselor' },
  { id: '5', title: 'Resume Templates for Freshers', description: 'ATS-friendly resume templates optimized for campus placement.', category: 'resume', resource_type: 'template', difficulty: 'beginner', tags: ['ATS', 'Freshers'], estimated_minutes: 30, upvotes: 203, view_count: 890, author_name: 'TPO Cell' },
  { id: '6', title: 'Top 50 HR Interview Questions', description: 'Most frequently asked HR questions with model answers and tips.', category: 'hr', resource_type: 'article', difficulty: 'intermediate', tags: ['HR', 'Interview'], estimated_minutes: 40, upvotes: 178, view_count: 670, author_name: 'Placement Team' },
];

const TYPE_ICONS = { article: '📝', video: '🎬', problem_set: '🧩', mock_test: '📋', cheatsheet: '📌', roadmap: '🗺️', template: '📎' };

export default function PrepHub() {
  const [resources, setResources] = useState(MOCK_RESOURCES);
  const [category, setCategory] = useState('all');
  const [difficulty, setDifficulty] = useState('all');
  const [search, setSearch] = useState('');
  const [progress, setProgress] = useState({});

  const filtered = resources.filter(r => {
    if (category !== 'all' && r.category !== category) return false;
    if (difficulty !== 'all' && r.difficulty !== difficulty) return false;
    if (search && !r.title.toLowerCase().includes(search.toLowerCase()) &&
        !r.tags.some(t => t.toLowerCase().includes(search.toLowerCase()))) return false;
    return true;
  });

  const handleUpvote = (id) => {
    setResources(prev => prev.map(r => r.id === id ? { ...r, upvotes: r.upvotes + 1 } : r));
  };

  const handleProgressToggle = (id) => {
    setProgress(prev => {
      const current = prev[id] || 'not_started';
      const next = current === 'not_started' ? 'in_progress' : current === 'in_progress' ? 'completed' : 'not_started';
      return { ...prev, [id]: next };
    });
  };

  const progressColors = { not_started: 'var(--text-muted)', in_progress: '#f59e0b', completed: '#22c55e' };
  const progressLabels = { not_started: 'Start', in_progress: 'In Progress', completed: 'Completed ✓' };

  const stats = {
    total: resources.length,
    completed: Object.values(progress).filter(v => v === 'completed').length,
    in_progress: Object.values(progress).filter(v => v === 'in_progress').length,
  };

  return (
    <div style={{ padding: '2rem' }}>
      <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
        📚 Placement Prep Resources
      </h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
        Curated resources to ace your campus placement interviews.
      </p>

      {/* Stats Bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        {[
          { label: 'Total Resources', value: stats.total, color: '#6366f1' },
          { label: 'Completed', value: stats.completed, color: '#22c55e' },
          { label: 'In Progress', value: stats.in_progress, color: '#f59e0b' },
        ].map(s => (
          <div key={s.label} style={{ background: 'var(--bg-secondary)', borderRadius: '12px', padding: '1rem', border: '1px solid var(--border-primary)' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        {CATEGORIES.map(c => (
          <button key={c.key} onClick={() => setCategory(c.key)} style={{
            padding: '0.4rem 0.8rem', borderRadius: '20px', border: 'none', cursor: 'pointer',
            background: category === c.key ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
            color: category === c.key ? '#fff' : 'var(--text-secondary)',
            fontSize: '0.8rem', fontWeight: 500, transition: 'all 0.15s',
          }}>{c.icon} {c.label}</button>
        ))}
      </div>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search resources or tags..."
          style={{ flex: 1, minWidth: '200px', padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--border-primary)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }} />
        <select value={difficulty} onChange={e => setDifficulty(e.target.value)} style={{
          padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--border-primary)',
          background: 'var(--bg-secondary)', color: 'var(--text-primary)',
        }}>
          {DIFFICULTIES.map(d => <option key={d.key} value={d.key}>{d.label}</option>)}
        </select>
      </div>

      {/* Resource Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '1.25rem' }}>
        {filtered.map(r => {
          const pStatus = progress[r.id] || 'not_started';
          return (
            <div key={r.id} style={{
              background: 'var(--bg-secondary)', borderRadius: '12px', padding: '1.5rem',
              border: '1px solid var(--border-primary)', display: 'flex', flexDirection: 'column',
              transition: 'transform 0.2s, box-shadow 0.2s',
            }} onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 8px 25px rgba(0,0,0,0.15)'; }}
               onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = ''; }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '1.5rem' }}>{TYPE_ICONS[r.resource_type] || '📝'}</span>
                <span style={{
                  padding: '0.15rem 0.5rem', borderRadius: '6px', fontSize: '0.7rem', fontWeight: 600,
                  background: r.difficulty === 'beginner' ? 'rgba(34,197,94,0.12)' : r.difficulty === 'intermediate' ? 'rgba(245,158,11,0.12)' : 'rgba(239,68,68,0.12)',
                  color: r.difficulty === 'beginner' ? '#22c55e' : r.difficulty === 'intermediate' ? '#f59e0b' : '#ef4444',
                }}>{r.difficulty}</span>
              </div>

              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.4rem' }}>{r.title}</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', lineHeight: 1.4, marginBottom: '0.75rem', flex: 1 }}>{r.description}</p>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem', marginBottom: '0.75rem' }}>
                {r.tags.map(tag => (
                  <span key={tag} style={{ background: 'rgba(99,102,241,0.1)', color: '#6366f1', padding: '0.1rem 0.4rem', borderRadius: '4px', fontSize: '0.7rem' }}>{tag}</span>
                ))}
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                <span>⏱ {r.estimated_minutes} min · 👁 {r.view_count}</span>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <button onClick={() => handleUpvote(r.id)} style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    👍 {r.upvotes}
                  </button>
                  <button onClick={() => handleProgressToggle(r.id)} style={{
                    padding: '0.3rem 0.7rem', borderRadius: '6px', border: 'none', cursor: 'pointer',
                    background: `${progressColors[pStatus]}22`, color: progressColors[pStatus],
                    fontSize: '0.72rem', fontWeight: 600,
                  }}>{progressLabels[pStatus]}</button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
