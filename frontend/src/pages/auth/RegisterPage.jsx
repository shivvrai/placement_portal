/**
 * Register page — role selection + student-specific fields.
 * Department code uses a dropdown of standard departments.
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '../../api/endpoints';

// Standard college departments — edit this list to match your institution
const DEPARTMENTS = [
  { code: 'CS',    name: 'Computer Science & Engineering' },
  { code: 'IT',    name: 'Information Technology' },
  { code: 'EC',    name: 'Electronics & Communication' },
  { code: 'EE',    name: 'Electrical Engineering' },
  { code: 'ME',    name: 'Mechanical Engineering' },
  { code: 'CE',    name: 'Civil Engineering' },
  { code: 'CH',    name: 'Chemical Engineering' },
  { code: 'AI',    name: 'Artificial Intelligence & ML' },
  { code: 'DS',    name: 'Data Science' },
  { code: 'CY',    name: 'Cyber Security' },
  { code: 'BT',    name: 'Biotechnology' },
  { code: 'MCA',   name: 'MCA' },
  { code: 'MBA',   name: 'MBA' },
  { code: 'OTHER', name: 'Other' },
];

export default function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    first_name: '', last_name: '', email: '', password: '',
    role: 'student', roll_number: '', department_code: '',
    current_semester: 1, admission_year: new Date().getFullYear(),
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const update = (k, v) => setForm(f => ({ ...f, [k]: v }));

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      await authApi.register(form);
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally { setLoading(false); }
  }

  const needsDept = ['student', 'faculty', 'hod'].includes(form.role);

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'var(--space-6)', position: 'relative', overflow: 'hidden' }}>
      {/* Background orbs */}
      <div style={{ position: 'absolute', width: 500, height: 500, borderRadius: '50%', background: 'radial-gradient(circle, rgba(99,102,241,0.07) 0%, transparent 70%)', top: -150, right: -100, pointerEvents: 'none' }} />
      <div style={{ position: 'absolute', width: 400, height: 400, borderRadius: '50%', background: 'radial-gradient(circle, rgba(6,182,212,0.05) 0%, transparent 70%)', bottom: -100, left: -80, pointerEvents: 'none' }} />

      <div style={{ width: '100%', maxWidth: 500, position: 'relative' }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 'var(--space-8)' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 52, height: 52, borderRadius: 'var(--border-radius-lg)', background: 'var(--gradient-primary)', marginBottom: 'var(--space-3)', fontSize: '1.6rem', boxShadow: 'var(--shadow-glow)' }}>🎓</div>
          <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, background: 'var(--gradient-accent)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
            Create Account
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)', marginTop: 4 }}>Join the CCIP platform</p>
        </div>

        {/* Card */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 'var(--border-radius-xl)', padding: 'var(--space-8)', boxShadow: 'var(--shadow-lg)' }}>
          {error && (
            <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 'var(--border-radius-sm)', padding: 'var(--space-3)', color: 'var(--accent-danger)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-5)' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>

            {/* Name row */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
              <div className="input-group">
                <label htmlFor="reg-first-name">First Name</label>
                <input id="reg-first-name" className="input" placeholder="Arjun" value={form.first_name} onChange={e => update('first_name', e.target.value)} required style={{ width: '100%' }} />
              </div>
              <div className="input-group">
                <label htmlFor="reg-last-name">Last Name</label>
                <input id="reg-last-name" className="input" placeholder="Sharma" value={form.last_name} onChange={e => update('last_name', e.target.value)} required style={{ width: '100%' }} />
              </div>
            </div>

            {/* Email */}
            <div className="input-group">
              <label htmlFor="reg-email">Email</label>
              <input id="reg-email" className="input" type="email" placeholder="you@college.edu" value={form.email} onChange={e => update('email', e.target.value)} required style={{ width: '100%' }} />
            </div>

            {/* Password */}
            <div className="input-group">
              <label htmlFor="reg-password">Password</label>
              <input id="reg-password" className="input" type="password" placeholder="Min 8 characters" value={form.password} onChange={e => update('password', e.target.value)} minLength={8} required style={{ width: '100%' }} />
            </div>

            {/* Role */}
            <div className="input-group">
              <label htmlFor="reg-role">Role</label>
              <select id="reg-role" className="input" value={form.role} onChange={e => update('role', e.target.value)} style={{ width: '100%' }}>
                <option value="student">Student</option>
                <option value="tpo">TPO (Placement Officer)</option>
                <option value="faculty">Faculty</option>
                <option value="hod">HOD</option>
              </select>
            </div>

            {/* Department — dropdown, shown for student/faculty/hod */}
            {needsDept && (
              <div className="input-group">
                <label htmlFor="reg-dept">Department</label>
                <select
                  id="reg-dept"
                  className="input"
                  value={form.department_code}
                  onChange={e => update('department_code', e.target.value)}
                  required
                  style={{ width: '100%' }}
                >
                  <option value="" disabled>— Select your department —</option>
                  {DEPARTMENTS.map(d => (
                    <option key={d.code} value={d.code}>
                      {d.code} — {d.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Student-only fields */}
            {form.role === 'student' && (
              <>
                <div className="input-group">
                  <label htmlFor="reg-roll">Roll Number</label>
                  <input id="reg-roll" className="input" placeholder="e.g. CS2021001" value={form.roll_number} onChange={e => update('roll_number', e.target.value)} required style={{ width: '100%' }} />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
                  <div className="input-group">
                    <label htmlFor="reg-semester">Current Semester</label>
                    <select id="reg-semester" className="input" value={form.current_semester} onChange={e => update('current_semester', +e.target.value)} style={{ width: '100%' }}>
                      {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={s}>Semester {s}</option>)}
                    </select>
                  </div>
                  <div className="input-group">
                    <label htmlFor="reg-year">Admission Year</label>
                    <select id="reg-year" className="input" value={form.admission_year} onChange={e => update('admission_year', +e.target.value)} style={{ width: '100%' }}>
                      {[2020,2021,2022,2023,2024,2025,2026].map(y => <option key={y} value={y}>{y}</option>)}
                    </select>
                  </div>
                </div>
              </>
            )}

            <button id="register-submit" type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%', height: 44, fontSize: 'var(--font-size-base)', marginTop: 'var(--space-2)' }}>
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </form>

          <p style={{ textAlign: 'center', marginTop: 'var(--space-5)', fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)' }}>
            Already have an account?{' '}
            <Link to="/login" style={{ color: 'var(--accent-primary)', fontWeight: 500 }}>Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
