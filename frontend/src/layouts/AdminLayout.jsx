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
            padding: '12px 32px',
            borderBottom: '1px solid var(--border-color, #374151)',
            background: 'var(--bg-secondary, #111827)',
          }}
        >
          <NotificationBell />
        </header>
        <Outlet />
      </main>
    </div>
  );
}
