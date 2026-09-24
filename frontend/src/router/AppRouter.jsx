/**
 * Application router — role-based routing for all 4 portals.
 * Route protection via ProtectedRoute component.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Auth pages
import LoginPage from '../pages/auth/LoginPage';
import RegisterPage from '../pages/auth/RegisterPage';

// Admin Portal
import AdminLayout from '../layouts/AdminLayout';
import AdminDashboard from '../pages/admin/AdminDashboard';
import UserManagement from '../pages/admin/UserManagement';
import SystemSettings from '../pages/admin/SystemSettings';

// Student portal
import StudentLayout from '../layouts/StudentLayout';
import StudentDashboard from '../pages/student/Dashboard';
import StudentProfile from '../pages/student/Profile';
import JobMatches from '../pages/student/JobMatches';
import SkillGap from '../pages/student/SkillGap';
import Roadmap from '../pages/student/Roadmap';
import Notifications from '../pages/student/Notifications';
import PlacementDrives from '../pages/student/PlacementDrives';
import DriveDetail from '../pages/student/DriveDetail';
import InterviewExperiences from '../pages/student/InterviewExperiences';
import Copilot from '../pages/student/Copilot';
import AssessmentsList from '../pages/student/AssessmentsList';
import AssessmentTake from '../pages/student/AssessmentTake';
import PublicPortfolio from '../pages/student/PublicPortfolio';
import MockInterview from '../pages/student/MockInterview';
import MockInterviewHistory from '../pages/student/MockInterviewHistory';
import QuizCenter from '../pages/student/QuizCenter';
import SkillTrends from '../pages/student/SkillTrends';
import Benchmark from '../pages/student/Benchmark';
import AssessmentAnalytics from '../pages/student/AssessmentAnalytics';

// TPO portal
import TPOLayout from '../layouts/TPOLayout';
import TPODashboard from '../pages/tpo/Dashboard';
import TPOStudents from '../pages/tpo/Students';
import TPODrives from '../pages/tpo/Drives';
import TPOAnalytics from '../pages/tpo/Analytics';
import BIStudio from '../pages/tpo/BIStudio';

// Faculty/HOD portal
import FacultyLayout from '../layouts/FacultyLayout';
import FacultyDashboard from '../pages/faculty/Dashboard';
import CurriculumMap from '../pages/faculty/CurriculumMap';
import ProposalManager from '../pages/faculty/ProposalManager';

// Shared
import NotFound from '../pages/NotFound';

function ProtectedRoute({ children, roles }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: '100vh', background: 'var(--bg-primary)', color: 'var(--text-secondary)'
      }}>
        Loading...
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/login" replace />;

  return children;
}

export function AppRouter() {
  const { user } = useAuth();

  return (
    <BrowserRouter>
      <Routes>
        {/* Admin Routes */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute roles={['admin']}>
              <AdminLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<AdminDashboard />} />
          <Route path="users" element={<UserManagement />} />
          <Route path="settings" element={<SystemSettings />} />
        </Route>

        {/* Public */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/portfolio/:studentId" element={<PublicPortfolio />} />
        <Route path="/student/portfolio/:studentId" element={<PublicPortfolio />} />

        {/* Root redirect based on role */}
        <Route
          path="/"
          element={
            user
              ? <Navigate to={`/${user.role === 'admin' ? 'admin' : user.role === 'student' ? 'student' : user.role === 'tpo' ? 'tpo' : 'faculty'}/dashboard`} replace />
              : <Navigate to="/login" replace />
          }
        />

        {/* ─── Student Portal ─── */}
        <Route
          path="/student"
          element={
            <ProtectedRoute roles={['student']}>
              <StudentLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<StudentDashboard />} />
          <Route path="profile" element={<StudentProfile />} />
          <Route path="matches" element={<JobMatches />} />
          <Route path="skill-gap" element={<SkillGap />} />
          <Route path="roadmap" element={<Roadmap />} />
          <Route path="career-roadmap" element={<Roadmap />} />
          <Route path="notifications" element={<Notifications />} />
          <Route path="drives" element={<PlacementDrives />} />
          <Route path="drives/:id" element={<DriveDetail />} />
          <Route path="experiences" element={<InterviewExperiences />} />
          <Route path="copilot" element={<Copilot />} />
          <Route path="assessments" element={<AssessmentsList />} />
          <Route path="assessments/:id/take" element={<AssessmentTake />} />
          <Route path="assessments/analytics" element={<AssessmentAnalytics />} />
          <Route path="skill-trends" element={<SkillTrends />} />
          <Route path="benchmark" element={<Benchmark />} />
          <Route path="mock-interview" element={<MockInterview />} />
          <Route path="mock-interview/history" element={<MockInterviewHistory />} />
          <Route path="quiz" element={<QuizCenter />} />
        </Route>

        {/* ─── TPO Portal ─── */}
        <Route
          path="/tpo"
          element={
            <ProtectedRoute roles={['tpo', 'admin']}>
              <TPOLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<TPODashboard />} />
          <Route path="students" element={<TPOStudents />} />
          <Route path="drives" element={<TPODrives />} />
          <Route path="drives/:id" element={<DriveDetail />} />
          <Route path="analytics" element={<TPOAnalytics />} />
          <Route path="bi-studio" element={<BIStudio />} />
        </Route>

        {/* ─── Faculty/HOD Portal ─── */}
        <Route
          path="/faculty"
          element={
            <ProtectedRoute roles={['faculty', 'hod']}>
              <FacultyLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<FacultyDashboard />} />
          <Route path="curriculum" element={<CurriculumMap />} />
          <Route path="proposals" element={<ProposalManager />} />
          <Route path="students" element={<TPOStudents />} />
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
