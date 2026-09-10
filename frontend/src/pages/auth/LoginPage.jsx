/**
 * Login page — premium dark design with gradient accents.
 */

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const user = await login(email, password);
      const portal = user.role === 'student' ? '/student/dashboard'
        : user.role === 'tpo' || user.role === 'admin' ? '/tpo/dashboard'
        : '/faculty/dashboard';
      navigate(portal, { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-primary)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 'var(--space-6)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Background gradient orbs */}
      <div style={{
        position: 'absolute', width: 600, height: 600, borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%)',
        top: -200, left: -100, pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute', width: 500, height: 500, borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(6,182,212,0.06) 0%, transparent 70%)',
        bottom: -150, right: -100, pointerEvents: 'none',
      }} />

      <div style={{ width: '100%', maxWidth: 440, position: 'relative' }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 'var(--space-10)' }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            width: 64, height: 64, borderRadius: 'var(--border-radius-lg)',
            background: 'var(--gradient-primary)', marginBottom: 'var(--space-4)',
            fontSize: '2rem', boxShadow: 'var(--shadow-glow)',
          }}>
            🎓
          </div>
          <h1 style={{
            fontSize: 'var(--font-size-3xl)', fontWeight: 700,
            background: 'var(--gradient-accent)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            backgroundClip: 'text', lineHeight: 1.2,
          }}>
            CCIP
          </h1>
          <p style={{ color: 'var(--text-muted)', marginTop: 'var(--space-2)', fontSize: 'var(--font-size-sm)' }}>
            Campus Career & Curriculum Intelligence Platform
          </p>
        </div>

        {/* Card */}
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--border-radius-xl)',
          padding: 'var(--space-8)',
          boxShadow: 'var(--shadow-lg)',
        }}>
          <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 600, marginBottom: 'var(--space-6)' }}>
            Sign in
          </h2>

          {error && (
            <div style={{
              background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: 'var(--border-radius-sm)', padding: 'var(--space-3) var(--space-4)',
              color: 'var(--accent-danger)', fontSize: 'var(--font-size-sm)',
              marginBottom: 'var(--space-5)',
            }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
            <div className="input-group">
              <label htmlFor="login-email">Email address</label>
              <input
                id="login-email"
                className="input"
                type="email"
                placeholder="you@college.edu"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                autoComplete="email"
                style={{ width: '100%' }}
              />
            </div>

            <div className="input-group">
              <label htmlFor="login-password">Password</label>
              <input
                id="login-password"
                className="input"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                style={{ width: '100%' }}
              />
            </div>

            <button
              id="login-submit"
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ width: '100%', height: 44, fontSize: 'var(--font-size-base)' }}
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <p style={{
            textAlign: 'center', marginTop: 'var(--space-6)',
            fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)',
          }}>
            Don't have an account?{' '}
            <Link to="/register" style={{ color: 'var(--accent-primary)', fontWeight: 500 }}>
              Register
            </Link>
          </p>
        </div>

        {/* Demo credentials hint */}
        <div style={{
          marginTop: 'var(--space-5)', textAlign: 'center',
          fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)',
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-2)'
        }}>
          <div>Quick Fill Demo Credentials</div>
          <select 
            onChange={(e) => {
              const role = e.target.value;
              const creds = {
                student:  { email: 'priya.agarwal0@ccip.edu', password: 'student123' },
                tpo:      { email: 'tpo@ccip.edu',            password: 'tpo123' },
                faculty:  { email: 'faculty@ccip.edu',         password: 'faculty123' },
                admin:    { email: 'tpo@ccip.edu',             password: 'tpo123' },
              };
              if (role && creds[role]) {
                setEmail(creds[role].email);
                setPassword(creds[role].password);
              }
            }}
            style={{
              padding: '6px 12px',
              fontSize: 'var(--font-size-xs)',
              background: 'var(--bg-tertiary)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--border-radius-sm)',
              color: 'var(--text-primary)',
              cursor: 'pointer',
              outline: 'none'
            }}
            defaultValue=""
          >
            <option value="" disabled>Select a role...</option>
            <option value="student">Student (Priya Agarwal)</option>
            <option value="faculty">Faculty (Dr. Sharma)</option>
            <option value="tpo">TPO (Admin)</option>
          </select>
        </div>
      </div>
    </div>
  );
}
