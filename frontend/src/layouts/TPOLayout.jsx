/**
 * TPO portal layout.
 */

import { Outlet } from 'react-router-dom';
import AppSidebar from '../components/AppSidebar';
import NotificationBell from '../components/NotificationBell';

const TPO_NAV = [
  {
    label: null,
    items: [
      { path: '/tpo/dashboard', icon: '🏠', label: 'Dashboard' },
    ],
  },
  {
    label: 'Management',
    items: [
      { path: '/tpo/students', icon: '👥', label: 'Students' },
      { path: '/tpo/drives', icon: '🏢', label: 'Placement Drives' },
    ],
  },
  {
    label: 'Insights',
    items: [
      { path: '/tpo/analytics', icon: '📈', label: 'Analytics' },
      { path: '/tpo/bi-studio', icon: '📊', label: 'BI Studio' },
    ],
  },
];

export default function TPOLayout() {
  return (
    <div className="layout">
      <AppSidebar logo="CCIP" subtitle="TPO Portal" navItems={TPO_NAV} />
      <main className="main-content">
        <div style={{
          display: 'flex',
          justifyContent: 'flex-end',
          alignItems: 'center',
          padding: '12px 32px',
          borderBottom: '1px solid var(--border-color)',
          background: 'var(--bg-secondary)',
        }}>
          <NotificationBell />
        </div>
        <Outlet />
      </main>
    </div>
  );
}
