/**
 * Typed API functions for all CCIP endpoints.
 * Frontend developers call these — not axios directly.
 * 
 * When VITE_USE_MOCKS=true, these return stub data from /public/mocks/
 */

import { api } from './client';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

async function mockOr(mockFile, apiFn) {
  if (USE_MOCKS) {
    const res = await fetch(`/mocks/${mockFile}`);
    return { data: await res.json() };
  }
  return apiFn();
}

// ─── Auth ─────────────────────────────────────────────────────────
export const authApi = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (data) => api.post('/auth/register', data),
  refresh: (token) => api.post('/auth/refresh', { refresh_token: token }),
  me: () => api.get('/auth/me'),
};

// ─── Student Profile ──────────────────────────────────────────────
export const studentApi = {
  getProfile: (id) => mockOr('student_profile.json', () => api.get(`/students/${id}`)),
  updateProfile: (id, data) => api.patch(`/students/${id}`, data),
  getSkills: (id) => mockOr('student_skills.json', () => api.get(`/students/${id}/skills`)),
  getAcademicRecords: (id) => mockOr('academic_records.json', () => api.get(`/students/${id}/academic-records`)),
  getAttendance: (id) => mockOr('attendance.json', () => api.get(`/students/${id}/attendance`)),
  uploadResume: (id, file) => {
    const form = new FormData();
    form.append('file', file);
    return api.post(`/students/${id}/resume`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  updateConsent: (id, consent) => api.patch(`/students/${id}/consent`, consent),
};

// ─── Matching & Intelligence ──────────────────────────────────────
export const intelligenceApi = {
  getMatches: (studentId, params) =>
    mockOr('job_matches.json', () => api.get(`/matching/students/${studentId}/jobs`, { params })),
  getSkillGap: (studentId, jobId) =>
    mockOr('skill_gap.json', () => api.get(`/gaps/students/${studentId}/jobs/${jobId}`)),
  getRoadmap: (studentId) =>
    mockOr('roadmap.json', () => api.get(`/roadmap/students/${studentId}`)),
  generateRoadmap: (studentId, targetRole) =>
    api.post(`/roadmap/students/${studentId}/generate`, { target_role: targetRole }),
  updateTask: (taskId, status) =>
    api.patch(`/roadmap/tasks/${taskId}`, { status }),
};

// ─── Placement Drives ─────────────────────────────────────────────
export const placementApi = {
  getDrives: (params) => mockOr('drives.json', () => api.get('/drives', { params })),
  getDrive: (id) => mockOr('drive_detail.json', () => api.get(`/drives/${id}`)),
  apply: (driveId) => api.post(`/drives/${driveId}/apply`),
  getMyApplications: () => mockOr('applications.json', () => api.get('/applications/mine')),
  // TPO
  createDrive: (data) => api.post('/drives', data),
  updateDrive: (id, data) => api.patch(`/drives/${id}`, data),
  shortlistStudents: (driveId) => api.get(`/drives/${driveId}/shortlisted`),
};

// ─── Analytics ────────────────────────────────────────────────────
export const analyticsApi = {
  getPlacementStats: (params) =>
    mockOr('placement_stats.json', () => api.get('/analytics/placement', { params })),
  getSkillDemand: (params) =>
    mockOr('skill_demand.json', () => api.get('/analytics/skill-demand', { params })),
  getCurriculumGaps: (deptCode) =>
    mockOr('curriculum_gaps.json', () => api.get(`/analytics/curriculum-gaps/${deptCode}`)),
  getDepartmentOverview: (deptCode) =>
    mockOr('dept_overview.json', () => api.get(`/analytics/departments/${deptCode}`)),
};

// ─── Curriculum ───────────────────────────────────────────────────
export const curriculumApi = {
  getSubjects: (dept, semester) =>
    mockOr('subjects.json', () => api.get('/curriculum/subjects', { params: { dept, semester } })),
  getSubjectSkills: (subjectId) =>
    api.get(`/curriculum/subjects/${subjectId}/skills`),
  suggestSkillMappings: (subjectId) =>
    api.post(`/curriculum/subjects/${subjectId}/suggest-mappings`),
};

// ─── AI Career Copilot ────────────────────────────────────────────
export const copilotApi = {
  getConversations: () => api.get('/copilot/conversations'),
  createConversation: () => api.post('/copilot/conversations'),
  sendMessage: (convId, message) =>
    api.post(`/copilot/conversations/${convId}/messages`, { message }),
  getHistory: (convId) => api.get(`/copilot/conversations/${convId}`),
};

// ─── Skills Taxonomy ──────────────────────────────────────────────
export const skillsApi = {
  getAll: (params) => mockOr('skills.json', () => api.get('/skills', { params })),
  search: (query) => api.get('/skills/search', { params: { q: query } }),
};

// ─── TPO / Admin ──────────────────────────────────────────────────
export const tpoApi = {
  getStudents: (params) => mockOr('students_list.json', () => api.get('/students', { params })),
  getStudent: (id) => api.get(`/students/${id}`),
  syncUMS: (rollNumber) => api.post('/ums/sync', { roll_number: rollNumber }),
};

// ─── Assessments ──────────────────────────────────────────────────
export const assessmentsApi = {
  getSkills: () => api.get('/assessments/skills'),
  start: (topic, difficulty) => api.post('/assessments/start', { topic, difficulty }),
  submit: (sessionId, answers) => api.post(`/assessments/${sessionId}/submit`, { answers }),
  getHistory: () => api.get('/assessments/history'),
};

