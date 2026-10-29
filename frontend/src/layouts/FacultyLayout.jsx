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
      { path: '/faculty/proposals', icon: '📋', label: 'BoS Proposals' },
      { path: '/faculty/students', icon: '👥', label: 'Students Roster' },
      { path: '/faculty/exam-results', icon: '📊', label: 'Exam Results' },
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
