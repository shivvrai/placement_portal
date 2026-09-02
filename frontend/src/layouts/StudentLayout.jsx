/**
 * Student portal layout — sidebar + outlet.
 */

import { Outlet } from 'react-router-dom';
import AppSidebar from '../components/AppSidebar';

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
        <Outlet />
      </main>
    </div>
  );
}
