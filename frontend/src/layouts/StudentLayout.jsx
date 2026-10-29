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
      { path: '/student/notifications', icon: '🔔', label: 'Notifications' },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { path: '/student/matches', icon: '🎯', label: 'Job Matches' },
      { path: '/student/skill-gap', icon: '📊', label: 'Skill Gap' },
      // { path: '/student/roadmap', icon: '🗺️', label: 'Career Roadmap' }, // Commented out
      { path: '/student/assessments', icon: '📝', label: 'Assessments' },
      { path: '/student/exam-results', icon: '🎓', label: 'Exam Results' },
      // { path: '/student/skill-trends', icon: '📈', label: 'Skill Trends' }, // Commented out
      { path: '/student/benchmark', icon: '🏆', label: 'Peer Benchmark' },
    ],
  },
  {
    label: 'Placement & Careers',
    items: [
      { path: '/student/drives', icon: '🏢', label: 'Placement Drives' },
      { path: '/student/applications', icon: '📋', label: 'Application Tracker' },
      { path: '/student/vault', icon: '📁', label: 'Document Vault' },
      { path: '/student/company-insights', icon: '🏢', label: 'Company Insights' },
      { path: '/student/experiences', icon: '💡', label: 'Interview Experiences' },
    ],
  },
  {
    label: 'Community & Prep',
    items: [
      { path: '/student/mentorship', icon: '🤝', label: 'Alumni Mentorship' },
      { path: '/student/prep', icon: '📚', label: 'Prep Hub' },
    ],
  },
];

export default function StudentLayout() {
  return (
    <div className="layout">
      <AppSidebar logo="CCIP" subtitle="Student Portal" navItems={STUDENT_NAV} />
      <main className="main-content">
        <header
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            alignItems: 'center',
            padding: '10px 28px',
            borderBottom: '1px solid var(--border-color)',
            background: 'var(--bg-secondary)',
            height: 'var(--header-height)',
            transition: 'background-color 0.3s ease, border-color 0.3s ease',
          }}
        >
          <NotificationBell />
        </header>
        <Outlet />
      </main>
    </div>
  );
}
