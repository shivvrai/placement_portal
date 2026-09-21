/**
 * TPO Drives — Manage placement drives: create, edit, monitor progress, shortlist.
 * Connected to live FastAPI backend via placementApi.
 */

import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { placementApi } from '../../api/endpoints';
import DriveApplicantReviewer from './DriveApplicantReviewer';

const STATUS_CFG = {
  open:        { color: '#22c55e', bg: 'rgba(34,197,94,0.12)', label: 'Open' },
  in_progress: { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', label: 'In Progress' },
  upcoming:    { color: '#6366f1', bg: 'rgba(99,102,241,0.12)', label: 'Upcoming' },
  completed:   { color: 'var(--text-muted)', bg: 'var(--bg-tertiary)', label: 'Completed' },
  cancelled:   { color: '#ef4444', bg: 'rgba(239,68,68,0.12)', label: 'Cancelled' },
};

const ALL_DEPTS = ['CS', 'IT', 'ECE', 'ME', 'EEE'];

// ─── Create Drive Modal ────────────────────────────────────────────
function CreateDriveModal({ onClose, onCreated }) {
  const [form, setForm] = useState({
    company_name: '',
    company_location: '',
    company_industry: 'Technology',
    title: '',
    roles_offered: '',
    salary_ctc: '',
    drive_date: '',
    registration_deadline: '',
    min_cgpa: 7.0,
    max_backlogs: 0,
    eligible_departments: ['CS', 'IT'],
    description: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const toggleDept = (dept) => {
    setForm(f => {
      const exists = f.eligible_departments.includes(dept);
      return {
        ...f,
        eligible_departments: exists
          ? f.eligible_departments.filter(d => d !== dept)
          : [...f.eligible_departments, dept],
      };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.company_name.trim() || !form.title.trim()) {
      setError('Company Name and Drive Title are required.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const rolesArray = form.roles_offered
        ? form.roles_offered.split(',').map(r => r.trim()).filter(Boolean)
        : [form.title.trim()];

      const payload = {
        company_name: form.company_name.trim(),
        company_location: form.company_location.trim() || null,
        company_industry: form.company_industry.trim() || null,
        title: form.title.trim(),
        description: form.description.trim() || null,
        drive_date: form.drive_date || null,
        registration_deadline: form.registration_deadline
          ? `${form.registration_deadline}T23:59:59`
          : null,
        min_cgpa: form.min_cgpa !== '' ? parseFloat(form.min_cgpa) : null,
        max_backlogs: form.max_backlogs !== '' ? parseInt(form.max_backlogs, 10) : 0,
        eligible_departments: form.eligible_departments,
        roles_offered: rolesArray,
        salary_ctc: form.salary_ctc !== '' ? parseFloat(form.salary_ctc) : null,
        academic_year: '2026-27',
      };

      await placementApi.createDrive(payload);
      onCreated();
      onClose();
    } catch (err) {
      console.error('Failed to create drive:', err);
      setError(err.response?.data?.detail || 'Failed to create placement drive. Please check the inputs.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
        zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 'var(--space-6)',
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'var(--bg-card)', border: '1px solid var(--border-color)',
          borderRadius: 'var(--border-radius-lg)', padding: 'var(--space-8)',
          width: '100%', maxWidth: 640, maxHeight: '90vh', overflowY: 'auto',
        }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-5)' }}>
          <h2 style={{ fontWeight: 700, fontSize: 'var(--font-size-xl)' }}>Create Placement Drive</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '1.5rem' }}>×</button>
        </div>

        {error && (
          <div style={{ padding: 'var(--space-3)', background: 'rgba(239,68,68,0.1)', color: '#ef4444', borderRadius: 'var(--border-radius)', marginBottom: 'var(--space-4)', fontSize: 'var(--font-size-sm)' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
            <div className="input-group">
              <label>Company Name *</label>
              <input className="input" placeholder="e.g. Google, Amazon" required value={form.company_name} onChange={set('company_name')} />
            </div>
            <div className="input-group">
              <label>Industry</label>
              <input className="input" placeholder="e.g. Technology, Finance" value={form.company_industry} onChange={set('company_industry')} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
            <div className="input-group">
              <label>Drive Title *</label>
              <input className="input" placeholder="e.g. Summer SDE Hiring 2026" required value={form.title} onChange={set('title')} />
            </div>
            <div className="input-group">
              <label>Location</label>
              <input className="input" placeholder="e.g. Bangalore, Remote" value={form.company_location} onChange={set('company_location')} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--space-4)' }}>
            <div className="input-group">
              <label>Salary (LPA)</label>
              <input className="input" type="number" step="0.5" min="0" placeholder="e.g. 18.5" value={form.salary_ctc} onChange={set('salary_ctc')} />
            </div>
            <div className="input-group">
              <label>Min CGPA</label>
              <input className="input" type="number" step="0.1" min="0" max="10" value={form.min_cgpa} onChange={set('min_cgpa')} />
            </div>
            <div className="input-group">
              <label>Max Backlogs</label>
              <input className="input" type="number" min="0" max="10" value={form.max_backlogs} onChange={set('max_backlogs')} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
            <div className="input-group">
              <label>Registration Deadline</label>
              <input className="input" type="date" value={form.registration_deadline} onChange={set('registration_deadline')} />
            </div>
            <div className="input-group">
              <label>Drive Date</label>
              <input className="input" type="date" value={form.drive_date} onChange={set('drive_date')} />
            </div>
          </div>

          <div className="input-group">
            <label>Roles Offered (comma-separated)</label>
            <input className="input" placeholder="e.g. SDE-1, Data Engineer, QA Intern" value={form.roles_offered} onChange={set('roles_offered')} />
          </div>

          <div className="input-group">
            <label style={{ marginBottom: 'var(--space-2)' }}>Eligible Departments</label>
            <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
              {ALL_DEPTS.map(dept => {
                const active = form.eligible_departments.includes(dept);
                return (
                  <button
                    type="button"
                    key={dept}
                    onClick={() => toggleDept(dept)}
                    style={{
                      padding: '6px 14px',
                      borderRadius: 999,
                      border: `1px solid ${active ? 'var(--accent-primary)' : 'var(--border-color)'}`,
                      background: active ? 'var(--accent-primary-subtle)' : 'var(--bg-tertiary)',
                      color: active ? 'var(--accent-primary)' : 'var(--text-secondary)',
                      cursor: 'pointer',
                      fontSize: 'var(--font-size-xs)',
                      fontWeight: 600,
                    }}
                  >
                    {active ? '✓ ' : '+ '}{dept}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="input-group">
            <label>Description & Requirements</label>
            <textarea
              className="input"
              rows={3}
              placeholder="Candidate requirements, process details, and selection criteria..."
              value={form.description}
              onChange={set('description')}
            />
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-3)' }}>
            <button type="submit" className="btn btn-primary" disabled={submitting} style={{ flex: 1 }}>
              {submitting ? 'Creating Drive...' : 'Create Drive'}
            </button>
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={submitting} style={{ flex: 1 }}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Edit Drive Modal ──────────────────────────────────────────────
function EditDriveModal({ drive, onClose, onUpdated }) {
  const [form, setForm] = useState({
    title: drive.title || '',
    description: drive.description || '',
    status: drive.status || 'open',
    salary_ctc: drive.salary_ctc || '',
    min_cgpa: drive.min_cgpa || '',
    max_backlogs: drive.max_backlogs ?? 0,
    drive_date: drive.drive_date || '',
    registration_deadline: drive.registration_deadline ? drive.registration_deadline.split('T')[0] : '',
    eligible_departments: drive.eligible_departments || [],
    roles_offered: Array.isArray(drive.roles_offered) ? drive.roles_offered.join(', ') : '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const toggleDept = (dept) => {
    setForm(f => {
      const exists = f.eligible_departments.includes(dept);
      return {
        ...f,
        eligible_departments: exists
          ? f.eligible_departments.filter(d => d !== dept)
          : [...f.eligible_departments, dept],
      };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setError(null);

      const rolesArray = form.roles_offered
        ? form.roles_offered.split(',').map(r => r.trim()).filter(Boolean)
        : [];

      const payload = {
        title: form.title.trim(),
        description: form.description.trim() || null,
        status: form.status,
        salary_ctc: form.salary_ctc !== '' ? parseFloat(form.salary_ctc) : null,
        min_cgpa: form.min_cgpa !== '' ? parseFloat(form.min_cgpa) : null,
        max_backlogs: form.max_backlogs !== '' ? parseInt(form.max_backlogs, 10) : 0,
        drive_date: form.drive_date || null,
        registration_deadline: form.registration_deadline ? `${form.registration_deadline}T23:59:59` : null,
        eligible_departments: form.eligible_departments,
        roles_offered: rolesArray.length > 0 ? rolesArray : undefined,
      };

      await placementApi.updateDrive(drive.id, payload);
      onUpdated();
      onClose();
    } catch (err) {
      console.error('Failed to update drive:', err);
      setError(err.response?.data?.detail || 'Failed to update drive');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
        zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 'var(--space-6)',
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'var(--bg-card)', border: '1px solid var(--border-color)',
          borderRadius: 'var(--border-radius-lg)', padding: 'var(--space-8)',
          width: '100%', maxWidth: 640, maxHeight: '90vh', overflowY: 'auto',
        }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-5)' }}>
          <h2 style={{ fontWeight: 700, fontSize: 'var(--font-size-xl)' }}>Edit Placement Drive</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '1.5rem' }}>×</button>
        </div>

        {error && (
          <div style={{ padding: 'var(--space-3)', background: 'rgba(239,68,68,0.1)', color: '#ef4444', borderRadius: 'var(--border-radius)', marginBottom: 'var(--space-4)', fontSize: 'var(--font-size-sm)' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 'var(--space-4)' }}>
            <div className="input-group">
              <label>Drive Title</label>
              <input className="input" required value={form.title} onChange={set('title')} />
            </div>
            <div className="input-group">
              <label>Status</label>
              <select className="input" value={form.status} onChange={set('status')}>
                <option value="upcoming">Upcoming</option>
                <option value="open">Open</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--space-4)' }}>
            <div className="input-group">
              <label>Salary (LPA)</label>
              <input className="input" type="number" step="0.5" min="0" value={form.salary_ctc} onChange={set('salary_ctc')} />
            </div>
            <div className="input-group">
              <label>Min CGPA</label>
              <input className="input" type="number" step="0.1" min="0" max="10" value={form.min_cgpa} onChange={set('min_cgpa')} />
            </div>
            <div className="input-group">
              <label>Max Backlogs</label>
              <input className="input" type="number" min="0" max="10" value={form.max_backlogs} onChange={set('max_backlogs')} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
            <div className="input-group">
              <label>Registration Deadline</label>
              <input className="input" type="date" value={form.registration_deadline} onChange={set('registration_deadline')} />
            </div>
            <div className="input-group">
              <label>Drive Date</label>
              <input className="input" type="date" value={form.drive_date} onChange={set('drive_date')} />
            </div>
          </div>

          <div className="input-group">
            <label>Roles Offered</label>
            <input className="input" value={form.roles_offered} onChange={set('roles_offered')} placeholder="e.g. SDE-1, Data Analyst" />
          </div>

          <div className="input-group">
            <label style={{ marginBottom: 'var(--space-2)' }}>Eligible Departments</label>
            <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
              {ALL_DEPTS.map(dept => {
                const active = form.eligible_departments.includes(dept);
                return (
                  <button
                    type="button"
                    key={dept}
                    onClick={() => toggleDept(dept)}
                    style={{
                      padding: '6px 14px',
                      borderRadius: 999,
                      border: `1px solid ${active ? 'var(--accent-primary)' : 'var(--border-color)'}`,
                      background: active ? 'var(--accent-primary-subtle)' : 'var(--bg-tertiary)',
                      color: active ? 'var(--accent-primary)' : 'var(--text-secondary)',
                      cursor: 'pointer',
                      fontSize: 'var(--font-size-xs)',
                      fontWeight: 600,
                    }}
                  >
                    {active ? '✓ ' : '+ '}{dept}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="input-group">
            <label>Description</label>
            <textarea className="input" rows={3} value={form.description} onChange={set('description')} />
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-3)' }}>
            <button type="submit" className="btn btn-primary" disabled={submitting} style={{ flex: 1 }}>
              {submitting ? 'Saving Changes...' : 'Save Changes'}
            </button>
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={submitting} style={{ flex: 1 }}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Shortlist Modal ───────────────────────────────────────────────
function ShortlistModal({ drive, onClose }) {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadShortlisted() {
      if (!drive?.id) return;
      try {
        setLoading(true);
        setError(null);
        const res = await placementApi.shortlistStudents(drive.id);
        setStudents(res.data || []);
      } catch (err) {
        console.error('Failed to load shortlisted students:', err);
        setError('Failed to load shortlisted students.');
      } finally {
        setLoading(false);
      }
    }
    loadShortlisted();
  }, [drive?.id]);

  if (!drive) return null;

  return (
    <div
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
        zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 'var(--space-6)',
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'var(--bg-card)', border: '1px solid var(--border-color)',
          borderRadius: 'var(--border-radius-lg)', padding: 'var(--space-8)',
          width: '100%', maxWidth: 720, maxHeight: '85vh', overflowY: 'auto',
        }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-5)' }}>
          <div>
            <h2 style={{ fontWeight: 700, fontSize: 'var(--font-size-xl)' }}>
              {drive.company?.name || drive.company} — Shortlisted Candidates
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-xs)', marginTop: 2 }}>
              Drive: {drive.title}
            </p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '1.5rem' }}>×</button>
        </div>

        {loading ? (
          <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading candidate records...
          </div>
        ) : error ? (
          <div style={{ padding: 'var(--space-4)', background: 'rgba(239,68,68,0.1)', color: '#ef4444', borderRadius: 'var(--border-radius)', textAlign: 'center' }}>
            {error}
          </div>
        ) : students.length === 0 ? (
          <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--text-muted)' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: 'var(--space-2)' }}>👥</div>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>No Shortlisted Candidates Yet</div>
            <p style={{ fontSize: 'var(--font-size-sm)' }}>
              Students who pass initial screening or reach interview rounds will appear here.
            </p>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Student</th>
                  <th style={{ textAlign: 'center' }}>CGPA</th>
                  <th>Current Stage</th>
                  <th>Status</th>
                  <th>Applied On</th>
                </tr>
              </thead>
              <tbody>
                {students.map(s => {
                  const fullName = `${s.first_name || ''} ${s.last_name || ''}`.trim() || 'Student';
                  const dateStr = s.applied_at ? new Date(s.applied_at).toLocaleDateString('en-IN') : '—';
                  return (
                    <tr key={s.application_id || s.student_id}>
                      <td>
                        <div style={{ fontWeight: 600 }}>{fullName}</div>
                        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                          {s.roll_number}
                        </div>
                      </td>
                      <td style={{ textAlign: 'center', fontWeight: 600 }}>
                        {s.cgpa ? Number(s.cgpa).toFixed(2) : '—'}
                      </td>
                      <td style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                        {s.current_stage || 'Application Submitted'}
                      </td>
                      <td>
                        <span style={{
                          padding: '3px 10px', borderRadius: 999, fontSize: 'var(--font-size-xs)', fontWeight: 600,
                          background: s.status === 'selected' ? 'rgba(34,197,94,0.12)' : 'rgba(245,158,11,0.12)',
                          color: s.status === 'selected' ? '#22c55e' : '#f59e0b',
                          textTransform: 'capitalize',
                        }}>
                          {s.status}
                        </span>
                      </td>
                      <td style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                        {dateStr}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Post Announcement Modal ───────────────────────────────────────
function PostAnnouncementModal({ drive, onClose, onPosted }) {
  const [form, setForm] = useState({
    title: '',
    message: '',
    urgency: 'normal',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const companyName = drive.company?.name || drive.company || drive.title;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.title.trim() || !form.message.trim()) {
      setError('Title and message are required.');
      return;
    }
    try {
      setSubmitting(true);
      setError(null);
      await placementApi.postAnnouncement(drive.id, {
        title: form.title.trim(),
        message: form.message.trim(),
        urgency: form.urgency,
      });
      if (onPosted) onPosted();
      onClose();
    } catch (err) {
      console.error('Failed to post announcement:', err);
      setError(err.response?.data?.detail || 'Failed to post announcement.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed', inset: 0, background: 'rgba(5, 8, 18, 0.75)',
        backdropFilter: 'blur(6px)',
        zIndex: 1200, display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 'var(--space-6)',
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'var(--bg-card)', border: '1px solid var(--border-color)',
          borderRadius: 'var(--border-radius-lg)', padding: 'var(--space-8)',
          width: '100%', maxWidth: 540, boxShadow: '0 20px 50px rgba(0,0,0,0.6)',
        }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-4)' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: '1.3rem' }}>📢</span>
              <h2 style={{ fontWeight: 700, fontSize: 'var(--font-size-lg)', margin: 0 }}>
                Post Drive Announcement
              </h2>
            </div>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginTop: 2, margin: 0 }}>
              Drive: {companyName} — {drive.title}
            </p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '1.5rem' }}>×</button>
        </div>

        {error && (
          <div style={{ padding: '8px 12px', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: 'var(--border-radius-sm)', marginBottom: 'var(--space-3)', fontSize: 'var(--font-size-xs)' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div className="input-group">
            <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Announcement Title *</label>
            <input
              className="input"
              required
              placeholder="e.g. PPT Venue Shift / Interview Shortlist Released"
              value={form.title}
              onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
            />
          </div>

          <div className="input-group">
            <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Urgency Level</label>
            <select
              className="input"
              value={form.urgency}
              onChange={e => setForm(f => ({ ...f, urgency: e.target.value }))}
            >
              <option value="normal">Normal (Standard broadcast)</option>
              <option value="important">Important (Yellow alert badge)</option>
              <option value="urgent">Urgent (Red priority alert banner)</option>
            </select>
          </div>

          <div className="input-group">
            <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>Message Details *</label>
            <textarea
              className="input"
              rows={4}
              required
              placeholder="Write the clear announcement message for all student applicants..."
              value={form.message}
              onChange={e => setForm(f => ({ ...f, message: e.target.value }))}
              style={{ resize: 'vertical' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-3)', marginTop: 'var(--space-2)' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Broadcasting...' : '📢 Broadcast Announcement'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Drive Card ────────────────────────────────────────────────────
function DriveCard({ drive, onViewShortlist, onEdit, onReviewApplicants, onAnnouncement }) {
  const companyName = drive.company?.name || drive.company || 'Unknown Company';
  const location = drive.company?.location || drive.location || 'Remote / Multiple';
  const roles = drive.roles_offered?.length > 0 ? drive.roles_offered.join(', ') : drive.title;
  const statusKey = drive.status || 'open';
  const sc = STATUS_CFG[statusKey] || STATUS_CFG.open;

  const registered = drive.registered_count ?? drive.registered ?? 0;
  const shortlisted = drive.shortlisted_count ?? drive.shortlisted ?? 0;
  const selected = drive.selected_count ?? drive.selected ?? 0;

  const deadlineStr = drive.registration_deadline
    ? drive.registration_deadline.split('T')[0]
    : drive.deadline || 'TBA';
  const driveDateStr = drive.drive_date || 'TBA';
  const depts = drive.eligible_departments?.length > 0 ? drive.eligible_departments.join(', ') : 'All Branches';

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 'var(--font-size-lg)' }}>{companyName}</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)', marginTop: 2 }}>
            {roles} · 📍 {location} {drive.salary_ctc ? `· 💰 ₹${drive.salary_ctc} LPA` : ''}
          </div>
        </div>
        <span style={{
          padding: '4px 14px', borderRadius: 999,
          fontSize: 'var(--font-size-xs)', fontWeight: 600,
          background: sc.bg, color: sc.color,
        }}>
          ● {sc.label}
        </span>
      </div>

      {drive.description && (
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
          {drive.description}
        </p>
      )}

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-3)' }}>
        {[
          { label: 'Registered', value: registered, color: '#6366f1' },
          { label: 'Shortlisted', value: shortlisted, color: '#f59e0b' },
          { label: 'Selected / Hired', value: selected, color: '#22c55e' },
        ].map(s => (
          <div key={s.label} style={{ textAlign: 'center', padding: 'var(--space-3)', background: 'var(--bg-tertiary)', borderRadius: 'var(--border-radius-sm)' }}>
            <div style={{ fontWeight: 700, fontSize: 'var(--font-size-lg)', color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Meta tags */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-4)', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
        <span>📅 Deadline: <strong style={{ color: 'var(--text-secondary)' }}>{deadlineStr}</strong></span>
        <span>🏢 Drive Date: <strong style={{ color: 'var(--text-secondary)' }}>{driveDateStr}</strong></span>
        {drive.min_cgpa && <span>📊 Min CGPA: <strong style={{ color: 'var(--text-secondary)' }}>{drive.min_cgpa}</strong></span>}
        <span>🎓 Eligible: <strong style={{ color: 'var(--text-secondary)' }}>{depts}</strong></span>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-3)', marginTop: 'var(--space-2)' }}>
        <button
          className="btn btn-primary"
          style={{ height: 34, fontSize: 'var(--font-size-xs)' }}
          onClick={() => onReviewApplicants(drive)}
        >
          👥 Review Applicants
        </button>
        <Link
          to={`/tpo/drives/${drive.id}`}
          className="btn btn-secondary"
          style={{ height: 34, fontSize: 'var(--font-size-xs)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}
        >
          📋 Logistics & Roster
        </Link>
        <button
          className="btn btn-secondary"
          style={{ height: 34, fontSize: 'var(--font-size-xs)' }}
          onClick={() => onAnnouncement(drive)}
        >
          📢 Announce
        </button>
        <button
          className="btn btn-secondary"
          style={{ height: 34, fontSize: 'var(--font-size-xs)' }}
          onClick={() => onViewShortlist(drive)}
        >
          Shortlist {shortlisted > 0 ? `(${shortlisted})` : ''}
        </button>
        <button
          className="btn btn-secondary"
          style={{ height: 34, fontSize: 'var(--font-size-xs)' }}
          onClick={() => onEdit(drive)}
        >
          ✏️ Edit
        </button>
      </div>
    </div>
  );
}

// ─── Main TPO Drives Component ─────────────────────────────────────
export default function TPODrives() {
  const [drives, setDrives] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [showCreate, setShowCreate] = useState(false);
  const [editingDrive, setEditingDrive] = useState(null);
  const [shortlistDrive, setShortlistDrive] = useState(null);
  const [reviewingDrive, setReviewingDrive] = useState(null);
  const [announcementDrive, setAnnouncementDrive] = useState(null);
  const [toastMsg, setToastMsg] = useState(null);

  const fetchDrives = useCallback(async () => {
    try {
      setLoading(true);
      const params = filter !== 'all' ? { status: filter } : {};
      const res = await placementApi.getDrives(params);
      const list = res.data?.data || (Array.isArray(res.data) ? res.data : []);
      setDrives(list);
    } catch (err) {
      console.error('Failed to load placement drives:', err);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchDrives();
  }, [fetchDrives]);

  const counts = {
    total: drives.length,
    open: drives.filter(d => d.status === 'open').length,
    in_progress: drives.filter(d => d.status === 'in_progress').length,
    completed: drives.filter(d => d.status === 'completed').length,
  };

  return (
    <div>
      <div className="page-header">
        <h1>Placement Drives</h1>
        <p>Create, manage, and track candidate progress across institutional placement drives</p>
      </div>

      {toastMsg && (
        <div style={{
          padding: '10px 16px', borderRadius: 'var(--border-radius)',
          background: 'rgba(34,197,94,0.15)', color: '#22c55e',
          border: '1px solid rgba(34,197,94,0.4)', marginBottom: 'var(--space-4)',
          fontSize: 'var(--font-size-sm)', fontWeight: 500,
        }}>
          ✓ {toastMsg}
        </div>
      )}

      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>

        {/* Toolbar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-3)' }}>
          <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
            {['all', 'open', 'upcoming', 'in_progress', 'completed'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`btn ${filter === f ? 'btn-primary' : 'btn-secondary'}`}
                style={{ height: 34, fontSize: 'var(--font-size-xs)', textTransform: 'capitalize' }}
              >
                {f === 'all' ? 'All Drives' : f.replace('_', ' ')}
              </button>
            ))}
          </div>
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            + Create Drive
          </button>
        </div>

        {/* Summary KPI row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--space-4)' }}>
          {[
            { label: 'Total Drives Listed', value: counts.total, color: 'var(--accent-primary)' },
            { label: 'Open for Registration', value: counts.open, color: '#22c55e' },
            { label: 'Interviews in Progress', value: counts.in_progress, color: '#f59e0b' },
            { label: 'Completed Drives', value: counts.completed, color: 'var(--text-muted)' },
          ].map(s => (
            <div key={s.label} style={{
              padding: 'var(--space-4)',
              background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 'var(--border-radius)',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: 2 }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Drives list */}
        {loading ? (
          <div style={{ padding: 'var(--space-12)', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading placement drives...
          </div>
        ) : drives.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: 'var(--space-12)' }}>
            <div style={{ fontSize: '3rem', marginBottom: 'var(--space-3)' }}>🏢</div>
            <div style={{ fontWeight: 600, fontSize: 'var(--font-size-lg)', marginBottom: 'var(--space-2)' }}>
              No Placement Drives Found
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)', maxWidth: 440, margin: '0 auto var(--space-4)' }}>
              {filter !== 'all' ? `There are currently no drives with status "${filter}".` : 'No placement drives have been created yet.'}
            </p>
            <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
              Create First Drive
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            {drives.map(d => (
              <DriveCard
                key={d.id}
                drive={d}
                onViewShortlist={setShortlistDrive}
                onEdit={setEditingDrive}
                onReviewApplicants={setReviewingDrive}
                onAnnouncement={setAnnouncementDrive}
              />
            ))}
          </div>
        )}

      </div>

      {showCreate && (
        <CreateDriveModal
          onClose={() => setShowCreate(false)}
          onCreated={fetchDrives}
        />
      )}

      {editingDrive && (
        <EditDriveModal
          drive={editingDrive}
          onClose={() => setEditingDrive(null)}
          onUpdated={fetchDrives}
        />
      )}

      {shortlistDrive && (
        <ShortlistModal
          drive={shortlistDrive}
          onClose={() => setShortlistDrive(null)}
        />
      )}

      {reviewingDrive && (
        <DriveApplicantReviewer
          drive={reviewingDrive}
          onClose={() => setReviewingDrive(null)}
          onDriveUpdated={fetchDrives}
        />
      )}

      {announcementDrive && (
        <PostAnnouncementModal
          drive={announcementDrive}
          onClose={() => setAnnouncementDrive(null)}
          onPosted={() => {
            setToastMsg('Announcement posted! Broadcast notifications delivered to applicants.');
            setTimeout(() => setToastMsg(null), 4000);
          }}
        />
      )}
    </div>
  );
}
