/**
 * Recruiter portal layout - sidebar navigation for company HR users.
 */

import { Outlet, NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NAV_ITEMS = [
  { path: '/recruiter/dashboard', icon: '🏠', label: 'Dashboard' },
  { path: '/recruiter/drives', icon: '🏢', label: 'Placement Drives' },
];

export default function RecruiterLayout() {
  const { user, logout } = useAuth();

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-primary)' }}>
      {/* Sidebar */}
      <aside style={{
        width: 240, background: 'var(--bg-secondary)', borderRight: '1px solid var(--border-color)',
        display: 'flex', flexDirection: 'column', padding: '24px 0',
      }}>
        <div style={{ padding: '0 24px', marginBottom: 28 }}>
          <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--primary)', letterSpacing: 0.5 }}>CCIP</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>Recruiter CRM Portal</div>
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                display: 'flex', alignItems: 'center', gap: 12, padding: '12px 24px',
                color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                background: isActive ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                fontWeight: isActive ? 700 : 500, fontSize: '0.9rem', textDecoration: 'none',
                borderLeft: isActive ? '3px solid var(--primary)' : '3px solid transparent',
              })}
            >
              <span>{item.icon}</span> {item.label}
            </NavLink>
          ))}
        </nav>
        <div style={{ marginTop: 'auto', padding: '20px 24px', borderTop: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            {user?.first_name} {user?.last_name}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: 12 }}>
            Recruiter · {user?.email}
          </div>
          <button onClick={logout} className="btn btn-ghost" style={{ width: '100%', fontSize: '0.82rem', height: 32 }}>
            Sign Out
          </button>
        </div>
      </aside>
      {/* Main Content */}
      <main style={{ flex: 1, overflowY: 'auto' }}>
        <Outlet />
      </main>
    </div>
  );
}
