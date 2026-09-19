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
    label: 'Placement & Careers',
    items: [
      { path: '/student/drives', icon: '🏢', label: 'Placement Drives' },
      { path: '/student/experiences', icon: '💡', label: 'Interview Experiences' },
    ],
  },
];

export default function StudentLayout() {
  return (
    <div className="layout">
      <AppSidebar logo="CCIP" subtitle="Student Portal" navItems={STUDENT_NAV} />
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
