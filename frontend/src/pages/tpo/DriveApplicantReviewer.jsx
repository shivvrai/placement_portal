/**
 * DriveApplicantReviewer — Full-width interactive applicant review drawer for TPOs.
 * Allows moving candidates through interview stages, scheduling interviews,
 * recording offers, rejecting candidates, and filtering candidate pipelines.
 */

import { useState, useEffect, useMemo } from 'react';
import { placementApi } from '../../api/endpoints';
import OfferModal from './OfferModal';

const STAGES = [
  'Online Assessment (OA)',
  'Technical Interview 1',
  'Technical Interview 2',
  'HR Interview',
  'Final Round',
];

const STATUS_CONFIG = {
  applied:     { label: 'Applied',      color: '#6366f1', bg: 'rgba(99,102,241,0.12)' },
  shortlisted: { label: 'Shortlisted',  color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  in_progress: { label: 'In Progress',  color: '#06b6d4', bg: 'rgba(6,182,212,0.12)' },
  selected:    { label: 'Selected ✓',   color: '#22c55e', bg: 'rgba(34,197,94,0.12)' },
  rejected:    { label: 'Rejected ✗',   color: '#ef4444', bg: 'rgba(239,68,68,0.12)' },
  withdrawn:   { label: 'Withdrawn',    color: 'var(--text-muted)', bg: 'var(--bg-tertiary)' },
};

export default function DriveApplicantReviewer({ drive, onClose, onDriveUpdated }) {
  const [applicants, setApplicants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [stageFilter, setStageFilter] = useState('all');
  const [branchFilter, setBranchFilter] = useState('all');
  const [cgpaFilter, setCgpaFilter] = useState('all');

  // Sub-modal states
  const [activeMenuAppId, setActiveMenuAppId] = useState(null);
  const [advanceModalApp, setAdvanceModalApp] = useState(null);
  const [scheduleModalApp, setScheduleModalApp] = useState(null);
  const [feedbackModalApp, setFeedbackModalApp] = useState(null);
  const [rejectModalApp, setRejectModalApp] = useState(null);
  const [offerModalApp, setOfferModalApp] = useState(null);

  // Form states for mini-modals
  const [stageForm, setStageForm] = useState({
    stage: 'Technical Interview 1',
    status: 'in_progress',
    scheduled_at: '',
    meeting_link: '',
    venue: '',
    feedback: '',
  });

  const [scheduleForm, setScheduleForm] = useState({
    scheduled_at: '',
    meeting_link: '',
    venue: '',
  });

  const [feedbackText, setFeedbackText] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  // Bulk selection and Kanban state
  const [selectedApps, setSelectedApps] = useState(new Set());
  const [viewMode, setViewMode] = useState('table'); // 'table' | 'kanban'
  const [dragOverCol, setDragOverCol] = useState(null);
  const [draggedAppId, setDraggedAppId] = useState(null);

  // Auto-shortlist wizard state
  const [shortlistWizardOpen, setShortlistWizardOpen] = useState(false);
  const [wizardStep, setWizardStep] = useState(1);
  const [wizardCriteria, setWizardCriteria] = useState({
    min_cgpa: drive?.min_cgpa || 7.0,
    max_backlogs: drive?.max_backlogs ?? 0,
    required_skills: [],
    eligible_departments: drive?.eligible_departments || [],
    min_projects: null,
    has_resume: true,
    min_match_score: 60,
  });
  const [newSkillInput, setNewSkillInput] = useState('');
  const [dryRunResult, setDryRunResult] = useState(null);
  const [executeResult, setExecuteResult] = useState(null);
  const [wizardLoading, setWizardLoading] = useState(false);

  // Bulk action state
  const [bulkConfirmAction, setBulkConfirmAction] = useState(null);
  const [bulkActionLoading, setBulkActionLoading] = useState(false);

  const toggleSelectAll = () => {
    if (selectedApps.size === filtered.length) {
      setSelectedApps(new Set());
    } else {
      setSelectedApps(new Set(filtered.map(a => a.application_id)));
    }
  };

  const toggleSelectApp = (appId) => {
    const s = new Set(selectedApps);
    if (s.has(appId)) s.delete(appId);
    else s.add(appId);
    setSelectedApps(s);
  };

  const executeBulkAction = async (action) => {
    setBulkActionLoading(true);
    const ids = Array.from(selectedApps);
    const statusMap = {
      shortlist: 'shortlisted',
      next_round: 'in_progress',
      reject: 'rejected',
    };
    try {
      await placementApi.bulkUpdateStatus(drive.id, ids, statusMap[action]);
      await loadApplicants();
      setSelectedApps(new Set());
      setBulkConfirmAction(null);
    } catch (err) {
      console.error('Bulk action error:', err);
      alert('Failed to execute bulk action: ' + (err.response?.data?.detail || 'Error'));
    } finally {
      setBulkActionLoading(false);
    }
  };

  const handleKanbanDrop = async (appId, targetStatus) => {
    try {
      await placementApi.overrideApplication(drive.id, appId, targetStatus, 'Moved via Kanban drag-and-drop');
      updateLocalApplicant(appId, { status: targetStatus });
      if (onDriveUpdated) onDriveUpdated();
    } catch (err) {
      console.error('Kanban status update failed:', err);
      await loadApplicants();
    }
  };

  const runDryRun = async () => {
    setWizardLoading(true);
    try {
      const res = await placementApi.shortlistDryRun(drive.id, wizardCriteria);
      setDryRunResult(res.data);
      setWizardStep(2);
    } catch (err) {
      alert('Dry-run failed: ' + (err.response?.data?.detail || 'Error'));
    } finally {
      setWizardLoading(false);
    }
  };

  const runExecuteShortlist = async () => {
    setWizardLoading(true);
    try {
      const res = await placementApi.shortlistExecute(drive.id, wizardCriteria);
      setExecuteResult(res.data);
      setWizardStep(3);
      await loadApplicants();
      if (onDriveUpdated) onDriveUpdated();
    } catch (err) {
      alert('Execution failed: ' + (err.response?.data?.detail || 'Error'));
    } finally {
      setWizardLoading(false);
    }
  };

  // Load applicants
  const loadApplicants = async () => {
    if (!drive?.id) return;
    try {
      setLoading(true);
      setError(null);
      const res = await placementApi.getAllApplicants(drive.id);
      setApplicants(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error('Failed to load drive applicants:', err);
      setError('Failed to fetch applicants. Please check the backend connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApplicants();
  }, [drive?.id]);

  // Live Stats Bar Calculations
  const stats = useMemo(() => {
    return {
      total: applicants.length,
      shortlisted: applicants.filter(a => a.status === 'shortlisted').length,
      in_progress: applicants.filter(a => a.status === 'in_progress').length,
      selected: applicants.filter(a => a.status === 'selected').length,
      rejected: applicants.filter(a => a.status === 'rejected').length,
      applied: applicants.filter(a => a.status === 'applied').length,
    };
  }, [applicants]);

  // Available Branches
  const allBranches = useMemo(() => {
    const set = new Set();
    applicants.forEach(a => {
      if (a.department) set.add(a.department);
    });
    return Array.from(set);
  }, [applicants]);

  // Filtered applicants
  const filtered = useMemo(() => {
    return applicants.filter(a => {
      // Search
      if (search.trim()) {
        const q = search.toLowerCase();
        const fullName = `${a.first_name || ''} ${a.last_name || ''}`.toLowerCase();
        const roll = (a.roll_number || '').toLowerCase();
        if (!fullName.includes(q) && !roll.includes(q)) return false;
      }

      // Status
      if (statusFilter !== 'all' && a.status !== statusFilter) return false;

      // Stage
      if (stageFilter !== 'all') {
        if (stageFilter === 'none' && a.current_stage) return false;
        if (stageFilter !== 'none' && (!a.current_stage || !a.current_stage.toLowerCase().includes(stageFilter.toLowerCase()))) return false;
      }

      // Branch
      if (branchFilter !== 'all' && a.department !== branchFilter) return false;

      // CGPA
      if (cgpaFilter !== 'all') {
        const min = parseFloat(cgpaFilter);
        if ((a.cgpa ?? 0) < min) return false;
      }

      return true;
    });
  }, [applicants, search, statusFilter, stageFilter, branchFilter, cgpaFilter]);

  // Helper to update local applicant row
  const updateLocalApplicant = (appId, updates) => {
    setApplicants(prev => prev.map(a => (a.application_id === appId ? { ...a, ...updates } : a)));
  };

  // Submit Stage Advance
  const handleAdvanceSubmit = async (e) => {
    e.preventDefault();
    if (!advanceModalApp) return;
    try {
      setActionLoading(true);
      const payload = {
        current_stage: stageForm.stage,
        status: stageForm.status,
        stage_status: stageForm.status === 'selected' ? 'passed' : 'scheduled',
        scheduled_at: stageForm.scheduled_at ? new Date(stageForm.scheduled_at).toISOString() : null,
        meeting_link: stageForm.meeting_link.trim() || null,
        venue: stageForm.venue.trim() || null,
        feedback: stageForm.feedback.trim() || null,
      };

      await placementApi.updateApplicationStage(drive.id, advanceModalApp.application_id, payload);

      updateLocalApplicant(advanceModalApp.application_id, {
        current_stage: stageForm.stage,
        status: stageForm.status,
        feedback: payload.feedback || advanceModalApp.feedback,
      });

      const movedToSelected = stageForm.status === 'selected';
      const targetApp = advanceModalApp;
      setAdvanceModalApp(null);

      // If moved to selected, auto-prompt offer recording modal
      if (movedToSelected) {
        setOfferModalApp(targetApp);
      }
      if (onDriveUpdated) onDriveUpdated();
    } catch (err) {
      console.error('Failed to advance candidate stage:', err);
      alert(err.response?.data?.detail || 'Failed to update candidate stage.');
    } finally {
      setActionLoading(false);
    }
  };

  // Submit Interview Schedule
  const handleScheduleSubmit = async (e) => {
    e.preventDefault();
    if (!scheduleModalApp) return;
    try {
      setActionLoading(true);
      const payload = {
        scheduled_at: scheduleForm.scheduled_at ? new Date(scheduleForm.scheduled_at).toISOString() : null,
        meeting_link: scheduleForm.meeting_link.trim() || null,
        venue: scheduleForm.venue.trim() || null,
        stage_status: 'scheduled',
      };

      await placementApi.updateApplicationStage(drive.id, scheduleModalApp.application_id, payload);

      updateLocalApplicant(scheduleModalApp.application_id, {
        status: scheduleModalApp.status === 'applied' ? 'in_progress' : scheduleModalApp.status,
      });

      setScheduleModalApp(null);
      if (onDriveUpdated) onDriveUpdated();
    } catch (err) {
      console.error('Failed to schedule interview:', err);
      alert(err.response?.data?.detail || 'Failed to schedule interview.');
    } finally {
      setActionLoading(false);
    }
  };

  // Submit Internal Feedback
  const handleFeedbackSubmit = async (e) => {
    e.preventDefault();
    if (!feedbackModalApp) return;
    try {
      setActionLoading(true);
      const payload = {
        feedback: feedbackText.trim(),
      };

      await placementApi.updateApplicationStage(drive.id, feedbackModalApp.application_id, payload);

      updateLocalApplicant(feedbackModalApp.application_id, {
        feedback: feedbackText.trim(),
      });

      setFeedbackModalApp(null);
    } catch (err) {
      console.error('Failed to save feedback:', err);
      alert('Failed to save feedback.');
    } finally {
      setActionLoading(false);
    }
  };

  // Submit Reject Candidate
  const handleRejectSubmit = async () => {
    if (!rejectModalApp) return;
    try {
      setActionLoading(true);
      const payload = {
        status: 'rejected',
        stage_status: 'failed',
        feedback: rejectReason.trim() || 'Candidate was not selected for further rounds.',
      };

      await placementApi.updateApplicationStage(drive.id, rejectModalApp.application_id, payload);

      updateLocalApplicant(rejectModalApp.application_id, {
        status: 'rejected',
        feedback: payload.feedback,
      });

      setRejectModalApp(null);
      if (onDriveUpdated) onDriveUpdated();
    } catch (err) {
      console.error('Failed to reject candidate:', err);
      alert(err.response?.data?.detail || 'Failed to reject candidate.');
    } finally {
      setActionLoading(false);
    }
  };

  // Offer success handler
  const handleOfferRecorded = (offerData) => {
    if (offerModalApp) {
      updateLocalApplicant(offerModalApp.application_id, {
        status: 'selected',
        offer_ctc_lpa: offerData.offer_ctc_lpa,
        offer_designation: offerData.offer_designation,
        offer_fixed_lpa: offerData.offer_fixed_lpa,
        offer_variable_lpa: offerData.offer_variable_lpa,
      });
    }
    if (onDriveUpdated) onDriveUpdated();
  };

  const companyName = drive.company?.name || drive.company || 'Placement Drive';

  return (
    <div
      style={{
        position: 'fixed', inset: 0,
        background: 'rgba(5, 8, 18, 0.7)',
        backdropFilter: 'blur(6px)',
        zIndex: 1050,
        display: 'flex', justifyContent: 'flex-end',
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%', maxWidth: '1180px',
          height: '100vh',
          background: 'var(--bg-secondary)',
          borderLeft: '1px solid var(--border-color)',
          boxShadow: '-16px 0 50px rgba(0,0,0,0.6)',
          display: 'flex', flexDirection: 'column',
          animation: 'slideInRight 0.25s ease-out',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Top Header */}
        <div style={{
          padding: 'var(--space-5) var(--space-8)',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          background: 'var(--bg-card)',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: '1.4rem' }}>📋</span>
              <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                Applicant Review: {companyName}
              </h2>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-xs)', marginTop: 2, margin: 0 }}>
              Role: {drive.title} {drive.salary_ctc ? `· ₹${drive.salary_ctc} LPA` : ''}
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button
              className="btn btn-primary"
              style={{ fontSize: '0.85rem', padding: '6px 14px', display: 'flex', alignItems: 'center', gap: 6 }}
              onClick={() => {
                setShortlistWizardOpen(true);
                setWizardStep(1);
                setDryRunResult(null);
                setExecuteResult(null);
              }}
            >
              <span>⚡</span> Auto-Shortlist Engine
            </button>

            <div style={{ display: 'flex', border: '1px solid var(--border-color)', borderRadius: 8, overflow: 'hidden' }}>
              <button
                type="button"
                onClick={() => setViewMode('table')}
                style={{
                  padding: '6px 12px', border: 'none', cursor: 'pointer', fontSize: '0.82rem', fontWeight: 600,
                  background: viewMode === 'table' ? 'var(--primary)' : 'var(--bg-tertiary)',
                  color: viewMode === 'table' ? '#fff' : 'var(--text-secondary)',
                }}
              >
                📋 Table
              </button>
              <button
                type="button"
                onClick={() => setViewMode('kanban')}
                style={{
                  padding: '6px 12px', border: 'none', cursor: 'pointer', fontSize: '0.82rem', fontWeight: 600,
                  background: viewMode === 'kanban' ? 'var(--primary)' : 'var(--bg-tertiary)',
                  color: viewMode === 'kanban' ? '#fff' : 'var(--text-secondary)',
                }}
              >
                📊 Kanban Board
              </button>
            </div>

            <button
              onClick={onClose}
              style={{
                background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
                borderRadius: '50%', width: 36, height: 36, display: 'flex',
                alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
                color: 'var(--text-secondary)', fontSize: '1.2rem',
              }}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Live Stats Summary Bar */}
        <div style={{
          padding: '12px var(--space-8)',
          background: 'var(--bg-primary)',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex', flexWrap: 'wrap', gap: 'var(--space-6)',
          alignItems: 'center', fontSize: 'var(--font-size-sm)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ color: 'var(--text-muted)' }}>Total Applicants:</span>
            <strong style={{ color: 'var(--text-primary)' }}>{stats.total}</strong>
          </div>
          <span style={{ color: 'var(--border-color)' }}>|</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#f59e0b' }} />
            <span style={{ color: 'var(--text-muted)' }}>Shortlisted:</span>
            <strong style={{ color: '#f59e0b' }}>{stats.shortlisted}</strong>
          </div>
          <span style={{ color: 'var(--border-color)' }}>|</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#06b6d4' }} />
            <span style={{ color: 'var(--text-muted)' }}>In Progress:</span>
            <strong style={{ color: '#06b6d4' }}>{stats.in_progress}</strong>
          </div>
          <span style={{ color: 'var(--border-color)' }}>|</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#22c55e' }} />
            <span style={{ color: 'var(--text-muted)' }}>Selected:</span>
            <strong style={{ color: '#22c55e' }}>{stats.selected}</strong>
          </div>
          <span style={{ color: 'var(--border-color)' }}>|</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#ef4444' }} />
            <span style={{ color: 'var(--text-muted)' }}>Rejected:</span>
            <strong style={{ color: '#ef4444' }}>{stats.rejected}</strong>
          </div>
        </div>

        {/* Bulk Action Toolbar */}
        {selectedApps.size > 0 && (
          <div style={{
            padding: '10px var(--space-8)',
            background: 'rgba(99, 102, 241, 0.12)',
            borderBottom: '1px solid rgba(99, 102, 241, 0.3)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>✓ {selectedApps.size} candidate(s) selected</span>
              <button
                type="button"
                className="btn btn-ghost"
                style={{ fontSize: '0.75rem', height: 24, padding: '0 8px' }}
                onClick={() => setSelectedApps(new Set())}
              >
                Deselect
              </button>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ fontSize: '0.8rem', padding: '4px 12px', borderColor: '#f59e0b', color: '#f59e0b' }}
                onClick={() => setBulkConfirmAction('shortlist')}
              >
                ✓ Shortlist Selected
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ fontSize: '0.8rem', padding: '4px 12px', borderColor: '#06b6d4', color: '#06b6d4' }}
                onClick={() => setBulkConfirmAction('next_round')}
              >
                ➡️ Advance to Tech Round
              </button>
              <button
                type="button"
                className="btn btn-ghost"
                style={{ fontSize: '0.8rem', padding: '4px 12px', color: '#ef4444', border: '1px solid rgba(239, 68, 68, 0.4)' }}
                onClick={() => setBulkConfirmAction('reject')}
              >
                ❌ Reject Selected
              </button>
            </div>
          </div>
        )}

        {/* Filters Toolbar */}
        <div style={{
          padding: 'var(--space-4) var(--space-8)',
          background: 'var(--bg-secondary)',
          borderBottom: '1px solid var(--border-color)',
          display: 'grid', gridTemplateColumns: '1.8fr 1fr 1fr 1fr 1fr',
          gap: 'var(--space-3)', alignItems: 'center',
        }}>
          {/* Search */}
          <div style={{ position: 'relative' }}>
            <input
              className="input"
              style={{ paddingLeft: 32, height: 36, fontSize: 'var(--font-size-xs)' }}
              placeholder="🔍 Search student name or roll #..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>

          {/* Status Filter */}
          <select
            className="input"
            style={{ height: 36, fontSize: 'var(--font-size-xs)' }}
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
          >
            <option value="all">All Statuses ({applicants.length})</option>
            <option value="applied">Applied ({stats.applied})</option>
            <option value="shortlisted">Shortlisted ({stats.shortlisted})</option>
            <option value="in_progress">In Progress ({stats.in_progress})</option>
            <option value="selected">Selected ({stats.selected})</option>
            <option value="rejected">Rejected ({stats.rejected})</option>
          </select>

          {/* Stage Filter */}
          <select
            className="input"
            style={{ height: 36, fontSize: 'var(--font-size-xs)' }}
            value={stageFilter}
            onChange={e => setStageFilter(e.target.value)}
          >
            <option value="all">All Stages</option>
            <option value="OA">Online Assessment (OA)</option>
            <option value="Technical Interview 1">Tech Round 1</option>
            <option value="Technical Interview 2">Tech Round 2</option>
            <option value="HR">HR Round</option>
            <option value="Final">Final Round</option>
            <option value="none">No Stage Set</option>
          </select>

          {/* Branch Filter */}
          <select
            className="input"
            style={{ height: 36, fontSize: 'var(--font-size-xs)' }}
            value={branchFilter}
            onChange={e => setBranchFilter(e.target.value)}
          >
            <option value="all">All Branches</option>
            {allBranches.map(b => (
              <option key={b} value={b}>{b}</option>
            ))}
          </select>

          {/* CGPA Filter */}
          <select
            className="input"
            style={{ height: 36, fontSize: 'var(--font-size-xs)' }}
            value={cgpaFilter}
            onChange={e => setCgpaFilter(e.target.value)}
          >
            <option value="all">All CGPA</option>
            <option value="7.0">CGPA ≥ 7.0</option>
            <option value="7.5">CGPA ≥ 7.5</option>
            <option value="8.0">CGPA ≥ 8.0</option>
            <option value="8.5">CGPA ≥ 8.5</option>
            <option value="9.0">CGPA ≥ 9.0</option>
          </select>
        </div>

        {/* Main Applicants Table Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '0 var(--space-8) var(--space-8)' }}>
          {loading ? (
            <div style={{ padding: 'var(--space-12)', textAlign: 'center', color: 'var(--text-muted)' }}>
              Loading applicants for this drive...
            </div>
          ) : error ? (
            <div style={{ padding: 'var(--space-6)', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: 'var(--border-radius)', textAlign: 'center', marginTop: 'var(--space-6)' }}>
              {error}
            </div>
          ) : filtered.length === 0 ? (
            <div style={{ padding: 'var(--space-12)', textAlign: 'center', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: 8 }}>🔍</div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>No matching applicants found</div>
              <p style={{ fontSize: 'var(--font-size-sm)' }}>Try adjusting your filters or search criteria.</p>
            </div>
          ) : viewMode === 'kanban' ? (
            /* Kanban Board View */
            <div style={{ display: 'flex', gap: 16, overflowX: 'auto', padding: '16px 0', minHeight: 520, alignItems: 'flex-start' }}>
              {[
                { key: 'applied', label: 'Applied', color: '#6366f1', icon: '📥' },
                { key: 'shortlisted', label: 'Shortlisted', color: '#f59e0b', icon: '⚡' },
                { key: 'in_progress', label: 'Tech Round', color: '#06b6d4', icon: '💻' },
                { key: 'selected', label: 'Selected / Offer', color: '#22c55e', icon: '🎉' },
                { key: 'rejected', label: 'Rejected', color: '#ef4444', icon: '❌' },
              ].map(col => {
                const colApps = filtered.filter(a => a.status === col.key);
                const isDragTarget = dragOverCol === col.key;
                return (
                  <div
                    key={col.key}
                    onDragOver={(e) => { e.preventDefault(); setDragOverCol(col.key); }}
                    onDragLeave={() => setDragOverCol(null)}
                    onDrop={(e) => {
                      e.preventDefault();
                      setDragOverCol(null);
                      if (draggedAppId) {
                        handleKanbanDrop(draggedAppId, col.key);
                        setDraggedAppId(null);
                      }
                    }}
                    style={{
                      minWidth: 220, maxWidth: 240, flex: '1 0 220px',
                      background: isDragTarget ? 'rgba(99,102,241,0.1)' : 'var(--bg-card)',
                      border: isDragTarget ? `2px dashed ${col.color}` : '1px solid var(--border-color)',
                      borderRadius: 12, padding: 12,
                      boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                      display: 'flex', flexDirection: 'column', gap: 8,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                      <div style={{ fontWeight: 700, fontSize: '0.85rem', color: col.color, display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span>{col.icon}</span> {col.label}
                      </div>
                      <span style={{
                        background: `${col.color}25`, color: col.color,
                        borderRadius: 99, padding: '2px 8px', fontSize: '0.72rem', fontWeight: 700,
                      }}>
                        {colApps.length}
                      </span>
                    </div>

                    <div style={{ minHeight: 400, display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {colApps.map(app => {
                        const fullName = `${app.first_name || ''} ${app.last_name || ''}`.trim() || 'Candidate';
                        return (
                          <div
                            key={app.application_id}
                            draggable
                            onDragStart={() => setDraggedAppId(app.application_id)}
                            style={{
                              background: 'var(--bg-secondary)',
                              borderRadius: 8, padding: '10px 12px',
                              border: '1px solid var(--border-color)',
                              cursor: 'grab', fontSize: '0.82rem',
                              boxShadow: '0 2px 6px rgba(0,0,0,0.1)',
                            }}
                          >
                            <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>
                              {fullName}
                            </div>
                            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                              {app.roll_number} · {app.department}
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 6 }}>
                              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: app.cgpa >= 8 ? '#22c55e' : 'var(--text-muted)' }}>
                                CGPA: {app.cgpa ? app.cgpa.toFixed(2) : 'N/A'}
                              </span>
                              {app.offer_ctc_lpa && (
                                <span style={{ fontSize: '0.7rem', color: '#22c55e', fontWeight: 700 }}>
                                  ₹{app.offer_ctc_lpa}L
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                      {colApps.length === 0 && (
                        <div style={{ textAlign: 'center', padding: '40px 10px', color: 'var(--text-muted)', fontSize: '0.75rem', border: '1px dashed var(--border-color)', borderRadius: 8 }}>
                          Drag candidates here
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="table-container" style={{ marginTop: 'var(--space-4)' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '12px 8px', width: 36, textAlign: 'center' }}>
                      <input
                        type="checkbox"
                        checked={filtered.length > 0 && selectedApps.size === filtered.length}
                        onChange={toggleSelectAll}
                        title="Select All"
                      />
                    </th>
                    <th style={{ padding: '12px 8px' }}>Roll No</th>
                    <th style={{ padding: '12px 8px' }}>Candidate Name</th>
                    <th style={{ padding: '12px 8px', textAlign: 'center' }}>Branch</th>
                    <th style={{ padding: '12px 8px', textAlign: 'center' }}>CGPA</th>
                    <th style={{ padding: '12px 8px' }}>Status</th>
                    <th style={{ padding: '12px 8px' }}>Current Stage</th>
                    <th style={{ padding: '12px 8px', textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(app => {
                    const fullName = `${app.first_name || ''} ${app.last_name || ''}`.trim() || 'Candidate';
                    const sc = STATUS_CONFIG[app.status] || STATUS_CONFIG.applied;
                    const isSelected = app.status === 'selected';
                    const isRejected = app.status === 'rejected';
                    const isMenuOpen = activeMenuAppId === app.application_id;

                    return (
                      <tr
                        key={app.application_id}
                        style={{
                          borderBottom: '1px solid rgba(255,255,255,0.05)',
                          transition: 'background 0.15s',
                        }}
                      >
                        {/* Selection Checkbox */}
                        <td style={{ padding: '12px 8px', width: 36, textAlign: 'center' }}>
                          <input
                            type="checkbox"
                            checked={selectedApps.has(app.application_id)}
                            onChange={() => toggleSelectApp(app.application_id)}
                          />
                        </td>

                        {/* Roll Number */}
                        <td style={{ padding: '12px 8px', fontFamily: 'var(--font-mono)', fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>
                          {app.roll_number}
                        </td>

                        {/* Name & Offer Badge */}
                        <td style={{ padding: '12px 8px' }}>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{fullName}</div>
                          {app.offer_ctc_lpa && (
                            <div style={{ marginTop: 2 }}>
                              <span style={{
                                padding: '2px 8px', borderRadius: 999,
                                fontSize: '0.7rem', fontWeight: 700,
                                background: 'rgba(34,197,94,0.15)', color: '#22c55e',
                                border: '1px solid rgba(34,197,94,0.3)',
                              }}>
                                💰 ₹{app.offer_ctc_lpa} LPA ✓
                              </span>
                            </div>
                          )}
                        </td>

                        {/* Branch */}
                        <td style={{ padding: '12px 8px', textAlign: 'center', fontSize: 'var(--font-size-xs)' }}>
                          <span style={{
                            padding: '2px 8px', borderRadius: 999,
                            background: 'var(--bg-tertiary)', color: 'var(--text-secondary)',
                            fontWeight: 600,
                          }}>
                            {app.department || 'CS'}
                          </span>
                        </td>

                        {/* CGPA */}
                        <td style={{ padding: '12px 8px', textAlign: 'center', fontWeight: 600, fontSize: 'var(--font-size-sm)' }}>
                          {app.cgpa != null ? Number(app.cgpa).toFixed(2) : '—'}
                        </td>

                        {/* Status */}
                        <td style={{ padding: '12px 8px' }}>
                          <span style={{
                            padding: '3px 10px', borderRadius: 999,
                            fontSize: 'var(--font-size-xs)', fontWeight: 600,
                            background: sc.bg, color: sc.color,
                            whiteSpace: 'nowrap',
                          }}>
                            ● {sc.label}
                          </span>
                        </td>

                        {/* Stage & Notes Preview */}
                        <td style={{ padding: '12px 8px', fontSize: 'var(--font-size-xs)' }}>
                          <div style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>
                            {app.current_stage || '—'}
                          </div>
                          {app.feedback && (
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', maxWidth: 200, truncate: 'ellipsis', marginTop: 2 }} title={app.feedback}>
                              💬 {app.feedback}
                            </div>
                          )}
                        </td>

                        {/* Actions Button & Popover */}
                        <td style={{ padding: '12px 8px', textAlign: 'right', position: 'relative' }}>
                          <div style={{ display: 'inline-flex', gap: 6, alignItems: 'center' }}>
                            {isSelected && (
                              <button
                                className="btn btn-secondary"
                                style={{ height: 30, padding: '0 10px', fontSize: 'var(--font-size-xs)', color: '#22c55e', borderColor: '#22c55e40' }}
                                onClick={() => setOfferModalApp(app)}
                                title="Record or update offer details"
                              >
                                📝 Offer
                              </button>
                            )}

                            <button
                              className="btn btn-primary"
                              style={{ height: 30, padding: '0 12px', fontSize: 'var(--font-size-xs)' }}
                              onClick={() => setActiveMenuAppId(isMenuOpen ? null : app.application_id)}
                            >
                              ⚡ Actions ▾
                            </button>
                          </div>

                          {/* Action Popover Menu */}
                          {isMenuOpen && (
                            <div
                              style={{
                                position: 'absolute', right: 8, top: 44,
                                width: 220, background: 'var(--bg-card)',
                                border: '1px solid var(--border-color)',
                                borderRadius: 'var(--border-radius)',
                                boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
                                zIndex: 100, textAlign: 'left',
                                overflow: 'hidden',
                              }}
                            >
                              <button
                                style={menuItemStyle}
                                onClick={() => {
                                  setActiveMenuAppId(null);
                                  setAdvanceModalApp(app);
                                  setStageForm(prev => ({ ...prev, stage: app.current_stage || 'Technical Interview 1' }));
                                }}
                              >
                                ⏩ Advance to Next Stage
                              </button>

                              <button
                                style={menuItemStyle}
                                onClick={() => {
                                  setActiveMenuAppId(null);
                                  setScheduleModalApp(app);
                                }}
                              >
                                📅 Schedule Interview
                              </button>

                              <button
                                style={menuItemStyle}
                                onClick={() => {
                                  setActiveMenuAppId(null);
                                  setFeedbackModalApp(app);
                                  setFeedbackText(app.feedback || '');
                                }}
                              >
                                💬 Add Internal Feedback
                              </button>

                              {isSelected ? (
                                <button
                                  style={{ ...menuItemStyle, color: '#22c55e' }}
                                  onClick={() => {
                                    setActiveMenuAppId(null);
                                    setOfferModalApp(app);
                                  }}
                                >
                                  📝 Record Official Offer
                                </button>
                              ) : (
                                <button
                                  style={{ ...menuItemStyle, color: '#22c55e' }}
                                  onClick={() => {
                                    setActiveMenuAppId(null);
                                    setAdvanceModalApp(app);
                                    setStageForm({
                                      stage: 'Final Round',
                                      status: 'selected',
                                      scheduled_at: '',
                                      meeting_link: '',
                                      venue: '',
                                      feedback: 'Candidate selected for official placement offer.',
                                    });
                                  }}
                                >
                                  🎉 Mark Selected & Offer
                                </button>
                              )}

                              {!isRejected && (
                                <button
                                  style={{ ...menuItemStyle, color: '#ef4444', borderTop: '1px solid var(--border-color)' }}
                                  onClick={() => {
                                    setActiveMenuAppId(null);
                                    setRejectModalApp(app);
                                    setRejectReason('');
                                  }}
                                >
                                  ❌ Reject Candidate
                                </button>
                              )}
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* ─── MODAL 1: Advance Stage Modal ─── */}
        {advanceModalApp && (
          <div style={overlayStyle} onClick={() => setAdvanceModalApp(null)}>
            <div style={modalCardStyle} onClick={e => e.stopPropagation()}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
                <h3 style={{ margin: 0, fontSize: 'var(--font-size-lg)', fontWeight: 700 }}>
                  Advance Candidate: {advanceModalApp.first_name} {advanceModalApp.last_name}
                </h3>
                <button onClick={() => setAdvanceModalApp(null)} style={closeBtnStyle}>×</button>
              </div>

              <form onSubmit={handleAdvanceSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <div className="input-group">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Target Stage *</label>
                  <select
                    className="input"
                    value={stageForm.stage}
                    onChange={e => setStageForm(f => ({ ...f, stage: e.target.value }))}
                  >
                    {STAGES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>

                <div className="input-group">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Overall Application Status</label>
                  <select
                    className="input"
                    value={stageForm.status}
                    onChange={e => setStageForm(f => ({ ...f, status: e.target.value }))}
                  >
                    <option value="shortlisted">Shortlisted</option>
                    <option value="in_progress">In Progress (Interviewing)</option>
                    <option value="selected">Selected (Hired) 🎉</option>
                  </select>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
                  <div className="input-group">
                    <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Schedule Interview (Optional)</label>
                    <input
                      className="input"
                      type="datetime-local"
                      value={stageForm.scheduled_at}
                      onChange={e => setStageForm(f => ({ ...f, scheduled_at: e.target.value }))}
                    />
                  </div>
                  <div className="input-group">
                    <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Meeting Link (Virtual)</label>
                    <input
                      className="input"
                      placeholder="https://meet.google.com/..."
                      value={stageForm.meeting_link}
                      onChange={e => setStageForm(f => ({ ...f, meeting_link: e.target.value }))}
                    />
                  </div>
                </div>

                <div className="input-group">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>In-Person Venue (Optional)</label>
                  <input
                    className="input"
                    placeholder="e.g. CS Lab 3 / Seminar Hall"
                    value={stageForm.venue}
                    onChange={e => setStageForm(f => ({ ...f, venue: e.target.value }))}
                  />
                </div>

                <div className="input-group">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Internal TPO Feedback Notes</label>
                  <textarea
                    className="input"
                    rows={2}
                    placeholder="Notes for internal record..."
                    value={stageForm.feedback}
                    onChange={e => setStageForm(f => ({ ...f, feedback: e.target.value }))}
                  />
                </div>

                <div style={{ display: 'flex', gap: 10, marginTop: 'var(--space-3)' }}>
                  <button type="button" className="btn btn-secondary" onClick={() => setAdvanceModalApp(null)} style={{ flex: 1 }}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary" disabled={actionLoading} style={{ flex: 1.5 }}>
                    {actionLoading ? 'Updating...' : '✓ Confirm & Advance'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ─── MODAL 2: Schedule Interview Modal ─── */}
        {scheduleModalApp && (
          <div style={overlayStyle} onClick={() => setScheduleModalApp(null)}>
            <div style={modalCardStyle} onClick={e => e.stopPropagation()}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
                <h3 style={{ margin: 0, fontSize: 'var(--font-size-lg)', fontWeight: 700 }}>
                  📅 Schedule Interview: {scheduleModalApp.first_name} {scheduleModalApp.last_name}
                </h3>
                <button onClick={() => setScheduleModalApp(null)} style={closeBtnStyle}>×</button>
              </div>

              <form onSubmit={handleScheduleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <div className="input-group">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Interview Date & Time *</label>
                  <input
                    className="input"
                    type="datetime-local"
                    required
                    value={scheduleForm.scheduled_at}
                    onChange={e => setScheduleForm(f => ({ ...f, scheduled_at: e.target.value }))}
                  />
                </div>

                <div className="input-group">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Virtual Meeting URL</label>
                  <input
                    className="input"
                    placeholder="https://meet.google.com/xyz-abc"
                    value={scheduleForm.meeting_link}
                    onChange={e => setScheduleForm(f => ({ ...f, meeting_link: e.target.value }))}
                  />
                </div>

                <div className="input-group">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Physical Venue (if on-campus)</label>
                  <input
                    className="input"
                    placeholder="e.g. Placement Cell Interview Room 2"
                    value={scheduleForm.venue}
                    onChange={e => setScheduleForm(f => ({ ...f, venue: e.target.value }))}
                  />
                </div>

                <div style={{ display: 'flex', gap: 10, marginTop: 'var(--space-3)' }}>
                  <button type="button" className="btn btn-secondary" onClick={() => setScheduleModalApp(null)} style={{ flex: 1 }}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary" disabled={actionLoading} style={{ flex: 1.5 }}>
                    {actionLoading ? 'Saving...' : '✓ Schedule & Notify Student'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ─── MODAL 3: Internal Feedback Modal ─── */}
        {feedbackModalApp && (
          <div style={overlayStyle} onClick={() => setFeedbackModalApp(null)}>
            <div style={modalCardStyle} onClick={e => e.stopPropagation()}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
                <h3 style={{ margin: 0, fontSize: 'var(--font-size-lg)', fontWeight: 700 }}>
                  💬 Internal TPO Feedback
                </h3>
                <button onClick={() => setFeedbackModalApp(null)} style={closeBtnStyle}>×</button>
              </div>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: 'var(--space-3)' }}>
                Internal notes for {feedbackModalApp.first_name} {feedbackModalApp.last_name} ({feedbackModalApp.roll_number}). Not visible to students.
              </p>

              <form onSubmit={handleFeedbackSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <textarea
                  className="input"
                  rows={4}
                  required
                  placeholder="Record interviewer remarks, coding assessment score, communication skills rating..."
                  value={feedbackText}
                  onChange={e => setFeedbackText(e.target.value)}
                />
                <div style={{ display: 'flex', gap: 10, marginTop: 'var(--space-2)' }}>
                  <button type="button" className="btn btn-secondary" onClick={() => setFeedbackModalApp(null)} style={{ flex: 1 }}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary" disabled={actionLoading} style={{ flex: 1.5 }}>
                    {actionLoading ? 'Saving...' : 'Save Feedback'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ─── MODAL 4: Reject Candidate Confirmation ─── */}
        {rejectModalApp && (
          <div style={overlayStyle} onClick={() => setRejectModalApp(null)}>
            <div style={modalCardStyle} onClick={e => e.stopPropagation()}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
                <h3 style={{ margin: 0, fontSize: 'var(--font-size-lg)', fontWeight: 700, color: '#ef4444' }}>
                  ❌ Reject Candidate
                </h3>
                <button onClick={() => setRejectModalApp(null)} style={closeBtnStyle}>×</button>
              </div>
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                Are you sure you want to mark <strong>{rejectModalApp.first_name} {rejectModalApp.last_name}</strong> ({rejectModalApp.roll_number}) as Not Selected?
              </p>

              <div className="input-group" style={{ margin: 'var(--space-3) 0' }}>
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Rejection Reason / Notes (Optional)</label>
                <textarea
                  className="input"
                  rows={2}
                  placeholder="e.g. Did not meet round 2 cut-off / company quota reached"
                  value={rejectReason}
                  onChange={e => setRejectReason(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', gap: 10, marginTop: 'var(--space-3)' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setRejectModalApp(null)} style={{ flex: 1 }}>
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn"
                  onClick={handleRejectSubmit}
                  disabled={actionLoading}
                  style={{ flex: 1.5, background: '#ef4444', color: 'white' }}
                >
                  {actionLoading ? 'Rejecting...' : 'Confirm Rejection'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ─── MODAL 5: Offer Recording Modal ─── */}
        {offerModalApp && (
          <OfferModal
            driveId={drive.id}
            application={offerModalApp}
            onClose={() => setOfferModalApp(null)}
            onSuccess={handleOfferRecorded}
          />
        )}

        {/* ─── MODAL 6: Auto-Shortlist Wizard Modal ─── */}
        {shortlistWizardOpen && (
          <div style={overlayStyle} onClick={() => setShortlistWizardOpen(false)}>
            <div style={{ ...modalCardStyle, maxWidth: 640, maxHeight: '90vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: '1.4rem' }}>⚡</span>
                  <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700 }}>Auto-Shortlist Wizard</h3>
                </div>
                <button onClick={() => setShortlistWizardOpen(false)} style={closeBtnStyle}>×</button>
              </div>

              {/* Steps bar */}
              <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
                {['1. Criteria Config', '2. Dry-Run Preview', '3. Execution'].map((st, idx) => (
                  <div
                    key={st}
                    style={{
                      flex: 1, padding: '8px', borderRadius: 8, textAlign: 'center',
                      fontSize: '0.78rem', fontWeight: 700,
                      background: wizardStep === idx + 1 ? 'var(--primary)' : 'var(--bg-tertiary)',
                      color: wizardStep === idx + 1 ? '#fff' : 'var(--text-muted)',
                    }}
                  >
                    {st}
                  </div>
                ))}
              </div>

              {/* STEP 1: Criteria Config */}
              {wizardStep === 1 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, marginBottom: 6 }}>
                      Minimum CGPA Threshold ({wizardCriteria.min_cgpa ?? 'None'})
                    </label>
                    <input
                      type="range" min="5.0" max="10.0" step="0.1"
                      value={wizardCriteria.min_cgpa || 7.0}
                      onChange={e => setWizardCriteria(c => ({ ...c, min_cgpa: parseFloat(e.target.value) }))}
                      style={{ width: '100%' }}
                    />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, marginBottom: 6 }}>Max Active Backlogs</label>
                      <select
                        className="input"
                        value={wizardCriteria.max_backlogs ?? ''}
                        onChange={e => setWizardCriteria(c => ({ ...c, max_backlogs: e.target.value === '' ? null : parseInt(e.target.value) }))}
                      >
                        <option value="">No limit</option>
                        <option value="0">0 (Strictly No Backlogs)</option>
                        <option value="1">Max 1 Backlog</option>
                        <option value="2">Max 2 Backlogs</option>
                      </select>
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, marginBottom: 6 }}>Min Projects Count</label>
                      <select
                        className="input"
                        value={wizardCriteria.min_projects ?? ''}
                        onChange={e => setWizardCriteria(c => ({ ...c, min_projects: e.target.value === '' ? null : parseInt(e.target.value) }))}
                      >
                        <option value="">Any</option>
                        <option value="1">At least 1 Project</option>
                        <option value="2">At least 2 Projects</option>
                        <option value="3">At least 3 Projects</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, marginBottom: 6 }}>
                      ML Match Score Threshold ({wizardCriteria.min_match_score || 0}%)
                    </label>
                    <input
                      type="range" min="0" max="95" step="5"
                      value={wizardCriteria.min_match_score || 0}
                      onChange={e => setWizardCriteria(c => ({ ...c, min_match_score: parseInt(e.target.value) || null }))}
                      style={{ width: '100%' }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, marginBottom: 6 }}>Required Skills (Must Have All)</label>
                    <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                      <input
                        className="input"
                        placeholder="e.g. Python, React, SQL..."
                        value={newSkillInput}
                        onChange={e => setNewSkillInput(e.target.value)}
                        onKeyDown={e => {
                          if (e.key === 'Enter' && newSkillInput.trim()) {
                            e.preventDefault();
                            setWizardCriteria(c => ({ ...c, required_skills: [...c.required_skills, newSkillInput.trim()] }));
                            setNewSkillInput('');
                          }
                        }}
                      />
                      <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={() => {
                          if (newSkillInput.trim()) {
                            setWizardCriteria(c => ({ ...c, required_skills: [...c.required_skills, newSkillInput.trim()] }));
                            setNewSkillInput('');
                          }
                        }}
                      >
                        Add
                      </button>
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {wizardCriteria.required_skills.map((sk, idx) => (
                        <span key={idx} style={{ padding: '4px 10px', borderRadius: 99, background: 'var(--primary)', color: '#fff', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: 6 }}>
                          {sk}
                          <span style={{ cursor: 'pointer' }} onClick={() => setWizardCriteria(c => ({ ...c, required_skills: c.required_skills.filter((_, i) => i !== idx) }))}>✕</span>
                        </span>
                      ))}
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <input
                      type="checkbox"
                      id="req-resume"
                      checked={wizardCriteria.has_resume || false}
                      onChange={e => setWizardCriteria(c => ({ ...c, has_resume: e.target.checked || null }))}
                    />
                    <label htmlFor="req-resume" style={{ fontSize: '0.85rem' }}>Require Uploaded Resume PDF</label>
                  </div>

                  <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
                    <button type="button" className="btn btn-secondary" onClick={() => setShortlistWizardOpen(false)} style={{ flex: 1 }}>Cancel</button>
                    <button type="button" className="btn btn-primary" onClick={runDryRun} disabled={wizardLoading} style={{ flex: 1.5 }}>
                      {wizardLoading ? 'Running Dry-Run...' : '👁 Run Dry-Run Preview →'}
                    </button>
                  </div>
                </div>
              )}

              {/* STEP 2: Dry Run Preview */}
              {wizardStep === 2 && dryRunResult && (
                <div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
                    <div style={{ padding: 16, borderRadius: 10, background: 'rgba(34, 197, 94, 0.12)', border: '1px solid rgba(34, 197, 94, 0.3)', textAlign: 'center' }}>
                      <div style={{ fontSize: '2rem', fontWeight: 800, color: '#22c55e' }}>{dryRunResult.would_shortlist}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Candidates Would Shortlist</div>
                    </div>
                    <div style={{ padding: 16, borderRadius: 10, background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.3)', textAlign: 'center' }}>
                      <div style={{ fontSize: '2rem', fontWeight: 800, color: '#ef4444' }}>{dryRunResult.would_skip}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Candidates Unqualified</div>
                    </div>
                  </div>

                  <div style={{ marginBottom: 16 }}>
                    <div style={{ fontWeight: 700, fontSize: '0.88rem', marginBottom: 8 }}>Preview Passing Candidates ({dryRunResult.preview_pass?.length}):</div>
                    <div style={{ maxHeight: 140, overflowY: 'auto', border: '1px solid var(--border-color)', borderRadius: 8, padding: 8 }}>
                      {(dryRunResult.preview_pass || []).map((s, i) => (
                        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', padding: '4px 8px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                          <span>{s.first_name} {s.last_name} ({s.department})</span>
                          <span style={{ color: '#22c55e', fontWeight: 600 }}>CGPA: {s.cgpa?.toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: 10 }}>
                    <button type="button" className="btn btn-secondary" onClick={() => setWizardStep(1)} style={{ flex: 1 }}>← Edit Criteria</button>
                    <button type="button" className="btn btn-primary" onClick={runExecuteShortlist} disabled={wizardLoading || dryRunResult.would_shortlist === 0} style={{ flex: 1.5 }}>
                      {wizardLoading ? 'Executing Shortlist...' : `✅ Confirm & Shortlist ${dryRunResult.would_shortlist} Students`}
                    </button>
                  </div>
                </div>
              )}

              {/* STEP 3: Execution Result */}
              {wizardStep === 3 && executeResult && (
                <div style={{ textAlign: 'center', padding: '20px 0' }}>
                  <div style={{ fontSize: '3rem', marginBottom: 16 }}>🎉</div>
                  <h3 style={{ margin: '0 0 8px 0', fontSize: '1.2rem', color: '#22c55e' }}>Shortlisting Successfully Executed!</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: 20 }}>
                    Successfully updated <strong style={{ color: '#22c55e' }}>{executeResult.shortlisted}</strong> candidate status to <strong>Shortlisted</strong>.<br />
                    In-app notifications have been dispatched to all qualified students.
                  </p>
                  <button type="button" className="btn btn-primary" onClick={() => setShortlistWizardOpen(false)}>Done</button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ─── MODAL 7: Bulk Action Confirmation Modal ─── */}
        {bulkConfirmAction && (
          <div style={overlayStyle} onClick={() => setBulkConfirmAction(null)}>
            <div style={modalCardStyle} onClick={e => e.stopPropagation()}>
              <h3 style={{ margin: '0 0 12px 0', fontSize: '1.1rem' }}>Confirm Bulk Action</h3>
              <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginBottom: 20 }}>
                Are you sure you want to <strong>{bulkConfirmAction === 'shortlist' ? 'Shortlist' : bulkConfirmAction === 'next_round' ? 'Advance to Tech Round' : 'Reject'}</strong> all {selectedApps.size} selected candidate(s)?
              </p>
              <div style={{ display: 'flex', gap: 10 }}>
                <button className="btn btn-secondary" onClick={() => setBulkConfirmAction(null)} style={{ flex: 1 }}>Cancel</button>
                <button
                  className="btn btn-primary"
                  style={{ flex: 1, background: bulkConfirmAction === 'reject' ? '#ef4444' : 'var(--primary)' }}
                  onClick={() => executeBulkAction(bulkConfirmAction)}
                  disabled={bulkActionLoading}
                >
                  {bulkActionLoading ? 'Processing...' : 'Confirm Action'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const menuItemStyle = {
  display: 'block',
  width: '100%',
  padding: '10px 14px',
  background: 'none',
  border: 'none',
  textAlign: 'left',
  fontSize: '0.82rem',
  fontWeight: 500,
  color: 'var(--text-primary)',
  cursor: 'pointer',
  transition: 'background 0.15s',
};

const overlayStyle = {
  position: 'fixed', inset: 0,
  background: 'rgba(5, 8, 18, 0.75)',
  backdropFilter: 'blur(6px)',
  zIndex: 1300, display: 'flex',
  alignItems: 'center', justifyContent: 'center',
  padding: 'var(--space-6)',
};

const modalCardStyle = {
  background: 'var(--bg-card)',
  border: '1px solid var(--border-color)',
  borderRadius: 'var(--border-radius-lg)',
  boxShadow: '0 20px 50px rgba(0,0,0,0.6)',
  padding: 'var(--space-6)',
  width: '100%', maxWidth: 500,
};

const closeBtnStyle = {
  background: 'none', border: 'none',
  cursor: 'pointer', color: 'var(--text-muted)',
  fontSize: '1.4rem', lineHeight: 1,
};
