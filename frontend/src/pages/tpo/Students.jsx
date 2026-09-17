/**
 * TPO Students & Talent Pool Cohort Builder —
 * Advanced multi-criteria search, cohort builder, recruiter CSV exports,
 * and batch drive invitations.
 */

import { useState, useEffect, useCallback } from 'react';
import { tpoApi, placementApi } from '../../api/endpoints';

const DEPTS = ['CS', 'IT', 'ECE', 'ME', 'EEE'];
const GRAD_YEARS = [2024, 2025, 2026, 2027];

const STATUS_CFG = {
  placed:     { color: '#22c55e', bg: 'rgba(34,197,94,0.1)',  label: '✅ Placed' },
  unplaced:   { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', label: '○ Unplaced' },
  selected:   { color: '#22c55e', bg: 'rgba(34,197,94,0.1)',  label: '✅ Selected' },
  shortlisted:{ color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', label: '⭐ Shortlisted' },
  applied:    { color: '#6366f1', bg: 'rgba(99,102,241,0.1)', label: '📋 Applied' },
  in_progress:{ color: '#06b6d4', bg: 'rgba(6,182,212,0.1)', label: '⏳ In Progress' },
  unregistered:{ color: 'var(--text-muted)', bg: 'var(--bg-tertiary)', label: '○ Unregistered' },
};

function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export default function TPOStudents() {
  const [activeTab, setActiveTab] = useState('builder'); // 'builder' | 'cohorts'

  // Query Builder Filter State
  const [minCGPA, setMinCGPA] = useState(7.5);
  const [maxCGPA, setMaxCGPA] = useState(10.0);
  const [maxBacklogs, setMaxBacklogs] = useState(0);
  const [selectedBranches, setSelectedBranches] = useState(['CS', 'IT']);
  const [gradYear, setGradYear] = useState(2026);
  const [placementStatus, setPlacementStatus] = useState('any'); // 'any' | 'unplaced' | 'placed'
  const [mustHaveSkills, setMustHaveSkills] = useState(['Docker', 'Python']);
  const [mustSkillInput, setMustSkillInput] = useState('');
  const [anyOfSkills, setAnyOfSkills] = useState(['Kubernetes']);
  const [anySkillInput, setAnySkillInput] = useState('');

  // Results State
  const [students, setStudents] = useState([]);
  const [totalStudents, setTotalStudents] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Selection & Action Bar State
  const [selectedIds, setSelectedIds] = useState([]);
  const [filterPanelOpen, setFilterPanelOpen] = useState(true);

  // Modals
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [cohortName, setCohortName] = useState('');
  const [cohortDesc, setCohortDesc] = useState('');
  const [savingCohort, setSavingCohort] = useState(false);

  const [inviteModalOpen, setInviteModalOpen] = useState(false);
  const [drives, setDrives] = useState([]);
  const [selectedDriveId, setSelectedDriveId] = useState('');
  const [inviting, setInviting] = useState(false);
  const [activeCohortForInvite, setActiveCohortForInvite] = useState(null);

  // Saved Cohorts State
  const [savedCohorts, setSavedCohorts] = useState([]);
  const [cohortsLoading, setCohortsLoading] = useState(false);

  // UMS sync state
  const [syncingId, setSyncingId] = useState(null);

  // ─── Query Execution ─────────────────────────────────────────────
  const runQuery = useCallback(async (targetPage = 1) => {
    try {
      setLoading(true);
      setError(null);
      const payload = {
        min_cgpa: minCGPA ? parseFloat(minCGPA) : undefined,
        max_cgpa: maxCGPA ? parseFloat(maxCGPA) : undefined,
        max_backlogs: maxBacklogs !== '' ? parseInt(maxBacklogs, 10) : undefined,
        departments: selectedBranches.length > 0 ? selectedBranches : undefined,
        graduation_year: gradYear ? parseInt(gradYear, 10) : undefined,
        placement_status: placementStatus !== 'any' ? placementStatus : undefined,
        must_have_skills: mustHaveSkills.length > 0 ? mustHaveSkills : undefined,
        any_of_skills: anyOfSkills.length > 0 ? anyOfSkills : undefined,
      };

      const res = await tpoApi.queryStudents(payload, { page: targetPage, page_size: pageSize });
      const data = res.data;
      setStudents(data.students || []);
      setTotalStudents(data.total || 0);
      setPage(data.page || targetPage);
    } catch (err) {
      console.error('Talent query failed:', err);
      // Fallback to general getStudents if query endpoint fails
      try {
        const fbRes = await tpoApi.getStudents({ page: targetPage, per_page: pageSize });
        const list = fbRes.data?.data || fbRes.data || [];
        setStudents(list);
        setTotalStudents(fbRes.data?.meta?.total || list.length);
      } catch (fbErr) {
        setError('Failed to query students from database.');
      }
    } finally {
      setLoading(false);
    }
  }, [minCGPA, maxCGPA, maxBacklogs, selectedBranches, gradYear, placementStatus, mustHaveSkills, anyOfSkills, pageSize]);

  // Load Saved Cohorts
  const fetchCohorts = useCallback(async () => {
    try {
      setCohortsLoading(true);
      const res = await tpoApi.getCohorts();
      setSavedCohorts(res.data || []);
    } catch (err) {
      console.warn('Failed to load cohorts:', err);
    } finally {
      setCohortsLoading(false);
    }
  }, []);

  // Load active drives for invite dropdown
  const fetchDrives = useCallback(async () => {
    try {
      const res = await placementApi.getDrives({ status: 'upcoming' });
      const list = res.data?.data || res.data || [];
      setDrives(list);
      if (list.length > 0) setSelectedDriveId(list[0].id);
    } catch (err) {
      console.warn('Failed to load drives:', err);
    }
  }, []);

  useEffect(() => {
    runQuery(1);
    fetchCohorts();
    fetchDrives();
  }, [runQuery, fetchCohorts, fetchDrives]);

  // Skill Tag Handlers
  const addMustSkill = () => {
    const trimmed = mustSkillInput.trim();
    if (trimmed && !mustHaveSkills.includes(trimmed)) {
      setMustHaveSkills([...mustHaveSkills, trimmed]);
      setMustSkillInput('');
    }
  };
  const removeMustSkill = (skill) => {
    setMustHaveSkills(mustHaveSkills.filter(s => s !== skill));
  };

  const addAnySkill = () => {
    const trimmed = anySkillInput.trim();
    if (trimmed && !anyOfSkills.includes(trimmed)) {
      setAnyOfSkills([...anyOfSkills, trimmed]);
      setAnySkillInput('');
    }
  };
  const removeAnySkill = (skill) => {
    setAnyOfSkills(anyOfSkills.filter(s => s !== skill));
  };

  const toggleBranch = (branch) => {
    if (selectedBranches.includes(branch)) {
      setSelectedBranches(selectedBranches.filter(b => b !== branch));
    } else {
      setSelectedBranches([...selectedBranches, branch]);
    }
  };

  const resetFilters = () => {
    setMinCGPA(0);
    setMaxCGPA(10.0);
    setMaxBacklogs(0);
    setSelectedBranches(['CS', 'IT', 'ECE', 'ME', 'EEE']);
    setGradYear(2026);
    setPlacementStatus('any');
    setMustHaveSkills([]);
    setAnyOfSkills([]);
  };

  // Selection Checkbox Handlers
  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIds(students.map(s => s.id));
    } else {
      setSelectedIds([]);
    }
  };

  const toggleSelectStudent = (id) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter(i => i !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  // UMS sync
  const handleSyncUMS = async (student) => {
    try {
      setSyncingId(student.id);
      await tpoApi.syncUMS(student.roll_number);
      alert(`UMS sync completed successfully for ${student.roll_number}`);
      runQuery(page);
    } catch (err) {
      alert(`UMS sync failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setSyncingId(null);
    }
  };

  // Save Cohort Action
  const handleSaveCohortSubmit = async (e) => {
    e.preventDefault();
    if (!cohortName.trim()) return;
    try {
      setSavingCohort(true);
      const criteria = {
        min_cgpa: minCGPA,
        max_cgpa: maxCGPA,
        max_backlogs: maxBacklogs,
        branches: selectedBranches,
        graduation_year: gradYear,
        placement_status: placementStatus,
        must_have_skills: mustHaveSkills,
        any_of_skills: anyOfSkills,
      };
      await tpoApi.saveCohort({
        name: cohortName.trim(),
        description: cohortDesc.trim() || undefined,
        criteria,
        student_ids: selectedIds.length > 0 ? selectedIds : students.map(s => s.id),
      });
      alert(`Cohort "${cohortName}" saved successfully!`);
      setSaveModalOpen(false);
      setCohortName('');
      setCohortDesc('');
      fetchCohorts();
      setActiveTab('cohorts');
    } catch (err) {
      alert(`Failed to save cohort: ${err.response?.data?.detail || err.message}`);
    } finally {
      setSavingCohort(false);
    }
  };

  // Export CSV from Cohort
  const handleExportCohortCSV = async (cohort) => {
    try {
      const res = await tpoApi.exportCohortCSV(cohort.id);
      const safeName = cohort.name.replace(/[^a-zA-Z0-9_-]/g, '_');
      downloadBlob(new Blob([res.data], { type: 'text/csv' }), `cohort_${safeName}.csv`);
    } catch (err) {
      alert('Failed to export cohort CSV.');
    }
  };

  // Export CSV for currently selected students
  const handleExportSelectedCSV = () => {
    const selectedStudents = students.filter(s => selectedIds.includes(s.id));
    if (selectedStudents.length === 0) return;

    const headers = ['Roll Number', 'Name', 'Email', 'Branch', 'CGPA', 'Skills', 'Placement Status', 'Phone'];
    const rows = selectedStudents.map(s => [
      s.roll_number,
      `"${s.first_name} ${s.last_name}"`,
      s.email,
      s.department,
      s.cgpa ?? 'N/A',
      `"${(s.skills || []).join('; ')}"`,
      s.placement_status,
      s.phone || 'N/A'
    ]);
    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    downloadBlob(new Blob([csvContent], { type: 'text/csv' }), `selected_talent_${Date.now()}.csv`);
  };

  // Batch Invite to Drive
  const handleBatchInviteSubmit = async () => {
    if (!selectedDriveId) {
      alert('Please select an active recruitment drive.');
      return;
    }
    try {
      setInviting(true);
      if (activeCohortForInvite) {
        // Invite from saved cohort
        const res = await tpoApi.inviteCohortToDrive(activeCohortForInvite.id, selectedDriveId);
        alert(`Success! Batch invitation sent to ${res.data.invited_count} students for "${res.data.drive_title}".`);
      } else {
        // First save selected as temporary cohort or alert success
        const tempRes = await tpoApi.saveCohort({
          name: `Drive Invite Shortlist - ${new Date().toLocaleDateString()}`,
          description: 'Instant shortlist for campus drive invitation',
          criteria: {},
          student_ids: selectedIds,
        });
        const res = await tpoApi.inviteCohortToDrive(tempRes.data.id, selectedDriveId);
        alert(`Success! Batch invitation sent to ${res.data.invited_count} students for "${res.data.drive_title}".`);
        fetchCohorts();
      }
      setInviteModalOpen(false);
      setActiveCohortForInvite(null);
    } catch (err) {
      alert(`Batch invite failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setInviting(false);
    }
  };

  const handleArchiveCohort = async (cohortId) => {
    if (!window.confirm('Are you sure you want to archive this cohort?')) return;
    try {
      await tpoApi.archiveCohort(cohortId);
      fetchCohorts();
    } catch (err) {
      alert('Failed to archive cohort.');
    }
  };

  const allSelected = students.length > 0 && selectedIds.length === students.length;

  return (
    <div>
      {/* Page Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 700, color: 'var(--accent-primary)', textTransform: 'uppercase' }}>
              Corporate Recruitment Engine
            </span>
          </div>
          <h1>Talent Pool & Cohort Builder</h1>
          <p>Precision multi-criteria search, recruiter candidate shortlists, CSV exports, and batch invitations</p>
        </div>

        {/* Tab Toggle */}
        <div style={{ display: 'flex', background: 'var(--bg-tertiary)', borderRadius: 'var(--border-radius)', padding: 4, gap: 4 }}>
          <button
            className={`btn ${activeTab === 'builder' ? 'btn-primary' : ''}`}
            onClick={() => setActiveTab('builder')}
            style={{ height: 36, fontSize: 'var(--font-size-sm)', background: activeTab !== 'builder' ? 'transparent' : undefined }}
          >
            🔍 Talent Search & Builder
          </button>
          <button
            className={`btn ${activeTab === 'cohorts' ? 'btn-primary' : ''}`}
            onClick={() => setActiveTab('cohorts')}
            style={{ height: 36, fontSize: 'var(--font-size-sm)', background: activeTab !== 'cohorts' ? 'transparent' : undefined }}
          >
            📚 Saved Cohorts ({savedCohorts.length})
          </button>
        </div>
      </div>

      <div className="page-body">
        {/* ─── TAB 1: COHORT BUILDER ─────────────────────────────────── */}
        {activeTab === 'builder' && (
          <div style={{ display: 'grid', gridTemplateColumns: filterPanelOpen ? '320px 1fr' : '1fr', gap: 'var(--space-6)', alignItems: 'start' }}>
            
            {/* Filter Panel (Left) */}
            {filterPanelOpen && (
              <div className="card" style={{ padding: 'var(--space-5)', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ fontSize: 'var(--font-size-base)', fontWeight: 700 }}>Build Talent Cohort</h3>
                  <button
                    onClick={() => setFilterPanelOpen(false)}
                    style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 'var(--font-size-sm)' }}
                  >
                    ◀ Hide
                  </button>
                </div>

                {/* CGPA Range */}
                <div>
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    CGPA Range
                  </label>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-2)', marginTop: 4 }}>
                    <input
                      className="input"
                      type="number"
                      step="0.1"
                      min="0"
                      max="10"
                      placeholder="Min (e.g. 7.5)"
                      value={minCGPA}
                      onChange={(e) => setMinCGPA(e.target.value)}
                    />
                    <input
                      className="input"
                      type="number"
                      step="0.1"
                      min="0"
                      max="10"
                      placeholder="Max (10.0)"
                      value={maxCGPA}
                      onChange={(e) => setMaxCGPA(e.target.value)}
                    />
                  </div>
                </div>

                {/* Max Backlogs */}
                <div>
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Max Active Backlogs
                  </label>
                  <input
                    className="input"
                    type="number"
                    min="0"
                    style={{ marginTop: 4 }}
                    value={maxBacklogs}
                    onChange={(e) => setMaxBacklogs(e.target.value)}
                  />
                </div>

                {/* Branches */}
                <div>
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Branches
                  </label>
                  <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap', marginTop: 4 }}>
                    {DEPTS.map((b) => (
                      <label key={b} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 'var(--font-size-xs)', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={selectedBranches.includes(b)}
                          onChange={() => toggleBranch(b)}
                        />
                        {b}
                      </label>
                    ))}
                  </div>
                </div>

                {/* Graduation Year */}
                <div>
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Graduation Year
                  </label>
                  <select
                    className="input"
                    style={{ marginTop: 4 }}
                    value={gradYear}
                    onChange={(e) => setGradYear(e.target.value)}
                  >
                    {GRAD_YEARS.map(y => (
                      <option key={y} value={y}>{y} Batch</option>
                    ))}
                  </select>
                </div>

                {/* Placement Status */}
                <div>
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Placement Status
                  </label>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 4, fontSize: 'var(--font-size-xs)' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                      <input
                        type="radio"
                        name="placement_status"
                        checked={placementStatus === 'any'}
                        onChange={() => setPlacementStatus('any')}
                      />
                      Any Status
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                      <input
                        type="radio"
                        name="placement_status"
                        checked={placementStatus === 'unplaced'}
                        onChange={() => setPlacementStatus('unplaced')}
                      />
                      Unplaced Only
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                      <input
                        type="radio"
                        name="placement_status"
                        checked={placementStatus === 'placed'}
                        onChange={() => setPlacementStatus('placed')}
                      />
                      Placed Candidates
                    </label>
                  </div>
                </div>

                {/* Must-Have Skills */}
                <div>
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Must-Have Skills (AND)
                  </label>
                  <div style={{ display: 'flex', gap: 4, marginTop: 4 }}>
                    <input
                      className="input"
                      placeholder="e.g. Docker"
                      value={mustSkillInput}
                      onChange={(e) => setMustSkillInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addMustSkill())}
                      style={{ fontSize: 'var(--font-size-xs)' }}
                    />
                    <button className="btn btn-secondary" type="button" onClick={addMustSkill} style={{ padding: '0 10px', height: 36 }}>
                      +
                    </button>
                  </div>
                  <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 6 }}>
                    {mustHaveSkills.map(s => (
                      <span key={s} className="badge badge-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                        {s}
                        <span onClick={() => removeMustSkill(s)} style={{ cursor: 'pointer', fontWeight: 800 }}>×</span>
                      </span>
                    ))}
                  </div>
                </div>

                {/* Any-Of Skills */}
                <div>
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Any-Of Skills (OR)
                  </label>
                  <div style={{ display: 'flex', gap: 4, marginTop: 4 }}>
                    <input
                      className="input"
                      placeholder="e.g. Kubernetes"
                      value={anySkillInput}
                      onChange={(e) => setAnySkillInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addAnySkill())}
                      style={{ fontSize: 'var(--font-size-xs)' }}
                    />
                    <button className="btn btn-secondary" type="button" onClick={addAnySkill} style={{ padding: '0 10px', height: 36 }}>
                      +
                    </button>
                  </div>
                  <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 6 }}>
                    {anyOfSkills.map(s => (
                      <span key={s} className="badge badge-success" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                        {s}
                        <span onClick={() => removeAnySkill(s)} style={{ cursor: 'pointer', fontWeight: 800 }}>×</span>
                      </span>
                    ))}
                  </div>
                </div>

                {/* Query Actions */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', marginTop: 'var(--space-2)' }}>
                  <button className="btn btn-primary" onClick={() => runQuery(1)} disabled={loading}>
                    {loading ? 'Executing Query...' : '🔍 Run Query'}
                  </button>
                  <button className="btn btn-secondary" onClick={resetFilters}>
                    🔄 Reset Filters
                  </button>
                </div>
              </div>
            )}

            {/* Results Area (Right) */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                  {!filterPanelOpen && (
                    <button className="btn btn-secondary" onClick={() => setFilterPanelOpen(true)} style={{ height: 34, fontSize: 'var(--font-size-xs)' }}>
                      ▶ Show Filters
                    </button>
                  )}
                  <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600 }}>
                    {loading ? 'Searching talent pool...' : `${totalStudents} matching students found`}
                  </span>
                </div>

                {selectedIds.length > 0 && (
                  <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--accent-primary)', fontWeight: 700 }}>
                    {selectedIds.length} candidate{selectedIds.length > 1 ? 's' : ''} selected
                  </span>
                )}
              </div>

              {error && (
                <div className="card" style={{ padding: 'var(--space-4)', color: 'var(--accent-danger)', background: 'rgba(239,68,68,0.08)' }}>
                  {error}
                </div>
              )}

              {/* Table */}
              <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th style={{ width: 40, textAlign: 'center' }}>
                          <input
                            type="checkbox"
                            checked={allSelected}
                            onChange={handleSelectAll}
                            disabled={students.length === 0}
                          />
                        </th>
                        <th>Student Candidate</th>
                        <th>Roll Number</th>
                        <th>Branch</th>
                        <th>CGPA</th>
                        <th>Matched Skills</th>
                        <th>Status</th>
                        <th style={{ textAlign: 'right' }}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {students.map((s) => {
                        const isSelected = selectedIds.includes(s.id);
                        const statusKey = (s.placement_status || 'unplaced').toLowerCase();
                        const stCfg = STATUS_CFG[statusKey] || STATUS_CFG.unplaced;
                        const fullName = `${s.first_name || ''} ${s.last_name || ''}`.trim() || 'Candidate';

                        return (
                          <tr key={s.id} style={{ background: isSelected ? 'rgba(99, 102, 241, 0.05)' : undefined }}>
                            <td style={{ textAlign: 'center' }}>
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => toggleSelectStudent(s.id)}
                              />
                            </td>
                            <td>
                              <div style={{ fontWeight: 600 }}>{fullName}</div>
                              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{s.email}</div>
                            </td>
                            <td style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--font-size-xs)' }}>
                              {s.roll_number}
                            </td>
                            <td>
                              <span className="badge badge-primary">{s.department || 'CS'}</span>
                            </td>
                            <td style={{ fontWeight: 700 }}>
                              {s.cgpa ? parseFloat(s.cgpa).toFixed(2) : '—'}
                            </td>
                            <td>
                              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', maxWidth: 260 }}>
                                {(s.skills || []).slice(0, 3).map(sk => (
                                  <span key={sk} style={{ padding: '1px 6px', borderRadius: 4, background: 'var(--bg-tertiary)', fontSize: 11 }}>
                                    {sk}
                                  </span>
                                ))}
                                {(s.skills?.length || 0) > 3 && (
                                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                                    +{(s.skills?.length || 0) - 3}
                                  </span>
                                )}
                              </div>
                            </td>
                            <td>
                              <span
                                style={{
                                  padding: '2px 8px',
                                  borderRadius: 999,
                                  fontSize: 'var(--font-size-xs)',
                                  fontWeight: 600,
                                  background: stCfg.bg,
                                  color: stCfg.color,
                                }}
                              >
                                {stCfg.label}
                              </span>
                            </td>
                            <td style={{ textAlign: 'right' }}>
                              <button
                                className="btn btn-secondary"
                                onClick={() => handleSyncUMS(s)}
                                disabled={syncingId === s.id}
                                style={{ padding: '2px 8px', fontSize: 11, height: 'auto' }}
                              >
                                {syncingId === s.id ? 'Syncing...' : '🔄 UMS'}
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {students.length === 0 && !loading && (
                  <div style={{ textAlign: 'center', padding: 'var(--space-12)', color: 'var(--text-muted)' }}>
                    <div style={{ fontSize: '2rem', marginBottom: 8 }}>🔍</div>
                    <h3>No candidates matched this query criteria</h3>
                    <p style={{ fontSize: 'var(--font-size-sm)', marginTop: 4 }}>
                      Try relaxing CGPA thresholds, clearing must-have skills, or enabling additional departments.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ─── TAB 2: SAVED COHORTS ──────────────────────────────────── */}
        {activeTab === 'cohorts' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2>Saved Talent Cohorts</h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                  Pre-screened candidate pools ready for distribution to corporate recruiters
                </p>
              </div>
              <button
                className="btn btn-primary"
                onClick={() => setActiveTab('builder')}
              >
                + Build New Cohort
              </button>
            </div>

            {cohortsLoading ? (
              <div className="card" style={{ textAlign: 'center', padding: 'var(--space-12)' }}>
                Loading saved cohorts...
              </div>
            ) : savedCohorts.length > 0 ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 'var(--space-5)' }}>
                {savedCohorts.map((cohort) => (
                  <div key={cohort.id} className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <h3 style={{ fontSize: 'var(--font-size-base)', fontWeight: 700 }}>{cohort.name}</h3>
                        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 2 }}>
                          Created: {cohort.created_at ? new Date(cohort.created_at).toLocaleDateString() : 'Recent'}
                        </div>
                      </div>
                      <span className="badge badge-primary" style={{ fontSize: 'var(--font-size-xs)' }}>
                        👥 {cohort.student_count} Candidates
                      </span>
                    </div>

                    <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', margin: 0, minHeight: 36 }}>
                      {cohort.description || 'Pre-screened talent group generated from precision query criteria.'}
                    </p>

                    {/* Criteria snapshot */}
                    {cohort.criteria && (
                      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        {cohort.criteria.min_cgpa && (
                          <span style={{ fontSize: 10, padding: '1px 6px', background: 'var(--bg-tertiary)', borderRadius: 4 }}>
                            CGPA ≥ {cohort.criteria.min_cgpa}
                          </span>
                        )}
                        {cohort.criteria.branches && (
                          <span style={{ fontSize: 10, padding: '1px 6px', background: 'var(--bg-tertiary)', borderRadius: 4 }}>
                            {cohort.criteria.branches.join(', ')}
                          </span>
                        )}
                        {cohort.criteria.must_have_skills?.length > 0 && (
                          <span style={{ fontSize: 10, padding: '1px 6px', background: 'rgba(99,102,241,0.1)', color: 'var(--accent-primary)', borderRadius: 4 }}>
                            Skills: {cohort.criteria.must_have_skills.join(', ')}
                          </span>
                        )}
                      </div>
                    )}

                    {/* Actions */}
                    <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-2)', borderTop: '1px solid var(--border-color)', paddingTop: 'var(--space-3)' }}>
                      <button
                        className="btn btn-secondary"
                        onClick={() => handleExportCohortCSV(cohort)}
                        style={{ flex: 1, height: 32, fontSize: 'var(--font-size-xs)' }}
                      >
                        📥 Export CSV
                      </button>
                      <button
                        className="btn btn-primary"
                        onClick={() => {
                          setActiveCohortForInvite(cohort);
                          setInviteModalOpen(true);
                        }}
                        style={{ flex: 1, height: 32, fontSize: 'var(--font-size-xs)' }}
                      >
                        📩 Invite to Drive
                      </button>
                      <button
                        onClick={() => handleArchiveCohort(cohort.id)}
                        style={{ background: 'none', border: 'none', color: 'var(--accent-danger)', cursor: 'pointer', padding: '0 8px', fontSize: 14 }}
                        title="Archive cohort"
                      >
                        🗑
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="card" style={{ textAlign: 'center', padding: 'var(--space-12)', color: 'var(--text-muted)' }}>
                <div style={{ fontSize: '2rem', marginBottom: 8 }}>📚</div>
                <h3>No saved talent cohorts yet</h3>
                <p style={{ fontSize: 'var(--font-size-sm)', marginTop: 4 }}>
                  Use the Query Builder to filter candidates and click "Save as Cohort" to build your first recruiter list.
                </p>
                <button
                  className="btn btn-primary"
                  onClick={() => setActiveTab('builder')}
                  style={{ marginTop: 'var(--space-4)' }}
                >
                  Go to Query Builder
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ─── STICKY BOTTOM ACTION BAR (When candidates selected) ─── */}
      {selectedIds.length > 0 && activeTab === 'builder' && (
        <div
          style={{
            position: 'fixed',
            bottom: 24,
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'var(--bg-card)',
            border: '2px solid var(--accent-primary)',
            borderRadius: 'var(--border-radius-lg)',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)',
            padding: 'var(--space-3) var(--space-6)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-4)',
            zIndex: 900,
            animation: 'fadeIn 0.2s ease',
          }}
        >
          <span style={{ fontWeight: 700, fontSize: 'var(--font-size-sm)' }}>
            🎯 {selectedIds.length} candidate{selectedIds.length > 1 ? 's' : ''} selected
          </span>
          <button
            className="btn btn-primary"
            onClick={() => setSaveModalOpen(true)}
            style={{ height: 36, fontSize: 'var(--font-size-xs)' }}
          >
            💾 Save as Cohort
          </button>
          <button
            className="btn btn-secondary"
            onClick={handleExportSelectedCSV}
            style={{ height: 36, fontSize: 'var(--font-size-xs)' }}
          >
            📥 Export CSV
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => {
              setActiveCohortForInvite(null);
              setInviteModalOpen(true);
            }}
            style={{ height: 36, fontSize: 'var(--font-size-xs)' }}
          >
            📩 Invite to Drive
          </button>
          <button
            onClick={() => setSelectedIds([])}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 'var(--font-size-xs)' }}
          >
            ✕ Deselect
          </button>
        </div>
      )}

      {/* ─── MODAL: SAVE AS COHORT ──────────────────────────────────── */}
      {saveModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.65)',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 'var(--space-4)',
          }}
          onClick={() => setSaveModalOpen(false)}
        >
          <div
            className="card"
            style={{ width: '100%', maxWidth: 480, padding: 'var(--space-6)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700, marginBottom: 'var(--space-4)' }}>
              Save as Recruiter Cohort
            </h3>
            <form onSubmit={handleSaveCohortSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div>
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Cohort Name *</label>
                <input
                  className="input"
                  placeholder="e.g. Tier-1 Product Companies 2026"
                  value={cohortName}
                  onChange={(e) => setCohortName(e.target.value)}
                  required
                  style={{ marginTop: 4 }}
                />
              </div>

              <div>
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Description (Optional)</label>
                <textarea
                  className="input"
                  rows={3}
                  placeholder="e.g. CS/IT students with CGPA > 8.0, proficient in Docker & React with 0 backlogs."
                  value={cohortDesc}
                  onChange={(e) => setCohortDesc(e.target.value)}
                  style={{ marginTop: 4 }}
                />
              </div>

              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>
                Target size: <strong>{selectedIds.length > 0 ? selectedIds.length : totalStudents}</strong> students
              </div>

              <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-2)' }}>
                <button type="submit" className="btn btn-primary" disabled={savingCohort} style={{ flex: 1 }}>
                  {savingCohort ? 'Saving...' : 'Confirm & Save Cohort'}
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => setSaveModalOpen(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ─── MODAL: INVITE TO DRIVE ─────────────────────────────────── */}
      {inviteModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.65)',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 'var(--space-4)',
          }}
          onClick={() => setInviteModalOpen(false)}
        >
          <div
            className="card"
            style={{ width: '100%', maxWidth: 480, padding: 'var(--space-6)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700, marginBottom: 'var(--space-4)' }}>
              Batch Invite Candidates to Campus Drive
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div>
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Select Active Drive *</label>
                <select
                  className="input"
                  style={{ marginTop: 4 }}
                  value={selectedDriveId}
                  onChange={(e) => setSelectedDriveId(e.target.value)}
                >
                  {drives.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.company?.name || d.company || 'Recruiter'} — {d.title} ({d.roles_offered?.[0] || 'SDE'})
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ padding: 'var(--space-3)', background: 'var(--bg-tertiary)', borderRadius: 'var(--border-radius)', fontSize: 'var(--font-size-xs)' }}>
                ℹ️ This will dispatch direct notifications to{' '}
                <strong>{activeCohortForInvite ? activeCohortForInvite.student_count : selectedIds.length}</strong> candidate(s)
                inviting them to submit their application before drive registration closes.
              </div>

              <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-2)' }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleBatchInviteSubmit}
                  disabled={inviting || !selectedDriveId}
                  style={{ flex: 1 }}
                >
                  {inviting ? 'Dispatching Invites...' : 'Dispatch Invitations'}
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => setInviteModalOpen(false)}>
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
