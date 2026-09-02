/**
 * TPO portal layout.
 */

import { Outlet } from 'react-router-dom';
import AppSidebar from '../components/AppSidebar';

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
    ],
  },
];

export default function TPOLayout() {
  return (
    <div className="layout">
      <AppSidebar logo="CCIP" subtitle="TPO Portal" navItems={TPO_NAV} />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
