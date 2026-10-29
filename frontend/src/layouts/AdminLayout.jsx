/**
 * Admin portal layout — sidebar + outlet.
 */

import { Outlet } from 'react-router-dom';
import AppSidebar from '../components/AppSidebar';
import NotificationBell from '../components/NotificationBell';

const ADMIN_NAV = [
  {
    label: null,
    items: [
      { path: '/admin/dashboard', icon: '⚡', label: 'Dashboard' },
    ],
  },
  {
    label: 'Administration',
    items: [
      { path: '/admin/users', icon: '👥', label: 'User Management' },
      { path: '/admin/settings', icon: '⚙️', label: 'System Settings' },
    ],
  },
  {
    label: 'Platform Views',
    items: [
      { path: '/tpo/dashboard', icon: '🏢', label: 'TPO Portal' },
      { path: '/faculty/dashboard', icon: '🎓', label: 'Faculty Portal' },
    ],
  },
];

export default function AdminLayout() {
  return (
    <div className="layout">
      <AppSidebar logo="CCIP" subtitle="Admin Panel" navItems={ADMIN_NAV} />
      <main className="main-content">
        <header
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            alignItems: 'center',
            padding: '10px 28px',
            borderBottom: '1px solid var(--border-color)',
            background: 'var(--bg-secondary)',
            height: 'var(--header-height)',
            transition: 'background-color 0.3s ease, border-color 0.3s ease',
          }}
        >
          <NotificationBell />
        </header>
        <Outlet />
      </main>
    </div>
  );
}
