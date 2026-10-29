/**
 * Register page — clean minimal design matching the login redesign.
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

  const needsDept = form.role === 'student';

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-primary)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '48px 24px',
      transition: 'background-color 0.3s ease',
    }}>
      <div style={{ width: '100%', maxWidth: 480 }}>
        {/* Header */}
        <div style={{ marginBottom: 32 }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 40,
            height: 40,
            borderRadius: 10,
            background: 'var(--accent-primary)',
            marginBottom: 20,
            boxShadow: '0 2px 12px rgba(124, 58, 237, 0.3)',
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
              <path d="M6 12v5c3 3 9 3 12 0v-5" />
            </svg>
          </div>
          <h1 style={{
            fontSize: 'var(--font-size-2xl)',
            fontWeight: 600,
            letterSpacing: '-0.03em',
            color: 'var(--text-primary)',
            marginBottom: 4,
          }}>
            Create your account
          </h1>
          <p style={{
            color: 'var(--text-muted)',
            fontSize: 'var(--font-size-sm)',
          }}>
            Join the CCIP platform to get started
          </p>
        </div>

        {/* Form Card */}
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--border-radius-xl)',
          padding: '28px',
          boxShadow: 'var(--shadow-card)',
        }}>
          {error && (
            <div style={{
              background: 'rgba(239,68,68,0.08)',
              border: '1px solid rgba(239,68,68,0.2)',
              borderRadius: 'var(--border-radius-sm)',
              padding: '10px 14px',
              color: 'var(--accent-danger)',
              fontSize: 'var(--font-size-sm)',
              marginBottom: 20,
              fontWeight: 500,
            }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* Name row */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div className="input-group">
                <label htmlFor="reg-first-name">First name</label>
                <input id="reg-first-name" className="input" placeholder="Arjun" value={form.first_name} onChange={e => update('first_name', e.target.value)} required style={{ width: '100%' }} />
              </div>
              <div className="input-group">
                <label htmlFor="reg-last-name">Last name</label>
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
                  <option value="" disabled>Select your department</option>
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
                  <label htmlFor="reg-roll">Roll number</label>
                  <input id="reg-roll" className="input" placeholder="e.g. CS2021001" value={form.roll_number} onChange={e => update('roll_number', e.target.value)} required style={{ width: '100%' }} />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div className="input-group">
                    <label htmlFor="reg-semester">Semester</label>
                    <select id="reg-semester" className="input" value={form.current_semester} onChange={e => update('current_semester', +e.target.value)} style={{ width: '100%' }}>
                      {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={s}>Semester {s}</option>)}
                    </select>
                  </div>
                  <div className="input-group">
                    <label htmlFor="reg-year">Admission year</label>
                    <select id="reg-year" className="input" value={form.admission_year} onChange={e => update('admission_year', +e.target.value)} style={{ width: '100%' }}>
                      {[2020,2021,2022,2023,2024,2025,2026].map(y => <option key={y} value={y}>{y}</option>)}
                    </select>
                  </div>
                </div>
              </>
            )}

            <button
              id="register-submit"
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{
                width: '100%',
                height: 40,
                fontSize: 'var(--font-size-sm)',
                fontWeight: 600,
                marginTop: 4,
              }}
            >
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </form>

          <p style={{
            textAlign: 'center',
            marginTop: 20,
            fontSize: 'var(--font-size-sm)',
            color: 'var(--text-muted)',
          }}>
            Already have an account?{' '}
            <Link to="/login" style={{ color: 'var(--accent-primary)', fontWeight: 500 }}>
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
