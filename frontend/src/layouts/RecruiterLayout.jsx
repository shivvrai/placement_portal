/**
 * Recruiter portal layout — now uses shared AppSidebar for consistency.
 */

import { Outlet } from 'react-router-dom';
import AppSidebar from '../components/AppSidebar';

const RECRUITER_NAV = [
  {
    label: null,
    items: [
      { path: '/recruiter/dashboard', icon: '🏠', label: 'Dashboard' },
      { path: '/recruiter/drives', icon: '🏢', label: 'Placement Drives' },
    ],
  },
];

export default function RecruiterLayout() {
  return (
    <div className="layout">
      <AppSidebar logo="CCIP" subtitle="Recruiter CRM" navItems={RECRUITER_NAV} />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
