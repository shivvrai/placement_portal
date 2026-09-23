/**
 * Student portal layout — sidebar + outlet.
 */

import { Outlet } from 'react-router-dom';
import AppSidebar from '../components/AppSidebar';
import NotificationBell from '../components/NotificationBell';

const STUDENT_NAV = [
  {
    label: null,
    items: [
      { path: '/student/dashboard', icon: '🏠', label: 'Dashboard' },
      { path: '/student/profile', icon: '👤', label: 'My Profile' },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { path: '/student/matches', icon: '🎯', label: 'Job Matches' },
      { path: '/student/skill-gap', icon: '📊', label: 'Skill Gap' },
      { path: '/student/roadmap', icon: '🗺️', label: 'Career Roadmap' },
      { path: '/student/copilot', icon: '🤖', label: 'AI Copilot' },
      { path: '/student/assessments', icon: '📝', label: 'Assessments' },
    ],
  },
  {
    label: 'Placement',
    items: [
      { path: '/student/drives', icon: '🏢', label: 'Placement Drives' },
    ],
  },
];

export default function StudentLayout() {
  return (
    <div className="layout">
      <AppSidebar logo="CCIP" subtitle="Student Portal" navItems={STUDENT_NAV} />
      <main className="main-content">
        <header style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', padding: '16px 24px', background: '#fff', borderBottom: '1px solid #f0f0f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <NotificationBell />
          </div>
        </header>
        <Outlet />
      </main>
    </div>
  );
}
