/**
 * Shared sidebar navigation component.
 * Receives navItems config and renders role-appropriate nav.
 * Includes integrated theme toggle.
 */

import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ThemeToggle from './ThemeToggle';

export default function AppSidebar({ logo, subtitle, navItems, footerItems = [] }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside className="sidebar">
      {/* Logo + Theme Toggle */}
      <div className="sidebar-header">
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div>
            <div className="sidebar-logo">{logo}</div>
            {subtitle && (
              <div style={{
                fontSize: 'var(--font-size-xs)',
                color: 'var(--text-muted)',
                marginTop: 2,
                fontWeight: 500,
                letterSpacing: '-0.01em',
              }}>
                {subtitle}
              </div>
            )}
          </div>
          <ThemeToggle compact />
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {navItems.map((section) => (
          <div key={section.label || 'main'} style={{ marginBottom: 4 }}>
            {section.label && (
              <div className="nav-section-label">{section.label}</div>
            )}
            {section.items.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
              >
                <span style={{ fontSize: '0.95rem', lineHeight: 1, opacity: 0.85 }}>{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* User info + logout */}
      <div style={{
        padding: '12px 14px',
        borderTop: '1px solid var(--sidebar-border)',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          marginBottom: 10,
        }}>
          <div style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            background: 'var(--accent-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 'var(--font-size-xs)',
            fontWeight: 600,
            color: 'white',
            flexShrink: 0,
            letterSpacing: '0.02em',
          }}>
            {user?.first_name?.[0]}{user?.last_name?.[0]}
          </div>
          <div style={{ overflow: 'hidden', minWidth: 0 }}>
            <div style={{
              fontSize: 'var(--font-size-sm)',
              fontWeight: 600,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              color: 'var(--text-primary)',
              letterSpacing: '-0.01em',
            }}>
              {user?.first_name} {user?.last_name}
            </div>
            <div style={{
              fontSize: '0.6875rem',
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              fontWeight: 500,
            }}>
              {user?.role}
            </div>
          </div>
        </div>
        <button
          className="btn btn-ghost"
          onClick={handleLogout}
          style={{
            width: '100%',
            justifyContent: 'flex-start',
            height: 32,
            fontSize: 'var(--font-size-xs)',
            gap: 8,
            color: 'var(--text-muted)',
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          Sign out
        </button>
      </div>
    </aside>
  );
}
