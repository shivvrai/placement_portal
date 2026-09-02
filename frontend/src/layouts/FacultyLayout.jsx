/**
 * Faculty / HOD portal layout.
 */

import { Outlet } from 'react-router-dom';
import AppSidebar from '../components/AppSidebar';

const FACULTY_NAV = [
  {
    label: null,
    items: [
      { path: '/faculty/dashboard', icon: '🏠', label: 'Dashboard' },
      { path: '/faculty/curriculum', icon: '📚', label: 'Curriculum Map' },
    ],
  },
];

export default function FacultyLayout() {
  return (
    <div className="layout">
      <AppSidebar logo="CCIP" subtitle="Faculty Portal" navItems={FACULTY_NAV} />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
