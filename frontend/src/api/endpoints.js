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
    try {
      const res = await fetch(`/mocks/${mockFile}`);
      if (res.ok) {
        return { data: await res.json() };
      }
    } catch {
      // fallback to api
    }
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
  // My (current) student profile endpoints - use JWT token for authentication
  getMyProfile: () => mockOr('student_profile.json', () => api.get('/students/me')),
  updateMyProfile: (data) => api.patch('/students/me', data),
  getMySkills: () => mockOr('student_skills.json', () => api.get('/students/me/skills')),
  addMySkill: (data) => api.post('/students/me/skills', data),
  deleteMySkill: (skillId) => {
    if (USE_MOCKS) {
      return Promise.resolve({ data: { message: 'Skill removed successfully' } });
    }
    return api.delete(`/students/me/skills/${encodeURIComponent(skillId)}`);
  },
  getMyAcademicRecords: () => mockOr('academic_records.json', () => api.get('/students/me/academic-records')),
  updateMyConsent: (consent) => api.patch('/students/me/consent', consent),

  // Portfolio: Projects
  getMyProjects: () => mockOr('student_projects.json', () => api.get('/students/me/projects')),
  addProject: (data) => api.post('/students/me/projects', data),
  deleteProject: (id) => api.delete(`/students/me/projects/${id}`),

  // Portfolio: Certifications
  getMyCertifications: () => mockOr('student_certifications.json', () => api.get('/students/me/certifications')),
  addCertification: (data) => api.post('/students/me/certifications', data),
  deleteCertification: (id) => api.delete(`/students/me/certifications/${id}`),

  // Portfolio: Work Experience
  getMyExperience: () => mockOr('student_experience.json', () => api.get('/students/me/experience')),
  addExperience: (data) => api.post('/students/me/experience', data),
  deleteExperience: (id) => api.delete(`/students/me/experience/${id}`),

  // Bulk Skills Confirmation
  bulkConfirmSkills: (data) => {
    if (USE_MOCKS) {
      return Promise.resolve({
        data: (data.skills || []).map((name, i) => ({
          id: `mock-skill-${i}-${Date.now()}`,
          skill: { name, category: 'tool' },
          confidence: 0.9,
          source: data.source || 'resume_verified',
          is_verified: true,
        }))
      });
    }
    return api.post('/students/me/skills/bulk', data);
  },

  // Public Recruiter Portfolio (No Auth Required)
  getPublicProfile: (id) => mockOr('public_profile.json', () => api.get(`/students/${id}/public-profile`)),

  // Legacy endpoints for backward compatibility (still work but require student ID)
  // Deprecated: prefer using the /me endpoints above
  getProfile: (id) => mockOr('student_profile.json', () => (id ? api.get(`/students/${id}`) : api.get('/students/me'))),
  updateProfile: (id, data) => (data ? api.patch(`/students/${id}`, data) : api.patch('/students/me', id)),
  getSkills: (id) => mockOr('student_skills.json', () => (id ? api.get(`/students/${id}/skills`) : api.get('/students/me/skills'))),
  addSkill: (data) => api.post('/students/me/skills', data),
  deleteSkill: (skillId) => {
    if (USE_MOCKS) {
      return Promise.resolve({ data: { message: 'Skill removed successfully' } });
    }
    return api.delete(`/students/me/skills/${encodeURIComponent(skillId)}`);
  },
  getAcademicRecords: (id) => mockOr('academic_records.json', () => (id ? api.get(`/students/${id}/academic-records`) : api.get('/students/me/academic-records'))),
  getAttendance: (id) => mockOr('attendance.json', () => (id ? api.get(`/students/${id}/attendance`) : api.get('/students/me/attendance'))),
  uploadResume: (idOrFile, file) => {
    const fileObj = (idOrFile instanceof File || idOrFile instanceof Blob) ? idOrFile : file;
    if (USE_MOCKS) {
      return Promise.resolve({
        data: {
          message: 'Resume uploaded. Review and confirm extracted skills.',
          status: 'processing',
          extracted_skills: [
            { name: 'Python', confidence: 0.95, raw: 'Python' },
            { name: 'React', confidence: 0.92, raw: 'React' },
            { name: 'FastAPI', confidence: 0.90, raw: 'FastAPI' },
            { name: 'PostgreSQL', confidence: 0.88, raw: 'PostgreSQL' },
            { name: 'Docker', confidence: 0.86, raw: 'Docker' },
            { name: 'REST APIs', confidence: 0.85, raw: 'REST APIs' },
            { name: 'Git', confidence: 0.92, raw: 'Git' },
            { name: 'SQL', confidence: 0.89, raw: 'SQL' },
            { name: 'Machine Learning', confidence: 0.78, raw: 'ML project' },
            { name: 'Java', confidence: 0.65, raw: 'JavaScript' },
            { name: 'Kubernetes', confidence: 0.72, raw: 'k8s' },
          ],
        },
      });
    }
    const form = new FormData();
    form.append('file', fileObj);
    return api.post('/resume/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  updateConsent: (idOrConsent, consent) => {
    const payload = consent !== undefined ? consent : idOrConsent;
    return api.patch('/students/me/consent', payload);
  },
};

// ─── Resume & NLP ────────────────────────────────────────────────
export const resumeApi = {
  upload: (file) => {
    if (USE_MOCKS) {
      return Promise.resolve({
        data: {
          message: 'Resume uploaded. Review and confirm extracted skills.',
          status: 'processing',
          extracted_skills: [
            { name: 'Python', confidence: 0.95, raw: 'Python' },
            { name: 'React', confidence: 0.92, raw: 'React' },
            { name: 'FastAPI', confidence: 0.90, raw: 'FastAPI' },
            { name: 'PostgreSQL', confidence: 0.88, raw: 'PostgreSQL' },
            { name: 'Docker', confidence: 0.86, raw: 'Docker' },
            { name: 'REST APIs', confidence: 0.85, raw: 'REST APIs' },
            { name: 'Git', confidence: 0.92, raw: 'Git' },
            { name: 'SQL', confidence: 0.89, raw: 'SQL' },
            { name: 'Machine Learning', confidence: 0.78, raw: 'ML project' },
            { name: 'Java', confidence: 0.65, raw: 'JavaScript' },
            { name: 'Kubernetes', confidence: 0.72, raw: 'k8s' },
          ],
        },
      });
    }
    const form = new FormData();
    form.append('file', file);
    return api.post('/resume/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getStatus: () => api.get('/resume/status'),
  reparse: () => api.post('/resume/reparse'),
};


// ─── Matching & Intelligence ──────────────────────────────────────
export const intelligenceApi = {
  getMatches: (studentId, params) =>
    mockOr('job_matches.json', () => api.get(`/matching/students/${studentId}/jobs`, { params })),
  getMyMatches: (params) => api.get('/matching/me', { params }),
  getSkillGap: (studentId, targetRole) =>
    mockOr('skill_gap.json', () => api.get(`/matching/students/${studentId}/gap`, { params: { target_role: targetRole } })),
  getMySkillGap: (targetRole) =>
    api.get('/gaps/me', { params: { target_role: targetRole } }),
  getRoadmap: (studentId) =>
    mockOr('roadmap.json', () => studentId ? api.get(`/roadmap/students/${studentId}`) : api.get('/roadmap/me')),
  generateRoadmap: (roleOrId, targetRole) =>
    targetRole
      ? api.post(`/roadmap/students/${roleOrId}/generate`, { target_role: targetRole })
      : api.post('/roadmap/me/generate', { target_role: roleOrId }),
  updateTask: (taskId, status) =>
    api.patch(`/roadmap/tasks/${taskId}`, { status }),
  injectRemedialTask: (payload) =>
    api.post('/roadmap/me/tasks', payload),
};

export const roadmapApi = intelligenceApi;

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
  getAllApplicants: (driveId) => api.get(`/drives/${driveId}/applicants`),
  updateApplicationStage: (driveId, appId, data) => api.patch(`/drives/${driveId}/applications/${appId}`, data),
  recordOffer: (driveId, appId, data) => api.post(`/drives/${driveId}/applications/${appId}/offer`, data),
  postAnnouncement: (driveId, data) => api.post(`/drives/${driveId}/announcements`, data),
  getAnnouncements: (driveId) => api.get(`/drives/${driveId}/announcements`),
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
  getDeptPlacement: () =>
    mockOr('dept_placement.json', () => api.get('/analytics/placement/departments')),
  getTopRecruiters: (params) =>
    mockOr('top_recruiters.json', () => api.get('/analytics/top-recruiters', { params })),
  getPlacementTrends: (params) =>
    mockOr('placement_trends.json', () => api.get('/analytics/trends', { params })),
  getPackageDistribution: () =>
    mockOr('package_dist.json', () => api.get('/analytics/package-distribution')),
  getYoYStats: () =>
    mockOr('yoy_stats.json', () => api.get('/analytics/yoy')),
  getSectorDistribution: () =>
    mockOr('sector_dist.json', () => api.get('/analytics/sectors')),
  getSkillTrends: () => api.get('/analytics/skills/trends'),
  // ─── Accreditation ──────────────────────────────────────────────
  getAccreditationPreview: (year = '2026-27') =>
    api.get('/analytics/accreditation/preview', { params: { academic_year: year } }),
  getAccreditationReport: (year = '2026-27') =>
    api.get('/analytics/accreditation/report', { params: { academic_year: year, format: 'json' } }),
  downloadAccreditationCSV: (year = '2026-27') =>
    api.get('/analytics/accreditation/report', {
      params: { academic_year: year, format: 'csv' },
      responseType: 'blob',
    }),
};

// ─── BI Studio (Superset + Power BI) ──────────────────────────────────────
export const biApi = {
  // Superset integration
  getEmbedToken: (dashboardId) =>
    api.get('/bi/embed-token', { params: { dashboard_id: dashboardId } }),
  getDashboards: () => api.get('/bi/dashboards'),
  getConfig: () => api.get('/bi/config'),

  // Data export
  exportData: (entity, format = 'csv') =>
    api.get(`/bi/export/${entity}`, { params: { format }, responseType: 'blob' }),

  // Entity counts
  getCounts: () => api.get('/bi/counts'),
};



// ─── Curriculum ───────────────────────────────────────────────────
export const curriculumApi = {
  getSubjects: (dept, semester) =>
    mockOr('subjects.json', () => api.get('/curriculum/subjects', { params: { dept, semester } })),
  getSubjectSkills: (subjectId) =>
    api.get(`/curriculum/subjects/${subjectId}/skills`),
  suggestSkillMappings: (subjectId, skillName = null) => {
    const payload = skillName ? { skill_name: skillName } : {};
    return api.post(`/curriculum/subjects/${subjectId}/suggest-mappings`, payload);
  },
  generateBoSProposal: (subjectId) => 
    api.post(`/curriculum/subjects/${subjectId}/generate-proposal`),
};

// ─── AI Career Copilot ────────────────────────────────────────────
export const copilotApi = {
  getConversations: () => api.get('/copilot/conversations'),
  createConversation: (title, initialMessage) =>
    api.post('/copilot/conversations', { title: title || undefined, initial_message: initialMessage || undefined }),
  sendMessage: (convId, message) =>
    api.post(`/copilot/conversations/${convId}/messages`, { content: message }),
  getHistory: (convId) => api.get(`/copilot/conversations/${convId}`),
  startMockInterview: (payload) => api.post('/copilot/mock-interview/start', payload),
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
  // Cohort Builder & Recruiter Search
  queryStudents: (query, params) => api.post('/tpo/cohorts/query', query, { params }),
  saveCohort: (data) => api.post('/tpo/cohorts', data),
  getCohorts: () => api.get('/tpo/cohorts'),
  exportCohortCSV: (cohortId) => api.get(`/tpo/cohorts/${cohortId}/export`, { responseType: 'blob' }),
  inviteCohortToDrive: (cohortId, driveId) =>
    api.post(`/tpo/cohorts/${cohortId}/invite-to-drive`, null, { params: { drive_id: driveId } }),
  archiveCohort: (cohortId) => api.delete(`/tpo/cohorts/${cohortId}`),
};


// ─── Assessments ──────────────────────────────────────────────────
export const assessmentsApi = {
  getSkills: () => api.get('/assessments/skills'),
  start: (topic, difficulty) => api.post('/assessments/start', { topic, difficulty }),
  submit: (sessionId, answers) => api.post(`/assessments/${sessionId}/submit`, { answers }),
  getHistory: () => api.get('/assessments/history'),
};

// ─── System & Audit ───────────────────────────────────────────────
export const systemApi = {
  getAuditLogs: (params) => api.get('/system/audit-logs', { params }),
};

// ─── Interview Experiences & Questions ─────────────────────────────
export const experiencesApi = {
  getExperiences: (params) => mockOr('experiences.json', () => api.get('/experiences', { params })),
  submitExperience: (data) => api.post('/experiences', data),
  upvoteExperience: (id) => api.post(`/experiences/${id}/upvote`),
};

// ─── In-App Notifications ─────────────────────────────────────────
export const notificationsApi = {
  getMine: (params) => mockOr('notifications.json', () => api.get('/notifications/mine', { params })),
  markRead: (id) => api.patch(`/notifications/${id}/read`),
  markAllRead: () => api.patch('/notifications/read-all'),
};

