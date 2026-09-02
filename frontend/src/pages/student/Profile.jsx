/**
 * Student Profile — tabs: Overview | Academic | Skills | Resume
 */

import { useState, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { useAuth } from '../../context/AuthContext';

// ─── Mock Data ────────────────────────────────────────────────────
const MOCK_PROFILE = {
  roll_number: 'CS21B042',
  department: 'Computer Science & Engineering',
  year: 4,
  section: 'B',
  cgpa: 8.1,
  phone: '+91 98765 43210',
  email: 'arjun.sharma@college.edu',
  bio: 'Passionate about data science and machine learning. Aspiring to build AI solutions that solve real-world problems. Currently exploring deep learning and MLOps.',
  linkedin: 'linkedin.com/in/arjunsharma',
  github: 'github.com/arjunsharma',
  consent_ai: true,
  consent_share: true,
};

const MOCK_CGPA_TREND = [
  { sem: 'Sem 1', cgpa: 7.4 },
  { sem: 'Sem 2', cgpa: 7.8 },
  { sem: 'Sem 3', cgpa: 8.0 },
  { sem: 'Sem 4', cgpa: 8.3 },
  { sem: 'Sem 5', cgpa: 8.1 },
  { sem: 'Sem 6', cgpa: 8.5 },
  { sem: 'Sem 7', cgpa: 8.1 },
];

const MOCK_SUBJECTS = [
  { code: 'CS401', name: 'Machine Learning', sem: 7, grade: 'S', marks: 95, credits: 4 },
  { code: 'CS402', name: 'Big Data Analytics', sem: 7, grade: 'A', marks: 87, credits: 4 },
  { code: 'CS403', name: 'Cloud Computing', sem: 7, grade: 'A', marks: 85, credits: 3 },
  { code: 'CS404', name: 'Natural Language Processing', sem: 7, grade: 'B', marks: 78, credits: 3 },
  { code: 'CS301', name: 'Database Management', sem: 6, grade: 'S', marks: 92, credits: 4 },
  { code: 'CS302', name: 'Software Engineering', sem: 6, grade: 'A', marks: 88, credits: 4 },
  { code: 'CS303', name: 'Computer Networks', sem: 6, grade: 'A', marks: 83, credits: 3 },
];

const MOCK_SKILLS = [
  { skill: 'Python', category: 'Programming', proficiency: 80, endorsements: 12, verified: true },
  { skill: 'SQL', category: 'Data', proficiency: 72, endorsements: 8, verified: true },
  { skill: 'Machine Learning', category: 'ML / AI', proficiency: 65, endorsements: 6, verified: false },
  { skill: 'React', category: 'Web', proficiency: 55, endorsements: 4, verified: false },
  { skill: 'Data Visualization', category: 'Data', proficiency: 60, endorsements: 5, verified: false },
  { skill: 'Git', category: 'Tools', proficiency: 78, endorsements: 9, verified: true },
  { skill: 'Docker', category: 'Tools', proficiency: 35, endorsements: 2, verified: false },
  { skill: 'Statistics', category: 'Data', proficiency: 58, endorsements: 3, verified: false },
];

const GRADE_COLORS = { S: '#22c55e', A: '#6366f1', B: '#f59e0b', C: '#f97316', F: '#ef4444' };

const TABS = ['Overview', 'Academic', 'Skills', 'Resume'];

// ─── Custom Tooltip ────────────────────────────────────────────────
function CGPATooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 8, padding: 'var(--space-3) var(--space-4)' }}>
      <div style={{ fontWeight: 600 }}>{label}</div>
      <div style={{ color: '#6366f1' }}>CGPA: {payload[0].value}</div>
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────
export default function StudentProfile() {
  const { user } = useAuth();
  const [tab, setTab] = useState('Overview');
  const [consent, setConsent] = useState({ ai: MOCK_PROFILE.consent_ai, share: MOCK_PROFILE.consent_share });
  const [resumeFile, setResumeFile] = useState(null);
  const fileRef = useRef(null);

  const profile = { ...MOCK_PROFILE, ...(user || {}) };

  return (
    <div>
      <div className="page-header">
        <h1>Student Profile</h1>
        <p>Manage your resume, skills, and academic record</p>
      </div>

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>

        {/* Profile header card */}
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-6)' }}>
          <div style={{
            width: 80, height: 80, borderRadius: '50%',
            background: 'var(--gradient-primary)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'white', flexShrink: 0,
          }}>
            {user?.first_name?.[0]}{user?.last_name?.[0]}
          </div>
          <div style={{ flex: 1 }}>
            <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700 }}>
              {user?.first_name || 'Arjun'} {user?.last_name || 'Sharma'}
            </h2>
            <div style={{ color: 'var(--text-secondary)', marginTop: 2 }}>{profile.department} · Year {profile.year}</div>
            <div style={{ display: 'flex', gap: 'var(--space-4)', marginTop: 'var(--space-3)', flexWrap: 'wrap' }}>
              <span className="badge badge-primary">🎓 {profile.roll_number}</span>
              <span className="badge badge-success">CGPA: {profile.cgpa}</span>
              <span className="badge badge-warning">Year {profile.year} · Section {profile.section}</span>
            </div>
          </div>
          <button className="btn btn-secondary" style={{ height: 36, flexShrink: 0 }}>✏️ Edit Profile</button>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--border-color)' }}>
          {TABS.map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              style={{
                padding: 'var(--space-3) var(--space-6)',
                background: 'none', border: 'none', cursor: 'pointer',
                fontSize: 'var(--font-size-sm)', fontWeight: 600,
                color: tab === t ? 'var(--accent-primary)' : 'var(--text-muted)',
                borderBottom: `2px solid ${tab === t ? 'var(--accent-primary)' : 'transparent'}`,
                marginBottom: -1,
                transition: 'all 0.15s',
              }}
            >
              {t}
            </button>
          ))}
        </div>

        {/* ── Overview Tab ────────────────────────────── */}
        {tab === 'Overview' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-6)' }}>

            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div style={{ fontWeight: 600 }}>Contact & Links</div>
              {[
                { icon: '✉️', label: 'Email', value: profile.email || user?.email },
                { icon: '📱', label: 'Phone', value: profile.phone },
                { icon: '💼', label: 'LinkedIn', value: profile.linkedin },
                { icon: '🐙', label: 'GitHub', value: profile.github },
              ].map(row => (
                <div key={row.label} style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'flex-start' }}>
                  <span style={{ fontSize: '1rem', width: 24 }}>{row.icon}</span>
                  <div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{row.label}</div>
                    <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-primary)' }}>{row.value || '—'}</div>
                  </div>
                </div>
              ))}
            </div>

            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Bio</div>
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                {profile.bio}
              </p>

              <div style={{ marginTop: 'var(--space-6)' }}>
                <div style={{ fontWeight: 600, marginBottom: 'var(--space-3)' }}>Data Consent</div>
                {[
                  { key: 'ai', label: 'Allow AI analysis of my academic data' },
                  { key: 'share', label: 'Share profile with recruiters' },
                ].map(c => (
                  <div key={c.key} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
                    <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>{c.label}</span>
                    <button
                      onClick={() => setConsent(prev => ({ ...prev, [c.key]: !prev[c.key] }))}
                      style={{
                        width: 44, height: 24, borderRadius: 999, border: 'none', cursor: 'pointer',
                        background: consent[c.key] ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                        position: 'relative', transition: 'background 0.2s',
                      }}
                    >
                      <div style={{
                        position: 'absolute', top: 3,
                        left: consent[c.key] ? 22 : 3,
                        width: 18, height: 18, borderRadius: '50%', background: 'white',
                        transition: 'left 0.2s',
                      }} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── Academic Tab ────────────────────────────── */}
        {tab === 'Academic' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>

            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>CGPA Trend</div>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={MOCK_CGPA_TREND} margin={{ left: 0, right: 16, top: 4, bottom: 4 }}>
                  <CartesianGrid stroke="var(--border-color)" strokeDasharray="4 4" />
                  <XAxis dataKey="sem" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                  <YAxis domain={[6, 10]} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                  <Tooltip content={<CGPATooltip />} />
                  <Line type="monotone" dataKey="cgpa" stroke="#6366f1" strokeWidth={2.5} dot={{ fill: '#6366f1', r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Subject-wise Performance</div>
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Code</th>
                      <th>Subject</th>
                      <th>Sem</th>
                      <th>Marks</th>
                      <th>Credits</th>
                      <th>Grade</th>
                    </tr>
                  </thead>
                  <tbody>
                    {MOCK_SUBJECTS.map(s => (
                      <tr key={s.code}>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{s.code}</td>
                        <td style={{ fontWeight: 500 }}>{s.name}</td>
                        <td style={{ color: 'var(--text-muted)' }}>{s.sem}</td>
                        <td>{s.marks}</td>
                        <td style={{ color: 'var(--text-muted)' }}>{s.credits}</td>
                        <td>
                          <span style={{
                            padding: '2px 10px', borderRadius: 999,
                            fontSize: 'var(--font-size-xs)', fontWeight: 700,
                            color: GRADE_COLORS[s.grade],
                            background: `${GRADE_COLORS[s.grade]}18`,
                          }}>
                            {s.grade}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ── Skills Tab ────────────────────────────── */}
        {tab === 'Skills' && (
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-5)' }}>
              <div style={{ fontWeight: 600 }}>My Skills</div>
              <button className="btn btn-primary" style={{ height: 36, fontSize: 'var(--font-size-sm)' }}>+ Add Skill</button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {MOCK_SKILLS.map(s => (
                <div key={s.skill} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
                  <div style={{ width: 160 }}>
                    <div style={{ fontWeight: 500, fontSize: 'var(--font-size-sm)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                      {s.skill}
                      {s.verified && <span title="Verified" style={{ color: '#6366f1', fontSize: '0.75rem' }}>✓</span>}
                    </div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{s.category}</div>
                  </div>
                  <div style={{ flex: 1, height: 8, background: 'var(--bg-tertiary)', borderRadius: 4, overflow: 'hidden' }}>
                    <div style={{
                      width: `${s.proficiency}%`, height: '100%',
                      background: s.proficiency >= 70 ? 'var(--accent-success)' : s.proficiency >= 50 ? '#6366f1' : 'var(--accent-warning)',
                      borderRadius: 4, transition: 'width 0.8s ease',
                    }} />
                  </div>
                  <span style={{ width: 36, textAlign: 'right', fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    {s.proficiency}
                  </span>
                  <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', width: 80 }}>
                    👍 {s.endorsements}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Resume Tab ────────────────────────────── */}
        {tab === 'Resume' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-6)' }}>
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Upload Resume</div>
              <div
                onClick={() => fileRef.current?.click()}
                style={{
                  border: `2px dashed ${resumeFile ? 'var(--accent-success)' : 'var(--border-color)'}`,
                  borderRadius: 'var(--border-radius)',
                  padding: 'var(--space-10)',
                  textAlign: 'center',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                  background: resumeFile ? 'rgba(34,197,94,0.05)' : 'var(--bg-tertiary)',
                }}
                onMouseOver={e => e.currentTarget.style.borderColor = 'var(--accent-primary)'}
                onMouseOut={e => e.currentTarget.style.borderColor = resumeFile ? 'var(--accent-success)' : 'var(--border-color)'}
              >
                <div style={{ fontSize: '2.5rem', marginBottom: 'var(--space-3)' }}>{resumeFile ? '✅' : '📄'}</div>
                {resumeFile ? (
                  <>
                    <div style={{ fontWeight: 600, color: 'var(--accent-success)' }}>{resumeFile.name}</div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 4 }}>
                      {(resumeFile.size / 1024).toFixed(0)} KB · Click to change
                    </div>
                  </>
                ) : (
                  <>
                    <div style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Drop your resume here</div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 4 }}>
                      PDF or DOCX · Max 5MB
                    </div>
                  </>
                )}
                <input
                  ref={fileRef}
                  type="file"
                  accept=".pdf,.docx"
                  style={{ display: 'none' }}
                  onChange={e => setResumeFile(e.target.files[0] || null)}
                />
              </div>
              {resumeFile && (
                <button className="btn btn-primary" style={{ width: '100%', marginTop: 'var(--space-4)' }}>
                  📤 Upload & Parse Skills
                </button>
              )}
            </div>

            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Parsed Skills Preview</div>
              {resumeFile ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: 'var(--space-2)' }}>
                    Skills detected in your resume:
                  </div>
                  {['Python', 'SQL', 'Machine Learning', 'Git', 'React', 'Data Visualization'].map(s => (
                    <div key={s} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 'var(--space-2) var(--space-3)', background: 'var(--bg-tertiary)', borderRadius: 'var(--border-radius-sm)' }}>
                      <span style={{ fontSize: 'var(--font-size-sm)' }}>{s}</span>
                      <span className="badge badge-success">Detected ✓</span>
                    </div>
                  ))}
                  <button className="btn btn-secondary" style={{ width: '100%', marginTop: 'var(--space-2)' }}>
                    Sync to Profile
                  </button>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--text-muted)' }}>
                  <div style={{ fontSize: '2rem', marginBottom: 'var(--space-3)' }}>🔍</div>
                  <p style={{ fontSize: 'var(--font-size-sm)' }}>Upload your resume to auto-detect skills</p>
                </div>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
