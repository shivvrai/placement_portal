/**
 * Login page — immersive, creative design with animated mesh background,
 * interactive demo credential explorer, 1-click instant login, show/hide password,
 * and resilient network/offline fallback.
 */

import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const DEMO_ROLES = [
  {
    role: 'student',
    label: 'Student',
    icon: '🎓',
    name: 'Priya Agarwal',
    tag: 'CS • Sem 8',
    email: 'priya.agarwal0@ccip.edu',
    password: 'student123',
    color: '#8b5cf6',
    portal: '/student/dashboard',
    desc: 'Career matching, skill gaps, roadmaps & placements',
  },
  {
    role: 'tpo',
    label: 'TPO Officer',
    icon: '🏢',
    name: 'Admin TPO',
    tag: 'Placement Cell',
    email: 'tpo@ccip.edu',
    password: 'tpo123',
    color: '#f59e0b',
    portal: '/tpo/dashboard',
    desc: 'Campus recruitment drives, student pipelines & BI analytics',
  },
  {
    role: 'faculty',
    label: 'Faculty',
    icon: '👨‍🏫',
    name: 'Dr. Sharma',
    tag: 'HOD Computer Science',
    email: 'faculty@ccip.edu',
    password: 'faculty123',
    color: '#06b6d4',
    portal: '/faculty/dashboard',
    desc: 'Curriculum industry alignment & syllabus proposal reviews',
  },
  {
    role: 'admin',
    label: 'Admin',
    icon: '🛡️',
    name: 'System Admin',
    tag: 'Super User',
    email: 'admin@ccip.edu',
    password: 'admin123',
    color: '#10b981',
    portal: '/admin/dashboard',
    desc: 'System health, global settings, and user permissions',
  },
  {
    role: 'recruiter',
    label: 'Recruiter',
    icon: '💼',
    name: 'Corporate HR',
    tag: 'Talent Acquisition',
    email: 'recruiter@ccip.edu',
    password: 'recruiter123',
    color: '#ec4899',
    portal: '/recruiter/dashboard',
    desc: 'Job listings, applicant review & interview scheduling',
  },
];

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  // Default to student demo credentials
  const [selectedRole, setSelectedRole] = useState(DEMO_ROLES[0]);
  const [email, setEmail] = useState(DEMO_ROLES[0].email);
  const [password, setPassword] = useState(DEMO_ROLES[0].password);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [networkError, setNetworkError] = useState(false);
  const [loading, setLoading] = useState(false);
  const [copiedField, setCopiedField] = useState(null);

  // Select a demo role: fills credentials and updates preview
  function handleSelectRole(cred) {
    setSelectedRole(cred);
    setEmail(cred.email);
    setPassword(cred.password);
    setError('');
    setNetworkError(false);
  }

  // Core login handler (supports live API and fallback mock mode)
  async function performLogin(targetEmail, targetPassword, options = {}) {
    setError('');
    setNetworkError(false);
    setLoading(true);

    try {
      const user = await login(targetEmail, targetPassword, options);
      const portal = user.role === 'student' ? '/student/dashboard'
        : user.role === 'admin' ? '/admin/dashboard'
        : user.role === 'tpo' ? '/tpo/dashboard'
        : user.role === 'recruiter' ? '/recruiter/dashboard'
        : '/faculty/dashboard';
      navigate(portal, { replace: true });
    } catch (err) {
      if (err.isNetworkError || !err.response) {
        setNetworkError(true);
        setError('Cannot connect to backend server at http://127.0.0.1:8000. You can proceed immediately using Demo Mode.');
      } else {
        setError(err.response?.data?.detail || 'Invalid email or password. Please verify credentials or pick a demo role.');
      }
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    performLogin(email, password);
  }

  function handleInstantDemoLogin(cred) {
    handleSelectRole(cred);
    performLogin(cred.email, cred.password);
  }

  function copyToClipboard(text, fieldName) {
    if (navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(text);
      setCopiedField(fieldName);
      setTimeout(() => setCopiedField(null), 1800);
    }
  }

  return (
    <div className="login-page">
      {/* Animated background blobs */}
      <div className="login-bg">
        <div className="blob blob-1" />
        <div className="blob blob-2" />
        <div className="blob blob-3" />
        <div className="grid-overlay" />
      </div>

      <div className="login-container">
        {/* Left branding panel */}
        <div className="login-brand">
          <div className="brand-content">
            <div className="brand-badge-pill">
              <span className="pulse-dot" />
              <span>Campus Intelligence v3.2</span>
            </div>

            <div className="brand-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
                <path d="M6 12v5c3 3 9 3 12 0v-5" />
              </svg>
            </div>

            <h1 className="brand-title">CCIP</h1>
            <p className="brand-subtitle">
              Campus Career &<br />
              Curriculum Intelligence
            </p>

            <div className="brand-features">
              {[
                { icon: '✦', text: 'AI-Powered Career & Job Matching', delay: '0.4s' },
                { icon: '◈', text: 'Real-time Skill Gap Taxonomy', delay: '0.55s' },
                { icon: '◆', text: 'Smart Multi-Role Placement Pipeline', delay: '0.7s' },
              ].map((f) => (
                <div key={f.text} className="brand-feature" style={{ animationDelay: f.delay }}>
                  <span className="feature-icon">{f.icon}</span>
                  <span>{f.text}</span>
                </div>
              ))}
            </div>

            <div className="brand-stat-row">
              <div className="brand-stat">
                <div className="brand-stat-value">500+</div>
                <div className="brand-stat-label">Students Placed</div>
              </div>
              <div className="brand-stat">
                <div className="brand-stat-value">95%</div>
                <div className="brand-stat-label">Placement Rate</div>
              </div>
              <div className="brand-stat">
                <div className="brand-stat-value">50+</div>
                <div className="brand-stat-label">Top Recruiters</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right form panel */}
        <div className="login-form-panel">
          <div className="login-form-wrapper">
            <div className="form-header" style={{ animationDelay: '0.1s' }}>
              <div className="welcome-tag">PORTAL AUTHENTICATION</div>
              <h2>Sign in to CCIP</h2>
              <p>Select your persona below or enter your registered account credentials</p>
            </div>

            {/* Quick Demo Credential Selector */}
            <div className="demo-panel form-field" style={{ animationDelay: '0.2s' }}>
              <div className="demo-header-row">
                <span className="demo-label">⚡ 1-Click Demo Accounts</span>
                <span className="demo-sublabel">Select any role to auto-fill</span>
              </div>

              <div className="demo-grid">
                {DEMO_ROLES.map((cred) => {
                  const isActive = selectedRole.role === cred.role;
                  return (
                    <button
                      key={cred.role}
                      type="button"
                      className={`demo-chip ${isActive ? 'is-active' : ''}`}
                      onClick={() => handleSelectRole(cred)}
                      style={{ '--chip-color': cred.color }}
                      title={`Switch to ${cred.label}`}
                    >
                      <span className="demo-chip-icon">{cred.icon}</span>
                      <span className="demo-chip-label">{cred.label}</span>
                      {isActive && <span className="demo-chip-dot" />}
                    </button>
                  );
                })}
              </div>

              {/* Active Credential Card */}
              {selectedRole && (
                <div
                  className="credential-info-card"
                  style={{
                    borderColor: `${selectedRole.color}40`,
                    background: `color-mix(in srgb, ${selectedRole.color} 5%, var(--bg-card))`,
                  }}
                >
                  <div className="card-top-row">
                    <div className="user-persona">
                      <span className="user-name">{selectedRole.name}</span>
                      <span className="user-badge" style={{ backgroundColor: `${selectedRole.color}20`, color: selectedRole.color }}>
                        {selectedRole.tag}
                      </span>
                    </div>

                    <button
                      type="button"
                      className="instant-login-btn"
                      style={{ backgroundColor: selectedRole.color }}
                      onClick={() => handleInstantDemoLogin(selectedRole)}
                      disabled={loading}
                    >
                      {loading ? 'Entering…' : `1-Click Login ➔`}
                    </button>
                  </div>

                  <p className="card-desc">{selectedRole.desc}</p>

                  <div className="credential-keys-row">
                    <div
                      className="cred-key-pill"
                      onClick={() => copyToClipboard(selectedRole.email, 'email')}
                      title="Click to copy email"
                    >
                      <span className="key-title">Email:</span>
                      <code className="key-val">{selectedRole.email}</code>
                      <span className="copy-badge">{copiedField === 'email' ? '✓ Copied' : 'Copy'}</span>
                    </div>

                    <div
                      className="cred-key-pill"
                      onClick={() => copyToClipboard(selectedRole.password, 'password')}
                      title="Click to copy password"
                    >
                      <span className="key-title">Pass:</span>
                      <code className="key-val">{selectedRole.password}</code>
                      <span className="copy-badge">{copiedField === 'password' ? '✓ Copied' : 'Copy'}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Error Banner */}
            {error && (
              <div className="form-error">
                <div className="error-header-line">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                  <span>{error}</span>
                </div>

                {networkError && (
                  <button
                    type="button"
                    className="demo-fallback-btn"
                    onClick={() => performLogin(email, password, { forceMock: true })}
                  >
                    🚀 Enter in Standalone Demo Mode ➔
                  </button>
                )}
              </div>
            )}

            {/* Standard Login Form */}
            <form onSubmit={handleSubmit} className="login-form">
              <div className="input-group form-field" style={{ animationDelay: '0.3s' }}>
                <label htmlFor="login-email">Email address</label>
                <div className="input-with-icon">
                  <svg className="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect width="20" height="16" x="2" y="4" rx="2" />
                    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
                  </svg>
                  <input
                    id="login-email"
                    className="input input-has-icon"
                    type="email"
                    placeholder="name@ccip.edu"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    required
                    autoComplete="email"
                  />
                </div>
              </div>

              <div className="input-group form-field" style={{ animationDelay: '0.4s' }}>
                <div className="password-label-row">
                  <label htmlFor="login-password">Password</label>
                  <button
                    type="button"
                    className="text-toggle-btn"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? 'Hide password' : 'Show password'}
                  </button>
                </div>
                <div className="input-with-icon">
                  <svg className="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                  <input
                    id="login-password"
                    className="input input-has-icon input-has-action"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Enter password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    className="input-action-icon"
                    onClick={() => setShowPassword(!showPassword)}
                    title={showPassword ? 'Hide password' : 'Show password'}
                    aria-label="Toggle password visibility"
                  >
                    {showPassword ? (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                        <line x1="1" y1="1" x2="23" y2="23" />
                      </svg>
                    ) : (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                        <circle cx="12" cy="12" r="3" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              <button
                id="login-submit"
                type="submit"
                className="btn btn-primary login-btn form-field"
                disabled={loading}
                style={{ animationDelay: '0.5s' }}
              >
                {loading ? (
                  <span className="btn-loading">
                    <span className="spinner" />
                    Authenticating…
                  </span>
                ) : (
                  <>
                    Sign In to Portal
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M5 12h14" /><path d="m12 5 7 7-7 7" />
                    </svg>
                  </>
                )}
              </button>
            </form>

            <p className="form-footer form-field" style={{ animationDelay: '0.6s' }}>
              New to CCIP?{' '}
              <Link to="/register">Create an account</Link>
            </p>
          </div>
        </div>
      </div>

      <style>{`
        .login-page {
          min-height: 100vh;
          background: var(--bg-primary);
          position: relative;
          overflow: hidden;
          transition: background-color 0.4s ease;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        /* ── Animated background ── */
        .login-bg {
          position: absolute;
          inset: 0;
          overflow: hidden;
          pointer-events: none;
        }

        .blob {
          position: absolute;
          border-radius: 50%;
          filter: blur(80px);
          animation: blob-move 20s ease-in-out infinite;
          will-change: transform;
        }

        .blob-1 {
          width: 500px;
          height: 500px;
          background: rgba(124, 58, 237, 0.12);
          top: -10%;
          left: 10%;
        }

        .blob-2 {
          width: 450px;
          height: 450px;
          background: rgba(6, 182, 212, 0.09);
          bottom: -5%;
          right: 10%;
          animation-delay: -7s;
          animation-duration: 25s;
        }

        .blob-3 {
          width: 320px;
          height: 320px;
          background: rgba(244, 114, 182, 0.07);
          top: 45%;
          left: 45%;
          animation-delay: -14s;
          animation-duration: 22s;
        }

        @keyframes blob-move {
          0%, 100% { transform: translate(0, 0) scale(1); }
          25% { transform: translate(40px, -50px) scale(1.08); }
          50% { transform: translate(-30px, 30px) scale(0.94); }
          75% { transform: translate(25px, 45px) scale(1.03); }
        }

        .grid-overlay {
          position: absolute;
          inset: 0;
          background-image:
            linear-gradient(var(--border-color) 1px, transparent 1px),
            linear-gradient(90deg, var(--border-color) 1px, transparent 1px);
          background-size: 48px 48px;
          opacity: 0.25;
        }

        /* ── Layout container ── */
        .login-container {
          position: relative;
          z-index: 1;
          display: flex;
          width: 100%;
          max-width: 1140px;
          min-height: 640px;
          margin: 32px 20px;
          background: var(--bg-card);
          border: 1px solid var(--border-color);
          border-radius: 24px;
          overflow: hidden;
          box-shadow: 0 20px 50px rgba(0, 0, 0, 0.12);
          backdrop-filter: blur(16px);
        }

        /* ── Left branding ── */
        .login-brand {
          flex: 0 0 42%;
          background: linear-gradient(145deg, var(--bg-secondary), var(--bg-tertiary));
          padding: 48px 40px;
          display: flex;
          flex-direction: column;
          justify-content: center;
          position: relative;
          border-right: 1px solid var(--border-color);
        }

        .brand-content {
          max-width: 380px;
        }

        .brand-badge-pill {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 4px 12px;
          border-radius: 999px;
          background: var(--accent-primary-subtle);
          border: 1px solid rgba(124, 58, 237, 0.2);
          font-size: 0.75rem;
          font-weight: 600;
          color: var(--accent-primary);
          margin-bottom: 24px;
        }

        .pulse-dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: #10b981;
          box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
          animation: pulse 2s infinite;
        }

        .brand-icon {
          width: 54px;
          height: 54px;
          border-radius: 16px;
          background: var(--gradient-primary);
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 20px;
          box-shadow: 0 8px 24px rgba(124, 58, 237, 0.35);
        }

        .brand-title {
          font-size: 3.2rem;
          font-weight: 800;
          letter-spacing: -0.05em;
          line-height: 1;
          background: var(--gradient-warm);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .brand-subtitle {
          font-size: 1.1rem;
          color: var(--text-secondary);
          margin-top: 10px;
          line-height: 1.4;
        }

        .brand-features {
          margin-top: 36px;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .brand-feature {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: var(--font-size-sm);
          color: var(--text-secondary);
        }

        .feature-icon {
          color: var(--accent-primary);
          font-size: 0.75rem;
          width: 26px;
          height: 26px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--accent-primary-subtle);
          border-radius: 8px;
          border: 1px solid rgba(124, 58, 237, 0.15);
          flex-shrink: 0;
        }

        .brand-stat-row {
          margin-top: 40px;
          display: flex;
          gap: 24px;
          padding-top: 24px;
          border-top: 1px solid var(--border-color);
        }

        .brand-stat-value {
          font-size: var(--font-size-xl);
          font-weight: 700;
          color: var(--text-primary);
        }

        .brand-stat-label {
          font-size: 0.75rem;
          color: var(--text-muted);
          margin-top: 2px;
        }

        /* ── Right form panel ── */
        .login-form-panel {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 40px 48px;
        }

        .login-form-wrapper {
          width: 100%;
          max-width: 440px;
        }

        .welcome-tag {
          font-size: 0.6875rem;
          font-weight: 700;
          letter-spacing: 0.08em;
          color: var(--accent-primary);
          margin-bottom: 6px;
        }

        .form-header h2 {
          font-size: 1.75rem;
          font-weight: 700;
          letter-spacing: -0.03em;
          color: var(--text-primary);
        }

        .form-header p {
          color: var(--text-muted);
          font-size: 0.875rem;
          margin-top: 4px;
          margin-bottom: 20px;
        }

        /* ── Demo Panel & Quick Selector ── */
        .demo-panel {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 14px;
          padding: 16px;
          margin-bottom: 20px;
        }

        .demo-header-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .demo-label {
          font-size: 0.75rem;
          font-weight: 700;
          color: var(--text-primary);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .demo-sublabel {
          font-size: 0.7rem;
          color: var(--text-muted);
        }

        .demo-grid {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          margin-bottom: 12px;
        }

        .demo-chip {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 5px 12px;
          border-radius: 999px;
          background: var(--bg-card);
          border: 1px solid var(--border-color);
          color: var(--text-secondary);
          font-size: 0.75rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .demo-chip:hover {
          border-color: var(--chip-color);
          color: var(--chip-color);
          background: color-mix(in srgb, var(--chip-color) 8%, var(--bg-card));
          transform: translateY(-1px);
        }

        .demo-chip.is-active {
          border-color: var(--chip-color);
          background: color-mix(in srgb, var(--chip-color) 14%, var(--bg-card));
          color: var(--chip-color);
          box-shadow: 0 2px 8px color-mix(in srgb, var(--chip-color) 25%, transparent);
        }

        .demo-chip-dot {
          width: 5px;
          height: 5px;
          border-radius: 50%;
          background: currentColor;
        }

        /* Credential Info Card */
        .credential-info-card {
          border: 1px solid;
          border-radius: 10px;
          padding: 12px;
          margin-top: 10px;
          animation: fadeIn 0.25s ease;
        }

        .card-top-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
        }

        .user-persona {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .user-name {
          font-weight: 700;
          font-size: 0.85rem;
          color: var(--text-primary);
        }

        .user-badge {
          font-size: 0.65rem;
          font-weight: 700;
          padding: 2px 8px;
          border-radius: 999px;
          letter-spacing: 0.02em;
        }

        .instant-login-btn {
          border: none;
          color: #ffffff;
          font-size: 0.75rem;
          font-weight: 600;
          padding: 5px 12px;
          border-radius: 6px;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 4px;
          transition: filter 0.2s, transform 0.2s;
          white-space: nowrap;
        }

        .instant-login-btn:hover {
          filter: brightness(1.1);
          transform: scale(1.02);
        }

        .card-desc {
          font-size: 0.75rem;
          color: var(--text-secondary);
          margin: 6px 0 10px;
          line-height: 1.35;
        }

        .credential-keys-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
        }

        .cred-key-pill {
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: var(--bg-card);
          border: 1px solid var(--border-color);
          border-radius: 6px;
          padding: 4px 8px;
          font-size: 0.7rem;
          cursor: pointer;
          transition: border-color 0.2s ease;
        }

        .cred-key-pill:hover {
          border-color: var(--accent-primary);
        }

        .key-title {
          color: var(--text-muted);
          font-weight: 600;
          margin-right: 4px;
        }

        .key-val {
          color: var(--text-primary);
          font-family: monospace;
          font-size: 0.7rem;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          flex: 1;
        }

        .copy-badge {
          font-size: 0.65rem;
          color: var(--accent-primary);
          font-weight: 600;
          margin-left: 6px;
        }

        /* ── Error Banner ── */
        .form-error {
          background: rgba(239, 68, 68, 0.08);
          border: 1px solid rgba(239, 68, 68, 0.25);
          border-radius: var(--border-radius-sm);
          padding: 12px 14px;
          color: var(--accent-danger);
          font-size: 0.8125rem;
          margin-bottom: 18px;
          animation: slideInUp 0.3s ease;
        }

        .error-header-line {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          line-height: 1.4;
        }

        .demo-fallback-btn {
          margin-top: 10px;
          width: 100%;
          background: var(--accent-primary);
          color: white;
          border: none;
          padding: 8px 12px;
          border-radius: 6px;
          font-size: 0.8rem;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          transition: opacity 0.2s;
        }

        .demo-fallback-btn:hover {
          opacity: 0.92;
        }

        /* ── Form Inputs ── */
        .login-form {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .password-label-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 4px;
        }

        .text-toggle-btn {
          background: none;
          border: none;
          color: var(--accent-primary);
          font-size: 0.72rem;
          font-weight: 600;
          cursor: pointer;
          padding: 0;
        }

        .input-with-icon {
          position: relative;
        }

        .input-icon {
          position: absolute;
          left: 14px;
          top: 50%;
          transform: translateY(-50%);
          color: var(--text-muted);
          pointer-events: none;
          transition: color 0.2s ease;
        }

        .input-action-icon {
          position: absolute;
          right: 12px;
          top: 50%;
          transform: translateY(-50%);
          background: none;
          border: none;
          color: var(--text-muted);
          cursor: pointer;
          padding: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: color 0.2s;
        }

        .input-action-icon:hover {
          color: var(--text-primary);
        }

        .input-has-icon {
          padding-left: 42px !important;
          width: 100% !important;
        }

        .input-has-action {
          padding-right: 40px !important;
        }

        .input-with-icon:focus-within .input-icon {
          color: var(--accent-primary);
        }

        .login-btn {
          width: 100%;
          height: 44px !important;
          font-size: 0.9375rem !important;
          gap: 8px;
          margin-top: 4px;
        }

        .btn-loading {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .spinner {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 0.6s linear infinite;
          display: inline-block;
        }

        .form-footer {
          text-align: center;
          margin-top: 20px;
          font-size: 0.8125rem;
          color: var(--text-muted);
        }

        .form-footer a {
          color: var(--accent-primary);
          font-weight: 600;
        }

        .form-footer a:hover {
          text-decoration: underline;
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(4px); }
          to { opacity: 1; transform: translateY(0); }
        }

        /* ── Responsive ── */
        @media (max-width: 900px) {
          .login-container {
            flex-direction: column;
            margin: 16px;
          }
          .login-brand {
            flex: none;
            padding: 32px 24px;
            border-right: none;
            border-bottom: 1px solid var(--border-color);
          }
          .brand-stat-row {
            display: none;
          }
          .login-form-panel {
            padding: 28px 20px;
          }
          .credential-keys-row {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}
