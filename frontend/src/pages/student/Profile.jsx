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

  // Toast Helper
  const showToast = useCallback((msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  }, []);

  // ─── Fetch All Profile Data ──────────────────────────────────────
  const loadData = useCallback(async (isInitial = false) => {
    try {
      if (isInitial) setLoading(true);

      const [profileRes, skillsRes, recordsRes, resumeRes] = await Promise.all([
        studentApi.getMyProfile(),
        studentApi.getMySkills(),
        studentApi.getMyAcademicRecords(),
        resumeApi.getStatus().catch(() => ({ data: null })),
      ]);

      const profData = profileRes.data;
      setProfile(profData);
      setSkills(Array.isArray(skillsRes.data) ? skillsRes.data : []);
      setAcademicRecords(Array.isArray(recordsRes.data) ? recordsRes.data : []);

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

  // ─── Resume Upload & Status Polling ──────────────────────────────
  const handleUploadResume = async () => {
    if (!resumeFile) return;

    setUploadingResume(true);
    setResumeError('');

    try {
      await studentApi.uploadResume(resumeFile);
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
            showToast('Resume parsed successfully! Skills updated.');
            // Re-fetch skills and profile
            loadData(false);
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

          <button
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
            style={{ height: 38, flexShrink: 0, display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <span>✏️</span> Edit Profile
          </button>
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
                  const isVerified = s.confidence >= 0.7 || s.source === 'assessment';
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
                          {isVerified && <span title="Verified competency" style={{ color: '#6366f1', fontSize: '0.85rem' }}>✓</span>}
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
                  <span className={`badge ${resumeStatus.resume_parsed ? 'badge-success' : 'badge-warning'}`}>
                    {resumeStatus.resume_parsed ? 'NLP Parsed ✓' : 'Processing...'}
                  </span>
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
    </div>
  );
}
