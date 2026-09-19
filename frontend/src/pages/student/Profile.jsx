/**
 * Student Profile — tabs: Overview | Academic | Skills | Resume
 * Connected to live FastAPI backend endpoints via studentApi, resumeApi, and skillsApi.
 */

import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts';
import { useAuth } from '../../context/AuthContext';
import { studentApi, resumeApi, skillsApi } from '../../api/endpoints';

// ─── Color Palettes & Helpers ─────────────────────────────────────
const GRADE_COLORS = {
  'S': '#22c55e',
  'A+': '#22c55e',
  'A': '#6366f1',
  'B+': '#3b82f6',
  'B': '#f59e0b',
  'C+': '#f97316',
  'C': '#f97316',
  'D': '#eab308',
  'F': '#ef4444',
};

const GRADE_POINTS = {
  'S': 10,
  'A+': 10,
  'A': 9,
  'B+': 8,
  'B': 7,
  'C+': 6,
  'C': 5,
  'D': 4,
  'F': 0,
};

const TABS = ['Overview', 'Academic', 'Skills', 'Resume'];

function formatDate(dStr) {
  if (!dStr) return '';
  try {
    const d = new Date(dStr);
    if (isNaN(d.getTime())) return dStr;
    return d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  } catch {
    return dStr;
  }
}

function formatDateRange(startDate, endDate, isOngoing = false) {
  if (!startDate) return isOngoing ? 'Present' : '';
  const start = formatDate(startDate);
  if (isOngoing || !endDate) return `${start} – Present`;
  const end = formatDate(endDate);
  return `${start} – ${end}`;
}

// ─── Custom Recharts Tooltip ──────────────────────────────────────
function CGPATooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        borderRadius: 8,
        padding: 'var(--space-3) var(--space-4)',
        boxShadow: 'var(--shadow-md)',
      }}
    >
      <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{label}</div>
      <div style={{ color: '#6366f1', fontSize: 'var(--font-size-sm)' }}>
        CGPA: {payload[0]?.value}
      </div>
      {payload[0]?.payload?.sgpa !== undefined && (
        <div style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-xs)', marginTop: 2 }}>
          Semester GPA: {payload[0].payload.sgpa}
        </div>
      )}
    </div>
  );
}

// ─── Main Student Profile Component ──────────────────────────────
export default function StudentProfile() {
  const { user } = useAuth();

  // Core data states
  const [profile, setProfile] = useState(null);
  const [skills, setSkills] = useState([]);
  const [academicRecords, setAcademicRecords] = useState([]);
  const [resumeStatus, setResumeStatus] = useState(null);

  // Portfolio states (Projects, Certifications, Experience)
  const [projects, setProjects] = useState([]);
  const [certifications, setCertifications] = useState([]);
  const [experience, setExperience] = useState([]);

  // UI & Loading states
  const [tab, setTab] = useState('Overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  // Consent saving state
  const [consentSaving, setConsentSaving] = useState(false);

  // Edit Profile Modal states
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editForm, setEditForm] = useState({
    phone: '',
    bio: '',
    linkedin_url: '',
    github_url: '',
    portfolio_url: '',
  });
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState('');

  // Add Project Modal states
  const [addProjectModalOpen, setAddProjectModalOpen] = useState(false);
  const [projectForm, setProjectForm] = useState({
    title: '',
    description: '',
    tech_stack: [],
    tech_input: '',
    github_url: '',
    live_url: '',
    start_date: '',
    end_date: '',
    is_ongoing: false,
    is_featured: false,
  });
  const [projectSaving, setProjectSaving] = useState(false);
  const [projectErrors, setProjectErrors] = useState({});

  // Add Certification Modal states
  const [addCertModalOpen, setAddCertModalOpen] = useState(false);
  const [certForm, setCertForm] = useState({
    name: '',
    issuing_organization: '',
    issue_date: '',
    expiration_date: '',
    credential_id: '',
    credential_url: '',
  });
  const [certSaving, setCertSaving] = useState(false);
  const [certErrors, setCertErrors] = useState({});

  // Add Work Experience Modal states
  const [addExpModalOpen, setAddExpModalOpen] = useState(false);
  const [expForm, setExpForm] = useState({
    company_name: '',
    role: '',
    location: '',
    employment_type: 'Internship',
    start_date: '',
    end_date: '',
    is_current: false,
    description: '',
    skills_used: [],
    skill_input: '',
  });
  const [expSaving, setExpSaving] = useState(false);
  const [expErrors, setExpErrors] = useState({});

  // Delete Confirmation Modal state
  const [deleteConfirmModal, setDeleteConfirmModal] = useState({
    isOpen: false,
    type: null,
    id: null,
    title: '',
    deleting: false,
  });

  // Highlight effect for newly added items
  const [justAddedId, setJustAddedId] = useState(null);

  // Add Skill Modal states
  const [addSkillModalOpen, setAddSkillModalOpen] = useState(false);
  const [selectedSkillId, setSelectedSkillId] = useState(null);
  const [skillName, setSkillName] = useState('');
  const [skillCategory, setSkillCategory] = useState('tool');
  const [skillConfidence, setSkillConfidence] = useState(0.75);
  const [skillProficiency, setSkillProficiency] = useState('intermediate');
  const [skillSuggestions, setSkillSuggestions] = useState([]);
  const [searchingSkills, setSearchingSkills] = useState(false);
  const [addSkillSaving, setAddSkillSaving] = useState(false);
  const [addSkillError, setAddSkillError] = useState('');

  // Delete skill loading ID
  const [deletingSkillId, setDeletingSkillId] = useState(null);

  // Resume Upload & Polling states
  const [resumeFile, setResumeFile] = useState(null);
  const [uploadingResume, setUploadingResume] = useState(false);
  const [resumePolling, setResumePolling] = useState(false);
  const [resumeError, setResumeError] = useState('');
  const fileRef = useRef(null);
  const pollTimerRef = useRef(null);

  // Review Extracted Resume Skills Modal states (Task 2)
  const [reviewSkillsModalOpen, setReviewSkillsModalOpen] = useState(false);
  const [extractedSkills, setExtractedSkills] = useState([]);
  const [selectedSkills, setSelectedSkills] = useState(new Set());
  const [missedSkillInput, setMissedSkillInput] = useState('');
  const [missedSkillSuggestions, setMissedSkillSuggestions] = useState([]);
  const [searchingMissedSkill, setSearchingMissedSkill] = useState(false);
  const [confirmingSkills, setConfirmingSkills] = useState(false);
  const [confirmSkillsError, setConfirmSkillsError] = useState('');

  // Share Public Portfolio states (Task 3)
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [shareCopied, setShareCopied] = useState(false);

  // Toast Helper
  const showToast = useCallback((msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  }, []);

  // ─── Fetch All Profile Data ──────────────────────────────────────
  const loadData = useCallback(async (isInitial = false) => {
    try {
      if (isInitial) setLoading(true);

      const [profileRes, skillsRes, recordsRes, resumeRes, projectsRes, certsRes, expRes] = await Promise.all([
        studentApi.getMyProfile(),
        studentApi.getMySkills(),
        studentApi.getMyAcademicRecords(),
        resumeApi.getStatus().catch(() => ({ data: null })),
        studentApi.getMyProjects().catch(() => ({ data: [] })),
        studentApi.getMyCertifications().catch(() => ({ data: [] })),
        studentApi.getMyExperience().catch(() => ({ data: [] })),
      ]);

      const profData = profileRes.data;
      setProfile(profData);
      setSkills(Array.isArray(skillsRes.data) ? skillsRes.data : []);
      setAcademicRecords(Array.isArray(recordsRes.data) ? recordsRes.data : []);
      setProjects(Array.isArray(projectsRes?.data) ? projectsRes.data : []);
      setCertifications(Array.isArray(certsRes?.data) ? certsRes.data : []);
      setExperience(Array.isArray(expRes?.data) ? expRes.data : []);

      if (resumeRes?.data) {
        setResumeStatus(resumeRes.data);
      }


      setEditForm({
        phone: profData?.phone || '',
        bio: profData?.bio || '',
        linkedin_url: profData?.linkedin_url || '',
        github_url: profData?.github_url || '',
        portfolio_url: profData?.portfolio_url || '',
      });

      setError(null);
    } catch (err) {
      console.error('Failed to load profile data:', err);
      setError(err.response?.data?.detail || 'Failed to load profile. Please verify your connection.');
    } finally {
      if (isInitial) setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user?.id) {
      loadData(true);
    }
  }, [user, loadData]);

  // Clean up any resume polling timer on unmount
  useEffect(() => {
    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, []);

  // ─── Dynamic CGPA Trend Computation ──────────────────────────────
  const cgpaTrend = useMemo(() => {
    if (!academicRecords || academicRecords.length === 0) {
      if (profile?.cgpa) {
        return [{ sem: `Sem ${profile.current_semester || 1}`, cgpa: Number(profile.cgpa), sgpa: Number(profile.cgpa) }];
      }
      return [];
    }

    // Group records by semester_number
    const semMap = {};
    academicRecords.forEach((rec) => {
      const semNum = rec.subject?.semester_number || 1;
      if (!semMap[semNum]) semMap[semNum] = [];
      semMap[semNum].push(rec);
    });

    const sortedSemesters = Object.keys(semMap).map(Number).sort((a, b) => a - b);
    let totalWeightedPoints = 0;
    let totalCredits = 0;

    return sortedSemesters.map((semNum) => {
      const recs = semMap[semNum];
      let semCredits = 0;
      let semPoints = 0;

      recs.forEach((r) => {
        const credits = r.subject?.credits || 3;
        const gradePt = r.grade_points !== null && r.grade_points !== undefined
          ? Number(r.grade_points)
          : (GRADE_POINTS[r.grade] !== undefined ? GRADE_POINTS[r.grade] : 7.0);

        semCredits += credits;
        semPoints += gradePt * credits;
      });

      totalCredits += semCredits;
      totalWeightedPoints += semPoints;

      const sgpa = semCredits > 0 ? Number((semPoints / semCredits).toFixed(2)) : 0;
      const runningCgpa = totalCredits > 0 ? Number((totalWeightedPoints / totalCredits).toFixed(2)) : sgpa;

      return {
        sem: `Sem ${semNum}`,
        sgpa,
        cgpa: runningCgpa,
      };
    });
  }, [academicRecords, profile]);

  // ─── Save Edit Profile ───────────────────────────────────────────
  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setEditSaving(true);
    setEditError('');

    try {
      const res = await studentApi.updateMyProfile(editForm);
      setProfile(res.data);
      setEditModalOpen(false);
      showToast('Profile updated successfully!');
    } catch (err) {
      setEditError(err.response?.data?.detail || 'Failed to update profile.');
    } finally {
      setEditSaving(false);
    }
  };

  // ─── Data Consent Toggles ─────────────────────────────────────────
  const handleConsentChange = async (field, value) => {
    setConsentSaving(true);
    // Optimistic local state update
    setProfile((prev) => (prev ? { ...prev, [field]: value } : prev));

    try {
      await studentApi.updateMyConsent({ [field]: value });
      showToast('Consent preference saved');
    } catch (err) {
      // Revert on error
      setProfile((prev) => (prev ? { ...prev, [field]: !value } : prev));
      showToast(err.response?.data?.detail || 'Failed to update consent', 'error');
    } finally {
      setConsentSaving(false);
    }
  };

  // ─── Portfolio: Add & Delete Handlers ─────────────────────────────

  // Projects Tag Helper
  const handleAddProjectTag = () => {
    const tag = (projectForm.tech_input || '').trim().replace(/,/g, '');
    if (tag && !projectForm.tech_stack.includes(tag)) {
      setProjectForm((prev) => ({
        ...prev,
        tech_stack: [...prev.tech_stack, tag],
        tech_input: '',
      }));
      setProjectErrors((prev) => ({ ...prev, tech_stack: null }));
    }
  };

  const handleRemoveProjectTag = (tagToRemove) => {
    setProjectForm((prev) => ({
      ...prev,
      tech_stack: prev.tech_stack.filter((t) => t !== tagToRemove),
    }));
  };

  const handleAddProjectSubmit = async (e) => {
    e.preventDefault();
    const errs = {};
    if (!projectForm.title || projectForm.title.trim().length < 3) {
      errs.title = 'Title must be at least 3 characters.';
    }
    if (!projectForm.description || projectForm.description.trim().length < 10) {
      errs.description = 'Description must be at least 10 characters.';
    }
    if (!projectForm.tech_stack || projectForm.tech_stack.length === 0) {
      errs.tech_stack = 'Please add at least one technology (press Enter or comma).';
    }
    if (projectForm.github_url && !/^https:\/\/github\.com\/.+/.test(projectForm.github_url.trim())) {
      errs.github_url = 'Must be a valid GitHub URL starting with https://github.com/...';
    }
    if (Object.keys(errs).length > 0) {
      setProjectErrors(errs);
      return;
    }
    setProjectErrors({});
    setProjectSaving(true);
    try {
      const payload = {
        title: projectForm.title.trim(),
        description: projectForm.description.trim(),
        tech_stack: projectForm.tech_stack,
        github_url: projectForm.github_url.trim() || null,
        live_url: projectForm.live_url.trim() || null,
        start_date: projectForm.start_date || null,
        end_date: projectForm.is_ongoing ? null : (projectForm.end_date || null),
        is_featured: Boolean(projectForm.is_featured),
      };
      const res = await studentApi.addProject(payload);
      const newProj = res.data;
      setProjects((prev) => [newProj, ...prev]);
      setAddProjectModalOpen(false);
      setProjectForm({
        title: '',
        description: '',
        tech_stack: [],
        tech_input: '',
        github_url: '',
        live_url: '',
        start_date: '',
        end_date: '',
        is_ongoing: false,
        is_featured: false,
      });
      setJustAddedId(newProj.id);
      setTimeout(() => setJustAddedId(null), 3000);
      showToast('Project added successfully!');
    } catch (err) {
      console.error('Failed to add project:', err);
      setProjectErrors({ general: err.response?.data?.detail || 'Failed to save project. Please try again.' });
    } finally {
      setProjectSaving(false);
    }
  };

  // Certifications
  const handleAddCertSubmit = async (e) => {
    e.preventDefault();
    const errs = {};
    if (!certForm.name || certForm.name.trim().length < 3) {
      errs.name = 'Certification name must be at least 3 characters.';
    }
    if (!certForm.issuing_organization || certForm.issuing_organization.trim().length < 2) {
      errs.issuing_organization = 'Issuing organization must be at least 2 characters.';
    }
    if (!certForm.issue_date) {
      errs.issue_date = 'Issue date is required.';
    }
    if (Object.keys(errs).length > 0) {
      setCertErrors(errs);
      return;
    }
    setCertErrors({});
    setCertSaving(true);
    try {
      const payload = {
        name: certForm.name.trim(),
        issuing_organization: certForm.issuing_organization.trim(),
        issue_date: certForm.issue_date,
        expiration_date: certForm.expiration_date || null,
        credential_id: certForm.credential_id.trim() || null,
        credential_url: certForm.credential_url.trim() || null,
      };
      const res = await studentApi.addCertification(payload);
      const newCert = res.data;
      setCertifications((prev) => [newCert, ...prev]);
      setAddCertModalOpen(false);
      setCertForm({
        name: '',
        issuing_organization: '',
        issue_date: '',
        expiration_date: '',
        credential_id: '',
        credential_url: '',
      });
      setJustAddedId(newCert.id);
      setTimeout(() => setJustAddedId(null), 3000);
      showToast('Certification added successfully!');
    } catch (err) {
      console.error('Failed to add certification:', err);
      setCertErrors({ general: err.response?.data?.detail || 'Failed to save certification. Please try again.' });
    } finally {
      setCertSaving(false);
    }
  };

  // Work Experience Tag Helper
  const handleAddExpSkill = () => {
    const skill = (expForm.skill_input || '').trim().replace(/,/g, '');
    if (skill && !expForm.skills_used.includes(skill)) {
      setExpForm((prev) => ({
        ...prev,
        skills_used: [...prev.skills_used, skill],
        skill_input: '',
      }));
    }
  };

  const handleRemoveExpSkill = (skillToRemove) => {
    setExpForm((prev) => ({
      ...prev,
      skills_used: prev.skills_used.filter((s) => s !== skillToRemove),
    }));
  };

  const handleAddExpSubmit = async (e) => {
    e.preventDefault();
    const errs = {};
    if (!expForm.company_name || expForm.company_name.trim().length < 2) {
      errs.company_name = 'Company name must be at least 2 characters.';
    }
    if (!expForm.role || expForm.role.trim().length < 2) {
      errs.role = 'Role must be at least 2 characters.';
    }
    if (!expForm.start_date) {
      errs.start_date = 'Start date is required.';
    }
    if (Object.keys(errs).length > 0) {
      setExpErrors(errs);
      return;
    }
    setExpErrors({});
    setExpSaving(true);
    try {
      const payload = {
        company_name: expForm.company_name.trim(),
        role: expForm.role.trim(),
        location: expForm.location.trim() || null,
        employment_type: expForm.employment_type || 'Internship',
        start_date: expForm.start_date,
        end_date: expForm.is_current ? null : (expForm.end_date || null),
        is_current: Boolean(expForm.is_current),
        description: expForm.description.trim() || null,
        skills_used: expForm.skills_used || [],
      };
      const res = await studentApi.addExperience(payload);
      const newExp = res.data;
      setExperience((prev) => [newExp, ...prev]);
      setAddExpModalOpen(false);
      setExpForm({
        company_name: '',
        role: '',
        location: '',
        employment_type: 'Internship',
        start_date: '',
        end_date: '',
        is_current: false,
        description: '',
        skills_used: [],
        skill_input: '',
      });
      setJustAddedId(newExp.id);
      setTimeout(() => setJustAddedId(null), 3000);
      showToast('Work experience added successfully!');
    } catch (err) {
      console.error('Failed to add work experience:', err);
      setExpErrors({ general: err.response?.data?.detail || 'Failed to save experience. Please try again.' });
    } finally {
      setExpSaving(false);
    }
  };

  // Delete Item Confirmed
  const handleConfirmDelete = async () => {
    const { type, id } = deleteConfirmModal;
    if (!type || !id) return;
    setDeleteConfirmModal((prev) => ({ ...prev, deleting: true }));
    try {
      if (type === 'project') {
        await studentApi.deleteProject(id);
        setProjects((prev) => prev.filter((p) => p.id !== id));
        showToast('Project deleted successfully.');
      } else if (type === 'certification') {
        await studentApi.deleteCertification(id);
        setCertifications((prev) => prev.filter((c) => c.id !== id));
        showToast('Certification deleted successfully.');
      } else if (type === 'experience') {
        await studentApi.deleteExperience(id);
        setExperience((prev) => prev.filter((e) => e.id !== id));
        showToast('Work experience deleted successfully.');
      }
      setDeleteConfirmModal({ isOpen: false, type: null, id: null, title: '', deleting: false });
    } catch (err) {
      console.error(`Failed to delete ${type}:`, err);
      showToast(err.response?.data?.detail || `Failed to delete ${type}.`, 'error');
      setDeleteConfirmModal((prev) => ({ ...prev, deleting: false }));
    }
  };

  // ─── Live Taxonomy Search for Add Skill ───────────────────────────
  useEffect(() => {
    if (!skillName || skillName.trim().length < 2) {
      setSkillSuggestions([]);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setSearchingSkills(true);
        const res = await skillsApi.search(skillName.trim());
        setSkillSuggestions(res.data || []);
      } catch {
        setSkillSuggestions([]);
      } finally {
        setSearchingSkills(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [skillName]);

  // ─── Add Skill Submission ─────────────────────────────────────────
  const handleAddSkill = async (e) => {
    e.preventDefault();
    if (!skillName.trim()) {
      setAddSkillError('Please enter a skill name.');
      return;
    }

    setAddSkillSaving(true);
    setAddSkillError('');

    try {
      const res = await studentApi.addMySkill({
        skill_id: selectedSkillId,
        skill_name: skillName.trim(),
        category: skillCategory,
        confidence: Number(skillConfidence),
        proficiency_level: skillProficiency,
      });

      // Refresh skills list directly from backend
      const skillsRes = await studentApi.getMySkills();
      setSkills(Array.isArray(skillsRes.data) ? skillsRes.data : []);

      setAddSkillModalOpen(false);
      setSkillName('');
      setSelectedSkillId(null);
      setSkillSuggestions([]);
      showToast(`Skill "${res.data.skill?.name || skillName}" added to your profile!`);
    } catch (err) {
      setAddSkillError(err.response?.data?.detail || 'Failed to add skill.');
    } finally {
      setAddSkillSaving(false);
    }
  };

  // ─── Delete Skill ─────────────────────────────────────────────────
  const handleDeleteSkill = async (skillId, skillDisplayName) => {
    if (!window.confirm(`Are you sure you want to remove "${skillDisplayName}" from your profile?`)) {
      return;
    }

    setDeletingSkillId(skillId);
    try {
      await studentApi.deleteMySkill(skillId);
      setSkills((prev) =>
        prev.filter((s) => s.id !== skillId && s.skill?.id !== skillId && s.skill_id !== skillId && (s.skill?.name || s.name) !== skillDisplayName)
      );
      showToast(`Removed "${skillDisplayName}"`);
      // Background re-fetch to ensure exact sync with database
      try {
        const fresh = await studentApi.getMySkills();
        if (Array.isArray(fresh.data)) {
          setSkills(fresh.data);
        }
      } catch (refreshErr) {
        console.warn('Background skills reload warning:', refreshErr);
      }
    } catch (err) {
      console.error('Delete skill error:', err);
      showToast(err.response?.data?.detail || 'Failed to remove skill', 'error');
    } finally {
      setDeletingSkillId(null);
    }
  };

  // ─── Search taxonomy for missed skills in review modal ─────────────
  useEffect(() => {
    if (!missedSkillInput || missedSkillInput.trim().length < 2) {
      setMissedSkillSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      setSearchingMissedSkill(true);
      try {
        const res = await skillsApi.search(missedSkillInput.trim());
        setMissedSkillSuggestions(res.data || []);
      } catch {
        setMissedSkillSuggestions([]);
      } finally {
        setSearchingMissedSkill(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [missedSkillInput]);

  const openReviewSkillsModal = (rawSkills) => {
    if (!rawSkills || !Array.isArray(rawSkills) || rawSkills.length === 0) return;

    const normalized = rawSkills.map((s) => {
      const name = s.name || s.matched_to || s.skill?.name || (typeof s === 'string' ? s : 'Unknown');
      let conf = s.confidence !== undefined ? Number(s.confidence) : 0.85;
      if (conf > 1.0) conf = conf / 100.0;
      return {
        name,
        confidence: Math.min(1.0, Math.max(0.0, conf)),
        raw: s.raw || s.evidence_text || name,
      };
    });

    // High confidence (>=0.85) pre-checked
    // Probable match (0.60–0.84) also pre-checked per prompt spec
    const preSelected = new Set(
      normalized
        .filter((s) => s.confidence >= 0.60)
        .map((s) => s.name)
    );

    setExtractedSkills(normalized);
    setSelectedSkills(preSelected);
    setConfirmSkillsError('');
    setReviewSkillsModalOpen(true);
  };

  const handleToggleSkillSelection = (skillName) => {
    setSelectedSkills((prev) => {
      const next = new Set(prev);
      if (next.has(skillName)) {
        next.delete(skillName);
      } else {
        next.add(skillName);
      }
      return next;
    });
  };

  const handleAddMissedSkill = (skillNameToAdd) => {
    const name = (skillNameToAdd || missedSkillInput).trim();
    if (!name) return;

    setExtractedSkills((prev) => {
      if (prev.some((s) => s.name.toLowerCase() === name.toLowerCase())) {
        return prev;
      }
      return [
        ...prev,
        {
          name,
          confidence: 1.0,
          raw: 'Manually added',
        },
      ];
    });

    setSelectedSkills((prev) => {
      const next = new Set(prev);
      next.add(name);
      return next;
    });

    setMissedSkillInput('');
    setMissedSkillSuggestions([]);
  };

  const handleConfirmAndSyncSkills = async () => {
    if (selectedSkills.size === 0) {
      setConfirmSkillsError('Please select at least one skill to confirm.');
      return;
    }

    setConfirmingSkills(true);
    setConfirmSkillsError('');

    try {
      const skillsArray = Array.from(selectedSkills);
      await studentApi.bulkConfirmSkills({
        skills: skillsArray,
        source: 'resume_verified',
      });

      showToast(`✓ ${skillsArray.length} skills confirmed & synced to your profile!`);
      setReviewSkillsModalOpen(false);

      // Refresh data and switch to Skills tab
      await loadData(false);
      setTab('Skills');
    } catch (err) {
      setConfirmSkillsError(err.response?.data?.detail || 'Failed to confirm skills. Please try again.');
    } finally {
      setConfirmingSkills(false);
    }
  };

  const handleSharePortfolio = () => {
    const studentId = profile?.id || user?.id;
    if (!studentId) return;
    const url = `${window.location.origin}/portfolio/${studentId}`;
    try {
      navigator.clipboard.writeText(url);
      setShareCopied(true);
      showToast('Link copied! ✓');
      setTimeout(() => setShareCopied(false), 2000);
    } catch {
      // Fallback
    }
    setShareModalOpen(true);
  };

  // ─── Resume Upload & Status Polling ──────────────────────────────
  const handleUploadResume = async () => {
    if (!resumeFile) return;

    setUploadingResume(true);
    setResumeError('');

    try {
      const res = await studentApi.uploadResume(resumeFile);

      // Check if backend returned extracted_skills directly
      if (
        res?.data?.extracted_skills &&
        Array.isArray(res.data.extracted_skills) &&
        res.data.extracted_skills.length > 0
      ) {
        setUploadingResume(false);
        openReviewSkillsModal(res.data.extracted_skills);
        return;
      }

      showToast('Resume uploaded. Background NLP extraction started...');
      setResumePolling(true);

      // Start polling status
      let attempts = 0;
      pollTimerRef.current = setInterval(async () => {
        attempts += 1;
        try {
          const statusRes = await resumeApi.getStatus();
          setResumeStatus(statusRes.data);

          if (statusRes.data?.resume_parsed) {
            clearInterval(pollTimerRef.current);
            setResumePolling(false);
            setUploadingResume(false);

            if (
              statusRes.data?.extracted_skills &&
              Array.isArray(statusRes.data.extracted_skills) &&
              statusRes.data.extracted_skills.length > 0
            ) {
              openReviewSkillsModal(statusRes.data.extracted_skills);
            } else {
              showToast('Resume parsed successfully! Skills updated.');
              loadData(false);
            }
          } else if (attempts >= 15) {
            // Stop polling after 30 seconds
            clearInterval(pollTimerRef.current);
            setResumePolling(false);
            setUploadingResume(false);
            loadData(false);
          }
        } catch (pollErr) {
          console.warn('Status poll error:', pollErr);
        }
      }, 2000);
    } catch (err) {
      setResumeError(err.response?.data?.detail || 'Failed to upload resume. Ensure file is PDF or DOCX under 5MB.');
      setUploadingResume(false);
    }
  };

  // ─── Render: Loading & Error States ──────────────────────────────
  if (loading) {
    return (
      <div
        className="page-body"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
          gap: 'var(--space-4)',
          color: 'var(--text-secondary)',
        }}
      >
        <div style={{ fontSize: '2rem' }}>⏳</div>
        <div style={{ fontSize: 'var(--font-size-base)', fontWeight: 500 }}>Loading your student profile...</div>
      </div>
    );
  }

  if (error && !profile) {
    return (
      <div
        className="page-body"
        style={{
          padding: 'var(--space-10)',
          textAlign: 'center',
          color: 'var(--accent-danger)',
        }}
      >
        <div style={{ fontSize: '2.5rem', marginBottom: 'var(--space-3)' }}>⚠️</div>
        <h2 style={{ fontSize: 'var(--font-size-xl)', marginBottom: 'var(--space-2)' }}>Unable to Load Profile</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--space-6)' }}>{error}</p>
        <button className="btn btn-primary" onClick={() => loadData(true)}>
          🔄 Try Again
        </button>
      </div>
    );
  }

  // Fallbacks
  const displayFirstName = profile?.first_name || user?.first_name || 'Student';
  const displayLastName = profile?.last_name || user?.last_name || '';
  const displayDepartment = profile?.department?.name || profile?.department?.code || (typeof profile?.department === 'string' ? profile.department : 'Engineering');
  const displaySemester = profile?.current_semester || 1;
  const displayYear = Math.ceil(displaySemester / 2);
  const displayCgpa = profile?.cgpa !== null && profile?.cgpa !== undefined ? Number(profile.cgpa).toFixed(2) : '—';
  const displayRoll = profile?.roll_number || 'N/A';

  const resumeSkills = skills.filter((s) => s.source === 'resume');

  return (
    <div>
      {/* Toast Notification Banner */}
      {toast && (
        <div
          style={{
            position: 'fixed',
            top: 24,
            right: 24,
            zIndex: 1000,
            padding: '12px 20px',
            borderRadius: 'var(--border-radius)',
            background: toast.type === 'error' ? 'var(--accent-danger)' : 'var(--accent-success)',
            color: 'white',
            fontWeight: 600,
            fontSize: 'var(--font-size-sm)',
            boxShadow: 'var(--shadow-lg)',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <span>{toast.type === 'error' ? '❌' : '✅'}</span>
          <span>{toast.msg}</span>
        </div>
      )}

      {/* Page Header */}
      <div className="page-header">
        <h1>Student Profile</h1>
        <p>Manage your academic identity, verified competencies, and AI career credentials</p>
      </div>

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>

        {/* Profile Header Card */}
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-6)', flexWrap: 'wrap' }}>
          <div
            style={{
              width: 80,
              height: 80,
              borderRadius: '50%',
              background: 'var(--gradient-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 'var(--font-size-2xl)',
              fontWeight: 700,
              color: 'white',
              flexShrink: 0,
            }}
          >
            {displayFirstName[0]}
            {displayLastName[0] || ''}
          </div>

          <div style={{ flex: 1, minWidth: 260 }}>
            <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700 }}>
              {displayFirstName} {displayLastName}
            </h2>
            <div style={{ color: 'var(--text-secondary)', marginTop: 2 }}>
              {displayDepartment} · Year {displayYear} (Sem {displaySemester})
            </div>
            <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-3)', flexWrap: 'wrap' }}>
              <span className="badge badge-primary">🎓 {displayRoll}</span>
              <span className="badge badge-success">CGPA: {displayCgpa}</span>
              <span className="badge badge-warning">Year {displayYear}</span>
              {resumeStatus?.resume_parsed && (
                <span className="badge badge-info">📄 Resume Verified</span>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', flexShrink: 0 }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleSharePortfolio}
              style={{
                height: 38,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                borderColor: 'var(--accent-primary)',
                color: 'var(--accent-primary)',
                fontWeight: 600,
              }}
            >
              <span>🔗</span> Share Verified Portfolio
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                setEditForm({
                  phone: profile?.phone || '',
                  bio: profile?.bio || '',
                  linkedin_url: profile?.linkedin_url || '',
                  github_url: profile?.github_url || '',
                  portfolio_url: profile?.portfolio_url || '',
                });
                setEditModalOpen(true);
              }}
              style={{ height: 38, display: 'flex', alignItems: 'center', gap: 6 }}
            >
              <span>✏️</span> Edit Profile
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--border-color)' }}>
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              style={{
                padding: 'var(--space-3) var(--space-6)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: 'var(--font-size-sm)',
                fontWeight: 600,
                color: tab === t ? 'var(--accent-primary)' : 'var(--text-muted)',
                borderBottom: `2px solid ${tab === t ? 'var(--accent-primary)' : 'transparent'}`,
                marginBottom: -1,
                transition: 'all 0.15s',
              }}
            >
              {t}
              {t === 'Skills' && ` (${skills.length})`}
              {t === 'Academic' && ` (${academicRecords.length})`}
            </button>
          ))}
        </div>

        {/* ─── TAB 1: OVERVIEW ──────────────────────────────────── */}
        {tab === 'Overview' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 'var(--space-6)' }}>
            {/* Contact & Links Card */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div style={{ fontWeight: 600, fontSize: 'var(--font-size-base)' }}>Contact & Links</div>

              {[
                { icon: '✉️', label: 'Email', value: profile?.email || user?.email, isLink: false },
                { icon: '📱', label: 'Phone', value: profile?.phone, isLink: false },
                { icon: '💼', label: 'LinkedIn', value: profile?.linkedin_url, isLink: true },
                { icon: '🐙', label: 'GitHub', value: profile?.github_url, isLink: true },
                { icon: '🌐', label: 'Portfolio', value: profile?.portfolio_url, isLink: true },
              ].map((row) => (
                <div key={row.label} style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'flex-start' }}>
                  <span style={{ fontSize: '1.1rem', width: 24 }}>{row.icon}</span>
                  <div style={{ flex: 1, overflow: 'hidden' }}>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{row.label}</div>
                    {row.value ? (
                      row.isLink ? (
                        <a
                          href={row.value.startsWith('http') ? row.value : `https://${row.value}`}
                          target="_blank"
                          rel="noreferrer"
                          style={{
                            fontSize: 'var(--font-size-sm)',
                            color: 'var(--accent-primary)',
                            display: 'block',
                            textOverflow: 'ellipsis',
                            overflow: 'hidden',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {row.value}
                        </a>
                      ) : (
                        <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-primary)' }}>{row.value}</div>
                      )
                    ) : (
                      <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)' }}>— Not provided —</div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Bio & Data Privacy Card */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: 'var(--font-size-base)', marginBottom: 'var(--space-3)' }}>
                  Professional Bio
                </div>
                <p
                  style={{
                    fontSize: 'var(--font-size-sm)',
                    color: profile?.bio ? 'var(--text-secondary)' : 'var(--text-muted)',
                    lineHeight: 1.7,
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {profile?.bio || 'No bio provided yet. Click "Edit Profile" to introduce your technical interests and career aspirations.'}
                </p>
              </div>

              <div style={{ marginTop: 'var(--space-8)', borderTop: '1px solid var(--border-color)', paddingTop: 'var(--space-4)' }}>
                <div style={{ fontWeight: 600, marginBottom: 'var(--space-3)', fontSize: 'var(--font-size-sm)' }}>
                  Data Privacy & Consent Settings
                </div>

                {[
                  {
                    field: 'consent_resume_analysis',
                    label: 'Allow resume analysis & AI career recommendation',
                    checked: Boolean(profile?.consent_resume_analysis),
                  },
                  {
                    field: 'consent_profile_visible',
                    label: 'Make profile discoverable to verified campus recruiters',
                    checked: Boolean(profile?.consent_profile_visible),
                  },
                ].map((item) => (
                  <div
                    key={item.field}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: 'var(--space-3)',
                      gap: 'var(--space-3)',
                    }}
                  >
                    <label
                      htmlFor={item.field}
                      style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', cursor: 'pointer', flex: 1 }}
                    >
                      {item.label}
                    </label>

                    <label
                      style={{
                        position: 'relative',
                        display: 'inline-block',
                        width: 44,
                        height: 24,
                        flexShrink: 0,
                        cursor: consentSaving ? 'not-allowed' : 'pointer',
                      }}
                    >
                      <input
                        id={item.field}
                        type="checkbox"
                        checked={item.checked}
                        disabled={consentSaving}
                        onChange={(e) => handleConsentChange(item.field, e.target.checked)}
                        style={{ opacity: 0, width: 0, height: 0, position: 'absolute' }}
                      />
                      <span
                        style={{
                          position: 'absolute',
                          inset: 0,
                          background: item.checked ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                          borderRadius: 999,
                          transition: 'background 0.2s',
                        }}
                      >
                        <span
                          style={{
                            position: 'absolute',
                            top: 3,
                            left: item.checked ? 22 : 3,
                            width: 18,
                            height: 18,
                            borderRadius: '50%',
                            background: 'white',
                            transition: 'left 0.2s',
                            boxShadow: '0 1px 3px rgba(0,0,0,0.25)',
                          }}
                        />
                      </span>
                    </label>
                  </div>
                ))}
              </div>
            </div>

            {/* ─── Projects Section ─── */}
            <div className="card" style={{ gridColumn: '1 / -1' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
                <div>
                  <h3 style={{ fontSize: 'var(--font-size-base)', fontWeight: 600 }}>Projects</h3>
                  <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                    Personal and academic software projects showcasing technical craftsmanship
                  </p>
                </div>
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    setProjectErrors({});
                    setAddProjectModalOpen(true);
                  }}
                  style={{ height: 36, fontSize: 'var(--font-size-sm)', display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  <span>+</span> Add Project
                </button>
              </div>

              {projects.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 'var(--space-8) var(--space-4)', color: 'var(--text-muted)' }}>
                  <div style={{ fontSize: '2rem', marginBottom: 'var(--space-2)' }}>🚀</div>
                  <div style={{ fontWeight: 500 }}>No projects added yet</div>
                  <div style={{ fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
                    Showcase your work to campus recruiters by clicking "+ Add Project".
                  </div>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                  {projects.map((proj) => (
                    <div
                      key={proj.id}
                      style={{
                        padding: 'var(--space-4)',
                        borderRadius: 'var(--border-radius-sm)',
                        background: 'var(--bg-tertiary)',
                        border: justAddedId === proj.id ? '1px solid var(--accent-primary)' : '1px solid var(--border-color)',
                        transition: 'all 0.3s ease',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 'var(--space-3)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
                          <span style={{ fontWeight: 600, fontSize: 'var(--font-size-base)', color: 'var(--text-primary)' }}>
                            {proj.title}
                          </span>
                          {proj.is_featured && (
                            <span className="badge badge-warning" style={{ fontSize: '0.7rem' }}>
                              ⭐ Featured
                            </span>
                          )}
                        </div>
                        <button
                          className="btn-icon"
                          title="Delete Project"
                          onClick={() => setDeleteConfirmModal({
                            isOpen: true,
                            type: 'project',
                            id: proj.id,
                            title: proj.title,
                            deleting: false,
                          })}
                          style={{
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            color: 'var(--text-muted)',
                            padding: 4,
                            borderRadius: 4,
                            fontSize: '1rem',
                          }}
                          onMouseOver={(e) => (e.currentTarget.style.color = 'var(--accent-danger)')}
                          onMouseOut={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
                        >
                          🗑
                        </button>
                      </div>

                      {proj.description && (
                        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', marginTop: 6, lineHeight: 1.5 }}>
                          {proj.description}
                        </p>
                      )}

                      {proj.tech_stack && proj.tech_stack.length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
                          {proj.tech_stack.map((tech) => (
                            <span
                              key={tech}
                              style={{
                                fontSize: '0.75rem',
                                padding: '2px 8px',
                                borderRadius: 4,
                                background: 'rgba(99, 102, 241, 0.12)',
                                color: 'var(--accent-primary)',
                                fontWeight: 500,
                              }}
                            >
                              {tech}
                            </span>
                          ))}
                        </div>
                      )}

                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12, flexWrap: 'wrap', gap: 8, fontSize: 'var(--font-size-xs)' }}>
                        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                          {proj.github_url && (
                            <a
                              href={proj.github_url}
                              target="_blank"
                              rel="noreferrer"
                              style={{ color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', gap: 4 }}
                            >
                              <span>🐙</span> {proj.github_url.replace(/^https?:\/\//, '')}
                            </a>
                          )}
                          {proj.live_url && (
                            <a
                              href={proj.live_url.startsWith('http') ? proj.live_url : `https://${proj.live_url}`}
                              target="_blank"
                              rel="noreferrer"
                              style={{ color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', gap: 4 }}
                            >
                              <span>🔗</span> {proj.live_url.replace(/^https?:\/\//, '')}
                            </a>
                          )}
                        </div>
                        <div style={{ color: 'var(--text-muted)' }}>
                          {formatDateRange(proj.start_date, proj.end_date)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* ─── Certifications Section ─── */}
            <div className="card" style={{ gridColumn: '1 / -1' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
                <div>
                  <h3 style={{ fontSize: 'var(--font-size-base)', fontWeight: 600 }}>Certifications</h3>
                  <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                    Industry-recognized certifications and professional credentials
                  </p>
                </div>
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    setCertErrors({});
                    setAddCertModalOpen(true);
                  }}
                  style={{ height: 36, fontSize: 'var(--font-size-sm)', display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  <span>+</span> Add Certification
                </button>
              </div>

              {certifications.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 'var(--space-8) var(--space-4)', color: 'var(--text-muted)' }}>
                  <div style={{ fontSize: '2rem', marginBottom: 'var(--space-2)' }}>🏅</div>
                  <div style={{ fontWeight: 500 }}>No certifications added yet</div>
                  <div style={{ fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
                    Add credentials and verified certificates by clicking "+ Add Certification".
                  </div>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                  {certifications.map((cert) => (
                    <div
                      key={cert.id}
                      style={{
                        padding: 'var(--space-4)',
                        borderRadius: 'var(--border-radius-sm)',
                        background: 'var(--bg-tertiary)',
                        border: justAddedId === cert.id ? '1px solid var(--accent-primary)' : '1px solid var(--border-color)',
                        transition: 'all 0.3s ease',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 'var(--space-3)' }}>
                        <div>
                          <div style={{ fontWeight: 600, fontSize: 'var(--font-size-base)', color: 'var(--text-primary)' }}>
                            {cert.name || cert.title}
                          </div>
                          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginTop: 2 }}>
                            {cert.issuing_organization || cert.issuer}
                            {cert.issue_date && ` · Issued: ${formatDate(cert.issue_date)}`}
                          </div>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                          {cert.expiration_date ? (
                            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                              Expires: {formatDate(cert.expiration_date)}
                            </span>
                          ) : null}
                          <button
                            className="btn-icon"
                            title="Delete Certification"
                            onClick={() => setDeleteConfirmModal({
                              isOpen: true,
                              type: 'certification',
                              id: cert.id,
                              title: cert.name || cert.title,
                              deleting: false,
                            })}
                            style={{
                              background: 'none',
                              border: 'none',
                              cursor: 'pointer',
                              color: 'var(--text-muted)',
                              padding: 4,
                              borderRadius: 4,
                              fontSize: '1rem',
                            }}
                            onMouseOver={(e) => (e.currentTarget.style.color = 'var(--accent-danger)')}
                            onMouseOut={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
                          >
                            🗑
                          </button>
                        </div>
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 10, flexWrap: 'wrap', gap: 8, fontSize: 'var(--font-size-xs)' }}>
                        <div style={{ color: 'var(--text-muted)' }}>
                          {cert.credential_id && (
                            <span>Credential ID: <span style={{ fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{cert.credential_id}</span></span>
                          )}
                        </div>
                        {cert.credential_url && (
                          <a
                            href={cert.credential_url.startsWith('http') ? cert.credential_url : `https://${cert.credential_url}`}
                            target="_blank"
                            rel="noreferrer"
                            style={{ color: 'var(--accent-primary)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}
                          >
                            <span>🔗</span> Verify Credential
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* ─── Work Experience Section ─── */}
            <div className="card" style={{ gridColumn: '1 / -1' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
                <div>
                  <h3 style={{ fontSize: 'var(--font-size-base)', fontWeight: 600 }}>Work Experience</h3>
                  <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                    Internships, full-time positions, and relevant industrial engagements
                  </p>
                </div>
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    setExpErrors({});
                    setAddExpModalOpen(true);
                  }}
                  style={{ height: 36, fontSize: 'var(--font-size-sm)', display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  <span>+</span> Add Experience
                </button>
              </div>

              {experience.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 'var(--space-8) var(--space-4)', color: 'var(--text-muted)' }}>
                  <div style={{ fontSize: '2rem', marginBottom: 'var(--space-2)' }}>💼</div>
                  <div style={{ fontWeight: 500 }}>No work experience added yet</div>
                  <div style={{ fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
                    Highlight your industry experience by clicking "+ Add Experience".
                  </div>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                  {experience.map((exp) => (
                    <div
                      key={exp.id}
                      style={{
                        padding: 'var(--space-4)',
                        borderRadius: 'var(--border-radius-sm)',
                        background: 'var(--bg-tertiary)',
                        border: justAddedId === exp.id ? '1px solid var(--accent-primary)' : '1px solid var(--border-color)',
                        transition: 'all 0.3s ease',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 'var(--space-3)' }}>
                        <div>
                          <div style={{ fontWeight: 600, fontSize: 'var(--font-size-base)', color: 'var(--text-primary)' }}>
                            {exp.role}
                          </div>
                          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginTop: 2, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                            <span style={{ fontWeight: 500 }}>{exp.company_name}</span>
                            {exp.location && <span>· {exp.location}</span>}
                            <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>
                              {exp.employment_type || 'Internship'}
                            </span>
                          </div>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                            {formatDateRange(exp.start_date, exp.end_date, exp.is_current)}
                          </span>
                          <button
                            className="btn-icon"
                            title="Delete Experience"
                            onClick={() => setDeleteConfirmModal({
                              isOpen: true,
                              type: 'experience',
                              id: exp.id,
                              title: `${exp.role} at ${exp.company_name}`,
                              deleting: false,
                            })}
                            style={{
                              background: 'none',
                              border: 'none',
                              cursor: 'pointer',
                              color: 'var(--text-muted)',
                              padding: 4,
                              borderRadius: 4,
                              fontSize: '1rem',
                            }}
                            onMouseOver={(e) => (e.currentTarget.style.color = 'var(--accent-danger)')}
                            onMouseOut={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
                          >
                            🗑
                          </button>
                        </div>
                      </div>

                      {exp.skills_used && exp.skills_used.length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', alignSelf: 'center' }}>Skills:</span>
                          {exp.skills_used.map((sk) => (
                            <span
                              key={sk}
                              style={{
                                fontSize: '0.75rem',
                                padding: '2px 8px',
                                borderRadius: 4,
                                background: 'var(--bg-card)',
                                color: 'var(--text-secondary)',
                                border: '1px solid var(--border-color)',
                              }}
                            >
                              {sk}
                            </span>
                          ))}
                        </div>
                      )}

                      {exp.description && (
                        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', marginTop: 8, lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
                          {exp.description}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ─── TAB 2: ACADEMIC ──────────────────────────────────── */}
        {tab === 'Academic' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
            {/* Academic Summary KPI Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-4)' }}>
              <div className="card" style={{ padding: 'var(--space-4)' }}>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>Cumulative CGPA</div>
                <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--accent-primary)', marginTop: 4 }}>
                  {displayCgpa}
                </div>
              </div>
              <div className="card" style={{ padding: 'var(--space-4)' }}>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>Total Courses Recorded</div>
                <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
                  {academicRecords.length}
                </div>
              </div>
              <div className="card" style={{ padding: 'var(--space-4)' }}>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>Total Credits Earned</div>
                <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--accent-success)', marginTop: 4 }}>
                  {academicRecords.reduce((acc, r) => acc + (r.subject?.credits || 0), 0)}
                </div>
              </div>
              <div className="card" style={{ padding: 'var(--space-4)' }}>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>Active Backlogs</div>
                <div
                  style={{
                    fontSize: 'var(--font-size-2xl)',
                    fontWeight: 700,
                    color: academicRecords.filter((r) => r.status === 'failed').length > 0 ? 'var(--accent-danger)' : 'var(--accent-success)',
                    marginTop: 4,
                  }}
                >
                  {academicRecords.filter((r) => r.status === 'failed').length}
                </div>
              </div>
            </div>

            {/* CGPA Trend Chart */}
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Semester-wise Performance Trend</span>
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                  Derived from institutional grade records
                </span>
              </div>
              {cgpaTrend.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={cgpaTrend} margin={{ left: 0, right: 16, top: 4, bottom: 4 }}>
                    <CartesianGrid stroke="var(--border-color)" strokeDasharray="4 4" />
                    <XAxis dataKey="sem" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                    <YAxis domain={[5, 10]} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                    <Tooltip content={<CGPATooltip />} />
                    <Line
                      type="monotone"
                      dataKey="cgpa"
                      name="CGPA"
                      stroke="#6366f1"
                      strokeWidth={2.5}
                      dot={{ fill: '#6366f1', r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="sgpa"
                      name="SGPA"
                      stroke="#06b6d4"
                      strokeWidth={1.5}
                      strokeDasharray="3 3"
                      dot={{ fill: '#06b6d4', r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div style={{ textAlign: 'center', padding: 'var(--space-6)', color: 'var(--text-muted)' }}>
                  No semester trend data available yet.
                </div>
              )}
            </div>

            {/* Subject-wise Performance Table */}
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)' }}>Course Grade History</div>
              {academicRecords.length > 0 ? (
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th>Code</th>
                        <th>Subject Name</th>
                        <th>Sem</th>
                        <th>Marks</th>
                        <th>Credits</th>
                        <th>Grade</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {academicRecords.map((s) => {
                        const gradeColor = GRADE_COLORS[s.grade] || '#6366f1';
                        return (
                          <tr key={s.id || s.subject?.code}>
                            <td style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                              {s.subject?.code}
                            </td>
                            <td style={{ fontWeight: 500 }}>{s.subject?.name}</td>
                            <td style={{ color: 'var(--text-muted)' }}>{s.subject?.semester_number}</td>
                            <td>{s.marks !== null && s.marks !== undefined ? s.marks : '—'}</td>
                            <td style={{ color: 'var(--text-muted)' }}>{s.subject?.credits}</td>
                            <td>
                              <span
                                style={{
                                  padding: '2px 10px',
                                  borderRadius: 999,
                                  fontSize: 'var(--font-size-xs)',
                                  fontWeight: 700,
                                  color: gradeColor,
                                  background: `${gradeColor}18`,
                                }}
                              >
                                {s.grade || '—'}
                              </span>
                            </td>
                            <td>
                              <span
                                className={`badge ${s.status === 'completed' ? 'badge-success' : s.status === 'failed' ? 'badge-danger' : 'badge-warning'}`}
                              >
                                {s.status}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--text-muted)' }}>
                  <p>No academic records synced from the university management system yet.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ─── TAB 3: SKILLS ────────────────────────────────────── */}
        {tab === 'Skills' && (
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-5)', flexWrap: 'wrap', gap: 12 }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: 'var(--font-size-base)' }}>Verified Skill Profile</div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 2 }}>
                  Confidence scores computed from coursework, assessments, and parsed resumes
                </div>
              </div>
              <button
                className="btn btn-primary"
                onClick={() => {
                  setSkillName('');
                  setSkillCategory('tool');
                  setSkillConfidence(0.75);
                  setSkillProficiency('intermediate');
                  setAddSkillError('');
                  setAddSkillModalOpen(true);
                }}
                style={{ height: 36, fontSize: 'var(--font-size-sm)', display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <span>+</span> Add Skill
              </button>
            </div>

            {skills.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                {skills.map((s) => {
                  const sName = s.skill?.name || s.name || 'Skill';
                  const sCategory = s.skill?.category || s.category || 'tool';
                  const sPercent = Math.round((s.confidence ?? 0.5) * 100);
                  const isVerified = s.is_verified || s.source === 'resume_verified' || s.source === 'assessment' || s.confidence >= 0.75;
                  const sId = s.id || s.skill?.id || s.skill_id || sName;

                  return (
                    <div
                      key={s.id || sName}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 'var(--space-4)',
                        padding: '8px 12px',
                        background: 'var(--bg-tertiary)',
                        borderRadius: 'var(--border-radius-sm)',
                        flexWrap: 'wrap',
                      }}
                    >
                      <div style={{ width: 170, minWidth: 140 }}>
                        <div style={{ fontWeight: 500, fontSize: 'var(--font-size-sm)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                          <span>{sName}</span>
                          {isVerified && (
                            <span
                              title={s.source === 'resume_verified' || s.is_verified ? "Verified via Resume Confirmation" : "Verified competency"}
                              style={{
                                color: s.source === 'resume_verified' || s.is_verified ? 'var(--accent-success, #22c55e)' : '#6366f1',
                                fontSize: '0.85rem',
                                fontWeight: 'bold',
                              }}
                            >
                              ✓
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                          {sCategory}
                        </div>
                      </div>

                      {/* Progress Bar */}
                      <div style={{ flex: 1, minWidth: 160, height: 8, background: 'var(--bg-card)', borderRadius: 4, overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${sPercent}%`,
                            height: '100%',
                            background: sPercent >= 75 ? 'var(--accent-success)' : sPercent >= 55 ? '#6366f1' : 'var(--accent-warning)',
                            borderRadius: 4,
                            transition: 'width 0.8s ease',
                          }}
                        />
                      </div>

                      {/* Percentage */}
                      <span style={{ width: 44, textAlign: 'right', fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {sPercent}%
                      </span>

                      {/* Source Tag */}
                      {s.source === 'resume_verified' ? (
                        <span
                          className="badge badge-success"
                          style={{
                            fontSize: '0.7rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 4,
                            background: 'rgba(34, 197, 94, 0.15)',
                            color: '#22c55e',
                            border: '1px solid rgba(34, 197, 94, 0.3)',
                          }}
                        >
                          ✓ Resume Verified
                        </span>
                      ) : (
                        <span
                          className="badge"
                          style={{
                            textTransform: 'capitalize',
                            fontSize: '0.7rem',
                            background: 'rgba(255,255,255,0.06)',
                            color: 'var(--text-secondary)',
                          }}
                        >
                          {s.source || 'manual'}
                        </span>
                      )}

                      {/* Proficiency badge */}
                      {s.proficiency_level && (
                        <span className="badge badge-primary" style={{ fontSize: '0.7rem', textTransform: 'capitalize' }}>
                          {s.proficiency_level}
                        </span>
                      )}

                      {/* Delete button */}
                      <button
                        title="Remove skill"
                        disabled={deletingSkillId === sId}
                        onClick={() => handleDeleteSkill(sId, sName)}
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          color: 'var(--text-muted)',
                          fontSize: '0.9rem',
                          padding: '4px 6px',
                          borderRadius: 4,
                        }}
                        onMouseOver={(e) => (e.currentTarget.style.color = 'var(--accent-danger)')}
                        onMouseOut={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
                      >
                        {deletingSkillId === sId ? '⏳' : '🗑️'}
                      </button>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: 'var(--space-12)', color: 'var(--text-muted)' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: 'var(--space-3)' }}>💡</div>
                <h3 style={{ fontSize: 'var(--font-size-base)', color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
                  No skills recorded yet
                </h3>
                <p style={{ fontSize: 'var(--font-size-sm)', maxWidth: 420, margin: '0 auto var(--space-4)' }}>
                  Add your skills manually or upload your resume in the Resume tab to automatically detect and index your technical competencies.
                </p>
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    setSkillName('');
                    setAddSkillModalOpen(true);
                  }}
                >
                  + Add First Skill
                </button>
              </div>
            )}
          </div>
        )}

        {/* ─── TAB 4: RESUME ────────────────────────────────────── */}
        {tab === 'Resume' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 'var(--space-6)' }}>
            {/* Upload Resume Card */}
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)', fontSize: 'var(--font-size-base)' }}>
                Upload & Ingest Resume
              </div>

              {resumeStatus?.resume_url && (
                <div
                  style={{
                    padding: 'var(--space-3) var(--space-4)',
                    background: 'var(--bg-tertiary)',
                    borderRadius: 'var(--border-radius-sm)',
                    marginBottom: 'var(--space-4)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>Current Resume on File</div>
                    <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {resumeStatus.resume_url.split(/[\\/]/).pop()}
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    {resumeStatus?.extracted_skills && resumeStatus.extracted_skills.length > 0 && (
                      <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={() => openReviewSkillsModal(resumeStatus.extracted_skills)}
                        style={{ height: 28, fontSize: '0.75rem', padding: '0 10px', display: 'flex', alignItems: 'center', gap: 4 }}
                      >
                        🔍 Review Skills
                      </button>
                    )}
                    <span className={`badge ${resumeStatus.resume_parsed ? 'badge-success' : 'badge-warning'}`}>
                      {resumeStatus.resume_parsed ? 'NLP Parsed ✓' : 'Processing...'}
                    </span>
                  </div>
                </div>
              )}

              {/* Drag & Drop Box */}
              <div
                onClick={() => fileRef.current?.click()}
                style={{
                  border: `2px dashed ${resumeFile ? 'var(--accent-success)' : 'var(--border-color)'}`,
                  borderRadius: 'var(--border-radius)',
                  padding: 'var(--space-8) var(--space-6)',
                  textAlign: 'center',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                  background: resumeFile ? 'rgba(34,197,94,0.05)' : 'var(--bg-tertiary)',
                }}
                onMouseOver={(e) => (e.currentTarget.style.borderColor = 'var(--accent-primary)')}
                onMouseOut={(e) => (e.currentTarget.style.borderColor = resumeFile ? 'var(--accent-success)' : 'var(--border-color)')}
              >
                <div style={{ fontSize: '2.5rem', marginBottom: 'var(--space-3)' }}>
                  {resumeFile ? '✅' : '📄'}
                </div>
                {resumeFile ? (
                  <>
                    <div style={{ fontWeight: 600, color: 'var(--accent-success)' }}>{resumeFile.name}</div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 4 }}>
                      {(resumeFile.size / 1024).toFixed(0)} KB · Click to change file
                    </div>
                  </>
                ) : (
                  <>
                    <div style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Select or Drop your resume here</div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 4 }}>
                      Supported formats: PDF, DOCX, TXT (Max 5MB)
                    </div>
                  </>
                )}
                <input
                  ref={fileRef}
                  type="file"
                  accept=".pdf,.docx,.txt"
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    setResumeFile(e.target.files[0] || null);
                    setResumeError('');
                  }}
                />
              </div>

              {resumeError && (
                <div style={{ color: 'var(--accent-danger)', fontSize: 'var(--font-size-xs)', marginTop: 'var(--space-3)' }}>
                  {resumeError}
                </div>
              )}

              {resumeFile && (
                <button
                  className="btn btn-primary"
                  disabled={uploadingResume || resumePolling}
                  onClick={handleUploadResume}
                  style={{ width: '100%', marginTop: 'var(--space-4)', height: 42, fontSize: 'var(--font-size-sm)' }}
                >
                  {uploadingResume || resumePolling ? '⏳ Extracting Skills (NLP Pipeline)...' : '📤 Upload & Parse Skills'}
                </button>
              )}
            </div>

            {/* Parsed Resume Skills Preview Card */}
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 'var(--space-4)', fontSize: 'var(--font-size-base)' }}>
                NLP Extracted Skills Preview
              </div>

              {resumeSkills.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: 'var(--space-1)' }}>
                    {resumeSkills.length} skills automatically extracted from your resume:
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 320, overflowY: 'auto' }}>
                    {resumeSkills.map((s) => (
                      <div
                        key={s.id || s.skill?.name}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: 'var(--space-2) var(--space-3)',
                          background: 'var(--bg-tertiary)',
                          borderRadius: 'var(--border-radius-sm)',
                        }}
                      >
                        <div>
                          <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 500 }}>
                            {s.skill?.name || s.name}
                          </div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                            {s.skill?.category || s.category}
                          </div>
                        </div>
                        <span className="badge badge-success">
                          {Math.round((s.confidence || 0.8) * 100)}% Confidence ✓
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: 'var(--space-10)', color: 'var(--text-muted)' }}>
                  <div style={{ fontSize: '2rem', marginBottom: 'var(--space-3)' }}>🔍</div>
                  <p style={{ fontSize: 'var(--font-size-sm)' }}>
                    Upload your resume to automatically parse and index skills into your placement profile.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

      </div>

      {/* ─── MODAL: EDIT PROFILE ───────────────────────────────── */}
      {editModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.7)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 999,
            padding: 'var(--space-4)',
          }}
          onClick={() => setEditModalOpen(false)}
        >
          <div
            className="card"
            style={{
              width: '100%',
              maxWidth: 520,
              maxHeight: '90vh',
              overflowY: 'auto',
              border: '1px solid var(--border-color)',
              boxShadow: 'var(--shadow-lg)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
              <h3 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700 }}>Edit Profile Information</h3>
              <button
                type="button"
                onClick={() => setEditModalOpen(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            {editError && (
              <div style={{ color: 'var(--accent-danger)', fontSize: 'var(--font-size-xs)', marginBottom: 'var(--space-3)' }}>
                {editError}
              </div>
            )}

            <form onSubmit={handleSaveProfile} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div className="input-group">
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Phone Number
                </label>
                <input
                  className="input"
                  type="text"
                  placeholder="+91 98765 43210"
                  value={editForm.phone}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, phone: e.target.value }))}
                />
              </div>

              <div className="input-group">
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Bio & Professional Summary
                </label>
                <textarea
                  className="input"
                  rows={4}
                  placeholder="Tell recruiters about your interests, key achievements, and project highlights..."
                  value={editForm.bio}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, bio: e.target.value }))}
                  style={{ resize: 'vertical' }}
                />
              </div>

              <div className="input-group">
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  LinkedIn URL
                </label>
                <input
                  className="input"
                  type="text"
                  placeholder="https://linkedin.com/in/username"
                  value={editForm.linkedin_url}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, linkedin_url: e.target.value }))}
                />
              </div>

              <div className="input-group">
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  GitHub Profile URL
                </label>
                <input
                  className="input"
                  type="text"
                  placeholder="https://github.com/username"
                  value={editForm.github_url}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, github_url: e.target.value }))}
                />
              </div>

              <div className="input-group">
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Personal Portfolio / Website
                </label>
                <input
                  className="input"
                  type="text"
                  placeholder="https://myportfolio.dev"
                  value={editForm.portfolio_url}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, portfolio_url: e.target.value }))}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-3)', marginTop: 'var(--space-4)' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setEditModalOpen(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={editSaving}
                >
                  {editSaving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ─── MODAL: ADD SKILL ──────────────────────────────────── */}
      {addSkillModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.7)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 999,
            padding: 'var(--space-4)',
          }}
          onClick={() => setAddSkillModalOpen(false)}
        >
          <div
            className="card"
            style={{
              width: '100%',
              maxWidth: 480,
              border: '1px solid var(--border-color)',
              boxShadow: 'var(--shadow-lg)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
              <h3 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700 }}>Add Skill to Profile</h3>
              <button
                type="button"
                onClick={() => setAddSkillModalOpen(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            {addSkillError && (
              <div style={{ color: 'var(--accent-danger)', fontSize: 'var(--font-size-xs)', marginBottom: 'var(--space-3)' }}>
                {addSkillError}
              </div>
            )}

            <form onSubmit={handleAddSkill} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div className="input-group" style={{ position: 'relative' }}>
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Skill Name *
                </label>
                <input
                  className="input"
                  type="text"
                  placeholder="e.g. Docker, React, PostgreSQL..."
                  value={skillName}
                  onChange={(e) => {
                    setSkillName(e.target.value);
                    setSelectedSkillId(null);
                  }}
                  autoFocus
                  required
                />

                {/* Suggestions Dropdown */}
                {skillSuggestions.length > 0 && (
                  <div
                    style={{
                      position: 'absolute',
                      top: '100%',
                      left: 0,
                      right: 0,
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border-color)',
                      borderRadius: 'var(--border-radius-sm)',
                      marginTop: 4,
                      zIndex: 10,
                      maxHeight: 180,
                      overflowY: 'auto',
                      boxShadow: 'var(--shadow-md)',
                    }}
                  >
                    {skillSuggestions.map((sug) => (
                      <div
                        key={sug.id}
                        onClick={() => {
                          setSkillName(sug.name);
                          setSelectedSkillId(sug.id);
                          if (sug.category) setSkillCategory(sug.category);
                          setSkillSuggestions([]);
                        }}
                        style={{
                          padding: '8px 12px',
                          cursor: 'pointer',
                          fontSize: 'var(--font-size-sm)',
                          borderBottom: '1px solid var(--border-color)',
                          display: 'flex',
                          justifyContent: 'space-between',
                        }}
                        onMouseOver={(e) => (e.currentTarget.style.background = 'var(--bg-tertiary)')}
                        onMouseOut={(e) => (e.currentTarget.style.background = 'transparent')}
                      >
                        <span>{sug.name}</span>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{sug.category}</span>
                      </div>
                    ))}
                  </div>
                )}
                {searchingSkills && (
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 2 }}>
                    Searching taxonomy...
                  </div>
                )}
              </div>

              <div className="input-group">
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Category
                </label>
                <select
                  className="input"
                  value={skillCategory}
                  onChange={(e) => setSkillCategory(e.target.value)}
                  style={{ background: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}
                >
                  <option value="language">Programming Language</option>
                  <option value="framework">Framework</option>
                  <option value="library">Library</option>
                  <option value="tool">Tool</option>
                  <option value="database">Database</option>
                  <option value="cloud">Cloud & DevOps</option>
                  <option value="concept">Core Concept</option>
                  <option value="methodology">Methodology</option>
                  <option value="soft_skill">Soft Skill</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div className="input-group">
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Proficiency Level
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
                  {[
                    { label: 'Beginner', val: 'beginner', score: 0.45 },
                    { label: 'Intermediate', val: 'intermediate', score: 0.70 },
                    { label: 'Advanced', val: 'advanced', score: 0.85 },
                    { label: 'Expert', val: 'expert', score: 0.95 },
                  ].map((p) => (
                    <button
                      key={p.val}
                      type="button"
                      onClick={() => {
                        setSkillProficiency(p.val);
                        setSkillConfidence(p.score);
                      }}
                      style={{
                        padding: '8px 4px',
                        borderRadius: 'var(--border-radius-sm)',
                        fontSize: 'var(--font-size-xs)',
                        fontWeight: 600,
                        cursor: 'pointer',
                        background: skillProficiency === p.val ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                        color: skillProficiency === p.val ? 'white' : 'var(--text-secondary)',
                        border: `1px solid ${skillProficiency === p.val ? 'var(--accent-primary)' : 'var(--border-color)'}`,
                        transition: 'all 0.15s',
                      }}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>

                {/* Range Slider for granular proficiency adjustment */}
                <div style={{ marginTop: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginBottom: 4 }}>
                    <span>Self-Assessed Proficiency Score</span>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{Math.round(skillConfidence * 100)}%</span>
                  </div>
                  <input
                    type="range"
                    min="10"
                    max="100"
                    step="5"
                    value={Math.round(skillConfidence * 100)}
                    onChange={(e) => setSkillConfidence(Number(e.target.value) / 100)}
                    style={{ width: '100%', cursor: 'pointer', accentColor: 'var(--accent-primary, #6366f1)' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-3)', marginTop: 'var(--space-4)' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setAddSkillModalOpen(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={addSkillSaving}
                >
                  {addSkillSaving ? 'Adding...' : 'Add to Profile'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ─── MODAL: Add Project ────────────────────────────────────────── */}
      {addProjectModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 'var(--space-4)',
          }}
          onClick={() => setAddProjectModalOpen(false)}
        >
          <div
            className="card"
            style={{
              width: '100%',
              maxWidth: 540,
              background: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)',
              maxHeight: '90vh',
              overflowY: 'auto',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
              <h3 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700 }}>Add Project</h3>
              <button
                type="button"
                onClick={() => setAddProjectModalOpen(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            {projectErrors.general && (
              <div style={{ color: 'var(--accent-danger)', fontSize: 'var(--font-size-xs)', marginBottom: 'var(--space-3)' }}>
                {projectErrors.general}
              </div>
            )}

            <form onSubmit={handleAddProjectSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div className="input-group">
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Project Title *
                </label>
                <input
                  className="input"
                  type="text"
                  placeholder="e.g. Real-time Chat App"
                  value={projectForm.title}
                  onChange={(e) => {
                    setProjectForm((p) => ({ ...p, title: e.target.value }));
                    if (projectErrors.title) setProjectErrors((p) => ({ ...p, title: null }));
                  }}
                  required
                />
                {projectErrors.title && (
                  <div style={{ color: 'var(--accent-danger)', fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
                    {projectErrors.title}
                  </div>
                )}
              </div>

              <div className="input-group">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Description *
                  </label>
                  <span style={{ fontSize: '0.7rem', color: projectForm.description.length < 10 ? 'var(--accent-warning)' : 'var(--text-muted)' }}>
                    {projectForm.description.length} chars (min 10)
                  </span>
                </div>
                <textarea
                  className="input"
                  rows={3}
                  placeholder="Explain the problem solved, architecture, and features..."
                  value={projectForm.description}
                  onChange={(e) => {
                    setProjectForm((p) => ({ ...p, description: e.target.value }));
                    if (projectErrors.description) setProjectErrors((p) => ({ ...p, description: null }));
                  }}
                  required
                />
                {projectErrors.description && (
                  <div style={{ color: 'var(--accent-danger)', fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
                    {projectErrors.description}
                  </div>
                )}
              </div>

              {/* Tech Stack Tag Input */}
              <div className="input-group">
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Tech Stack * (Press Enter or comma to add chip)
                </label>
                {projectForm.tech_stack.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
                    {projectForm.tech_stack.map((t) => (
                      <span
                        key={t}
                        style={{
                          fontSize: '0.75rem',
                          padding: '3px 8px',
                          borderRadius: 4,
                          background: 'rgba(99, 102, 241, 0.2)',
                          color: 'var(--accent-primary)',
                          border: '1px solid rgba(99, 102, 241, 0.4)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                        }}
                      >
                        {t}
                        <span
                          style={{ cursor: 'pointer', fontWeight: 'bold' }}
                          onClick={() => handleRemoveProjectTag(t)}
                        >
                          ✕
                        </span>
                      </span>
                    ))}
                  </div>
                )}
                <div style={{ display: 'flex', gap: 8 }}>
                  <input
                    className="input"
                    type="text"
                    placeholder="Type a skill (e.g. React) and press Enter..."
                    value={projectForm.tech_input}
                    onChange={(e) => setProjectForm((p) => ({ ...p, tech_input: e.target.value }))}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ',') {
                        e.preventDefault();
                        handleAddProjectTag();
                      }
                    }}
                  />
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={handleAddProjectTag}
                    style={{ whiteSpace: 'nowrap' }}
                  >
                    + Add
                  </button>
                </div>
                {projectErrors.tech_stack && (
                  <div style={{ color: 'var(--accent-danger)', fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
                    {projectErrors.tech_stack}
                  </div>
                )}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
                <div className="input-group">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    GitHub URL (optional)
                  </label>
                  <input
                    className="input"
                    type="url"
                    placeholder="https://github.com/..."
                    value={projectForm.github_url}
                    onChange={(e) => {
                      setProjectForm((p) => ({ ...p, github_url: e.target.value }));
                      if (projectErrors.github_url) setProjectErrors((p) => ({ ...p, github_url: null }));
                    }}
                  />
                  {projectErrors.github_url && (
                    <div style={{ color: 'var(--accent-danger)', fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
                      {projectErrors.github_url}
                    </div>
                  )}
                </div>

                <div className="input-group">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Live Demo URL (optional)
                  </label>
                  <input
                    className="input"
                    type="url"
                    placeholder="https://demo.app"
                    value={projectForm.live_url}
                    onChange={(e) => setProjectForm((p) => ({ ...p, live_url: e.target.value }))}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
                <div className="input-group">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Start Date
                  </label>
                  <input
                    className="input"
                    type="date"
                    value={projectForm.start_date}
                    onChange={(e) => setProjectForm((p) => ({ ...p, start_date: e.target.value }))}
                  />
                </div>

                <div className="input-group">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    End Date
                  </label>
                  <input
                    className="input"
                    type="date"
                    disabled={projectForm.is_ongoing}
                    value={projectForm.is_ongoing ? '' : projectForm.end_date}
                    onChange={(e) => setProjectForm((p) => ({ ...p, end_date: e.target.value }))}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: 'var(--space-6)', marginTop: 4 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 'var(--font-size-sm)' }}>
                  <input
                    type="checkbox"
                    checked={projectForm.is_ongoing}
                    onChange={(e) => setProjectForm((p) => ({ ...p, is_ongoing: e.target.checked }))}
                  />
                  <span>Ongoing Project</span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 'var(--font-size-sm)' }}>
                  <input
                    type="checkbox"
                    checked={projectForm.is_featured}
                    onChange={(e) => setProjectForm((p) => ({ ...p, is_featured: e.target.checked }))}
                  />
                  <span>⭐ Feature on Profile</span>
                </label>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-3)', marginTop: 'var(--space-4)' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setAddProjectModalOpen(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={projectSaving}
                >
                  {projectSaving ? 'Saving...' : 'Save Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ─── MODAL: Add Certification ───────────────────────────────────── */}
      {addCertModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 'var(--space-4)',
          }}
          onClick={() => setAddCertModalOpen(false)}
        >
          <div
            className="card"
            style={{
              width: '100%',
              maxWidth: 500,
              background: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)',
              maxHeight: '90vh',
              overflowY: 'auto',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
              <h3 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700 }}>Add Certification</h3>
              <button
                type="button"
                onClick={() => setAddCertModalOpen(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            {certErrors.general && (
              <div style={{ color: 'var(--accent-danger)', fontSize: 'var(--font-size-xs)', marginBottom: 'var(--space-3)' }}>
                {certErrors.general}
              </div>
            )}

            <form onSubmit={handleAddCertSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div className="input-group">
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Certification Name *
                </label>
                <input
                  className="input"
                  type="text"
                  placeholder="e.g. AWS Solutions Architect – Associate"
                  value={certForm.name}
                  onChange={(e) => {
                    setCertForm((c) => ({ ...c, name: e.target.value }));
                    if (certErrors.name) setCertErrors((c) => ({ ...c, name: null }));
                  }}
                  required
                />
                {certErrors.name && (
                  <div style={{ color: 'var(--accent-danger)', fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
                    {certErrors.name}
                  </div>
                )}
              </div>

              <div className="input-group">
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Issuing Organization *
                </label>
                <input
                  className="input"
                  type="text"
                  placeholder="e.g. Amazon Web Services, Google, Microsoft..."
                  value={certForm.issuing_organization}
                  onChange={(e) => {
                    setCertForm((c) => ({ ...c, issuing_organization: e.target.value }));
                    if (certErrors.issuing_organization) setCertErrors((c) => ({ ...c, issuing_organization: null }));
                  }}
                  required
                />
                {certErrors.issuing_organization && (
                  <div style={{ color: 'var(--accent-danger)', fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
                    {certErrors.issuing_organization}
                  </div>
                )}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
                <div className="input-group">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Issue Date *
                  </label>
                  <input
                    className="input"
                    type="date"
                    value={certForm.issue_date}
                    onChange={(e) => {
                      setCertForm((c) => ({ ...c, issue_date: e.target.value }));
                      if (certErrors.issue_date) setCertErrors((c) => ({ ...c, issue_date: null }));
                    }}
                    required
                  />
                  {certErrors.issue_date && (
                    <div style={{ color: 'var(--accent-danger)', fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
                      {certErrors.issue_date}
                    </div>
                  )}
                </div>

                <div className="input-group">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Expiration Date (optional)
                  </label>
                  <input
                    className="input"
                    type="date"
                    value={certForm.expiration_date}
                    onChange={(e) => setCertForm((c) => ({ ...c, expiration_date: e.target.value }))}
                  />
                </div>
              </div>

              <div className="input-group">
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Credential ID (optional)
                </label>
                <input
                  className="input"
                  type="text"
                  placeholder="e.g. AWS-SAA-2026-R4891"
                  value={certForm.credential_id}
                  onChange={(e) => setCertForm((c) => ({ ...c, credential_id: e.target.value }))}
                />
              </div>

              <div className="input-group">
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Verification URL (optional)
                </label>
                <input
                  className="input"
                  type="url"
                  placeholder="https://verify.certificate.url"
                  value={certForm.credential_url}
                  onChange={(e) => setCertForm((c) => ({ ...c, credential_url: e.target.value }))}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-3)', marginTop: 'var(--space-4)' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setAddCertModalOpen(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={certSaving}
                >
                  {certSaving ? 'Saving...' : 'Save Certification'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ─── MODAL: Add Work Experience ─────────────────────────────────── */}
      {addExpModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 'var(--space-4)',
          }}
          onClick={() => setAddExpModalOpen(false)}
        >
          <div
            className="card"
            style={{
              width: '100%',
              maxWidth: 540,
              background: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)',
              maxHeight: '90vh',
              overflowY: 'auto',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
              <h3 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700 }}>Add Work Experience</h3>
              <button
                type="button"
                onClick={() => setAddExpModalOpen(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            {expErrors.general && (
              <div style={{ color: 'var(--accent-danger)', fontSize: 'var(--font-size-xs)', marginBottom: 'var(--space-3)' }}>
                {expErrors.general}
              </div>
            )}

            <form onSubmit={handleAddExpSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
                <div className="input-group">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Company Name *
                  </label>
                  <input
                    className="input"
                    type="text"
                    placeholder="e.g. Razorpay, Google..."
                    value={expForm.company_name}
                    onChange={(e) => {
                      setExpForm((p) => ({ ...p, company_name: e.target.value }));
                      if (expErrors.company_name) setExpErrors((p) => ({ ...p, company_name: null }));
                    }}
                    required
                  />
                  {expErrors.company_name && (
                    <div style={{ color: 'var(--accent-danger)', fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
                      {expErrors.company_name}
                    </div>
                  )}
                </div>

                <div className="input-group">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Role / Position *
                  </label>
                  <input
                    className="input"
                    type="text"
                    placeholder="e.g. SWE Intern"
                    value={expForm.role}
                    onChange={(e) => {
                      setExpForm((p) => ({ ...p, role: e.target.value }));
                      if (expErrors.role) setExpErrors((p) => ({ ...p, role: null }));
                    }}
                    required
                  />
                  {expErrors.role && (
                    <div style={{ color: 'var(--accent-danger)', fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
                      {expErrors.role}
                    </div>
                  )}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
                <div className="input-group">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Location
                  </label>
                  <input
                    className="input"
                    type="text"
                    placeholder="e.g. Bengaluru, IN (or Remote)"
                    value={expForm.location}
                    onChange={(e) => setExpForm((p) => ({ ...p, location: e.target.value }))}
                  />
                </div>

                <div className="input-group">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Employment Type
                  </label>
                  <select
                    className="input"
                    value={expForm.employment_type}
                    onChange={(e) => setExpForm((p) => ({ ...p, employment_type: e.target.value }))}
                    style={{ background: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}
                  >
                    <option value="Internship">Internship</option>
                    <option value="Full-Time">Full-Time</option>
                    <option value="Part-Time">Part-Time</option>
                    <option value="Contract">Contract</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
                <div className="input-group">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Start Date *
                  </label>
                  <input
                    className="input"
                    type="date"
                    value={expForm.start_date}
                    onChange={(e) => {
                      setExpForm((p) => ({ ...p, start_date: e.target.value }));
                      if (expErrors.start_date) setExpErrors((p) => ({ ...p, start_date: null }));
                    }}
                    required
                  />
                  {expErrors.start_date && (
                    <div style={{ color: 'var(--accent-danger)', fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
                      {expErrors.start_date}
                    </div>
                  )}
                </div>

                <div className="input-group">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    End Date
                  </label>
                  <input
                    className="input"
                    type="date"
                    disabled={expForm.is_current}
                    value={expForm.is_current ? '' : expForm.end_date}
                    onChange={(e) => setExpForm((p) => ({ ...p, end_date: e.target.value }))}
                  />
                </div>
              </div>

              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 'var(--font-size-sm)' }}>
                <input
                  type="checkbox"
                  checked={expForm.is_current}
                  onChange={(e) => setExpForm((p) => ({ ...p, is_current: e.target.checked }))}
                />
                <span>Currently Working Here</span>
              </label>

              <div className="input-group">
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Description / Responsibilities
                </label>
                <textarea
                  className="input"
                  rows={3}
                  placeholder="Key contributions, projects delivered, metrics improved..."
                  value={expForm.description}
                  onChange={(e) => setExpForm((p) => ({ ...p, description: e.target.value }))}
                />
              </div>

              {/* Skills Used Tag Input */}
              <div className="input-group">
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Skills Used (Press Enter or comma to add chip)
                </label>
                {expForm.skills_used.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
                    {expForm.skills_used.map((sk) => (
                      <span
                        key={sk}
                        style={{
                          fontSize: '0.75rem',
                          padding: '3px 8px',
                          borderRadius: 4,
                          background: 'var(--bg-card)',
                          color: 'var(--text-secondary)',
                          border: '1px solid var(--border-color)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                        }}
                      >
                        {sk}
                        <span
                          style={{ cursor: 'pointer', fontWeight: 'bold' }}
                          onClick={() => handleRemoveExpSkill(sk)}
                        >
                          ✕
                        </span>
                      </span>
                    ))}
                  </div>
                )}
                <div style={{ display: 'flex', gap: 8 }}>
                  <input
                    className="input"
                    type="text"
                    placeholder="e.g. React, TypeScript, Docker..."
                    value={expForm.skill_input}
                    onChange={(e) => setExpForm((p) => ({ ...p, skill_input: e.target.value }))}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ',') {
                        e.preventDefault();
                        handleAddExpSkill();
                      }
                    }}
                  />
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={handleAddExpSkill}
                    style={{ whiteSpace: 'nowrap' }}
                  >
                    + Add
                  </button>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-3)', marginTop: 'var(--space-4)' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setAddExpModalOpen(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={expSaving}
                >
                  {expSaving ? 'Saving...' : 'Save Experience'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ─── MODAL: Delete Confirmation Dialog ─────────────────────────── */}
      {deleteConfirmModal.isOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1100,
            padding: 'var(--space-4)',
          }}
          onClick={() => {
            if (!deleteConfirmModal.deleting) {
              setDeleteConfirmModal({ isOpen: false, type: null, id: null, title: '', deleting: false });
            }
          }}
        >
          <div
            className="card"
            style={{
              width: '100%',
              maxWidth: 420,
              background: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)',
              textAlign: 'center',
              padding: 'var(--space-6)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ fontSize: '2.5rem', marginBottom: 'var(--space-2)' }}>🗑️</div>
            <h3 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700, marginBottom: 'var(--space-2)' }}>
              Confirm Deletion
            </h3>
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--space-2)' }}>
              Are you sure you want to delete this {deleteConfirmModal.type}?
            </p>
            {deleteConfirmModal.title && (
              <div
                style={{
                  fontSize: 'var(--font-size-sm)',
                  fontWeight: 600,
                  color: 'var(--text-primary)',
                  padding: 'var(--space-2) var(--space-3)',
                  background: 'var(--bg-tertiary)',
                  borderRadius: 'var(--border-radius-sm)',
                  marginBottom: 'var(--space-6)',
                  wordBreak: 'break-word',
                }}
              >
                "{deleteConfirmModal.title}"
              </div>
            )}
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: 'var(--space-6)' }}>
              This action cannot be undone.
            </p>

            <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--space-3)' }}>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={deleteConfirmModal.deleting}
                onClick={() => setDeleteConfirmModal({ isOpen: false, type: null, id: null, title: '', deleting: false })}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-danger"
                disabled={deleteConfirmModal.deleting}
                onClick={handleConfirmDelete}
                style={{ background: 'var(--accent-danger)', color: 'white' }}
              >
                {deleteConfirmModal.deleting ? 'Deleting...' : 'Delete Permanently'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── MODAL: Review Extracted Skills (Task 2) ───────────────────── */}
      {reviewSkillsModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 'var(--space-4)',
          }}
          onClick={() => !confirmingSkills && setReviewSkillsModalOpen(false)}
        >
          <div
            className="card"
            style={{
              width: '100%',
              maxWidth: 680,
              maxHeight: '90vh',
              overflowY: 'auto',
              border: '1px solid var(--border-color)',
              boxShadow: 'var(--shadow-xl)',
              background: 'var(--bg-card, #131722)',
              position: 'relative',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-4)' }}>
              <div>
                <h3 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                  Review Extracted Skills
                </h3>
                <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 4, marginBottom: 0 }}>
                  We found {extractedSkills.length} skills in your resume. Review and confirm before saving.
                </p>
              </div>
              <button
                type="button"
                onClick={() => !confirmingSkills && setReviewSkillsModalOpen(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  fontSize: '1.2rem',
                  cursor: 'pointer',
                  padding: 4,
                  lineHeight: 1,
                }}
              >
                ✕
              </button>
            </div>

            {confirmSkillsError && (
              <div
                style={{
                  padding: '8px 12px',
                  borderRadius: 'var(--border-radius-sm)',
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid var(--accent-danger)',
                  color: 'var(--accent-danger)',
                  fontSize: 'var(--font-size-xs)',
                  marginBottom: 'var(--space-4)',
                }}
              >
                {confirmSkillsError}
              </div>
            )}

            {/* High Confidence Section (>= 85%) */}
            {(() => {
              const highConf = extractedSkills.filter((s) => (s.confidence ?? 0.85) >= 0.85);
              if (highConf.length === 0) return null;
              return (
                <div style={{ marginBottom: 'var(--space-5)' }}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      paddingBottom: 'var(--space-2)',
                      borderBottom: '1px solid var(--border-color)',
                      marginBottom: 'var(--space-3)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600, fontSize: 'var(--font-size-sm)', color: '#22c55e' }}>
                      <span>🟢</span> High Confidence (≥ 85%)
                    </div>
                    <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                      Check all that are correct:
                    </span>
                  </div>

                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fill, minmax(190px, 1fr))',
                      gap: 8,
                    }}
                  >
                    {highConf.map((s) => {
                      const isChecked = selectedSkills.has(s.name);
                      return (
                        <div
                          key={s.name}
                          onClick={() => handleToggleSkillSelection(s.name)}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 10,
                            padding: '8px 12px',
                            background: isChecked ? 'rgba(34, 197, 94, 0.08)' : 'var(--bg-tertiary)',
                            border: `1px solid ${isChecked ? 'rgba(34, 197, 94, 0.4)' : 'var(--border-color)'}`,
                            borderRadius: 'var(--border-radius-sm)',
                            cursor: 'pointer',
                            transition: 'all 0.15s ease',
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => {}}
                            style={{ cursor: 'pointer', accentColor: '#22c55e', width: 16, height: 16 }}
                          />
                          <span style={{ flex: 1, fontSize: 'var(--font-size-xs)', fontWeight: 500, color: 'var(--text-primary)' }}>
                            {s.name}
                          </span>
                          <span
                            style={{
                              fontSize: '0.65rem',
                              padding: '2px 6px',
                              borderRadius: 4,
                              background: 'rgba(34, 197, 94, 0.15)',
                              color: '#22c55e',
                              fontWeight: 600,
                            }}
                          >
                            {Math.round((s.confidence ?? 0.85) * 100)}%
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })()}

            {/* Probable Match Section (60–84%) */}
            {(() => {
              const probable = extractedSkills.filter((s) => (s.confidence ?? 0.85) < 0.85);
              if (probable.length === 0) return null;
              return (
                <div style={{ marginBottom: 'var(--space-5)' }}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      paddingBottom: 'var(--space-2)',
                      borderBottom: '1px solid var(--border-color)',
                      marginBottom: 'var(--space-3)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600, fontSize: 'var(--font-size-sm)', color: '#eab308' }}>
                      <span>🟡</span> Probable Match (60–84%)
                    </div>
                    <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                      Verify these carefully:
                    </span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {probable.map((s) => {
                      const isChecked = selectedSkills.has(s.name);
                      const isSuspicious =
                        s.raw &&
                        s.raw.toLowerCase().includes('script') &&
                        s.name.toLowerCase() === 'java';

                      return (
                        <div
                          key={s.name}
                          onClick={() => handleToggleSkillSelection(s.name)}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            padding: '8px 12px',
                            background: isChecked ? 'rgba(234, 179, 8, 0.08)' : 'var(--bg-tertiary)',
                            border: `1px solid ${isChecked ? 'rgba(234, 179, 8, 0.4)' : 'var(--border-color)'}`,
                            borderRadius: 'var(--border-radius-sm)',
                            cursor: 'pointer',
                            flexWrap: 'wrap',
                            gap: 8,
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={() => {}}
                              style={{ cursor: 'pointer', accentColor: '#eab308', width: 16, height: 16 }}
                            />
                            <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-primary)' }}>
                              {s.name}
                            </span>
                            <span title="Review recommendation" style={{ fontSize: '0.85rem' }}>⚠️</span>
                            {s.raw && (
                              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                                (found: &ldquo;{s.raw}&rdquo;)
                              </span>
                            )}
                            {isSuspicious && (
                              <span
                                style={{
                                  fontSize: '0.65rem',
                                  fontWeight: 700,
                                  color: 'var(--accent-danger)',
                                  background: 'rgba(239, 68, 68, 0.15)',
                                  padding: '2px 6px',
                                  borderRadius: 4,
                                }}
                              >
                                UNCHECK if wrong!
                              </span>
                            )}
                          </div>
                          <span
                            style={{
                              fontSize: '0.65rem',
                              padding: '2px 6px',
                              borderRadius: 4,
                              background: 'rgba(234, 179, 8, 0.15)',
                              color: '#eab308',
                              fontWeight: 600,
                            }}
                          >
                            {Math.round((s.confidence ?? 0.70) * 100)}%
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })()}

            {/* Add a skill we missed Section */}
            <div
              style={{
                marginTop: 'var(--space-4)',
                padding: 'var(--space-3)',
                background: 'var(--bg-tertiary)',
                borderRadius: 'var(--border-radius-sm)',
                border: '1px solid var(--border-color)',
                position: 'relative',
              }}
            >
              <label
                style={{
                  display: 'block',
                  fontSize: 'var(--font-size-xs)',
                  fontWeight: 600,
                  color: 'var(--text-secondary)',
                  marginBottom: 'var(--space-2)',
                }}
              >
                ➕ Add a skill we missed:
              </label>
              <div style={{ display: 'flex', gap: 'var(--space-2)', position: 'relative' }}>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g. Docker, Kubernetes, GraphQL..."
                  value={missedSkillInput}
                  onChange={(e) => setMissedSkillInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddMissedSkill();
                    }
                  }}
                  style={{ flex: 1, height: 36, fontSize: 'var(--font-size-sm)' }}
                />
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => handleAddMissedSkill()}
                  disabled={!missedSkillInput.trim()}
                  style={{ height: 36, whiteSpace: 'nowrap', fontSize: 'var(--font-size-xs)' }}
                >
                  + Add
                </button>

                {/* Autocomplete Dropdown */}
                {missedSkillSuggestions.length > 0 && (
                  <div
                    style={{
                      position: 'absolute',
                      top: '100%',
                      left: 0,
                      right: 70,
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border-color)',
                      borderRadius: 'var(--border-radius-sm)',
                      marginTop: 4,
                      zIndex: 100,
                      maxHeight: 160,
                      overflowY: 'auto',
                      boxShadow: 'var(--shadow-lg)',
                    }}
                  >
                    {missedSkillSuggestions.map((sug) => (
                      <div
                        key={sug.id}
                        onClick={() => handleAddMissedSkill(sug.name)}
                        style={{
                          padding: '8px 12px',
                          cursor: 'pointer',
                          fontSize: 'var(--font-size-sm)',
                          borderBottom: '1px solid var(--border-color)',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                        onMouseOver={(e) => (e.currentTarget.style.background = 'var(--bg-tertiary)')}
                        onMouseOut={(e) => (e.currentTarget.style.background = 'transparent')}
                      >
                        <span style={{ fontWeight: 500 }}>{sug.name}</span>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                          {sug.category}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              {searchingMissedSkill && (
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 4 }}>
                  Searching skill taxonomy...
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginTop: 'var(--space-5)',
                paddingTop: 'var(--space-4)',
                borderTop: '1px solid var(--border-color)',
                flexWrap: 'wrap',
                gap: 'var(--space-3)',
              }}
            >
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setReviewSkillsModalOpen(false)}
                disabled={confirmingSkills}
                style={{ fontSize: 'var(--font-size-xs)' }}
              >
                ← Back
              </button>

              <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                <strong style={{ color: 'var(--accent-primary)', fontSize: 'var(--font-size-base)' }}>
                  {selectedSkills.size}
                </strong>{' '}
                skills selected
              </div>

              <button
                type="button"
                className="btn btn-primary"
                disabled={confirmingSkills || selectedSkills.size === 0}
                onClick={handleConfirmAndSyncSkills}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  height: 38,
                  padding: '0 18px',
                  fontWeight: 600,
                  fontSize: 'var(--font-size-sm)',
                }}
              >
                {confirmingSkills ? (
                  <>
                    <span className="spinner" style={{ width: 14, height: 14 }} />
                    Syncing...
                  </>
                ) : (
                  <>✓ Confirm & Sync to Profile</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── MODAL: Share Public Portfolio (Task 3) ─────────────────────── */}
      {shareModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 'var(--space-4)',
          }}
          onClick={() => setShareModalOpen(false)}
        >
          <div
            className="card"
            style={{
              width: '100%',
              maxWidth: 480,
              border: '1px solid var(--border-color)',
              boxShadow: 'var(--shadow-xl)',
              background: 'var(--bg-card, #131722)',
              textAlign: 'center',
              position: 'relative',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-4)' }}>
              <div style={{ textAlign: 'left' }}>
                <h3 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                  Share Verified Portfolio
                </h3>
                <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 4, marginBottom: 0 }}>
                  Recruiters can view your verified competencies, projects, and credentials without signing in.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShareModalOpen(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  fontSize: '1.2rem',
                  cursor: 'pointer',
                  padding: 4,
                  lineHeight: 1,
                }}
              >
                ✕
              </button>
            </div>

            {/* QR Code & Direct Link */}
            {(() => {
              const portfolioUrl = `${window.location.origin}/portfolio/${profile?.id || user?.id}`;
              const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(portfolioUrl)}`;

              return (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', margin: 'var(--space-3) 0' }}>
                  <div
                    style={{
                      padding: 12,
                      background: '#ffffff',
                      borderRadius: 12,
                      border: '1px solid var(--border-color)',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
                      marginBottom: 10,
                    }}
                  >
                    <img
                      src={qrCodeUrl}
                      alt="Portfolio QR Code"
                      width={150}
                      height={150}
                      style={{ display: 'block' }}
                    />
                  </div>
                  <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: 'var(--space-4)' }}>
                    Scan with any phone camera to instantly view portfolio
                  </span>

                  {/* Copy Link Input Box */}
                  <div style={{ display: 'flex', width: '100%', gap: 8 }}>
                    <input
                      type="text"
                      readOnly
                      value={portfolioUrl}
                      className="input"
                      style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-primary)', flex: 1 }}
                      onClick={(e) => e.target.select()}
                    />
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={() => {
                        navigator.clipboard.writeText(portfolioUrl);
                        setShareCopied(true);
                        showToast('Link copied! ✓');
                        setTimeout(() => setShareCopied(false), 2000);
                      }}
                      style={{ whiteSpace: 'nowrap', fontSize: 'var(--font-size-xs)', height: 38 }}
                    >
                      {shareCopied ? '✓ Copied' : 'Copy Link'}
                    </button>
                  </div>

                  <div style={{ marginTop: 'var(--space-4)', display: 'flex', justifyContent: 'center', gap: 12 }}>
                    <a
                      href={portfolioUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-secondary"
                      style={{ fontSize: 'var(--font-size-xs)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 6 }}
                    >
                      <span>↗</span> Open Public View
                    </a>
                  </div>

                  {!profile?.consent_profile_visible && (
                    <div
                      style={{
                        marginTop: 'var(--space-4)',
                        padding: '8px 12px',
                        borderRadius: 'var(--border-radius-sm)',
                        background: 'rgba(234, 179, 8, 0.12)',
                        border: '1px solid rgba(234, 179, 8, 0.3)',
                        color: 'var(--accent-warning)',
                        fontSize: 'var(--font-size-xs)',
                        textAlign: 'left',
                        lineHeight: 1.5,
                      }}
                    >
                      ⚠️ <strong>Public visibility is disabled:</strong> External recruiters won&apos;t be able to open this link until you enable &ldquo;Make profile discoverable&rdquo; in your Academic tab privacy settings.
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
}
