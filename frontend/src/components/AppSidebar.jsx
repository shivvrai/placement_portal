/**
 * Shared sidebar navigation component.
 * Receives navItems config and renders role-appropriate nav.
 */

import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function AppSidebar({ logo, subtitle, navItems, footerItems = [] }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-header">
        <div className="sidebar-logo">{logo}</div>
        {subtitle && (
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 4 }}>
            {subtitle}
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {navItems.map((section) => (
          <div key={section.label} style={{ marginBottom: 'var(--space-4)' }}>
            {section.label && (
              <div className="nav-section-label">{section.label}</div>
            )}
            {section.items.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
              >
                <span style={{ fontSize: '1.1rem' }}>{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* User info + logout */}
      <div style={{
        padding: 'var(--space-4)',
        borderTop: '1px solid var(--border-color)',
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 'var(--space-3)',
          marginBottom: 'var(--space-3)',
        }}>
          <div style={{
            width: 36, height: 36, borderRadius: '50%',
            background: 'var(--gradient-primary)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'white',
            flexShrink: 0,
          }}>
            {user?.first_name?.[0]}{user?.last_name?.[0]}
          </div>
          <div style={{ overflow: 'hidden' }}>
            <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, truncate: 'ellipsis' }}>
              {user?.first_name} {user?.last_name}
            </div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
              {user?.role?.toUpperCase()}
            </div>
          </div>
        </div>
        <button
          className="btn btn-ghost"
          onClick={handleLogout}
          style={{ width: '100%', justifyContent: 'flex-start', height: 36 }}
        >
          🚪 Sign out
        </button>
      </div>
    </aside>
  );
}
