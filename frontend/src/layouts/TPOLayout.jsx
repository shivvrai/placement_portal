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
      { path: '/tpo/calendar', icon: '📅', label: 'Drive Calendar' },
      { path: '/tpo/offers', icon: '📄', label: 'Offer Pipeline' },
      { path: '/tpo/exam-uploads', icon: '📊', label: 'Exam Uploads' },
    ],
  },
  {
    label: 'Insights',
    items: [
      { path: '/tpo/analytics', icon: '📈', label: 'Analytics' },
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
          padding: '10px 28px',
          borderBottom: '1px solid var(--border-color)',
          background: 'var(--bg-secondary)',
          height: 'var(--header-height)',
          transition: 'background-color 0.3s ease, border-color 0.3s ease',
        }}>
          <NotificationBell />
        </div>
        <Outlet />
      </main>
    </div>
  );
}
